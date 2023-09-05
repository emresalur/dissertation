from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.modules import BarChartModule, PieChartModule, NetworkModule, HexGridVisualization
from mesa.visualization.ModularVisualization import ModularServer, VisualizationElement
from mesa.visualization.UserParam import UserSettableParameter
from FinancialModel import FinancialModel
from FinancialAgent import FinancialAgent
import numpy as np
import matplotlib.pyplot as plt


class CustomCSS(VisualizationElement):
    package_includes = ["newstyle.css"]
    local_includes = ["newstyle.css"]


NUMBER_OF_CELLS = 10

NUMBER_OF_CELLS_X = 10

NUMBER_OF_CELLS_Y = 10

SIZE_OF_CANVAS_IN_PIXELS_X = 700

SIZE_OF_CANVAS_IN_PIXELS_Y = 700

simulation_params = {
    "number_of_agents": UserSettableParameter(
        "slider",
        "Number of agents",
        10,  #  default
        1,  # min
        20,  # max
        1,  # step
        description="Choose how many agents to include in the simulation.",
    ),

    "strategy": UserSettableParameter(
        "choice",
        "Trading Strategy",
        value="Asset Trading",  # default
        choices=["Asset Trading", "Wealth Trading",
                 "Mean Reversion", "Momentum"],
        description="Choose the trading strategy for the agents.",
    ),

    "initial_wealth": UserSettableParameter(
        "slider",
        "Initial Wealth",
        10,  # default
        1,  # min
        20,  # max
        1,  # step
        description="Choose the initial wealth of the agents.",
    ),

    "width": UserSettableParameter(
        "slider",
        "Width",
        10,  # default
        1,  # min
        20,  # max
        1,  # step
        description="Choose the width of the grid.",
    ),

    "height": UserSettableParameter(
        "slider",
        "Height",
        10,  # default
        1,  # min
        20,  # max
        1,  # step
        description="Choose the height of the grid.",
    )

}


def wealth_to_radius(wealth):
    """Maps the agent's wealth to a radius size."""
    return 0.1 + wealth * 0.03  # add 0.1 to make sure the minimum radius is 0.5


def agent_portrayal(agent):
    """Returns the portrayal of the given agent."""

    radius = wealth_to_radius(agent.wealth)

    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "r": radius,
        "Layer": 0 if agent.wealth > 0 else 1,
        "Color": "green",
        "text": agent.unique_id,
        "text_color": "black",
    }

    # Determine the agent's color based on its wealth
    if agent.wealth > 0:

        # Highlight the wealthiest agent after 10 steps
        if agent.wealth == agent.model.get_wealthiest_agent() and agent.model.schedule.time > 10:

            portrayal["Color"] = "gold"
            portrayal["Layer"] = 2
        else:

            portrayal["Color"] = "green"

        portrayal["Layer"] = 0

    # If the agent has no wealth, make it red
    else:

        portrayal["Color"] = "red"
        portrayal["Layer"] = 1

    return portrayal


chart_currents = PieChartModule(
    [
        {"Label": "Wealthy Agents", "Color": "Green"},
        {"Label": "Non Wealthy Agents", "Color": "Red"},
    ],

    data_collector_name="datacollector_currents",

)

wealthiest_agent = ChartModule(
    [
        {"Label": "Wealthiest Agent", "Color": "Purple"},
    ],

    data_collector_name="datacollector_wealthiest_agent",

    canvas_height=150,
    canvas_width=400

)

gini = ChartModule(
    [
        {"Label": "Gini", "Color": "Navy"},
    ],

    data_collector_name="datacollector_gini"
)

total_wealth = ChartModule(
    [
        {"Label": "Total Wealth", "Color": "Cyan"},
    ],

    data_collector_name="datacollector_total_wealth"
)

total_transactions = ChartModule(
    [
        {"Label": "Total Trades", "Color": "Orange"},
    ],

    data_collector_name="datacollector_trades"
)

total_interactions = ChartModule(
    [
        {"Label": "Total Interactions", "Color": "Pink"},
    ],

    data_collector_name="datacollector_interactions"
)

agent_wealth_labels_and_colors = [{"Label": f"Agent {i}", "Color": "blue"} for i in range(simulation_params["number_of_agents"].value)]

agent_wealth_chart = BarChartModule(agent_wealth_labels_and_colors,
                                    scope="agent",
                                    data_collector_name="datacollector_agent_wealth",
                                    canvas_height=300,
                                    canvas_width=1000)

# Create the grid with the user defined parameters
grid = CanvasGrid(agent_portrayal, simulation_params["width"].value,
                  simulation_params["height"].value, SIZE_OF_CANVAS_IN_PIXELS_X, SIZE_OF_CANVAS_IN_PIXELS_Y)

server = ModularServer(FinancialModel,
                       [grid,
                       chart_currents,                    
                        wealthiest_agent,
                        gini,
                        total_wealth,
                        total_transactions,
                        total_interactions,
                        CustomCSS()],
                       "Financial Model",
                       simulation_params,
                       8523)

server.launch()
