HS_KEYWORD_MAP = {
    "electronics": "85",
    "phone": "8517",
    "computer": "8471",
    "laptop": "8471",
    "rice": "1006",
    "coffee": "0901",
    "garment": "6201",
    "textile": "6307",
    "auto": "8708",
}


def suggest_hs_from_description(description: str) -> list[dict]:
    text = (description or "").lower()
    candidates = []
    for keyword, hs in HS_KEYWORD_MAP.items():
        if keyword in text:
            candidates.append({"hs_code": hs, "description": keyword, "score": 0.8})
    if not candidates:
        candidates.append({"hs_code": "9999", "description": "general", "score": 0.1})
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates









