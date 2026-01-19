from datetime import datetime
from typing import Dict, Optional, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.risk import RiskSnapshot
from app.engines.tracking.weather_risk import estimate_weather_risk
from app.engines.tracking.congestion_risk import estimate_congestion_risk
from app.engines.tracking.carrier_reliability import estimate_carrier_risk
from app.engines.tracking.risk_aggregator import aggregate_risk_components


class RiskService:
    """Provides risk computation for various factors."""

    def __init__(self, db: Session):
        self.db = db

    def aggregate_risk(self, context: Dict[str, str]) -> Dict[str, float]:
        """
        Aggregate risk using simple heuristics. Context keys may include:
        lat, lon, pod, carrier
        """
        weather = estimate_weather_risk(context.get("lat"), context.get("lon"))
        congestion = estimate_congestion_risk(context.get("pod"))
        carrier = estimate_carrier_risk(context.get("carrier"))
        return aggregate_risk_components(weather, congestion, carrier)

    def create_risk_snapshot(self, shipment_id: UUID, risk_components: Dict[str, float], timestamp: Optional[datetime] = None) -> RiskSnapshot:
        snapshot = RiskSnapshot(
            shipment_id=shipment_id,
            timestamp=timestamp or datetime.utcnow(),
            weather_risk=risk_components.get("weather_risk"),
            congestion_risk=risk_components.get("congestion_risk"),
            carrier_risk=risk_components.get("carrier_risk"),
            total_risk=risk_components.get("total_risk"),
            created_at=datetime.utcnow(),
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_latest_snapshot(self, shipment_id: UUID) -> Optional[RiskSnapshot]:
        return (
            self.db.query(RiskSnapshot)
            .filter(RiskSnapshot.shipment_id == shipment_id)
            .order_by(RiskSnapshot.timestamp.desc())
            .first()
        )

    def list_snapshots(self, shipment_id: UUID) -> List[RiskSnapshot]:
        return (
            self.db.query(RiskSnapshot)
            .filter(RiskSnapshot.shipment_id == shipment_id)
            .order_by(RiskSnapshot.timestamp.desc())
            .all()
        )

