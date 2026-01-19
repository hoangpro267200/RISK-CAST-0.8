from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.rate import Rate
from app.schemas.pricing import PricingQuoteRequest


class RateService:
    """Rate fetching and normalization service."""

    def __init__(self, db: Session):
        self.db = db

    def create_rate(self, data) -> Rate:
        rate = Rate(**data.dict(by_alias=True))
        self.db.add(rate)
        self.db.commit()
        self.db.refresh(rate)
        return rate

    def list_rates_by_lane(
        self, pol: str, pod: str, etd_start: Optional[datetime] = None, etd_end: Optional[datetime] = None
    ) -> List[Rate]:
        query = self.db.query(Rate).filter(Rate.pol == pol, Rate.pod == pod)
        if etd_start:
            query = query.filter(Rate.etd >= etd_start)
        if etd_end:
            query = query.filter(Rate.etd <= etd_end)
        return query.all()

    def mock_rate_source(self, request: PricingQuoteRequest) -> List[Rate]:
        """Placeholder for Pricing Engine integrations; returns in-memory mock rates."""
        base_etd = request.etd_from
        samples = [
            {
                "carrier": "MockLine A",
                "pol": request.pol,
                "pod": request.pod,
                "etd": base_etd,
                "base_freight": 1200.0,
                "surcharges": {"BAF": 100.0, "PSS": 50.0},
                "total_cost": None,
                "currency": "USD",
                "source_type": "mock",
            },
            {
                "carrier": "MockLine B",
                "pol": request.pol,
                "pod": request.pod,
                "etd": base_etd + timedelta(days=2),
                "base_freight": 1100.0,
                "surcharges": {"BAF": 120.0, "PSS": 40.0},
                "total_cost": None,
                "currency": "USD",
                "source_type": "mock",
            },
            {
                "carrier": "MockLine C",
                "pol": request.pol,
                "pod": request.pod,
                "etd": base_etd + timedelta(days=4),
                "base_freight": 1000.0,
                "surcharges": {"BAF": 130.0, "PSS": 60.0},
                "total_cost": None,
                "currency": "USD",
                "source_type": "mock",
            },
        ]
        return [Rate(**s) for s in samples]

