from mesa import Agent
import random
from Asset import Asset


class FinancialAgent(Agent):

    """An agent with fixed initial wealth."""

    def __init__(self, unique_id: int, model, wealth: int, strategy: str, mood: str):

        # Set the agent's unique_id and model.
        super().__init__(unique_id, model)

        # Set the agent's wealth.
        self.wealth = wealth

        # Set the agent's strategy.
        self.strategy = strategy

        # Set the agent's mood.
        self.mood = mood

        # Create an empty list for activities history
        self.history = []

        # Define an empty list for the agent's assets.
        self.assets = []

        # Add gold to the agent's assets.
        self.assets.append(Asset("Gold", 10, 1))

        # Add silver to the agent's assets.
        self.assets.append(Asset("Silver", 5, 1))

        # Set the mean reversion threshold
        self.mean_reversion_threshold = 0.2

        # Set the number of trades completed to 0.
        self.trades_completed = 0

        # Set the number of interactions to 0.
        self.interactions = 0

    def step(self):
        """A model step. Move, then trade with neighbors."""

        self.move()

        if self.wealth > 0:

            self.trade()

    def move(self):
        """Move the agent to a random empty cell."""

        # Get the position before moving.
        old_pos = self.pos

        # Get the neighborhood of the agent.
        possible_steps = self.model.grid.get_neighborhood(
            self.pos,
            moore=True,
            include_center=False
        )

        # Choose a random direction out of the possible steps.
        new_pos = self.random.choice(possible_steps)

        # Move the agent to the new position.
        self.model.grid.move_agent(self, new_pos)

        # Add the activity to the agent's history.
        self.history.append({'time': self.model.schedule.time,
                             'activity': 'move',
                             'old_pos': old_pos,
                             'new_pos': new_pos})

    def trade(self):
        """Trade with a random agent in the same cell."""

        # Get the agents in the same cell.
        cellmates = self.model.grid.get_cell_list_contents([self.pos])

        # If there is more than one agent in the cell, trade with one of them.
        if len(cellmates) > 1:

            # Choose a random agent to trade with.
            other = self.random.choice(cellmates)

            # Keep choosing until the other agent is not the same as the current agent
            while (other.unique_id == self.unique_id):

                other = self.random.choice(cellmates)

            # Increment the number of interactions.
            self.interactions += 1

            if self.get_strategy() == "Asset Trading":

                self.asset_trade(other)

            elif self.get_strategy() == "Wealth Trading":

                self.wealth_trade(other)

            elif self.get_strategy() == "Mean Reversion":

                self.set_price_fluctuation(-0.1, 10)

                self.mean_reversion(other)

            elif self.get_strategy() == "Momentum":
                
                self.set_price_fluctuation(0.05, 10)
                
                self.momentum_trade(other)

            # Add the activity to the agent's history.
            self.history.append({'time': self.model.schedule.time,
                                 'activity': 'trade',
                                 'other': other.unique_id,
                                 'wealth': self.wealth,
                                 'other_wealth': other.wealth})

    def asset_trade(self, other):

        # Check if the other agent has any assets.
        if len(other.assets) > 0:

            # Choose a random asset to trade.
            asset_to_trade = self.random.choice(other.assets)

            # Print the asset to trade.
            self.print_interest(other, asset_to_trade)

            # Get the price of the asset.
            asset_price = asset_to_trade.get_price()

            # If the agent has enough wealth to trade for the asset, trade.
            if self.wealth >= asset_price:

                # Take the asset from the other agent.
                self.assets.append(asset_to_trade)

                # Remove the asset from the other agent.
                other.assets.remove(asset_to_trade)

                # Give the other agent the price of the asset.
                other.wealth += asset_price

                # Take the price of the asset from the agent.
                self.wealth -= asset_price

                # Print the trade.
                self.confirm_trade(other, asset_to_trade)

    def wealth_trade(self, other):

        # Check if the other agent has any wealth.
        if other.wealth > 0:

            # Choose a random amount of wealth to trade.
            wealth_to_trade = self.random.randint(1, self.wealth)

            # If the agent has enough wealth to trade, trade.
            if self.wealth >= wealth_to_trade:

                # Give the other agent one wealth.
                other.wealth += wealth_to_trade

                # Take the wealth from the agent.
                self.wealth -= wealth_to_trade

                # Print the trade.
                print("Agent " + str(self.unique_id) + " traded " + str(wealth_to_trade) +
                      " units of wealth with Agent " + str(other.unique_id) + ".")

                # Add the trade to the number of trades completed.
                self.trades_completed += 1

    def mean_reversion(self, other):
        """ Implements mean reversion strategy. """

        # Check if the other agent has any assets.

        if len(other.assets) > 0:

            # Choose a random asset to trade.
            asset_to_trade = self.random.choice(other.assets)

            # Print the asset to trade.
            self.print_interest(other, asset_to_trade)

            # Get the price of the asset.
            asset_price = asset_to_trade.get_price()

            print("Asset price: " + str(asset_price))

            # Calculate the mean price of the asset.
            mean_price = asset_to_trade.get_mean_price()

            print("Mean price: " + str(mean_price))

            # Calculate the difference between the asset price and the mean price.
            price_difference = asset_price - mean_price

            print("Price difference: " + str(price_difference))

            # Check if the difference is greater than the mean reversion threshold.
            if abs(price_difference) > self.mean_reversion_threshold:

                # Print the wealth of the agent.
                print("Agent " + str(self.unique_id) + " has " +
                      str(self.wealth) + " units of wealth.")

                if self.wealth >= asset_price and asset_to_trade in other.assets:

                    self.assets.append(asset_to_trade)

                    other.assets.remove(asset_to_trade)

                    other.wealth += asset_price

                    self.wealth -= asset_price

                    self.confirm_trade(other, asset_to_trade)

                    # Add the updated price history to the asset.
                    asset_to_trade.add_price_to_history(asset_price)

                    # Print the updated price history.
                    for price in asset_to_trade.get_price_history():

                        print("The prices in the list are: " + str(price))

                    # Print the mean in the list.
                    print("The mean in the list is: " +
                          str(asset_to_trade.get_mean_price()))

    def momentum_trade(self, other):

        # Check if the other agent has any assets.
        if len(other.assets) > 0:

            # Choose a random asset to trade.
            asset_to_trade = self.random.choice(other.assets)

            # Print the asset to trade.
            self.print_interest(other, asset_to_trade)

            # Get the price of the asset.
            asset_price = asset_to_trade.get_price()

            # Check if the price of the asset is increasing or decreasing.
            asset_trend = self.get_asset_trend(asset_to_trade)

            print("Asset trend: " + str(asset_trend))

            # If the price is increasing and the agent has enough wealth to trade, trade.
            if asset_trend == 'up' and self.wealth >= asset_price:

                # Take the asset from the other agent.
                self.assets.append(asset_to_trade)

                # Remove the asset from the other agent.
                other.assets.remove(asset_to_trade)

                # Give the other agent the price of the asset.
                other.wealth += asset_price

                # Take the price of the asset from the agent.
                self.wealth -= asset_price

                # Print the trade.
                self.confirm_trade(other, asset_to_trade)

            # If the price is decreasing, wait for the trend to reverse.
            elif asset_trend == 'down' and other.wealth >= asset_price and len(self.assets) > 0:

                # Set the asset to trade to the asset that the other agent is waiting for.
                asset_to_trade = self.random.choice(self.assets)

                # Take the asset from the other agent.
                other.assets.append(asset_to_trade)

                # Remove the asset from the other agent.
                self.assets.remove(asset_to_trade)

                # Give the other agent the price of the asset.
                self.wealth += asset_price

                # Take the price of the asset from the agent.
                other.wealth -= asset_price

                # Print that the agent is waiting the trend to reverse.
                print("Agent " + str(self.unique_id) +
                      " is waiting for the trend to reverse before buying.")

                # Increment the nunmber of trades.
                self.trades_completed += 1

            # If the agent does not have enough wealth to trade, wait.
            else:

                print("Agent " + str(self.unique_id) +
                      " is waiting to accumulate more wealth before trading.")

    def get_asset_trend(self, asset):

        # Get the asset's price history.
        price_history = asset.get_price_history()

        asset.add_price_to_history(asset.get_price())

        # Check if the asset is increasing or decreasing.
        if len(price_history) >= 2 and price_history[-1] > price_history[-2]:

            return 'up'

        elif len(price_history) >= 2 and price_history[-1] < price_history[-2]:

            return 'down'

        else:

            return 'stable'

    def print_interest(self, other, asset):

        print("Agent " + str(self.unique_id) + " is interested in trading for " +
              str(asset.get_name()) + " with Agent " + str(other.unique_id) + ".")

    def confirm_trade(self, other, asset):

        print("Agent " + str(self.unique_id) + " traded " + str(asset.get_name()) + " with Agent " +
              str(other.unique_id) + " for " + str(asset.get_price()) + " units of wealth.")

        # Increment the number of trades completed.
        self.trades_completed += 1

    def set_price_fluctuation(self, price_fluctuation, iterations):

        if self.model.schedule.time % iterations == 0:

            for asset in self.assets:

                asset.price += price_fluctuation

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

    def get_color(self):

        return self.color

    def get_size(self):

        return self.size

    def get_label(self):

        return self.label

    def get_asset_names(self):

        asset_names = []

        for asset in self.assets:

            asset_names.append(asset.get_name())

        return asset_names

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
