class Asset:
    """Lightweight holding record. Price is managed by the Market."""

    def __init__(self, name: str, quantity: int):
        self.name = name
        self.quantity = quantity

    def __str__(self):
        return f"{self.name} (qty: {self.quantity})"
