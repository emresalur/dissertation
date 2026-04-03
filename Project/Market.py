class Market:
    """Centralized market that holds canonical prices and a simple order book."""

    def __init__(self, asset_configs):
        """
        asset_configs: list of dicts, e.g.
        [{"name": "Gold", "initial_price": 10.0}, {"name": "Silver", "initial_price": 5.0}]
        """
        self.assets = {}
        self.order_book = {}

        for cfg in asset_configs:
            name = cfg["name"]
            price = cfg["initial_price"]
            self.assets[name] = {
                "price": price,
                "historical_prices": [price],
                "demand": 0,
                "supply": 0,
            }
            self.order_book[name] = {"bids": [], "asks": []}

    def get_price(self, asset_name):
        return self.assets[asset_name]["price"]

    def get_mean_price(self, asset_name):
        hist = self.assets[asset_name]["historical_prices"]
        return sum(hist) / len(hist)

    def get_price_history(self, asset_name):
        return list(self.assets[asset_name]["historical_prices"])

    def get_asset_trend(self, asset_name):
        hist = self.assets[asset_name]["historical_prices"]
        if len(hist) >= 2:
            if hist[-1] > hist[-2]:
                return "up"
            elif hist[-1] < hist[-2]:
                return "down"
        return "stable"

    def get_asset_names(self):
        return list(self.assets.keys())

    def submit_order(self, agent_id, asset_name, order_type, price, quantity=1):
        """Submit a bid or ask order. order_type: 'bid' or 'ask'."""
        order = {"agent_id": agent_id, "price": price, "quantity": quantity}
        if order_type == "bid":
            self.order_book[asset_name]["bids"].append(order)
        else:
            self.order_book[asset_name]["asks"].append(order)

    def clear_orders(self, asset_name):
        """Simple price discovery: midpoint of best bid/ask, or keep last price."""
        bids = sorted(self.order_book[asset_name]["bids"],
                       key=lambda x: x["price"], reverse=True)
        asks = sorted(self.order_book[asset_name]["asks"],
                       key=lambda x: x["price"])

        if bids and asks and bids[0]["price"] >= asks[0]["price"]:
            new_price = (bids[0]["price"] + asks[0]["price"]) / 2
            self.assets[asset_name]["price"] = new_price
            self.assets[asset_name]["historical_prices"].append(new_price)
        else:
            # No matching orders — record current price to keep history ticking
            current = self.assets[asset_name]["price"]
            self.assets[asset_name]["historical_prices"].append(current)

        self.assets[asset_name]["demand"] = len(bids)
        self.assets[asset_name]["supply"] = len(asks)
        self.order_book[asset_name] = {"bids": [], "asks": []}

    def update_price(self, asset_name, new_price):
        """Direct price update (for fluctuations, events)."""
        self.assets[asset_name]["price"] = new_price
        self.assets[asset_name]["historical_prices"].append(new_price)
