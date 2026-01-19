import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models import Base


class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    weather_risk = Column(Float, nullable=True)
    congestion_risk = Column(Float, nullable=True)
    carrier_risk = Column(Float, nullable=True)
    total_risk = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    shipment = relationship("Shipment", back_populates="risk_snapshots")

