from datetime import datetime
from typing import List, Optional
from pydantic import Field
from .base import TimeStampedSchema
from .transport import Transport, RouteLeg
from .cargo import Cargo
from .risk_module import RiskModule
from .kpi import KPI


class Shipment(TimeStampedSchema):
    shipmentId: str = Field(default="")
    state: str = Field(default="UNKNOWN")
    transport: Transport = Field(default_factory=Transport)
    cargo: Cargo = Field(default_factory=Cargo)
    riskModules: List[RiskModule] = Field(default_factory=list)
    kpi: KPI = Field(default_factory=KPI)
    legs: List[RouteLeg] = Field(default_factory=list)
    updatedAt: Optional[datetime] = None




