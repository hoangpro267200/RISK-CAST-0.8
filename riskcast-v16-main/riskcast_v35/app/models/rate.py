import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models import Base


class Rate(Base):
    __tablename__ = "rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carrier = Column(String, nullable=False)
    pol = Column(String, nullable=False)
    pod = Column(String, nullable=False)
    etd = Column(DateTime, nullable=True)
    base_freight = Column(Numeric, nullable=True)
    surcharges = Column(JSONB, nullable=True)
    total_cost = Column(Numeric, nullable=True)
    currency = Column(String, nullable=True)
    source_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

