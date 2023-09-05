from mesa import Model
from mesa.agent import Agent
from mesa.time import RandomActivation
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter


class Trader(Agent):
    def __init__(self, unique_id, model, wealth, price):
        super().__init__(unique_id, model)
        self.wealth = wealth
        self.price = price

    def step(self):
        # Buy behaviour
        if self.wealth > self.price:
            self.buy()

        # Sell behaviour
        if self.wealth < self.price:
            self.sell()

        # Movement behaviour
        x, y = self.pos
        dx, dy = self.random.choice([(-1, 0), (1, 0), (0, -1), (0, 1)])
        new_pos_x = (x + dx) % self.model.grid.width
        new_pos_y = (y + dy) % self.model.grid.height
        self.model.grid.move_agent(self, (new_pos_x, new_pos_y))

    def buy(self):
        # Find a seller with a lower price
        sellers = [
            agent for agent in self.model.schedule.agents if agent.price < self.price]
        if not sellers:
            return

        # Choose a seller at random
        seller = self.random.choice(sellers)

        # Transfer money between buyer and seller
        transfer_amount = min(self.wealth - self.price,
                              seller.price - seller.wealth)
        seller.wealth += transfer_amount

    def sell(self):
        # Find a buyer with a higher price
        buyers = [
            agent for agent in self.model.schedule.agents if agent.price > self.price]
        if not buyers:
            return

        # Choose a buyer at random
        buyer = self.random.choice(buyers)

        # Transfer money between buyer and seller
        transfer_amount = min(buyer.wealth - buyer.price,
                              self.price - self.wealth)
        buyer.wealth -= transfer_amount


class FinanceModel(Model):
    def __init__(self, N, width, height):
        self.num_agents = N
        self.grid = MultiGrid(width, height, True)
        self.schedule = RandomActivation(self)
        self.datacollector = DataCollector(
            model_reporters={"Total_Wealth": total_wealth},
            agent_reporters={"Wealth": lambda a: a.wealth})

        # Create agents
        for i in range(self.num_agents):
            a = Trader(i, self, self.random.randrange(
                1, 100), self.random.randrange(1, 100))
            self.schedule.add(a)

            # Add the agent to a random grid cell
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            self.grid.place_agent(a, (x, y))

    def step(self):
        self.datacollector.collect(self)
        self.schedule.step()


def total_wealth(model):
    total = 0
    for agent in model.schedule.agents:
        total += agent.wealth
    return total


model = FinanceModel(N=100, width=10, height=10)
for i in range(100):
    model.step()


def agent_portrayal(agent):
    portrayal = {"Shape": "circle",
                 "Filled": "true",
                 "r": 0.5,
                 "Layer": 0,
                 "Color": "red"}
    return portrayal


grid = CanvasGrid(agent_portrayal, 10, 10, 500, 500)

chart = ChartModule([{"Label": "Total_Wealth",
                      "Color": "Black"}],
                    data_collector_name='datacollector')

model_params = {
    "N": UserSettableParameter('slider', "Number of traders", 100, 1, 200),
    "width": 10,
    "height": 10
}

server = ModularServer(FinanceModel,
                       [grid, chart],
                       "Finance Model",
                       model_params)
server.port = 8521  # The default

server.launch()
