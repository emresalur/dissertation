class Asset:
    def __init__(self, name: str, price: float, quantity: int):

        self.name = name

        self.price = price

        self.quantity = quantity

        # Initialize the list with the initial price
        self.historical_prices = [price]

        self.demand = 1

        self.supply = 1

    def get_price_history(self):

        return self.historical_prices

    def add_price_to_history(self, price):

        self.historical_prices.append(price)

    def __str__(self):

        return f"{self.name} {self.price}"

    def get_name(self):

        return self.name

    def get_price(self):

        return self.price

    def get_mean_price(self):

        return sum(self.historical_prices) / len(self.historical_prices)

    def update_price(self, new_price):

        self.price = new_price
        self.historical_prices.append(new_price)

    def set_name(self, name):

        self.name = name

    def set_price(self, price):

        self.price = price

    def get_demand(self):

        return self.demand

    def set_demand(self, demand):

        self.demand = demand

    def get_supply(self):

        return self.supply

    def set_supply(self, supply):

        self.supply = supply

    def get_quantity(self):

        return self.quantity

    def set_quantity(self, quantity):

        self.quantity = quantity
