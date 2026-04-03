from mesa import Agent
import random
from Asset import Asset


class FinancialAgent(Agent):

    """An agent with fixed initial wealth."""

    _AGENT_PREFIX = "Agent "

    def __init__(self, unique_id: int, model, wealth: int, strategy: str, mood: str):

        super().__init__(unique_id, model)

        self.wealth = wealth
        self.initial_wealth = wealth
        self.strategy = strategy
        self.mood = mood
        self.history = []
        self.assets = []

        # Each agent starts with 1 unit of each asset defined in the market
        for asset_name in self.model.market.get_asset_names():
            self.assets.append(Asset(asset_name, 1))

        self.mean_reversion_threshold = 0.2
        self.trades_completed = 0
        self.interactions = 0

        # --- Smart agent state ---

        # Risk Averse: tracks recent wealth changes over a sliding window
        self.wealth_history = [wealth]
        self.risk_window = 10
        self.fear_level = 0.0  # 0 = calm, 1 = maximum fear

        # Copycat: remembers which strategy it copied and when
        self.original_strategy = strategy
        self.copy_cooldown = 0

        # Adaptive (Q-learning): learns which action works best
        # States: "winning" (wealth > initial), "losing" (wealth < initial), "neutral"
        # Actions: "buy", "sell", "hold"
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.2  # exploration rate
        self.last_state = None
        self.last_action = None
        self.last_wealth = wealth

        # Portfolio tracking
        self.fees_paid = 0.0

    @property
    def net_worth(self):
        """Cash + market value of all held assets."""
        asset_value = sum(
            self.model.market.get_price(a.name) * a.quantity
            for a in self.assets
        )
        return self.wealth + asset_value

    def _pay_fee(self, trade_value):
        """Deduct transaction fee from wealth. Returns the fee paid."""
        fee = self.model.market.calculate_fee(trade_value)
        self.wealth -= fee
        self.fees_paid += fee
        return fee

    def step(self):
        """A model step. Move, then trade with neighbors."""
        self.move()
        if self.wealth > 0:
            self.trade()

    def move(self):
        """Move the agent to a random empty cell."""
        old_pos = self.pos

        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )

        new_pos = self.random.choice(possible_steps)
        self.model.grid.move_agent(self, new_pos)

        self.history.append({'time': self.model.schedule.time,
                             'activity': 'move',
                             'old_pos': old_pos,
                             'new_pos': new_pos})

    def trade(self):
        """Trade with a random agent in the same cell."""
        cellmates = self.model.grid.get_cell_list_contents([self.pos])

        if len(cellmates) > 1:
            other = self.random.choice(cellmates)

            while (other.unique_id == self.unique_id):
                other = self.random.choice(cellmates)

            self.interactions += 1

            if self.strategy == "Asset Trading":
                self.asset_trade(other)

            elif self.strategy == "Wealth Trading":
                self.wealth_trade(other)

            elif self.strategy == "Mean Reversion":
                self.mean_reversion(other)

            elif self.strategy == "Momentum":
                self.momentum_trade(other)

            elif self.strategy == "Copycat":
                self.copycat_trade(other)

            elif self.strategy == "Risk Averse":
                self.risk_averse_trade(other)

            elif self.strategy == "Adaptive":
                self.adaptive_trade(other)

            self.history.append({'time': self.model.schedule.time,
                                 'activity': 'trade',
                                 'other': other.unique_id,
                                 'wealth': self.wealth,
                                 'other_wealth': other.wealth})

    def asset_trade(self, other):
        if len(other.assets) > 0:
            asset_to_trade = self.random.choice(other.assets)
            asset_price = self.model.market.get_price(asset_to_trade.name)
            fee = self.model.market.transaction_cost * asset_price

            if self.wealth >= asset_price + fee:
                self.assets.append(asset_to_trade)
                other.assets.remove(asset_to_trade)
                other.wealth += asset_price
                self.wealth -= asset_price
                self._pay_fee(asset_price)

                self.model.market.submit_order(
                    self.unique_id, asset_to_trade.name, "bid", asset_price)

                self.confirm_trade(other, asset_to_trade)

    def wealth_trade(self, other):
        if other.wealth > 0 and self.wealth >= 1:
            wealth_to_trade = self.random.randint(1, int(self.wealth))

            if self.wealth >= wealth_to_trade:
                other.wealth += wealth_to_trade
                self.wealth -= wealth_to_trade

                print(self._AGENT_PREFIX + str(self.unique_id) + " traded " + str(wealth_to_trade) +
                      " units of wealth with " + self._AGENT_PREFIX + str(other.unique_id) + ".")

                self.trades_completed += 1

    def mean_reversion(self, other):
        """Implements mean reversion strategy using shared market prices."""
        if len(other.assets) > 0:
            asset_to_trade = self.random.choice(other.assets)

            self.print_interest(other, asset_to_trade)

            asset_price = self.model.market.get_price(asset_to_trade.name)
            mean_price = self.model.market.get_mean_price(asset_to_trade.name)
            price_difference = asset_price - mean_price

            if abs(price_difference) > self.mean_reversion_threshold:
                if self.wealth >= asset_price and asset_to_trade in other.assets:
                    self.assets.append(asset_to_trade)
                    other.assets.remove(asset_to_trade)
                    other.wealth += asset_price
                    self.wealth -= asset_price

                    # Submit order to market
                    self.model.market.submit_order(
                        self.unique_id, asset_to_trade.name, "bid", asset_price)

                    self.confirm_trade(other, asset_to_trade)

    def momentum_trade(self, other):
        """Implements momentum strategy using shared market trends."""
        if len(other.assets) > 0:
            asset_to_trade = self.random.choice(other.assets)

            self.print_interest(other, asset_to_trade)

            asset_price = self.model.market.get_price(asset_to_trade.name)
            asset_trend = self.model.market.get_asset_trend(asset_to_trade.name)

            # Buy on uptrend
            if asset_trend == 'up' and self.wealth >= asset_price:
                self.assets.append(asset_to_trade)
                other.assets.remove(asset_to_trade)
                other.wealth += asset_price
                self.wealth -= asset_price

                self.model.market.submit_order(
                    self.unique_id, asset_to_trade.name, "bid", asset_price)

                self.confirm_trade(other, asset_to_trade)

            # Sell on downtrend
            elif asset_trend == 'down' and other.wealth >= asset_price and len(self.assets) > 0:
                asset_to_sell = self.random.choice(self.assets)
                sell_price = self.model.market.get_price(asset_to_sell.name)

                other.assets.append(asset_to_sell)
                self.assets.remove(asset_to_sell)
                self.wealth += sell_price
                other.wealth -= sell_price

                self.model.market.submit_order(
                    other.unique_id, asset_to_sell.name, "ask", sell_price)

                self.trades_completed += 1

    # ---- COPYCAT STRATEGY ----

    def copycat_trade(self, other):
        """Observe neighbors, copy the wealthiest one's strategy, then trade using it."""
        # Every 5 steps, look around and potentially switch strategy
        if self.copy_cooldown <= 0:
            neighbors = self.model.grid.get_neighbors(
                self.pos, moore=True, include_center=False, radius=2)
            if neighbors:
                wealthiest = max(neighbors, key=lambda a: a.wealth)
                if wealthiest.wealth > self.wealth and wealthiest.strategy != "Copycat":
                    self.strategy = wealthiest.strategy
                    self.copy_cooldown = 5
        else:
            self.copy_cooldown -= 1

        # Execute using the copied strategy
        if self.strategy == "Copycat":
            # Fallback: do asset trading if no strategy copied yet
            self.asset_trade(other)
        elif self.strategy == "Asset Trading":
            self.asset_trade(other)
        elif self.strategy == "Wealth Trading":
            self.wealth_trade(other)
        elif self.strategy == "Mean Reversion":
            self.mean_reversion(other)
        elif self.strategy == "Momentum":
            self.momentum_trade(other)
        elif self.strategy == "Risk Averse":
            self.risk_averse_trade(other)

        # Always reset strategy label to Copycat for visualization
        self.strategy = "Copycat"

    # ---- RISK AVERSE STRATEGY ----

    def _update_fear(self):
        """Update wealth history, fear level, and mood."""
        self.wealth_history.append(self.wealth)
        if len(self.wealth_history) > self.risk_window:
            self.wealth_history = self.wealth_history[-self.risk_window:]

        if len(self.wealth_history) >= 2:
            recent_change = self.wealth - self.wealth_history[0]
            if recent_change < 0:
                self.fear_level = min(1.0, abs(recent_change) / max(self.initial_wealth, 1))
            else:
                self.fear_level = max(0.0, self.fear_level - 0.1)

        if self.fear_level > 0.7:
            self.mood = "fearful"
        elif self.fear_level > 0.3:
            self.mood = "cautious"
        else:
            self.mood = "confident"

    def _risk_averse_buy(self, other, asset_to_trade, asset_price, mean_price):
        """Buy if price is at or below mean (conservative)."""
        if asset_price <= mean_price and self.wealth >= asset_price:
            self.assets.append(asset_to_trade)
            other.assets.remove(asset_to_trade)
            other.wealth += asset_price
            self.wealth -= asset_price

            self.model.market.submit_order(
                self.unique_id, asset_to_trade.name, "bid", asset_price)
            self.confirm_trade(other, asset_to_trade)
            return True
        return False

    def _risk_averse_sell(self, other, mean_price):
        """Sell if price is well above mean (take profit)."""
        if len(self.assets) == 0:
            return
        asset_to_sell = self.random.choice(self.assets)
        sell_price = self.model.market.get_price(asset_to_sell.name)

        if other.wealth >= sell_price:
            other.assets.append(asset_to_sell)
            self.assets.remove(asset_to_sell)
            self.wealth += sell_price
            other.wealth -= sell_price

            self.model.market.submit_order(
                other.unique_id, asset_to_sell.name, "ask", sell_price)
            self.trades_completed += 1

    def risk_averse_trade(self, other):
        """Trade conservatively — reduce activity when losing wealth."""
        self._update_fear()

        # Fear makes agent skip trades probabilistically
        if random.random() < self.fear_level:
            return

        if len(other.assets) == 0:
            return

        asset_to_trade = self.random.choice(other.assets)
        asset_price = self.model.market.get_price(asset_to_trade.name)
        mean_price = self.model.market.get_mean_price(asset_to_trade.name)

        if not self._risk_averse_buy(other, asset_to_trade, asset_price, mean_price):
            if asset_price > mean_price * 1.2:
                self._risk_averse_sell(other, mean_price)

    # ---- ADAPTIVE (Q-LEARNING) STRATEGY ----

    def _get_state(self):
        """Discretize the current state for Q-learning."""
        # Wealth relative to initial
        if self.wealth > self.initial_wealth * 1.1:
            wealth_state = "winning"
        elif self.wealth < self.initial_wealth * 0.9:
            wealth_state = "losing"
        else:
            wealth_state = "neutral"

        # Market trend (use first asset as proxy)
        asset_names = self.model.market.get_asset_names()
        if asset_names:
            trend = self.model.market.get_asset_trend(asset_names[0])
        else:
            trend = "stable"

        # Asset count relative to starting
        n_assets = len(self.assets)
        n_market = len(asset_names)
        if n_assets > n_market:
            asset_state = "heavy"
        elif n_assets < n_market:
            asset_state = "light"
        else:
            asset_state = "balanced"

        return (wealth_state, trend, asset_state)

    def _get_q(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def _choose_action(self, state):
        """Epsilon-greedy action selection."""
        actions = ["buy", "sell", "hold"]
        if random.random() < self.epsilon:
            return random.choice(actions)
        q_values = {a: self._get_q(state, a) for a in actions}
        return max(q_values, key=q_values.get)

    def _update_q(self, reward):
        """Update Q-value for the last state-action pair."""
        if self.last_state is None or self.last_action is None:
            return
        current_state = self._get_state()
        actions = ["buy", "sell", "hold"]
        best_future = max(self._get_q(current_state, a) for a in actions)
        old_q = self._get_q(self.last_state, self.last_action)
        new_q = old_q + self.learning_rate * (
            reward + self.discount_factor * best_future - old_q)
        self.q_table[(self.last_state, self.last_action)] = new_q

    def adaptive_trade(self, other):
        """Q-learning agent that learns buy/sell/hold from experience."""
        # Calculate reward from last action
        reward = self.wealth - self.last_wealth
        self._update_q(reward)
        self.last_wealth = self.wealth

        # Choose action
        state = self._get_state()
        action = self._choose_action(state)

        self.last_state = state
        self.last_action = action

        if action == "buy" and len(other.assets) > 0:
            asset_to_trade = self.random.choice(other.assets)
            asset_price = self.model.market.get_price(asset_to_trade.name)

            if self.wealth >= asset_price:
                self.assets.append(asset_to_trade)
                other.assets.remove(asset_to_trade)
                other.wealth += asset_price
                self.wealth -= asset_price

                self.model.market.submit_order(
                    self.unique_id, asset_to_trade.name, "bid", asset_price)
                self.confirm_trade(other, asset_to_trade)

        elif action == "sell" and len(self.assets) > 0:
            asset_to_sell = self.random.choice(self.assets)
            sell_price = self.model.market.get_price(asset_to_sell.name)

            if other.wealth >= sell_price:
                other.assets.append(asset_to_sell)
                self.assets.remove(asset_to_sell)
                self.wealth += sell_price
                other.wealth -= sell_price

                self.model.market.submit_order(
                    other.unique_id, asset_to_sell.name, "ask", sell_price)
                self.trades_completed += 1

        # action == "hold": do nothing — agent waits for better conditions

    def print_interest(self, other, asset):
        print(self._AGENT_PREFIX + str(self.unique_id) + " is interested in trading for " +
              str(asset.get_name()) + " with Agent " + str(other.unique_id) + ".")

    def confirm_trade(self, other, asset):
        asset_price = self.model.market.get_price(asset.name)
        print(self._AGENT_PREFIX + str(self.unique_id) + " traded " + str(asset.get_name()) + " with Agent " +
              str(other.unique_id) + " for " + str(asset_price) + " units of wealth.")
        self.trades_completed += 1

    def add_asset(self, asset):
        self.assets.append(asset)

    def get_assets(self):
        return self.assets

    def get_strategy(self):
        return self.strategy

    def get_mood(self):
        return self.mood

    def get_wealth(self):
        return self.wealth

    def get_history(self):
        return self.history

    def get_unique_id(self):
        return self.unique_id

    def get_pos(self):
        return self.pos

    def get_asset_names(self):
        return [asset.get_name() for asset in self.assets]

    def set_treshold(self, mean_reversion_threshold):
        self.mean_reversion_threshold = mean_reversion_threshold

    def get_threshold(self):
        return self.mean_reversion_threshold

    def set_mood(self, mood):
        self.mood = mood

    def set_strategy(self, strategy):
        self.strategy = strategy

    def set_wealth(self, wealth):
        self.wealth = wealth

    def set_pos(self, pos):
        self.pos = pos
