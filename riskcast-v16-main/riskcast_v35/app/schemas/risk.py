from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class RiskSnapshotBase(BaseModel):
    shipment_id: UUID = Field(..., alias="shipmentId")
    timestamp: datetime
    weather_risk: Optional[float] = Field(None, alias="weatherRisk")
    congestion_risk: Optional[float] = Field(None, alias="congestionRisk")
    carrier_risk: Optional[float] = Field(None, alias="carrierRisk")
    total_risk: Optional[float] = Field(None, alias="totalRisk")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class RiskSnapshotResponse(RiskSnapshotBase):
    id: UUID
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

