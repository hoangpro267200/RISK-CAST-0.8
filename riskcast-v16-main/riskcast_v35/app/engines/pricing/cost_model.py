from app.models.rate import Rate


class CostModel:
    """Computes basic costs; advanced logic lives elsewhere."""

    def compute_base_cost(self, rate: Rate) -> float:
        return float(rate.base_freight or 0.0)

    def compute_total_cost(self, rate: Rate) -> float:
        base = self.compute_base_cost(rate)
        surcharges_total = 0.0
        if rate.surcharges:
            surcharges_total = float(sum(value or 0.0 for value in rate.surcharges.values()))
        if rate.total_cost is not None:
            return float(rate.total_cost)
        return base + surcharges_total

