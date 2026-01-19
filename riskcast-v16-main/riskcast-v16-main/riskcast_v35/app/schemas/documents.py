from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    shipment_id: UUID = Field(..., alias="shipmentId")
    doc_type: str = Field(..., alias="docType")
    content_json: Dict[str, Any] = Field(..., alias="contentJson")
    file_path: Optional[str] = Field(None, alias="filePath")
    status: Optional[str] = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    id: UUID
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True

