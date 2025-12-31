from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ShipmentBase(BaseModel):
    ref_code: str = Field(..., alias="refCode")
    shipper_name: Optional[str] = Field(None, alias="shipperName")
    consignee_name: Optional[str] = Field(None, alias="consigneeName")
    pol: str
    pod: str
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    status: Optional[str] = None
    price_info: Optional[Dict[str, Any]] = Field(None, alias="priceInfo")
    consolidation_info: Optional[Dict[str, Any]] = Field(None, alias="consolidationInfo")
    documents_info: Optional[Dict[str, Any]] = Field(None, alias="documentsInfo")
    customs_info: Optional[Dict[str, Any]] = Field(None, alias="customsInfo")
    risk_info: Optional[Dict[str, Any]] = Field(None, alias="riskInfo")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    shipper_name: Optional[str] = Field(None, alias="shipperName")
    consignee_name: Optional[str] = Field(None, alias="consigneeName")
    pol: Optional[str] = None
    pod: Optional[str] = None
    etd: Optional[datetime] = None
    eta: Optional[datetime] = None
    status: Optional[str] = None
    price_info: Optional[Dict[str, Any]] = Field(None, alias="priceInfo")
    consolidation_info: Optional[Dict[str, Any]] = Field(None, alias="consolidationInfo")
    documents_info: Optional[Dict[str, Any]] = Field(None, alias="documentsInfo")
    customs_info: Optional[Dict[str, Any]] = Field(None, alias="customsInfo")
    risk_info: Optional[Dict[str, Any]] = Field(None, alias="riskInfo")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentResponse(ShipmentBase):
    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


# Summary DTOs
from app.schemas.pricing import PricingOption
from app.schemas.risk import RiskSnapshotResponse
from app.schemas.tracking import TrackingEventResponse


class ShipmentCoreInfo(BaseModel):
    id: UUID
    ref_code: str = Field(..., alias="refCode")
    shipper_name: str = Field(..., alias="shipperName")
    consignee_name: str = Field(..., alias="consigneeName")
    pol: str
    pod: str
    etd: datetime
    eta: Optional[datetime]
    status: str

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentPricingInfo(BaseModel):
    available: bool = False
    best_option: Optional[PricingOption] = Field(None, alias="bestOption")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentConsolidationInfo(BaseModel):
    available: bool = False
    plan_id: Optional[UUID] = Field(None, alias="planId")
    containers_count: Optional[int] = Field(None, alias="containersCount")
    saving_percent: Optional[float] = Field(None, alias="savingPercent")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentDocumentsInfo(BaseModel):
    si_exists: bool
    bl_draft_exists: bool
    bl_final_exists: bool


class ShipmentTrackingInfo(BaseModel):
    has_tracking: bool
    latest_position: Optional[TrackingEventResponse] = Field(None, alias="latestPosition")
    latest_risk: Optional[RiskSnapshotResponse] = Field(None, alias="latestRisk")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentCustomsInfo(BaseModel):
    has_customs_profile: bool
    hs_code: Optional[str] = Field(None, alias="hsCode")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class ShipmentSummaryResponse(BaseModel):
    shipment: ShipmentCoreInfo
    pricing: ShipmentPricingInfo
    consolidation: ShipmentConsolidationInfo
    documents: ShipmentDocumentsInfo
    tracking: ShipmentTrackingInfo
    customs: ShipmentCustomsInfo

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

