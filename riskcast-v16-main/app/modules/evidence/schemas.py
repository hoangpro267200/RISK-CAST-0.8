"""
Evidence Schemas
Pydantic schemas for evidence
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class EvidenceType(str, Enum):
    """Types of evidence"""
    WEATHER_REPORT = "weather_report"
    PORT_DATA = "port_data"
    CARRIER_PERFORMANCE = "carrier_performance"
    DOCUMENT = "document"
    IMAGE = "image"
    OTHER = "other"


class EvidenceBase(BaseModel):
    """Base evidence schema"""
    evidence_type: EvidenceType
    title: str
    description: Optional[str] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    """Schema for creating evidence"""
    assessment_id: str


class EvidenceResponse(EvidenceBase):
    """Schema for evidence response"""
    id: str
    evidence_id: str
    assessment_id: str
    tenant_id: str
    file_name: Optional[str] = None
    file_size: Optional[str] = None
    mime_type: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True
