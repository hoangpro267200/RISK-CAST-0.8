import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ref_code = Column(String, nullable=False)
    shipper_name = Column(String, nullable=True)
    consignee_name = Column(String, nullable=True)
    pol = Column(String, nullable=False)
    pod = Column(String, nullable=False)
    etd = Column(DateTime, nullable=True)
    eta = Column(DateTime, nullable=True)
    status = Column(String, nullable=False, default="draft")
    price_info = Column(JSONB, nullable=True)
    consolidation_info = Column(JSONB, nullable=True)
    documents_info = Column(JSONB, nullable=True)
    customs_info = Column(JSONB, nullable=True)
    risk_info = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    documents = relationship(
        "Document",
        back_populates="shipment",
        cascade="all, delete-orphan",
    )
    tracking_events = relationship(
        "TrackingEvent",
        back_populates="shipment",
        cascade="all, delete-orphan",
    )
    risk_snapshots = relationship(
        "RiskSnapshot",
        back_populates="shipment",
        cascade="all, delete-orphan",
    )

