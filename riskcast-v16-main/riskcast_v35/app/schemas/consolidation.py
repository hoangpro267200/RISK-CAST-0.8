from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConsolidationPlanRequest(BaseModel):
    shipment_ids: Optional[List[UUID]] = Field(None, alias="shipmentIds")
    pol: Optional[str] = None
    pod: Optional[str] = None
    etd_from: Optional[datetime] = Field(None, alias="etdFrom")
    etd_to: Optional[datetime] = Field(None, alias="etdTo")
    container_capacity_cbm: float = Field(28.0, alias="containerCapacityCbm")
    lcl_rate_per_cbm: float = Field(..., alias="lclRatePerCbm")
    fcl_rate_per_container: float = Field(..., alias="fclRatePerContainer")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ContainerAssignment(BaseModel):
    container_id: str = Field(..., alias="containerId")
    total_volume: float = Field(..., alias="totalVolume")
    total_weight: float = Field(..., alias="totalWeight")
    shipment_ids: List[UUID] = Field(..., alias="shipmentIds")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ConsolidationPlanResponse(BaseModel):
    plan_id: UUID = Field(..., alias="planId")
    pol: str
    pod: str
    containers: List[ContainerAssignment]
    baseline_lcl_cost: float = Field(..., alias="baselineLclCost")
    optimized_fcl_cost: float = Field(..., alias="optimizedFclCost")
    saving_amount: float = Field(..., alias="savingAmount")
    saving_percent: float = Field(..., alias="savingPercent")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

