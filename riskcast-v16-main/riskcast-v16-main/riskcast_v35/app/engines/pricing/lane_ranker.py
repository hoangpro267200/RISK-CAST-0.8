class LaneRanker:
    """Ranks lanes based on adjusted cost; extensible for more criteria."""

    def rank(self, candidates: list, criteria: dict = None) -> dict:
        if not candidates:
            return {"best_option": None, "alternative_options": []}
        sorted_candidates = sorted(candidates, key=lambda x: x.get("adjusted_cost", float("inf")))
        best = sorted_candidates[0]
        alternatives = sorted_candidates[1:4]
        return {"best_option": best, "alternative_options": alternatives}

