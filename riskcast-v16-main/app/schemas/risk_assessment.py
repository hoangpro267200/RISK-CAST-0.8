"""
Risk Assessment Schemas
Pydantic schemas for risk assessment API v3
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class RiskAssessmentCreateRequest(BaseModel):
    """Schema for creating a risk assessment"""
    shipment_data: Dict[str, Any] = Field(..., description="Shipment data dictionary")
    corridor_id: Optional[str] = Field(None, description="Corridor ID (optional)")
    schema_version: Optional[str] = Field("v1", description="Input schema version")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "shipment_data": {
                    "cargo_value": 100000,
                    "distance": 5000,
                    "origin": "USNYC",
                    "destination": "GBLON"
                },
                "corridor_id": "550e8400-e29b-41d4-a716-446655440000",
                "schema_version": "v1"
            }
        }


class RiskRunSummaryResponse(BaseModel):
    """Summary response for risk run"""
    id: str = Field(..., description="Run ID")
    status: str = Field(..., description="Run status")
    engine_version: str = Field(..., description="Engine version")
    iterations: int = Field(..., description="Number of iterations")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    result_hash: Optional[str] = Field(None, description="Result hash (if completed)")
    
    class Config:
        from_attributes = True


class RiskAssessmentDetailResponse(BaseModel):
    """Detailed response for risk assessment"""
    id: str = Field(..., description="Assessment ID")
    tenant_id: str = Field(..., description="Tenant ID")
    input_hash: str = Field(..., description="SHA256 hash of canonical input")
    schema_version: str = Field(..., description="Input schema version")
    input_snapshot: Dict[str, Any] = Field(..., description="Canonical input snapshot")
    shipment_id: Optional[str] = Field(None, description="Shipment ID")
    corridor_id: Optional[str] = Field(None, description="Corridor ID")
    created_by_user_id: Optional[str] = Field(None, description="User ID who created this")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    runs: List[RiskRunSummaryResponse] = Field(default_factory=list, description="Linked risk runs")
    
    class Config:
        from_attributes = True


class RiskAssessmentResponse(BaseModel):
    """Response for risk assessment (without full snapshot)"""
    id: str = Field(..., description="Assessment ID")
    tenant_id: str = Field(..., description="Tenant ID")
    input_hash: str = Field(..., description="SHA256 hash of canonical input")
    schema_version: str = Field(..., description="Input schema version")
    shipment_id: Optional[str] = Field(None, description="Shipment ID")
    corridor_id: Optional[str] = Field(None, description="Corridor ID")
    created_by_user_id: Optional[str] = Field(None, description="User ID who created this")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class RiskAssessmentListResponse(BaseModel):
    """List response for risk assessments"""
    items: List[RiskAssessmentResponse] = Field(..., description="List of assessments")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    class Config:
        from_attributes = True
