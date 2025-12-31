import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models import Base


class ConsolidationPlan(Base):
    __tablename__ = "consolidation_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vessel_voyage = Column(String, nullable=True)
    pol = Column(String, nullable=False)
    pod = Column(String, nullable=False)
    containers = Column(JSONB, nullable=True)
    baseline_lcl_cost = Column(Numeric, nullable=True)
    optimized_fcl_cost = Column(Numeric, nullable=True)
    saving_amount = Column(Numeric, nullable=True)
    saving_percent = Column(Numeric, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

