from mesa import Agent
import random


class FinancialAgent(Agent):
    """ An agent with fixed initial wealth."""

    def __init__(self, unique_id, model, wealth, risk_aversion, strategy):
        super().__init__(unique_id, model)
        self.wealth = wealth
        self.risk_aversion = risk_aversion
        self.transactions = 0
        self.strategy = strategy
        self.history = []  # initialize an empty list for the agent's history

    def step(self):
        self.move()
        if self.wealth > 0:
            self.trade()

    def move(self):

        old_pos = self.pos
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )
        new_position = self.random.choice(possible_steps)
        new_pos = self.pos
        self.model.grid.move_agent(self, new_position)

        self.history.append({'time': self.model.schedule.time,
                             'activity': 'move',
                             'old_pos': old_pos,
                             'new_pos': new_pos})

    def trade(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        if len(cellmates) > 1:
            other = self.random.choice(cellmates)

            if self.get_strategy() == "Random":
                self.random_trade(other)
            elif self.get_strategy() == "Proportional":
                self.proportional_trade(other)
            elif self.get_strategy() == "Barter":
                self.barter_trade(other)
            elif self.get_strategy() == "Weighted":
                self.weighted_trade(other)
            elif self.get_strategy() == "Bundle":
                self.bundle_trade(other)

            self.transactions += 1

    def random_trade(self, other):
        # Randomly choose whether to make a trade or not.
        random_bool = random.choice([True, False])
        if random_bool:
            other.wealth += 1
            self.wealth -= 1

    def proportional_trade(self, other):
        proportion = 0.1
        # Offer is multiplied by the proportion.
        offer = (self.wealth * proportion)
        if offer > 0:
            other.wealth += offer
            self.wealth -= offer

    def barter_trade(self, other):
        if other.wealth > 0:
            # Offer is a random number between 1 and the other agent's wealth.
            offer = self.random.randint(1, other.wealth)
            # If the offer is greater than the agent's wealth, offer the agent's wealth.
            if offer > other.wealth:
                offer = other.wealth
            self.wealth -= offer
            other.wealth += offer

    def weighted_trade(self, other):
        trust_level = self.get_trust_level(other)
        risk_aversion = self.get_risk_aversion()

        # If trust level is high, give more.
        if trust_level >= 0.5 and self.wealth > 0:
            # Offer is the minimum of the agent's wealth and the other agent's wealth.
            offer = min(self.wealth, (1 - risk_aversion) * other.wealth)
            if offer > 0:
                other.wealth += offer
                self.wealth -= offer
        # If trust level is low, take more.
        elif trust_level < 0.5 and other.wealth > 0:
            # Offer is the minimum of the agent's wealth and the other agent's wealth.
            offer = min(other.wealth, risk_aversion * self.wealth)
            if offer > 0:
                self.wealth += offer
                other.wealth -= offer

    def get_trust_level(self, other):
        trust_coefficient = 0.5
        # If the other agent has more wealth, increase trust.
        if other.wealth > self.wealth:
            return trust_coefficient + trust_coefficient * (other.wealth - self.wealth) / self.wealth
        # If the other agent has less wealth, decrease trust.
        elif other.wealth < self.wealth:
            return trust_coefficient - trust_coefficient * (self.wealth - other.wealth) / self.wealth
        else:
            return trust_coefficient

    def get_risk_aversion(self):
        return self.risk_aversion

    def set_risk_aversion(self, risk_aversion):
        self.risk_aversion = risk_aversion

    def get_wealth(self):
        return self.wealth

    def get_transactions(self):
        return self.transactions

    def get_strategy(self):
        return self.model.strategy
