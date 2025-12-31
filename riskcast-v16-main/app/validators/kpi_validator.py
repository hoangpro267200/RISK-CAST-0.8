from app.models.kpi import KPI


def validate_kpi(data: dict) -> KPI:
    payload = dict(data or {})
    return KPI(
        riskScore=clamp(int(payload.get("riskScore") or 0), 0, 100),
        transitDays=int(payload.get("transitDays") or 0),
        shipmentValue=float(payload.get("shipmentValue") or 0),
        carrierRating=float(payload.get("carrierRating") or 0),
        delayRisk=clamp(float(payload.get("delayRisk") or 0), 0, 1),
        compliance=clamp(float(payload.get("compliance") or 0), 0, 1),
        carbonFootprint=float(payload.get("carbonFootprint") or 0),
        onTimeProbability=clamp(float(payload.get("onTimeProbability") or 0), 0, 1),
        congestion=clamp(float(payload.get("congestion") or 0), 0, 1),
        weatherImpact=clamp(float(payload.get("weatherImpact") or 0), 0, 1),
        politicalRisk=clamp(float(payload.get("politicalRisk") or 0), 0, 1),
        securityRisk=clamp(float(payload.get("securityRisk") or 0), 0, 1),
    )


def clamp(val, low, high):
    return max(low, min(high, val))




