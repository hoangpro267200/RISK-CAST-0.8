"""
Quote Management API Endpoints

Public API for:
- Request quotes
- View quotes
- Accept/decline quotes
- Quote analytics
"""

from datetime import datetime, date
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_audit
from app.shared.dependencies import get_current_user
from app.quotes.quote_manager import QuoteManager, QuoteStatus, DeclineReason
from app.pricing.pricing_engine import PricingEngine, CoverageType, DeductibleType
from app.core.audit.immutable_ledger import ImmutableAuditLedger


router = APIRouter(prefix="/quotes", tags=["Quotes"])


# ============================================================================
# Schemas
# ============================================================================

class QuoteRequest(BaseModel):
    """Request for a new quote."""
    # Shipment details
    origin_port: str = Field(..., description="Origin port code (e.g., CNSHA)")
    destination_port: str = Field(..., description="Destination port code (e.g., USLAX)")
    cargo_type: str = Field(..., description="Cargo type (e.g., ELECTRONICS)")
    cargo_value_usd: float = Field(..., gt=0, description="Cargo value in USD")
    container_count: int = Field(default=1, ge=1, description="Number of containers")
    packaging_quality: str = Field(default="STANDARD", description="BASIC, STANDARD, PREMIUM")
    
    # Dates
    departure_date: date = Field(..., description="Expected departure date")
    arrival_date: date = Field(..., description="Expected arrival date")
    
    # Carrier (optional)
    carrier_code: Optional[str] = Field(None, description="Carrier SCAC code")
    
    # Coverage options
    coverage_type: str = Field(default="ALL_RISKS", description="ALL_RISKS, NAMED_PERILS, TOTAL_LOSS_ONLY")
    coverage_limit_usd: Optional[float] = Field(None, description="Coverage limit (defaults to cargo value)")
    deductible_type: str = Field(default="PERCENTAGE", description="FIXED, PERCENTAGE, FRANCHISE")
    deductible_value: float = Field(default=0.01, description="Deductible value (amount or percentage)")
    
    # Optional add-ons
    include_war_risk: bool = Field(default=False, description="Include war risk coverage")
    include_strikes: bool = Field(default=False, description="Include strikes coverage")


class QuoteSummaryResponse(BaseModel):
    """Summary response for a quote."""
    quote_id: str
    quote_number: str
    status: str
    
    # Key figures
    cargo_value_usd: float
    total_premium_usd: float
    rate_per_mille: float
    
    # Risk
    risk_score: float
    risk_grade: str
    
    # Route
    origin: str
    destination: str
    
    # Validity
    created_at: datetime
    valid_until: datetime


class QuoteDetailResponse(BaseModel):
    """Detailed response for a quote."""
    quote_id: str
    quote_number: str
    status: str
    
    # Shipment
    origin_port: str
    destination_port: str
    cargo_type: str
    cargo_value_usd: float
    container_count: int
    transit_days: int
    departure_date: Optional[date]
    arrival_date: Optional[date]
    
    # Coverage
    coverage_type: str
    coverage_limit_usd: float
    deductible_amount: float
    deductible_description: str
    
    # Pricing
    total_premium_usd: float
    rate_per_mille: float
    pricing_breakdown: dict
    
    # Risk
    risk_score: float
    risk_grade: str
    expected_loss_ratio: float
    
    # Terms
    terms: dict
    exclusions: List[str]
    
    # Recommendations
    recommendations: List[str]
    
    # Validity
    valid_from: datetime
    valid_until: datetime
    
    # Metadata
    version: int
    created_at: datetime


class QuoteAcceptRequest(BaseModel):
    """Request to accept a quote."""
    acceptance_notes: Optional[str] = None


class QuoteDeclineRequest(BaseModel):
    """Request to decline a quote."""
    reason: str = Field(..., description="Decline reason code")
    reason_details: Optional[str] = None


class QuoteModifyRequest(BaseModel):
    """Request to modify a quote."""
    cargo_value_usd: Optional[float] = None
    coverage_limit_usd: Optional[float] = None
    deductible_value: Optional[float] = None
    coverage_type: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/request", response_model=QuoteDetailResponse)
async def request_quote(
    request: QuoteRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Request a new insurance quote.
    
    This runs a full risk assessment and calculates premium.
    Returns detailed quote with pricing breakdown.
    """
    # Import services
    from app.services.unified_data_service import UnifiedDataService
    from app.modules.model_versioning.models import RiskModelVersion
    from app.models.system_config import SystemConfig
    from app.core.risk_engine.v16.risk_engine_calibrated import (
        CalibratedRiskEngine,
        create_calibrated_risk_engine
    )
    
    # Get active model version
    config = db.query(SystemConfig).filter(
        SystemConfig.key == "active_model_version_id"
    ).first()
    
    if not config:
        raise HTTPException(status_code=500, detail="No active model version configured")
    
    model_version = db.query(RiskModelVersion).filter(
        RiskModelVersion.id == config.value
    ).first()
    
    if not model_version:
        raise HTTPException(status_code=500, detail="Active model version not found")
    
    # Collect data
    data_service = UnifiedDataService(audit=audit)
    shipment_data = await data_service.collect_shipment_data(
        origin_port=request.origin_port,
        destination_port=request.destination_port,
        cargo_type=request.cargo_type,
        cargo_value_usd=request.cargo_value_usd,
        container_count=request.container_count,
        departure_date=request.departure_date,
        expected_arrival_date=request.arrival_date,
        carrier_code=request.carrier_code
    )
    
    # Run risk assessment
    risk_engine = create_calibrated_risk_engine(
        model_version=model_version,
        audit=audit
    )
    risk_result = await risk_engine.run_assessment(
        shipment_data=shipment_data,
        cargo_value_usd=request.cargo_value_usd
    )
    
    # Create quote
    pricing_engine = PricingEngine(audit=audit)
    
    # Get tenant_id from request if available
    tenant_id = None
    if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    elif hasattr(current_user, 'id'):
        # Try to get from membership or context
        pass
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    # Convert coverage type string to enum
    try:
        coverage_type_enum = CoverageType[request.coverage_type]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid coverage_type: {request.coverage_type}")
    
    try:
        deductible_type_enum = DeductibleType[request.deductible_type]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid deductible_type: {request.deductible_type}")
    
    coverage_options = {
        "coverage_type": coverage_type_enum,
        "coverage_limit_usd": request.coverage_limit_usd,
        "deductible_type": deductible_type_enum,
        "deductible_value": Decimal(str(request.deductible_value)),
        "include_war_risk": request.include_war_risk,
        "include_strikes": request.include_strikes
    }
    
    shipment_details = {
        "origin_port": request.origin_port,
        "destination_port": request.destination_port,
        "cargo_type": request.cargo_type,
        "cargo_value_usd": request.cargo_value_usd,
        "container_count": request.container_count,
        "packaging_quality": request.packaging_quality,
        "departure_date": request.departure_date,
        "arrival_date": request.arrival_date,
        "transit_days": (request.arrival_date - request.departure_date).days
    }
    
    # Get customer_id from user if available
    customer_id = None
    created_by_user_id = None
    if current_user:
        created_by_user_id = str(current_user.id) if hasattr(current_user, 'id') else None
        # Would get customer_id from user relationship
        # For now, use None
    
    # Note: submission_id is optional - quote_manager will create placeholder if needed
    quote = await quote_manager.create_quote(
        risk_result=risk_result,
        shipment_details=shipment_details,
        coverage_options=coverage_options,
        submission_id=None,  # Would create submission in production
        customer_id=customer_id,
        created_by_user_id=created_by_user_id,
        tenant_id=tenant_id
    )
    
    return _to_detail_response(quote)


@router.get("/", response_model=List[QuoteSummaryResponse])
async def list_quotes(
    status: Optional[str] = Query(None, description="Filter by status"),
    created_after: Optional[datetime] = Query(None, description="Filter by creation date"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    List quotes for the current user/customer.
    """
    pricing_engine = PricingEngine(audit=audit)
    
    # Get tenant_id
    tenant_id = None
    if current_user and hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    status_filter = None
    if status:
        try:
            status_filter = QuoteStatus[status]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    customer_id = None
    if current_user:
        # Would get customer_id from user relationship
        pass
    
    quotes = await quote_manager.list_quotes(
        customer_id=customer_id,
        status=status_filter,
        created_after=created_after,
        tenant_id=tenant_id,
        limit=limit
    )
    
    return [
        QuoteSummaryResponse(
            quote_id=q.quote_id,
            quote_number=q.quote_number,
            status=q.status.value,
            cargo_value_usd=float(q.cargo_value_usd),
            total_premium_usd=float(q.total_premium_usd),
            rate_per_mille=float(q.total_premium_usd / q.cargo_value_usd * 1000) if q.cargo_value_usd > 0 else 0,
            risk_score=0.0,  # Would come from quote detail
            risk_grade=q.risk_grade,
            origin=q.origin,
            destination=q.destination,
            created_at=q.created_at,
            valid_until=q.valid_until
        )
        for q in quotes
    ]


@router.get("/{quote_id}", response_model=QuoteDetailResponse)
async def get_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Get detailed quote information.
    """
    pricing_engine = PricingEngine(audit=audit)
    
    tenant_id = None
    if current_user and hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    quote = await quote_manager.get_quote(quote_id)
    
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")
    
    return _to_detail_response(quote)


@router.post("/{quote_id}/accept")
async def accept_quote(
    quote_id: str,
    request: QuoteAcceptRequest,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Accept a quote.
    
    This marks the quote as accepted. To convert to a policy,
    use the /bind endpoint.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    pricing_engine = PricingEngine(audit=audit)
    
    tenant_id = None
    if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    try:
        quote = await quote_manager.accept_quote(
            quote_id=quote_id,
            accepted_by_user_id=str(current_user.id) if hasattr(current_user, 'id') else None,
            acceptance_notes=request.acceptance_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "status": "ACCEPTED",
        "quote_id": quote.quote_id,
        "quote_number": quote.quote_number,
        "message": "Quote accepted. Use /bind to convert to policy.",
        "next_step": f"/api/v3/quotes/{quote_id}/bind"
    }


@router.post("/{quote_id}/decline")
async def decline_quote(
    quote_id: str,
    request: QuoteDeclineRequest,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Decline a quote.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    pricing_engine = PricingEngine(audit=audit)
    
    tenant_id = None
    if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    try:
        reason = DeclineReason[request.reason]
    except KeyError:
        raise HTTPException(status_code=400, detail=f"Invalid decline reason: {request.reason}")
    
    try:
        quote = await quote_manager.decline_quote(
            quote_id=quote_id,
            declined_by_user_id=str(current_user.id) if hasattr(current_user, 'id') else None,
            reason=reason,
            reason_details=request.reason_details
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "status": "DECLINED",
        "quote_id": quote.quote_id,
        "quote_number": quote.quote_number,
        "reason": request.reason
    }


@router.post("/{quote_id}/bind")
async def bind_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Bind an accepted quote to create a policy.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    pricing_engine = PricingEngine(audit=audit)
    
    tenant_id = None
    if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    try:
        policy_id = await quote_manager.bind_quote_to_policy(
            quote_id=quote_id,
            bound_by_user_id=str(current_user.id) if hasattr(current_user, 'id') else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return {
        "status": "BOUND",
        "quote_id": quote_id,
        "policy_id": policy_id,
        "message": "Policy created successfully",
        "next_step": f"/api/v3/policies/{policy_id}"
    }


@router.put("/{quote_id}")
async def modify_quote(
    quote_id: str,
    request: QuoteModifyRequest,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Modify a pending quote.
    
    This will trigger a premium recalculation.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    pricing_engine = PricingEngine(audit=audit)
    
    tenant_id = None
    if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    modifications = {k: v for k, v in request.dict().items() if v is not None}
    
    if not modifications:
        raise HTTPException(status_code=400, detail="No modifications provided")
    
    try:
        quote = await quote_manager.modify_quote(
            quote_id=quote_id,
            modifications=modifications,
            modified_by_user_id=str(current_user.id) if hasattr(current_user, 'id') else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return _to_detail_response(quote)


@router.get("/{quote_id}/comparison")
async def compare_quote_options(
    quote_id: str,
    db: Session = Depends(get_db),
    audit: ImmutableAuditLedger = Depends(get_audit),
    current_user = Depends(get_current_user)
):
    """
    Compare different coverage options for a quote.
    
    Returns premium for different deductible levels and coverage types.
    """
    pricing_engine = PricingEngine(audit=audit)
    
    tenant_id = None
    if current_user and hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        tenant_id = current_user.tenant_id
    
    quote_manager = QuoteManager(db, pricing_engine, audit, tenant_id=tenant_id)
    
    quote = await quote_manager.get_quote(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail=f"Quote {quote_id} not found")
    
    # Calculate alternatives (simplified - would actually recalculate)
    base_premium = float(quote.pricing_result.total_premium_usd) if quote.pricing_result else 0
    
    alternatives = {
        "current": {
            "coverage_type": quote.coverage_type,
            "deductible_pct": float(quote.deductible_amount / quote.coverage_limit_usd * 100) if quote.coverage_limit_usd > 0 else 0,
            "premium": base_premium
        },
        "alternatives": [
            {
                "description": "Higher deductible (2%)",
                "coverage_type": quote.coverage_type,
                "deductible_pct": 2.0,
                "premium": base_premium * 0.85,
                "savings": base_premium * 0.15
            },
            {
                "description": "Named Perils only",
                "coverage_type": "NAMED_PERILS",
                "deductible_pct": 1.0,
                "premium": base_premium * 0.75,
                "savings": base_premium * 0.25
            },
            {
                "description": "Total Loss Only",
                "coverage_type": "TOTAL_LOSS_ONLY",
                "deductible_pct": 1.0,
                "premium": base_premium * 0.50,
                "savings": base_premium * 0.50
            }
        ]
    }
    
    return alternatives


# ============================================================================
# Helper Functions
# ============================================================================

def _to_detail_response(quote) -> QuoteDetailResponse:
    """Convert quote detail to response."""
    breakdown = {}
    deductible_desc = ""
    
    if quote.pricing_result and quote.pricing_result.breakdown:
        b = quote.pricing_result.breakdown
        breakdown = {
            "base_premium": float(b.base_premium),
            "risk_adjustment": float(b.risk_adjusted_premium - b.base_premium),
            "loadings": float(b.total_loadings),
            "discounts": float(b.total_discounts),
            "expenses": float(b.expenses_loading),
            "margin": float(b.profit_margin),
            "total": float(b.total_premium)
        }
        deductible_desc = b.deductible_description
    
    return QuoteDetailResponse(
        quote_id=quote.quote_id,
        quote_number=quote.quote_number,
        status=quote.status.value,
        origin_port=quote.origin_port,
        destination_port=quote.destination_port,
        cargo_type=quote.cargo_type,
        cargo_value_usd=float(quote.cargo_value_usd),
        container_count=quote.container_count,
        transit_days=quote.transit_days,
        departure_date=None,  # Would come from quote shipment details
        arrival_date=None,
        coverage_type=quote.coverage_type,
        coverage_limit_usd=float(quote.coverage_limit_usd),
        deductible_amount=float(quote.deductible_amount),
        deductible_description=deductible_desc,
        total_premium_usd=float(quote.pricing_result.total_premium_usd) if quote.pricing_result else 0,
        rate_per_mille=float(quote.pricing_result.premium_rate_per_mille) if quote.pricing_result else 0,
        pricing_breakdown=breakdown,
        risk_score=quote.risk_score,
        risk_grade=quote.risk_grade,
        expected_loss_ratio=quote.pricing_result.expected_loss_ratio if quote.pricing_result else 0,
        terms=quote.terms_and_conditions,
        exclusions=quote.exclusions,
        recommendations=quote.pricing_result.recommendations if quote.pricing_result else [],
        valid_from=quote.valid_from,
        valid_until=quote.valid_until,
        version=quote.version,
        created_at=quote.created_at
    )
