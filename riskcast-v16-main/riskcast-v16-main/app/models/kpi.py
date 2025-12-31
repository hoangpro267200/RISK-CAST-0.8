from pydantic import Field
from .base import BaseSchema


class KPI(BaseSchema):
    riskScore: int = Field(default=0, ge=0, le=100)
    transitDays: int = Field(default=0)
    shipmentValue: float = Field(default=0)
    carrierRating: float = Field(default=0)
    delayRisk: float = Field(default=0)
    compliance: float = Field(default=0)
    carbonFootprint: float = Field(default=0)
    onTimeProbability: float = Field(default=0)
    congestion: float = Field(default=0)
    weatherImpact: float = Field(default=0)
    politicalRisk: float = Field(default=0)
    securityRisk: float = Field(default=0)




