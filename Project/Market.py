import random


class Market:
    """Centralized market with supply/demand-driven pricing and transaction costs."""

    def __init__(self, asset_configs, transaction_cost=0.02):
        """
        asset_configs: list of dicts, e.g.
        [{"name": "Gold", "initial_price": 10.0}, ...]
        transaction_cost: fraction charged per trade (0.02 = 2%)
        """
        self.assets = {}
        self.order_book = {}
        self.transaction_cost = transaction_cost
        self.total_fees_collected = 0.0

        # Price movement sensitivity to order imbalance
        self.price_sensitivity = 0.03

        # Track OHLC data per asset for candlestick charts
        self.ohlc = {}

        for cfg in asset_configs:
            name = cfg["name"]
            price = cfg["initial_price"]
            self.assets[name] = {
                "price": price,
                "historical_prices": [price],
                "demand": 0,
                "supply": 0,
                "volume": 0,
            }
            self.order_book[name] = {"bids": [], "asks": []}
            self.ohlc[name] = []
            self._start_candle(name, price)

    def _start_candle(self, name, price):
        """Begin a new OHLC candle."""
        self.ohlc[name].append({
            "open": price, "high": price, "low": price, "close": price, "volume": 0
        })

    def _update_candle(self, name, price, volume=0):
        """Update the current candle with a new price tick."""
        candle = self.ohlc[name][-1]
        candle["high"] = max(candle["high"], price)
        candle["low"] = min(candle["low"], price)
        candle["close"] = price
        candle["volume"] += volume

    def get_price(self, asset_name):
        return self.assets[asset_name]["price"]

    def get_mean_price(self, asset_name):
        hist = self.assets[asset_name]["historical_prices"]
        return sum(hist) / len(hist)

    def get_price_history(self, asset_name):
        return list(self.assets[asset_name]["historical_prices"])

    def get_ohlc(self, asset_name):
        return list(self.ohlc[asset_name])

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

    def get_volatility(self, asset_name, window=20):
        """Standard deviation of recent price changes."""
        hist = self.assets[asset_name]["historical_prices"]
        if len(hist) < 2:
            return 0.0
        recent = hist[-window:]
        if len(recent) < 2:
            return 0.0
        returns = [(recent[i] - recent[i-1]) / max(recent[i-1], 0.01)
                    for i in range(1, len(recent))]
        if not returns:
            return 0.0
        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        return variance ** 0.5

    def calculate_fee(self, trade_value):
        """Calculate transaction fee and accumulate it."""
        fee = trade_value * self.transaction_cost
        self.total_fees_collected += fee
        return fee

    def submit_order(self, agent_id, asset_name, order_type, price, quantity=1):
        """Submit a bid or ask order. order_type: 'bid' or 'ask'."""
        order = {"agent_id": agent_id, "price": price, "quantity": quantity}
        if order_type == "bid":
            self.order_book[asset_name]["bids"].append(order)
        else:
            self.order_book[asset_name]["asks"].append(order)

    def clear_orders(self, asset_name):
        """Supply/demand-driven price discovery."""
        bids = self.order_book[asset_name]["bids"]
        asks = self.order_book[asset_name]["asks"]
        current_price = self.assets[asset_name]["price"]
        n_bids = len(bids)
        n_asks = len(asks)
        total_orders = n_bids + n_asks

        if total_orders > 0:
            # Order imbalance drives price: more bids = price up, more asks = price down
            imbalance = (n_bids - n_asks) / total_orders  # range [-1, 1]

            # Add noise for realism
            noise = random.uniform(-0.005, 0.005)

            # Price change proportional to imbalance
            price_change = current_price * self.price_sensitivity * (imbalance + noise)
            new_price = max(0.01, current_price + price_change)

            self.assets[asset_name]["price"] = new_price
            self.assets[asset_name]["historical_prices"].append(new_price)
            self.assets[asset_name]["volume"] = total_orders
            self._update_candle(asset_name, new_price, total_orders)
        else:
            # No orders — small random walk to prevent flat lines
            drift = current_price * random.uniform(-0.002, 0.002)
            new_price = max(0.01, current_price + drift)
            self.assets[asset_name]["price"] = new_price
            self.assets[asset_name]["historical_prices"].append(new_price)
            self._update_candle(asset_name, new_price, 0)

        self.assets[asset_name]["demand"] = n_bids
        self.assets[asset_name]["supply"] = n_asks
        self.order_book[asset_name] = {"bids": [], "asks": []}

    def close_candle(self, asset_name):
        """Close current candle and start a new one (call every N steps)."""
        current_price = self.assets[asset_name]["price"]
        self._start_candle(asset_name, current_price)

    def update_price(self, asset_name, new_price):
        """Direct price update (for events)."""
        new_price = max(0.01, new_price)
        self.assets[asset_name]["price"] = new_price
        self.assets[asset_name]["historical_prices"].append(new_price)
        self._update_candle(asset_name, new_price)
