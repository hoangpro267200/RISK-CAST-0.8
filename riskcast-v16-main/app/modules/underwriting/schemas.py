"""
Underwriting Schemas
Pydantic schemas for underwriting
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UnderwritingStatus(str, Enum):
    """Underwriting status"""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONDITIONAL = "conditional"


class UnderwritingDecisionCreate(BaseModel):
    """Schema for creating underwriting decision"""
    assessment_id: str
    decision: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)


class UnderwritingDecisionResponse(BaseModel):
    """Schema for underwriting decision response"""
    id: str
    decision_id: str
    assessment_id: str
    tenant_id: str
    status: UnderwritingStatus
    decision: Optional[str] = None
    conditions: List[str] = Field(default_factory=list)
    underwriter_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
