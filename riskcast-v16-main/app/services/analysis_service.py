from functools import lru_cache
from typing import Dict, List
from app.validators.risk_validator import validate_risk_modules
from app.validators.transport_validator import validate_transport
from app.validators.shipment_validator import validate_shipment
from app.models.risk_module import RiskModule


async def run_full_analysis(shipment_id: str) -> Dict:
    modules = validate_risk_modules([
        {"title": "Congestion", "score": 68},
        {"title": "Weather", "score": 55},
        {"title": "Security", "score": 42},
    ])
    risk_score = compute_risk_score(modules)
    return {
        "riskScore": risk_score,
        "modules": [m.dict() for m in modules],
        "kpi": {
            "riskScore": risk_score,
            "delayRisk": compute_delay_prob({}),
        },
        "flags": {"highRisk": risk_score > 70},
    }


def compute_risk_score(modules: List[RiskModule]) -> int:
    scores = [m.score for m in modules if m.score is not None]
    return int(sum(scores) / len(scores)) if scores else 0


def compute_delay_prob(transport: Dict) -> float:
    t = validate_transport(transport)
    base = 1 - (t.reliabilityScore if hasattr(t, "reliabilityScore") else 0)
    return min(1.0, max(0.0, base))


def compute_route_complexity(legs) -> int:
    return min(100, len(legs or []) * 15)




