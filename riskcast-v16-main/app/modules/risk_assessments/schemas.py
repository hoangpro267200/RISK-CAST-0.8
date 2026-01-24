"""
Risk Assessments Schemas
Pydantic schemas for risk assessments
RISKCAST V3 - Modular Monolith
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
import json


class RiskAssessmentInputV3(BaseModel):
    """
    Canonical v3 input schema for risk assessments.
    
    This is the normalized, versioned input format that gets stored
    in input_snapshot_json and hashed for deduplication.
    """
    # Origin location
    origin: Dict[str, Any] = Field(..., description="Origin location details")
    
    # Destination location
    destination: Dict[str, Any] = Field(..., description="Destination location details")
    
    # Cargo information
    cargo: Dict[str, Any] = Field(..., description="Cargo details")
    
    # Route parameters (optional)
    route_params: Optional[Dict[str, Any]] = Field(None, description="Route-specific parameters")
    
    # Transport mode
    transport_mode: Optional[str] = Field(None, description="Transport mode (sea, air, road, rail)")
    
    # Additional metadata
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        extra = 'forbid'  # Reject unknown fields
        json_schema_extra = {
            "example": {
                "origin": {
                    "port_code": "VNHPH",
                    "country": "VN",
                    "coordinates": {"lat": 20.8449, "lon": 106.6881}
                },
                "destination": {
                    "port_code": "USLAX",
                    "country": "US",
                    "coordinates": {"lat": 33.9416, "lon": -118.4085}
                },
                "cargo": {
                    "type": "electronics",
                    "value_usd": 100000,
                    "weight_kg": 1000
                },
                "route_params": {
                    "preferred_carrier": "MAERSK",
                    "transit_time_days": 30
                },
                "transport_mode": "sea"
            }
        }
    
    def compute_hash(self) -> str:
        """
        Compute SHA256 hash of canonical JSON representation.
        
        Returns:
            Hex digest of the hash
        """
        # Canonical JSON (sorted keys, no whitespace)
        canonical_json = json.dumps(
            self.model_dump(exclude_none=True, mode='json'),
            sort_keys=True,
            separators=(',', ':')
        )
        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()


class RiskAssessmentCreate(BaseModel):
    """Schema for creating a risk assessment"""
    input_data: RiskAssessmentInputV3 = Field(..., description="Risk assessment input data")
    shipment_id: Optional[str] = Field(None, description="Legacy shipment ID link")
    corridor_id: Optional[str] = Field(None, description="Corridor identifier")
    product_type: Optional[str] = Field(None, description="Product type identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "input_data": {
                    "origin": {"port_code": "VNHPH", "country": "VN"},
                    "destination": {"port_code": "USLAX", "country": "US"},
                    "cargo": {"type": "electronics", "value_usd": 100000}
                },
                "shipment_id": "SHIP-12345",
                "corridor_id": "VN-US-WEST",
                "product_type": "standard"
            }
        }


class RiskAssessmentUpdate(BaseModel):
    """Schema for updating a risk assessment"""
    status: Optional[str] = Field(None, description="New status (DRAFT, READY, ARCHIVED)")
    shipment_id: Optional[str] = Field(None, description="Legacy shipment ID link")
    corridor_id: Optional[str] = Field(None, description="Corridor identifier")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ['DRAFT', 'READY', 'ARCHIVED']:
            raise ValueError("Status must be one of: DRAFT, READY, ARCHIVED")
        return v


class RiskAssessmentResponse(BaseModel):
    """Schema for risk assessment response"""
    id: str = Field(..., description="Assessment ID (ULID)")
    tenant_id: str = Field(..., description="Tenant ID")
    created_by_user_id: Optional[str] = Field(None, description="User who created the assessment")
    status: str = Field(..., description="Assessment status")
    input_schema_version: str = Field(..., description="Input schema version")
    input_hash: str = Field(..., description="SHA256 hash of input data")
    shipment_id: Optional[str] = Field(None, description="Legacy shipment ID")
    corridor_id: Optional[str] = Field(None, description="Corridor identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "tenant_id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
                "created_by_user_id": "01ARZ3NDEKTSV4RRFFQ69G5FAX",
                "status": "READY",
                "input_schema_version": "risk_input_v3.0",
                "input_hash": "a1b2c3d4e5f6...",
                "shipment_id": "SHIP-12345",
                "corridor_id": "VN-US-WEST",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }


class RiskAssessmentListResponse(BaseModel):
    """Schema for paginated list of risk assessments"""
    items: list[RiskAssessmentResponse] = Field(..., description="List of assessments")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_prev: bool = Field(..., description="Whether there are previous pages")
