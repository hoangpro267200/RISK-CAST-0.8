from app.models.rate import Rate


def build_risk_context_from_rate(rate: Rate) -> dict:
    return {
        "pol": rate.pol,
        "pod": rate.pod,
        "carrier": rate.carrier,
        "etd": rate.etd.isoformat() if rate.etd else None,
    }


def apply_risk_adjustment(base_cost: float, risk: dict) -> float:
    total_risk = risk.get("total_risk") or risk.get("totalRisk") or 0.0
    return float(base_cost) * (1 + float(total_risk) * 0.01)









