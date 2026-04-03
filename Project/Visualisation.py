from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.modules import BarChartModule, PieChartModule
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement
from mesa.visualization.UserParam import UserSettableParameter
from FinancialModel import FinancialModel
from FinancialAgent import FinancialAgent
from strategies import STRATEGY_COLORS, STRATEGY_ABBREV


class CustomCSS(VisualizationElement):
    package_includes = ["newstyle.css"]
    local_includes = ["newstyle.css"]


SIZE_OF_CANVAS_IN_PIXELS_X = 700
SIZE_OF_CANVAS_IN_PIXELS_Y = 700

simulation_params = {
    "number_of_agents": UserSettableParameter(
        "slider",
        "Number of agents",
        10,
        1,
        20,
        1,
        description="Choose how many agents to include in the simulation.",
    ),

    "strategy_mode": UserSettableParameter(
        "choice",
        "Strategy Mode",
        value="Asset Trading",
        choices=["Asset Trading", "Wealth Trading",
                 "Mean Reversion", "Momentum",
                 "Copycat", "Risk Averse", "Adaptive",
                 "Random Mix", "Equal Distribution"],
        description="Single strategy for all agents, or a distribution mode.",
    ),

    "initial_wealth": UserSettableParameter(
        "slider",
        "Initial Wealth",
        10,
        1,
        20,
        1,
        description="Choose the initial wealth of the agents.",
    ),

    "asset_config": UserSettableParameter(
        "choice",
        "Asset Configuration",
        value="Gold:10,Silver:5",
        choices=[
            "Gold:10,Silver:5",
            "Gold:10,Silver:5,Oil:20",
            "Gold:10,Silver:5,Oil:20,Bitcoin:100",
            "Stock_A:50,Stock_B:30,Stock_C:10",
        ],
        description="Choose which assets are available in the market.",
    ),

    "event_mode": UserSettableParameter(
        "choice",
        "Market Event",
        value="None",
        choices=["None", "Market Crash", "Bull Run", "High Volatility"],
        description="Trigger a market-wide event at simulation start.",
    ),

    "width": UserSettableParameter(
        "slider",
        "Width",
        10,
        1,
        20,
        1,
        description="Choose the width of the grid.",
    ),

    "height": UserSettableParameter(
        "slider",
        "Height",
        10,
        1,
        20,
        1,
        description="Choose the height of the grid.",
    )
}


def wealth_to_radius(wealth):
    """Maps the agent's wealth to a radius size."""
    return 0.1 + wealth * 0.03


def agent_portrayal(agent):
    """Returns the portrayal of the given agent."""

    radius = wealth_to_radius(agent.wealth)
    strategy = agent.strategy_name
    abbrev = STRATEGY_ABBREV.get(strategy, "?")
    color = STRATEGY_COLORS.get(strategy, "gray")

    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "r": radius,
        "Layer": 0,
        "Color": color,
        "text": f"{agent.unique_id}:{abbrev}",
        "text_color": "black",
    }

    if agent.wealth > 0:
        # Highlight the wealthiest agent after 10 steps
        if (agent.wealth == agent.model.get_wealthiest_agent()
                and agent.model.schedule.time > 10):
            portrayal["Color"] = "gold"
            portrayal["Layer"] = 2
    else:
        portrayal["Color"] = "red"
        portrayal["Layer"] = 1

    return portrayal


# Charts
chart_currents = PieChartModule(
    [
        {"Label": "Wealthy Agents", "Color": "Green"},
        {"Label": "Non Wealthy Agents", "Color": "Red"},
    ],
    data_collector_name="datacollector_currents",
)

wealthiest_agent = ChartModule(
    [{"Label": "Wealthiest Agent", "Color": "Purple"}],
    data_collector_name="datacollector_wealthiest_agent",
    canvas_height=150,
    canvas_width=400
)

gini = ChartModule(
    [{"Label": "Gini", "Color": "Navy"}],
    data_collector_name="datacollector_gini"
)

total_wealth = ChartModule(
    [{"Label": "Total Wealth", "Color": "Cyan"}],
    data_collector_name="datacollector_total_wealth"
)

total_transactions = ChartModule(
    [{"Label": "Total Trades", "Color": "Orange"}],
    data_collector_name="datacollector_trades"
)

total_interactions = ChartModule(
    [{"Label": "Total Interactions", "Color": "Pink"}],
    data_collector_name="datacollector_interactions"
)

# Market price chart — labels cover all possible assets across configs
market_prices = ChartModule(
    [
        {"Label": "Gold Price", "Color": "#f1c40f"},
        {"Label": "Silver Price", "Color": "#95a5a6"},
        {"Label": "Oil Price", "Color": "#2c3e50"},
        {"Label": "Bitcoin Price", "Color": "#e74c3c"},
        {"Label": "Stock_A Price", "Color": "#1abc9c"},
        {"Label": "Stock_B Price", "Color": "#8e44ad"},
        {"Label": "Stock_C Price", "Color": "#d35400"},
    ],
    data_collector_name="datacollector_market_prices",
    canvas_height=200,
    canvas_width=500
)

# Strategy distribution chart
strategy_chart = ChartModule(
    [
        {"Label": "Asset Trading", "Color": "#2ecc71"},
        {"Label": "Wealth Trading", "Color": "#3498db"},
        {"Label": "Mean Reversion", "Color": "#e67e22"},
        {"Label": "Momentum", "Color": "#9b59b6"},
        {"Label": "Copycat", "Color": "#e74c3c"},
        {"Label": "Risk Averse", "Color": "#1abc9c"},
        {"Label": "Adaptive", "Color": "#f39c12"},
    ],
    data_collector_name="datacollector_strategies",
    canvas_height=150,
    canvas_width=400
)

# Grid
grid = CanvasGrid(
    agent_portrayal,
    simulation_params["width"].value,
    simulation_params["height"].value,
    SIZE_OF_CANVAS_IN_PIXELS_X,
    SIZE_OF_CANVAS_IN_PIXELS_Y
)

server = ModularServer(
    FinancialModel,
    [grid,
     chart_currents,
     market_prices,
     strategy_chart,
     wealthiest_agent,
     gini,
     total_wealth,
     total_transactions,
     total_interactions,
     CustomCSS()],
    "Financial Model",
    simulation_params,
    8523
)

server.launch()
