from app.engines.customs.hs_classifier import suggest_hs_from_description


class HSSuggester:
    """Suggests HS codes from item descriptions."""

    def suggest(self, item_description: str, context: dict = None) -> dict:
        candidates = suggest_hs_from_description(item_description)
        top = candidates[0] if candidates else {"hs_code": "9999", "description": "", "score": 0.1}
        return {
            "suggested_hs_code": top["hs_code"],
            "confidence_score": top["score"],
            "alternative_codes": [c["hs_code"] for c in candidates[1:]],
        }

