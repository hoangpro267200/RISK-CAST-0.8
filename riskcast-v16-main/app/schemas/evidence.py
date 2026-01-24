"""
Evidence Object Schemas
Pydantic schemas for evidence object API
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class EvidenceObjectCreate(BaseModel):
    """Schema for creating an evidence object"""
    tenant_id: str = Field(..., description="Tenant ID")
    content_hash: str = Field(..., min_length=64, max_length=64, description="SHA256 hash of content")
    content_type: str = Field(..., max_length=100, description="MIME type")
    content_size_bytes: Optional[int] = Field(None, ge=0, description="Size in bytes")
    storage_uri: str = Field(..., description="Storage URI (s3://bucket/path or file://path)")
    storage_provider: str = Field("local", max_length=50, description="Storage provider (local, s3, etc.)")
    filename: Optional[str] = Field(None, max_length=255, description="Original filename")
    description: Optional[str] = Field(None, description="Description")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    evidence_type: Optional[str] = Field(None, max_length=50, description="Type of evidence (DOCUMENT, IMAGE, DATA_EXPORT, etc.)")
    is_pii: bool = Field(False, description="Whether content contains PII")
    retention_class: str = Field("STANDARD", max_length=50, description="Retention classification")
    created_by_user_id: Optional[str] = Field(None, description="User ID who created this")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "content_type": "application/pdf",
                "content_size_bytes": 1024000,
                "storage_uri": "s3://my-bucket/evidence/2024/12/20/doc.pdf",
                "storage_provider": "s3",
                "filename": "risk_assessment_report.pdf",
                "description": "Risk assessment report for shipment XYZ",
                "metadata_json": {
                    "source": "manual_upload",
                    "tags": ["report", "assessment"]
                },
                "evidence_type": "DOCUMENT",
                "is_pii": False,
                "retention_class": "STANDARD",
                "created_by_user_id": "660e8400-e29b-41d4-a716-446655440000",
                "expires_at": "2025-12-20T00:00:00Z"
            }
        }


class EvidenceObjectResponse(BaseModel):
    """Schema for evidence object response"""
    id: str = Field(..., description="Evidence object ID (UUID)")
    tenant_id: str = Field(..., description="Tenant ID")
    content_hash: str = Field(..., description="SHA256 hash of content")
    content_type: str = Field(..., description="MIME type")
    content_size_bytes: Optional[int] = Field(None, description="Size in bytes")
    storage_uri: str = Field(..., description="Storage URI")
    storage_provider: str = Field(..., description="Storage provider")
    filename: Optional[str] = Field(None, description="Original filename")
    description: Optional[str] = Field(None, description="Description")
    metadata_json: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    evidence_type: Optional[str] = Field(None, description="Type of evidence")
    is_pii: bool = Field(..., description="Whether content contains PII")
    retention_class: str = Field(..., description="Retention classification")
    created_by_user_id: Optional[str] = Field(None, description="User ID who created this")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft delete timestamp")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "770e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
                "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "content_type": "application/pdf",
                "content_size_bytes": 1024000,
                "storage_uri": "s3://my-bucket/evidence/2024/12/20/doc.pdf",
                "storage_provider": "s3",
                "filename": "risk_assessment_report.pdf",
                "description": "Risk assessment report for shipment XYZ",
                "metadata_json": {
                    "source": "manual_upload",
                    "tags": ["report", "assessment"]
                },
                "evidence_type": "DOCUMENT",
                "is_pii": False,
                "retention_class": "STANDARD",
                "created_by_user_id": "660e8400-e29b-41d4-a716-446655440000",
                "created_at": "2024-12-20T10:00:00Z",
                "expires_at": "2025-12-20T00:00:00Z",
                "deleted_at": None
            }
        }


class EvidenceObjectListResponse(BaseModel):
    """Schema for evidence object list response"""
    items: list[EvidenceObjectResponse] = Field(..., description="List of evidence objects")
    total: int = Field(..., description="Total count")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    
    class Config:
        from_attributes = True


class EvidenceLinkResponse(BaseModel):
    """Schema for evidence link response"""
    id: str = Field(..., description="Link ID")
    tenant_id: str = Field(..., description="Tenant ID")
    evidence_id: str = Field(..., description="Evidence object ID")
    entity_type: str = Field(..., description="Entity type")
    entity_id: str = Field(..., description="Entity ID")
    link_type: str = Field(..., description="Link type")
    description: Optional[str] = Field(None, description="Description")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True
