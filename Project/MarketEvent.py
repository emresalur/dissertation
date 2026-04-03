import random


class MarketEvent:
    """A market-wide event that affects asset prices over a duration."""

    def __init__(self, name, event_type, magnitude, duration, target_assets=None):
        """
        name: display name ("Market Crash", "Bull Run")
        event_type: "crash", "boom", or "volatility_spike"
        magnitude: for crash/boom this is the total price multiplier
                   (0.5 = halve prices, 1.8 = 80% rise)
                   for volatility_spike this is the max per-step shock fraction
        duration: number of steps the event lasts
        target_assets: list of asset names, or None for all
        """
        self.name = name
        self.event_type = event_type
        self.magnitude = magnitude
        self.duration = duration
        self.target_assets = target_assets
        self.remaining_steps = 0
        self.active = False

    def activate(self):
        self.active = True
        self.remaining_steps = self.duration

    def tick(self, market):
        """Apply one step of the event. Returns True if still active."""
        if not self.active or self.remaining_steps <= 0:
            self.active = False
            return False

        targets = self.target_assets or market.get_asset_names()

        for asset_name in targets:
            current = market.get_price(asset_name)

            if self.event_type == "crash":
                step_factor = 1 - ((1 - self.magnitude) / self.duration)
                market.update_price(asset_name, current * step_factor)

            elif self.event_type == "boom":
                step_factor = 1 + ((self.magnitude - 1) / self.duration)
                market.update_price(asset_name, current * step_factor)

            elif self.event_type == "volatility_spike":
                shock = random.uniform(-self.magnitude, self.magnitude)
                market.update_price(asset_name, current * (1 + shock))

        self.remaining_steps -= 1
        if self.remaining_steps <= 0:
            self.active = False

        return self.active
