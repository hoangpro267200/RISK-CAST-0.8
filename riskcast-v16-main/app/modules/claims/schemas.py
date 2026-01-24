"""
Claims Schemas
Pydantic schemas for claims
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ClaimStatus(str, Enum):
    """Claim status"""
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    CLOSED = "closed"


class ClaimType(str, Enum):
    """Claim type"""
    CLASSICAL_MANUAL = "classical_manual"
    PARAMETRIC_AUTOMATIC = "parametric_automatic"


class ClaimCreate(BaseModel):
    """Schema for creating a claim"""
    policy_id: Optional[str] = None
    assessment_id: Optional[str] = None
    claim_type: ClaimType
    incident_date: Optional[datetime] = None
    loss_type: Optional[str] = None
    estimated_loss_usd: Optional[float] = None
    description: Optional[str] = None
    documents: List[str] = Field(default_factory=list)


class ClaimResponse(BaseModel):
    """Schema for claim response"""
    id: str
    claim_number: str
    policy_id: Optional[str] = None
    assessment_id: Optional[str] = None
    tenant_id: str
    claim_type: ClaimType
    status: ClaimStatus
    incident_date: Optional[datetime] = None
    loss_type: Optional[str] = None
    estimated_loss_usd: Optional[float] = None
    approved_amount_usd: Optional[float] = None
    paid_amount_usd: Optional[float] = None
    description: Optional[str] = None
    documents: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
