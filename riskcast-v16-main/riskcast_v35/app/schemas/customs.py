from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CustomsProfileBase(BaseModel):
    shipment_id: UUID = Field(..., alias="shipmentId")
    hs_code: Optional[str] = Field(None, alias="hsCode")
    declaration_xml: Optional[str] = Field(None, alias="declarationXml")
    risk_flag: Optional[int] = Field(None, alias="riskFlag")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class CustomsProfileResponse(CustomsProfileBase):
    id: UUID
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class HSSuggestionRequest(BaseModel):
    description: str


class HSCandidate(BaseModel):
    hs_code: str = Field(..., alias="hsCode")
    label: str
    score: float

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


class HSSuggestionResponse(BaseModel):
    description: str
    candidates: List[HSCandidate]


class CustomsDeclarationResponse(BaseModel):
    shipment_id: UUID = Field(..., alias="shipmentId")
    hs_code: str = Field(..., alias="hsCode")
    declaration_xml: str = Field(..., alias="declarationXml")
    created_at: datetime = Field(..., alias="createdAt")

    class Config:
        allow_population_by_field_name = True
        orm_mode = True

