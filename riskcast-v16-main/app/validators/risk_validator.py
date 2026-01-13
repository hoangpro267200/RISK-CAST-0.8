from app.models.risk_module import RiskModule


def validate_risk_modules(modules):
    arr = modules or []
    safe = []
    for m in arr:
        score = clamp(int(m.get("score") or m.get("value") or 0), 0, 100)
        level = m.get("level") or score_to_level(score)
        safe.append(
            RiskModule(
                title=str(m.get("title") or m.get("name") or ""),
                score=score,
                level=level,
                message=str(m.get("message") or m.get("description") or "No data"),
            )
        )
    return safe


def clamp(val, low, high):
    return max(low, min(high, val))


def score_to_level(score):
    if score <= 25:
        return "LOW"
    if score <= 55:
        return "MEDIUM"
    if score <= 75:
        return "HIGH"
    return "CRITICAL"




