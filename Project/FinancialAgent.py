from mesa import Agent
from Asset import Asset
from strategies import create_strategy


class FinancialAgent(Agent):

    """An agent with fixed initial wealth."""

    _AGENT_PREFIX = "Agent "

    def __init__(self, unique_id: int, model, wealth: int, strategy: str, mood: str):

        super().__init__(unique_id, model)

        self.wealth = wealth
        self.initial_wealth = wealth
        self.strategy = create_strategy(strategy, wealth)
        self.mood = mood
        self.history = []
        self.assets = []

        # Each agent starts with 1 unit of each asset defined in the market
        for asset_name in self.model.market.get_asset_names():
            self.assets.append(Asset(asset_name, 1))

        self.trades_completed = 0
        self.interactions = 0

        # Portfolio tracking
        self.fees_paid = 0.0

    @property
    def strategy_name(self):
        return self.strategy.name

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

            self.strategy.execute(self, other)

            self.history.append({'time': self.model.schedule.time,
                                 'activity': 'trade',
                                 'other': other.unique_id,
                                 'wealth': self.wealth,
                                 'other_wealth': other.wealth})

    # ---- Trade execution helpers (used by strategies) ----

    def execute_buy(self, other, asset):
        """Buy an asset from another agent at market price."""
        price = self.model.market.get_price(asset.name)
        self.assets.append(asset)
        other.assets.remove(asset)
        other.wealth += price
        self.wealth -= price

        self.model.market.submit_order(
            self.unique_id, asset.name, "bid", price)
        self.confirm_trade(other, asset)

    def execute_sell(self, other, asset):
        """Sell an asset to another agent at market price."""
        price = self.model.market.get_price(asset.name)
        other.assets.append(asset)
        self.assets.remove(asset)
        self.wealth += price
        other.wealth -= price

        self.model.market.submit_order(
            other.unique_id, asset.name, "ask", price)
        self.trades_completed += 1

    def print_interest(self, other, asset):
        print(self._AGENT_PREFIX + str(self.unique_id) + " is interested in trading for " +
              str(asset.name) + " with " + self._AGENT_PREFIX + str(other.unique_id) + ".")

    def confirm_trade(self, other, asset):
        asset_price = self.model.market.get_price(asset.name)
        print(self._AGENT_PREFIX + str(self.unique_id) + " traded " + str(asset.name) + " with " +
              self._AGENT_PREFIX + str(other.unique_id) + " for " + str(asset_price) + " units of wealth.")
        self.trades_completed += 1

    def set_strategy(self, strategy_name):
        self.strategy = create_strategy(strategy_name, self.initial_wealth)
