import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.models import Base


class CustomsProfile(Base):
    __tablename__ = "customs_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id"), nullable=False)
    hs_code = Column(String, nullable=True)
    declaration_xml = Column(Text, nullable=True)
    risk_flag = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

