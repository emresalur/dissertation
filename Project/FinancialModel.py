from mesa import Model
from FinancialAgent import FinancialAgent
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from Market import Market
from MarketEvent import MarketEvent
from strategies import STRATEGY_NAMES
import numpy as np


STRATEGIES = STRATEGY_NAMES

PREDEFINED_EVENTS = {
    "Market Crash": {"event_type": "crash", "magnitude": 0.5, "duration": 10},
    "Bull Run": {"event_type": "boom", "magnitude": 1.8, "duration": 15},
    "High Volatility": {"event_type": "volatility_spike", "magnitude": 0.15, "duration": 20},
}


class FinancialModel(Model):

    """A model with some number of agents."""

    def __init__(self, number_of_agents, width, height, strategy_mode,
                 initial_wealth, asset_config="Gold:10,Silver:5",
                 event_mode="None"):

        self.num_agents = number_of_agents

        self.grid = MultiGrid(width, height, True)

        self.strategy_mode = strategy_mode

        self.schedule = RandomActivation(self)

        if self.num_agents > self.grid.width * self.grid.height:
            print("Number of agents is bigger than the number of cells. "
                  "Reducing to " + str(self.grid.width * self.grid.height) + ".")
            self.num_agents = self.grid.width * self.grid.height

        # Initialize the market with configurable assets
        self.market = Market(self._parse_asset_config(asset_config))

        # Create agents (each gets a strategy based on strategy_mode)
        self.create_agents(self.num_agents, initial_wealth)

        # Setup market events
        self.events = []
        self._setup_events(event_mode)

        # Initialize data collectors
        self.initalize_data_collectors()

        self.trades_completed = 0
        self.total_wealth = self.compute_total_wealth()

    def _parse_asset_config(self, config_str):
        """Parse 'Gold:10,Silver:5' into list of dicts."""
        assets = []
        for item in config_str.split(","):
            parts = item.strip().split(":")
            if len(parts) == 2:
                assets.append({
                    "name": parts[0].strip(),
                    "initial_price": float(parts[1].strip())
                })
        return assets

    def _assign_strategy(self, agent_index):
        """Assign a strategy to an agent based on strategy_mode."""
        if self.strategy_mode in STRATEGIES:
            return self.strategy_mode
        elif self.strategy_mode == "Random Mix":
            return self.random.choice(STRATEGIES)
        elif self.strategy_mode == "Equal Distribution":
            return STRATEGIES[agent_index % len(STRATEGIES)]
        return "Asset Trading"

    def _setup_events(self, event_mode):
        """Activate a predefined market event if selected."""
        if event_mode != "None" and event_mode in PREDEFINED_EVENTS:
            cfg = PREDEFINED_EVENTS[event_mode]
            event = MarketEvent(
                name=event_mode,
                event_type=cfg["event_type"],
                magnitude=cfg["magnitude"],
                duration=cfg["duration"]
            )
            event.activate()
            self.events.append(event)

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()

        # Apply price fluctuations once per step (not per agent)
        self._apply_price_fluctuations()

        # Settle the order book for each asset
        for asset_name in self.market.get_asset_names():
            self.market.clear_orders(asset_name)

        # Close candles every 5 steps for OHLC chart
        if self.schedule.time > 0 and self.schedule.time % 5 == 0:
            for asset_name in self.market.get_asset_names():
                self.market.close_candle(asset_name)

        # Apply active market events
        self.events = [e for e in self.events if e.tick(self.market)]

        self.collect_data()

    def _apply_price_fluctuations(self):
        """Apply market-wide price fluctuations based on agent strategy distribution."""
        if self.schedule.time % 10 != 0 or self.schedule.time == 0:
            return

        # Count strategies in use
        mr_count = sum(1 for a in self.schedule.agents if a.strategy_name == "Mean Reversion")
        mm_count = sum(1 for a in self.schedule.agents if a.strategy_name == "Momentum")
        total = self.num_agents

        if total == 0:
            return

        # Weighted fluctuation based on strategy distribution
        fluctuation = 0.0
        if mr_count > 0:
            fluctuation += (-0.1) * (mr_count / total)
        if mm_count > 0:
            fluctuation += (0.05) * (mm_count / total)

        if fluctuation != 0.0:
            for asset_name in self.market.get_asset_names():
                current = self.market.get_price(asset_name)
                self.market.update_price(asset_name, current + fluctuation)

    def create_agents(self, number_of_agents, initial_wealth):
        for i in range(self.num_agents):
            strategy = self._assign_strategy(i)
            a = FinancialAgent(i, self, initial_wealth, strategy, "neutral")
            self.schedule.add(a)

            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)

            while not self.grid.is_cell_empty((x, y)):
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)

            self.grid.place_agent(a, (x, y))

    def agent_wealth_labels_and_colors(self):
        labels_and_colors = []
        for agent in self.schedule.agents:
            labels_and_colors.append(
                {"Label": f"Agent {agent.unique_id}", "Color": "blue"})
        return labels_and_colors

    def compute_gini(self):
        """Compute the Gini coefficient of the model."""
        agent_wealths = [agent.wealth for agent in self.schedule.agents]
        x = sorted(agent_wealths)
        N = self.num_agents
        total = sum(x)
        if N == 0 or total == 0:
            return 0
        B = sum(xi * (N - i) for i, xi in enumerate(x)) / (N * total)
        return (1 + (1 / N) - 2 * B)

    def get_wealthiest_agent(self):
        return max([agent.wealth for agent in self.schedule.agents])

    def compute_avg_wealth(self):
        return np.mean([agent.wealth for agent in self.schedule.agents])

    def current_wealthy_agents(self) -> int:
        return sum(1 for agent in self.schedule.agents if agent.wealth > 0)

    def current_non_wealthy_agents(self) -> int:
        return sum(1 for agent in self.schedule.agents if agent.wealth <= 0)

    def compute_total_wealth(self):
        return sum([agent.wealth for agent in self.schedule.agents])

    def compute_total_trades(self):
        return sum([agent.trades_completed for agent in self.schedule.agents])

    def compute_total_interactions(self):
        return sum([agent.interactions for agent in self.schedule.agents])

    def initalize_data_collectors(self):

        self.datacollector_gini = DataCollector(
            model_reporters={"Gini": self.compute_gini},
            agent_reporters={"Wealth": "wealth"}
        )

        self.datacollector_wealthiest_agent = DataCollector(
            model_reporters={"Wealthiest Agent": self.get_wealthiest_agent}
        )

        self.datacollector_currents = DataCollector(
            {
                "Wealthy Agents": self.current_wealthy_agents,
                "Non Wealthy Agents": self.current_non_wealthy_agents,
            }
        )

        self.datacollector_total_wealth = DataCollector(
            model_reporters={"Total Wealth": self.compute_total_wealth},
            agent_reporters={"Wealth": "wealth"}
        )

        self.datacollector_trades = DataCollector(
            model_reporters={"Total Trades": self.compute_total_trades},
            agent_reporters={"Trades": "trades_completed"}
        )

        self.datacollector_interactions = DataCollector(
            model_reporters={
                "Total Interactions": self.compute_total_interactions},
            agent_reporters={"Interactions": "interactions"}
        )

        self.datacollector_agent_wealth = DataCollector(
            agent_reporters={"Wealth": lambda a: a.wealth}
        )

        # Market price tracking
        market_reporters = {}
        for asset_name in self.market.get_asset_names():
            # Use default arg to capture asset_name in closure
            market_reporters[asset_name + " Price"] = (
                lambda m, name=asset_name: m.market.get_price(name)
            )
        self.datacollector_market_prices = DataCollector(
            model_reporters=market_reporters
        )

        # Strategy distribution tracking
        strategy_reporters = {}
        for strat in STRATEGIES:
            strategy_reporters[strat] = (
                lambda m, s=strat: sum(1 for a in m.schedule.agents if a.strategy_name == s)
            )
        self.datacollector_strategies = DataCollector(
            model_reporters=strategy_reporters
        )

    def collect_data(self):
        self.datacollector_gini.collect(self)
        self.datacollector_wealthiest_agent.collect(self)
        self.datacollector_currents.collect(self)
        self.datacollector_total_wealth.collect(self)
        self.datacollector_trades.collect(self)
        self.datacollector_interactions.collect(self)
        self.datacollector_agent_wealth.collect(self)
        self.datacollector_market_prices.collect(self)
        self.datacollector_strategies.collect(self)
