"""
Shipment Pydantic Schema for Validation
"""
from datetime import datetime
from typing import List, Optional
from pydantic import Field
from .base import BaseSchema, TimeStampedSchema
from .transport import Transport, RouteLeg
from .cargo import Cargo
from .risk_module import RiskModule
from .kpi import KPI


class Shipment(TimeStampedSchema):
    """Shipment model for validation"""
    shipmentId: str = Field(default="", alias="id")
    state: str = Field(default="UNKNOWN")
    transport: Transport = Field(default_factory=Transport)
    cargo: Cargo = Field(default_factory=Cargo)
    riskModules: List[RiskModule] = Field(default_factory=list, alias="modules")
    kpi: KPI = Field(default_factory=KPI)
    legs: List[RouteLeg] = Field(default_factory=list)
    
    class Config:
        allow_population_by_field_name = True


