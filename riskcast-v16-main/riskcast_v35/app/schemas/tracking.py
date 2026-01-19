from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TrackingEventCreateRequest(BaseModel):
    shipment_id: UUID = Field(..., alias="shipmentId")
    lat: float
    lon: float
    status: str
    source: str
    timestamp: datetime

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class TrackingEventResponse(BaseModel):
    id: UUID
    shipment_id: UUID = Field(..., alias="shipmentId")
    lat: float
    lon: float
    status: str
    source: str
    timestamp: datetime
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class RiskPoint(BaseModel):
    timestamp: datetime
    weather_risk: float = Field(..., alias="weatherRisk")
    congestion_risk: float = Field(..., alias="congestionRisk")
    carrier_risk: float = Field(..., alias="carrierRisk")
    total_risk: float = Field(..., alias="totalRisk")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class TrackingTimelineResponse(BaseModel):
    shipment_id: UUID = Field(..., alias="shipmentId")
    events: List[TrackingEventResponse]
    risk_timeline: List[RiskPoint] = Field(..., alias="riskTimeline")
    latest_position: Optional[TrackingEventResponse] = Field(None, alias="latestPosition")
    latest_risk: Optional[RiskPoint] = Field(None, alias="latestRisk")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

