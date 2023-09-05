import mesa
from mesa import Agent, Model
from mesa.time import RandomActivation


class MoneyAgent(Agent):
    """ An agent with fixed initial wealth. """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.wealth = 1

    def step(self):
        # The step function should return nothing. It should update the agent's
        # internal state, and any of the state variables in the model.
        self.wealth += 1


class MoneyModel(Model):
    """ A model with some number of agents."""

    def __init__(self, N):
        self.num_agents = N
        self.schedule = mesa.time.RandomActivation(self)

        # Create agents
        for i in range(self.num_agents):
            a = MoneyAgent(i, self)
            self.schedule.add(a)

    def step(self):
        """Advance the model by one step."""
        self.schedule.step()


# Create a model with 5 agents
model = MoneyModel(5)

# Run the model for 5 steps
for i in range(5):
    model.step()

# Print the wealth of each agent
for agent in model.schedule.agents:
    print(agent.wealth)
