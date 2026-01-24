"""
Pydantic schemas for claims.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LossType(str, Enum):
    """Loss type"""
    DAMAGE = "DAMAGE"
    LOSS = "LOSS"
    DELAY = "DELAY"
    CONTAMINATION = "CONTAMINATION"


class ClaimStatus(str, Enum):
    """Claim status"""
    FNOL_RECEIVED = "FNOL_RECEIVED"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    AWAITING_EVIDENCE = "AWAITING_EVIDENCE"
    APPROVED = "APPROVED"
    DECLINED = "DECLINED"
    AUTHORIZED = "AUTHORIZED"
    PAID = "PAID"
    CLOSED = "CLOSED"
    WITHDRAWN = "WITHDRAWN"


class FNOLRequest(BaseModel):
    """First Notice of Loss request."""
    loss_date: str = Field(description="Loss date (ISO format)")
    loss_location: str = Field(description="Loss location")
    loss_description: str = Field(description="Loss description")
    loss_type: LossType = Field(description="Type of loss")
    estimated_loss_cents: int = Field(gt=0, description="Estimated loss in cents")
    currency: Optional[str] = Field(default="USD", max_length=3, description="Currency code")
    reported_by: str = Field(description="Person who reported the loss")


class AdjudicationRequest(BaseModel):
    """Adjudication request."""
    decision: str = Field(description="Decision: APPROVED or DECLINED")
    reason: str = Field(min_length=1, description="Reason for decision")
    coverage_applies: bool = Field(default=True, description="Whether coverage applies")
    approved_amount_cents: Optional[int] = Field(None, ge=0, description="Approved amount in cents (if approved)")
    exclusions_checked: List[str] = Field(default_factory=list, description="Exclusions checked")
    calculation_method: Optional[str] = Field(None, description="Calculation method used")
    adjustments: List[Dict[str, Any]] = Field(default_factory=list, description="Adjustments made")
    notes: Optional[str] = Field(None, description="Adjudication notes")


class ClaimResponse(BaseModel):
    """Claim response (summary)."""
    id: str = Field(description="Claim ID (ULID)")
    tenant_id: str = Field(description="Tenant ID (ULID)")
    claim_number: str = Field(description="Claim number")
    policy_id: str = Field(description="Policy ID (ULID)")
    status: ClaimStatus = Field(description="Claim status")
    
    # FNOL snapshot
    fnol: Dict[str, Any] = Field(description="FNOL snapshot")
    
    # Evidence
    evidence_bundle_id: Optional[str] = Field(None, description="Evidence bundle ID (UUID)")
    
    # Investigation
    assigned_adjuster_id: Optional[str] = Field(None, description="Assigned adjuster ID (ULID)")
    assigned_at: Optional[datetime] = Field(None, description="Assignment timestamp")
    
    # Decision
    decision: Optional[str] = Field(None, description="Decision: APPROVED or DECLINED")
    approved_amount_cents: Optional[int] = Field(None, description="Approved amount in cents")
    approved_currency: Optional[str] = Field(None, description="Approved currency")
    
    # Payout
    payout_id: Optional[str] = Field(None, description="Payout ID (UUID)")
    
    # Timestamps
    created_at: datetime = Field(description="Created at")
    closed_at: Optional[datetime] = Field(None, description="Closed at")
    
    class Config:
        from_attributes = True


class ClaimDetailResponse(ClaimResponse):
    """Claim detail response with full data."""
    investigation_notes: Optional[str] = Field(None, description="Investigation notes")
    decision_reason: Optional[str] = Field(None, description="Decision reason")
    adjudication: Optional[Dict[str, Any]] = Field(None, description="Adjudication details")
    
    class Config:
        from_attributes = True


class ClaimEventResponse(BaseModel):
    """Claim event response."""
    id: str = Field(description="Event ID (ULID)")
    claim_id: str = Field(description="Claim ID (ULID)")
    event_type: str = Field(description="Event type")
    from_status: Optional[str] = Field(None, description="From status")
    to_status: Optional[str] = Field(None, description="To status")
    actor_type: str = Field(description="Actor type")
    actor_id: Optional[str] = Field(None, description="Actor ID (ULID)")
    payload: Optional[Dict[str, Any]] = Field(None, description="Event payload")
    created_at: datetime = Field(description="Created at")
    
    class Config:
        from_attributes = True
