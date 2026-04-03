from abc import ABC, abstractmethod
import random


class TradingStrategy(ABC):
    """Base class for all trading strategies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name used for visualization and data collection."""

    @abstractmethod
    def execute(self, agent, other):
        """Execute one trade interaction between agent and other."""


class AssetTradingStrategy(TradingStrategy):
    name = "Asset Trading"

    def execute(self, agent, other):
        if len(other.assets) > 0:
            asset = agent.random.choice(other.assets)
            price = agent.model.market.get_price(asset.name)
            fee = agent.model.market.transaction_cost * price

            if agent.wealth >= price + fee:
                agent.execute_buy(other, asset)
                agent._pay_fee(price)


class WealthTradingStrategy(TradingStrategy):
    name = "Wealth Trading"

    def execute(self, agent, other):
        if other.wealth > 0 and agent.wealth >= 1:
            amount = agent.random.randint(1, int(agent.wealth))

            if agent.wealth >= amount:
                other.wealth += amount
                agent.wealth -= amount

                print(agent._AGENT_PREFIX + str(agent.unique_id) + " traded " +
                      str(amount) + " units of wealth with " +
                      agent._AGENT_PREFIX + str(other.unique_id) + ".")

                agent.trades_completed += 1


class MeanReversionStrategy(TradingStrategy):
    name = "Mean Reversion"

    def __init__(self, threshold=0.2):
        self.threshold = threshold

    def execute(self, agent, other):
        if len(other.assets) > 0:
            asset = agent.random.choice(other.assets)
            agent.print_interest(other, asset)

            price = agent.model.market.get_price(asset.name)
            mean = agent.model.market.get_mean_price(asset.name)

            if abs(price - mean) > self.threshold:
                if agent.wealth >= price and asset in other.assets:
                    agent.execute_buy(other, asset)


class MomentumStrategy(TradingStrategy):
    name = "Momentum"

    def execute(self, agent, other):
        if len(other.assets) == 0:
            return

        asset = agent.random.choice(other.assets)
        agent.print_interest(other, asset)

        price = agent.model.market.get_price(asset.name)
        trend = agent.model.market.get_asset_trend(asset.name)

        if trend == 'up' and agent.wealth >= price:
            agent.execute_buy(other, asset)
        elif trend == 'down' and other.wealth >= price and len(agent.assets) > 0:
            asset_to_sell = agent.random.choice(agent.assets)
            agent.execute_sell(other, asset_to_sell)


class CopycatStrategy(TradingStrategy):
    name = "Copycat"

    def __init__(self, initial_wealth):
        self.copy_cooldown = 0
        self.copied_strategy_name = None
        # Own instances so stateful strategies maintain independent state
        self._fallbacks = {
            "Asset Trading": AssetTradingStrategy(),
            "Wealth Trading": WealthTradingStrategy(),
            "Mean Reversion": MeanReversionStrategy(),
            "Momentum": MomentumStrategy(),
            "Risk Averse": RiskAverseStrategy(initial_wealth),
            "Adaptive": AdaptiveStrategy(initial_wealth),
        }

    def execute(self, agent, other):
        if self.copy_cooldown <= 0:
            neighbors = agent.model.grid.get_neighbors(
                agent.pos, moore=True, include_center=False, radius=2)
            if neighbors:
                wealthiest = max(neighbors, key=lambda a: a.wealth)
                if (wealthiest.wealth > agent.wealth
                        and wealthiest.strategy.name != "Copycat"):
                    self.copied_strategy_name = wealthiest.strategy.name
                    self.copy_cooldown = 5
        else:
            self.copy_cooldown -= 1

        strategy = self._fallbacks.get(self.copied_strategy_name)
        if strategy:
            strategy.execute(agent, other)
        else:
            self._fallbacks["Asset Trading"].execute(agent, other)


class RiskAverseStrategy(TradingStrategy):
    name = "Risk Averse"

    def __init__(self, initial_wealth):
        self.wealth_history = [initial_wealth]
        self.risk_window = 10
        self.fear_level = 0.0
        self.initial_wealth = initial_wealth

    def _update_fear(self, agent):
        self.wealth_history.append(agent.wealth)
        if len(self.wealth_history) > self.risk_window:
            self.wealth_history = self.wealth_history[-self.risk_window:]

        if len(self.wealth_history) >= 2:
            recent_change = agent.wealth - self.wealth_history[0]
            if recent_change < 0:
                self.fear_level = min(
                    1.0, abs(recent_change) / max(self.initial_wealth, 1))
            else:
                self.fear_level = max(0.0, self.fear_level - 0.1)

        if self.fear_level > 0.7:
            agent.mood = "fearful"
        elif self.fear_level > 0.3:
            agent.mood = "cautious"
        else:
            agent.mood = "confident"

    def execute(self, agent, other):
        self._update_fear(agent)

        if random.random() < self.fear_level:
            return

        if len(other.assets) == 0:
            return

        asset = agent.random.choice(other.assets)
        price = agent.model.market.get_price(asset.name)
        mean = agent.model.market.get_mean_price(asset.name)

        if price <= mean and agent.wealth >= price:
            agent.execute_buy(other, asset)
        elif price > mean * 1.2 and len(agent.assets) > 0:
            asset_to_sell = agent.random.choice(agent.assets)
            sell_price = agent.model.market.get_price(asset_to_sell.name)
            if other.wealth >= sell_price:
                agent.execute_sell(other, asset_to_sell)


class AdaptiveStrategy(TradingStrategy):
    name = "Adaptive"

    def __init__(self, initial_wealth):
        self.q_table = {}
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.epsilon = 0.2
        self.last_state = None
        self.last_action = None
        self.last_wealth = initial_wealth

    def _get_state(self, agent):
        initial = agent.initial_wealth
        if agent.wealth > initial * 1.1:
            wealth_state = "winning"
        elif agent.wealth < initial * 0.9:
            wealth_state = "losing"
        else:
            wealth_state = "neutral"

        asset_names = agent.model.market.get_asset_names()
        trend = (agent.model.market.get_asset_trend(asset_names[0])
                 if asset_names else "stable")

        n_assets = len(agent.assets)
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
        actions = ["buy", "sell", "hold"]
        if random.random() < self.epsilon:
            return random.choice(actions)
        q_values = {a: self._get_q(state, a) for a in actions}
        return max(q_values, key=q_values.get)

    def _update_q(self, agent, reward):
        if self.last_state is None or self.last_action is None:
            return
        current_state = self._get_state(agent)
        actions = ["buy", "sell", "hold"]
        best_future = max(self._get_q(current_state, a) for a in actions)
        old_q = self._get_q(self.last_state, self.last_action)
        new_q = old_q + self.learning_rate * (
            reward + self.discount_factor * best_future - old_q)
        self.q_table[(self.last_state, self.last_action)] = new_q

    def execute(self, agent, other):
        reward = agent.wealth - self.last_wealth
        self._update_q(agent, reward)
        self.last_wealth = agent.wealth

        state = self._get_state(agent)
        action = self._choose_action(state)
        self.last_state = state
        self.last_action = action

        if action == "buy" and len(other.assets) > 0:
            asset = agent.random.choice(other.assets)
            price = agent.model.market.get_price(asset.name)
            if agent.wealth >= price:
                agent.execute_buy(other, asset)
        elif action == "sell" and len(agent.assets) > 0:
            asset = agent.random.choice(agent.assets)
            sell_price = agent.model.market.get_price(asset.name)
            if other.wealth >= sell_price:
                agent.execute_sell(other, asset)


STRATEGY_NAMES = [
    "Asset Trading", "Wealth Trading", "Mean Reversion", "Momentum",
    "Copycat", "Risk Averse", "Adaptive"
]

STRATEGY_COLORS = {
    "Asset Trading": "#2ecc71",     # green
    "Wealth Trading": "#3498db",    # blue
    "Mean Reversion": "#e67e22",    # orange
    "Momentum": "#9b59b6",          # purple
    "Copycat": "#e74c3c",           # red
    "Risk Averse": "#1abc9c",       # teal
    "Adaptive": "#f39c12",          # amber
}

STRATEGY_ABBREV = {
    "Asset Trading": "AT",
    "Wealth Trading": "WT",
    "Mean Reversion": "MR",
    "Momentum": "MM",
    "Copycat": "CC",
    "Risk Averse": "RA",
    "Adaptive": "AD",
}


def create_strategy(name, initial_wealth):
    """Factory function to create a strategy instance by name."""
    strategies = {
        "Asset Trading": lambda: AssetTradingStrategy(),
        "Wealth Trading": lambda: WealthTradingStrategy(),
        "Mean Reversion": lambda: MeanReversionStrategy(),
        "Momentum": lambda: MomentumStrategy(),
        "Copycat": lambda: CopycatStrategy(initial_wealth),
        "Risk Averse": lambda: RiskAverseStrategy(initial_wealth),
        "Adaptive": lambda: AdaptiveStrategy(initial_wealth),
    }
    return strategies[name]()
