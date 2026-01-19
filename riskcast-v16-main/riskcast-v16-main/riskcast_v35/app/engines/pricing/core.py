from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.engines.pricing.cost_model import CostModel
from app.engines.pricing.lane_ranker import LaneRanker
from app.engines.pricing.risk_adjust import apply_risk_adjustment, build_risk_context_from_rate
from app.models.rate import Rate
from app.schemas.pricing import PricingOption, PricingQuoteRequest, PricingQuoteResponse
from app.services.rate_service import RateService
from app.services.risk_service import RiskService
from app.services.shipment_service import ShipmentService


class PricingEngine:
    """Main engine for generating pricing quotes."""

    def __init__(self, db: Session, risk_service: RiskService, shipment_service: Optional[ShipmentService] = None):
        self.db = db
        self.risk_service = risk_service
        self.shipment_service = shipment_service
        self.rate_service = RateService(db)
        self.cost_model = CostModel()
        self.lane_ranker = LaneRanker()

    def quote(self, request: PricingQuoteRequest) -> PricingQuoteResponse:
        rates = self.rate_service.list_rates_by_lane(
            request.pol, request.pod, request.etd_from, request.etd_to
        )

        if not rates:
            rates = self.rate_service.mock_rate_source(request)

        candidates = self._build_candidates(rates)
        ranked = self.lane_ranker.rank(candidates)

        best_option = self._to_option(ranked.get("best_option")) if ranked.get("best_option") else None
        alt_options = [
            self._to_option(candidate) for candidate in ranked.get("alternative_options", []) if candidate
        ]

        response = PricingQuoteResponse(
            bestOption=best_option,
            alternatives=alt_options,
            requestedLane={
                "pol": request.pol,
                "pod": request.pod,
                "etdFrom": request.etd_from,
                "etdTo": request.etd_to,
                "incoterm": request.incoterm,
                "cargoDescription": request.cargo_description,
                "weight": request.weight,
                "volume": request.volume,
            },
            generatedAt=datetime.utcnow(),
        )
        # Optional: attach to shipment.price_info in future phases
        return response

    def _build_candidates(self, rates: List[Rate]) -> List[dict]:
        candidates = []
        for rate in rates:
            base_cost = self.cost_model.compute_total_cost(rate)
            risk_context = build_risk_context_from_rate(rate)
            risk = self.risk_service.aggregate_risk(risk_context)
            adjusted_cost = apply_risk_adjustment(base_cost, risk)
            candidates.append(
                {
                    "rate": rate,
                    "risk": risk,
                    "adjusted_cost": adjusted_cost,
                    "base_cost": base_cost,
                }
            )
        return candidates

    def _to_option(self, candidate: dict) -> PricingOption:
        rate: Rate = candidate["rate"]
        risk = candidate["risk"]
        adjusted_cost = candidate["adjusted_cost"]
        total_cost = candidate.get("base_cost", adjusted_cost)
        return PricingOption(
            carrier=rate.carrier,
            pol=rate.pol,
            pod=rate.pod,
            etd=rate.etd or datetime.utcnow(),
            totalCost=total_cost,
            currency=rate.currency or "USD",
            risk=risk,
            adjustedCost=adjusted_cost,
        )
