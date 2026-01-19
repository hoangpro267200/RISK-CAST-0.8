from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.shipment import Shipment
from app.models.tracking import TrackingEvent
from app.schemas.tracking import TrackingEventCreateRequest


class TrackingService:
    """Tracking CRUD helpers; advanced logic lives in engines."""

    def __init__(self, db: Session):
        self.db = db

    def create_tracking_event(self, data: TrackingEventCreateRequest) -> TrackingEvent:
        event = TrackingEvent(**data.dict(by_alias=True))
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_tracking_for_shipment(self, shipment_id: UUID) -> List[TrackingEvent]:
        return (
            self.db.query(TrackingEvent)
            .filter(TrackingEvent.shipment_id == shipment_id)
            .order_by(TrackingEvent.timestamp.desc())
            .all()
        )

    def list_recent_events(self, limit: int = 50) -> List[TrackingEvent]:
        return (
            self.db.query(TrackingEvent)
            .order_by(TrackingEvent.timestamp.desc())
            .limit(limit)
            .all()
        )

    def get_latest_event(self, shipment_id: UUID) -> Optional[TrackingEvent]:
        return (
            self.db.query(TrackingEvent)
            .filter(TrackingEvent.shipment_id == shipment_id)
            .order_by(TrackingEvent.timestamp.desc())
            .first()
        )

    def attach_position_to_shipment(self, shipment_id: UUID, position: dict) -> Optional[Shipment]:
        """
        Store latest position metadata on the shipment record for quick reads.
        Detailed history remains in tracking_events.
        """
        shipment = self.db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return None
        existing = shipment.risk_info or {}
        existing["latest_position"] = position
        shipment.risk_info = existing
        self.db.commit()
        self.db.refresh(shipment)
        return shipment

