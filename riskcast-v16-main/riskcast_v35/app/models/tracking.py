import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    shipment = relationship("Shipment", back_populates="tracking_events")

