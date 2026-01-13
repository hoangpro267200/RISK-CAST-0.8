from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PricingQuoteRequest(BaseModel):
    pol: str
    pod: str
    etd_from: datetime = Field(..., alias="etdFrom")
    etd_to: datetime = Field(..., alias="etdTo")
    incoterm: Optional[str] = None
    cargo_description: Optional[str] = Field(None, alias="cargoDescription")
    weight: Optional[float] = None
    volume: Optional[float] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PricingOption(BaseModel):
    carrier: str
    pol: str
    pod: str
    etd: datetime
    total_cost: float = Field(..., alias="totalCost")
    currency: str
    risk: Dict[str, float]
    adjusted_cost: float = Field(..., alias="adjustedCost")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class PricingQuoteResponse(BaseModel):
    best_option: Optional[PricingOption] = Field(None, alias="bestOption")
    alternatives: List[PricingOption] = []
    requested_lane: Dict[str, Any] = Field(..., alias="requestedLane")
    generated_at: datetime = Field(..., alias="generatedAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

