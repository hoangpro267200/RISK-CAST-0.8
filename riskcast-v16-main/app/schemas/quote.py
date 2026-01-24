"""
Pydantic schemas for quotes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    REPLACED = "REPLACED"


class QuotePricingInput(BaseModel):
    """Pricing input for quote calculation."""
    insured_value_cents: int = Field(gt=0, description="Insured value in cents")
    currency: str = Field(default="USD", max_length=3, description="Currency code")
    deductible_cents: int = Field(ge=0, default=0, description="Deductible in cents")
    minimum_premium_cents: Optional[int] = Field(None, ge=0, description="Minimum premium in cents")


class CoverageTerms(BaseModel):
    """Coverage terms for a quote."""
    coverage_type: str = Field(description="Type of coverage")
    extensions: List[str] = Field(default_factory=list, description="Coverage extensions")
    exclusions: List[str] = Field(default_factory=list, description="Exclusions")
    limits: Dict[str, Any] = Field(default_factory=dict, description="Coverage limits")
    conditions: List[str] = Field(default_factory=list, description="Policy conditions")


class QuoteCreateRequest(BaseModel):
    """Request to create a new quote."""
    submission_id: str = Field(description="Submission ID (ULID)")
    risk_run_id: str = Field(description="Risk run ID (ULID)")
    pricing_input: QuotePricingInput = Field(description="Pricing input")
    coverage_terms: CoverageTerms = Field(description="Coverage terms")
    evidence_bundle_id: Optional[str] = Field(None, description="Evidence bundle ID (UUID)")
    validity_days: Optional[int] = Field(default=30, ge=1, le=90, description="Validity period in days")


class QuoteReviseRequest(BaseModel):
    """Request to revise an existing quote."""
    pricing_input: QuotePricingInput = Field(description="New pricing input")
    coverage_terms: Optional[CoverageTerms] = Field(None, description="New coverage terms (uses original if not provided)")
    revision_reason: str = Field(min_length=1, description="Reason for revision")


class PricingBreakdown(BaseModel):
    """Breakdown of premium components."""
    base_premium_cents: int = Field(description="Base premium in cents")
    risk_loading_cents: int = Field(description="Risk loading in cents")
    taxes_fees_cents: int = Field(description="Taxes and fees in cents")


class PricingSnapshot(BaseModel):
    """Pricing snapshot (immutable after issuance)."""
    premium_cents: int = Field(description="Total premium in cents")
    currency: str = Field(description="Currency code")
    premium_breakdown: PricingBreakdown = Field(description="Premium breakdown")
    insured_value_cents: int = Field(description="Insured value in cents")
    deductible_cents: int = Field(description="Deductible in cents")
    rate_per_mille: float = Field(description="Rate per mille")
    risk_score_used: float = Field(description="Risk score used in calculation")
    expected_loss_rate: float = Field(description="Expected loss rate")


class RiskSummary(BaseModel):
    """Risk summary from risk run."""
    overall_risk_score: float = Field(description="Overall risk score")
    risk_factors: Dict[str, float] = Field(default_factory=dict, description="Risk factors")
    var_95: float = Field(description="Value at Risk 95%")
    var_99: Optional[float] = Field(None, description="Value at Risk 99%")
    expected_loss_cents: int = Field(description="Expected loss in cents")


class QuoteResponse(BaseModel):
    """Quote response (summary)."""
    id: str = Field(description="Quote ID (UUID)")
    tenant_id: str = Field(description="Tenant ID (ULID)")
    quote_number: str = Field(description="Quote number")
    submission_id: str = Field(description="Submission ID (ULID)")
    version: int = Field(description="Version number")
    is_latest: bool = Field(description="Is latest version")
    status: QuoteStatus = Field(description="Quote status")
    
    # Pinned references
    model_version_id: str = Field(description="Model version ID (ULID)")
    risk_run_id: str = Field(description="Risk run ID (ULID)")
    evidence_bundle_id: Optional[str] = Field(None, description="Evidence bundle ID (UUID)")
    
    # Quote hash
    quote_hash: Optional[str] = Field(None, description="Quote hash (SHA256)")
    
    # Validity
    valid_from: datetime = Field(description="Valid from")
    valid_until: datetime = Field(description="Valid until")
    
    # Timestamps
    issued_at: Optional[datetime] = Field(None, description="Issued at")
    accepted_at: Optional[datetime] = Field(None, description="Accepted at")
    created_at: datetime = Field(description="Created at")
    
    class Config:
        from_attributes = True


class QuoteDetailResponse(QuoteResponse):
    """Quote detail response with full data."""
    pricing_snapshot: PricingSnapshot = Field(description="Pricing snapshot")
    coverage_terms: CoverageTerms = Field(description="Coverage terms")
    risk_summary: Optional[RiskSummary] = Field(None, description="Risk summary")
    replaces_quote_id: Optional[str] = Field(None, description="Replaced quote ID (UUID)")
    
    class Config:
        from_attributes = True


class QuoteVersionHistoryResponse(BaseModel):
    """Quote version history response."""
    submission_id: str = Field(description="Submission ID (ULID)")
    versions: List[QuoteResponse] = Field(description="All quote versions")
    latest_version: int = Field(description="Latest version number")


class QuoteIntegrityResponse(BaseModel):
    """Quote integrity verification response."""
    valid: Optional[bool] = Field(None, description="Hash is valid (None if not issued)")
    stored_hash: Optional[str] = Field(None, description="Stored hash")
    computed_hash: Optional[str] = Field(None, description="Computed hash")
    verified_at: Optional[str] = Field(None, description="Verification timestamp")
    message: Optional[str] = Field(None, description="Verification message")
