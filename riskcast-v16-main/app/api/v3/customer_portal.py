"""
Customer Portal Dashboard API

Customer-facing endpoints for:
- Dashboard summary
- Active policies
- Quotes management
- Claims tracking
- Risk profile
- Personalized recommendations
- Spending analysis
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.api.deps import get_audit
from app.shared.dependencies import get_current_user, resolve_tenant_context, TenantContext
from app.core.audit.immutable_ledger import ImmutableAuditLedger


router = APIRouter(prefix="/portal", tags=["Customer Portal"])


# ============================================================================
# Schemas
# ============================================================================

class DashboardSummary(BaseModel):
    """Customer dashboard summary."""
    # Customer info
    customer_id: Optional[str] = None
    company_name: str
    tier: str
    credit_limit_usd: float
    credit_used_usd: float
    credit_available_usd: float
    
    # Active coverage
    active_policies_count: int
    total_coverage_usd: float
    total_premium_ytd_usd: float
    
    # Quotes
    pending_quotes_count: int
    pending_quotes_value_usd: float
    
    # Claims
    open_claims_count: int
    claims_ytd: int
    claims_paid_ytd_usd: float
    
    # Risk
    current_risk_score: float
    risk_grade: str
    risk_trend: str  # IMPROVING, STABLE, WORSENING
    
    # Alerts
    alerts: List[Dict[str, Any]]
    
    # Quick stats
    shipments_insured_ytd: int
    avg_premium_per_shipment: float


class PolicySummary(BaseModel):
    """Summary of an active policy."""
    policy_id: str
    policy_number: str
    status: str
    
    # Coverage
    coverage_type: str
    coverage_limit_usd: float
    deductible_usd: float
    
    # Premium
    premium_usd: float
    premium_paid: bool
    
    # Shipment
    origin: str
    destination: str
    cargo_type: str
    cargo_value_usd: float
    
    # Dates
    effective_from: date
    effective_to: date
    days_remaining: int
    
    # Risk
    risk_grade: str


class QuoteSummary(BaseModel):
    """Summary of a quote."""
    quote_id: str
    quote_number: str
    status: str
    
    # Shipment
    origin: str
    destination: str
    cargo_type: str
    cargo_value_usd: float
    
    # Pricing
    premium_usd: float
    rate_per_mille: float
    risk_grade: str
    
    # Validity
    created_at: datetime
    valid_until: datetime
    is_expiring_soon: bool  # Within 48 hours


class ClaimSummary(BaseModel):
    """Summary of a claim."""
    claim_id: str
    claim_number: str
    policy_number: str
    status: str
    
    # Amounts
    claimed_amount_usd: float
    approved_amount_usd: Optional[float]
    paid_amount_usd: Optional[float]
    
    # Details
    loss_type: str
    loss_date: Optional[date]
    filed_at: datetime
    
    # Progress
    current_stage: str
    estimated_resolution: Optional[str]
    documents_pending: List[str]


class RiskProfile(BaseModel):
    """Customer risk profile."""
    customer_id: Optional[str] = None
    
    # Overall risk
    overall_risk_score: float
    risk_grade: str
    risk_percentile: int  # vs other customers
    
    # Risk factors
    risk_factors: List[Dict[str, Any]]
    
    # Historical
    risk_history: List[Dict[str, Any]]  # Monthly scores
    
    # Loss history
    loss_ratio_3yr: float
    claims_frequency: float  # Claims per shipment
    avg_claim_severity: float
    
    # Comparison
    industry_avg_loss_ratio: float
    peer_avg_risk_score: float


class Recommendation(BaseModel):
    """Personalized recommendation."""
    id: str
    type: str  # COST_SAVING, RISK_REDUCTION, COVERAGE_GAP, RENEWAL
    priority: str  # HIGH, MEDIUM, LOW
    title: str
    description: str
    potential_benefit: str
    action_url: Optional[str]
    expires_at: Optional[datetime]


class SpendingAnalysis(BaseModel):
    """Premium spending analysis."""
    period: str
    total_premium_usd: float
    
    # Breakdown
    by_cargo_type: Dict[str, float]
    by_route: Dict[str, float]
    by_month: List[Dict[str, Any]]
    
    # Trends
    vs_previous_period_pct: float
    avg_rate_per_mille: float
    rate_trend: str  # DECREASING, STABLE, INCREASING
    
    # Savings
    discounts_applied_usd: float
    potential_savings_usd: float
    savings_recommendations: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get customer dashboard summary.
    
    Overview of policies, quotes, claims, and risk.
    """
    from app.modules.underwriting.models import Policy, PolicyStatus
    from app.models.quote import Quote
    from app.modules.claims.models import Claim, ClaimStatus
    
    tenant_id = tenant_context.tenant_id
    
    # Get customer info (if available through user or tenant)
    # For now, we'll use tenant_id as customer identifier
    company_name = f"Tenant {tenant_id[:8]}"
    tier = "STANDARD"
    credit_limit = 100000.0
    credit_used = 0.0
    
    # Active policies
    active_policies = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.status == PolicyStatus.ACTIVE
    ).all()
    
    total_coverage = 0.0
    for p in active_policies:
        if p.terms_json and isinstance(p.terms_json, dict):
            coverage = p.terms_json.get("coverage_limit_usd", 0)
            if coverage:
                total_coverage += float(coverage)
    
    # YTD premium
    year_start = date(date.today().year, 1, 1)
    year_start_dt = datetime.combine(year_start, datetime.min.time())
    
    ytd_policies = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.effective_from >= year_start_dt
    ).all()
    
    ytd_premium = 0.0
    for p in ytd_policies:
        if p.premium_json and isinstance(p.premium_json, dict):
            premium = p.premium_json.get("total_premium", 0)
            if premium:
                ytd_premium += float(premium)
    
    # Pending quotes
    pending_quotes = db.query(Quote).filter(
        Quote.tenant_id == tenant_id,
        Quote.status.in_(["PENDING", "ISSUED"])
    ).all()
    
    pending_value = 0.0
    for q in pending_quotes:
        if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
            value = q.pricing_snapshot_json.get("cargo_value", 0)
            if value:
                pending_value += float(value)
    
    # Claims
    open_claims = db.query(Claim).filter(
        Claim.tenant_id == tenant_id,
        Claim.status.in_([ClaimStatus.FNOL_RECEIVED, ClaimStatus.UNDER_INVESTIGATION, 
                         ClaimStatus.AWAITING_EVIDENCE, ClaimStatus.APPROVED])
    ).count()
    
    claims_ytd = db.query(Claim).filter(
        Claim.tenant_id == tenant_id,
        Claim.created_at >= year_start_dt
    ).all()
    
    claims_paid_ytd = 0.0
    for c in claims_ytd:
        if c.payouts:
            for payout in c.payouts:
                if payout.amount_cents:
                    claims_paid_ytd += float(payout.amount_cents) / 100.0
    
    # Risk trend (compare last 3 months)
    risk_trend = _calculate_risk_trend(db, tenant_id)
    
    # Alerts
    alerts = _generate_alerts(db, tenant_id, active_policies, pending_quotes)
    
    # Shipments insured YTD
    shipments_ytd = len(ytd_policies)
    
    avg_premium = float(ytd_premium) / shipments_ytd if shipments_ytd > 0 else 0
    
    # Credit calculation (simplified)
    credit_used = float(ytd_premium) * 0.1  # Assume 10% unpaid
    
    # Risk score (simplified - would come from customer model)
    current_risk_score = 0.5
    risk_grade = "C"
    
    return DashboardSummary(
        customer_id=None,
        company_name=company_name,
        tier=tier,
        credit_limit_usd=credit_limit,
        credit_used_usd=credit_used,
        credit_available_usd=credit_limit - credit_used,
        active_policies_count=len(active_policies),
        total_coverage_usd=total_coverage,
        total_premium_ytd_usd=ytd_premium,
        pending_quotes_count=len(pending_quotes),
        pending_quotes_value_usd=pending_value,
        open_claims_count=open_claims,
        claims_ytd=len(claims_ytd),
        claims_paid_ytd_usd=claims_paid_ytd,
        current_risk_score=current_risk_score,
        risk_grade=risk_grade,
        risk_trend=risk_trend,
        alerts=alerts,
        shipments_insured_ytd=shipments_ytd,
        avg_premium_per_shipment=avg_premium
    )


@router.get("/policies", response_model=List[PolicySummary])
async def get_active_policies(
    status: Optional[str] = Query(None, description="Filter by status"),
    include_expired: bool = Query(False, description="Include expired policies"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get customer's policies.
    """
    from app.modules.underwriting.models import Policy, PolicyStatus
    
    tenant_id = tenant_context.tenant_id
    
    query = db.query(Policy).filter(Policy.tenant_id == tenant_id)
    
    if status:
        try:
            status_enum = PolicyStatus[status]
            query = query.filter(Policy.status == status_enum)
        except KeyError:
            raise HTTPException(400, f"Invalid status: {status}")
    elif not include_expired:
        query = query.filter(Policy.status == PolicyStatus.ACTIVE)
    
    policies = query.order_by(Policy.effective_from.desc()).limit(limit).all()
    
    today = date.today()
    
    result = []
    for p in policies:
        # Extract data from JSON fields
        coverage_type = "ALL_RISKS"
        coverage_limit = 0.0
        deductible = 0.0
        premium = 0.0
        origin = ""
        destination = ""
        cargo_type = ""
        cargo_value = 0.0
        risk_grade = "C"
        
        if p.terms_json and isinstance(p.terms_json, dict):
            coverage_type = p.terms_json.get("coverage_type", "ALL_RISKS")
            coverage_limit = float(p.terms_json.get("coverage_limit_usd", 0))
            deductible = float(p.terms_json.get("deductible_amount", 0))
            origin = p.terms_json.get("origin_port", "")
            destination = p.terms_json.get("destination_port", "")
            cargo_type = p.terms_json.get("cargo_type", "")
            cargo_value = float(p.terms_json.get("cargo_value_usd", 0))
        
        if p.premium_json and isinstance(p.premium_json, dict):
            premium = float(p.premium_json.get("total_premium", 0))
        
        if p.risk_snapshot_json and isinstance(p.risk_snapshot_json, dict):
            risk_grade = p.risk_snapshot_json.get("risk_grade", "C")
        
        effective_to_date = p.effective_to.date() if p.effective_to else today
        days_remaining = (effective_to_date - today).days
        
        result.append(PolicySummary(
            policy_id=str(p.id),
            policy_number=p.policy_number,
            status=p.status.value if hasattr(p.status, 'value') else str(p.status),
            coverage_type=coverage_type,
            coverage_limit_usd=coverage_limit,
            deductible_usd=deductible,
            premium_usd=premium,
            premium_paid=True,  # Simplified - would check payment status
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            cargo_value_usd=cargo_value,
            effective_from=p.effective_from.date() if p.effective_from else today,
            effective_to=effective_to_date,
            days_remaining=days_remaining,
            risk_grade=risk_grade
        ))
    
    return result


@router.get("/quotes", response_model=List[QuoteSummary])
async def get_recent_quotes(
    status: Optional[str] = Query(None, description="Filter by status"),
    days: int = Query(30, le=90, description="Days to look back"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get customer's recent quotes.
    """
    from app.models.quote import Quote
    
    tenant_id = tenant_context.tenant_id
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(Quote).filter(
        Quote.tenant_id == tenant_id,
        Quote.created_at >= cutoff
    )
    
    if status:
        query = query.filter(Quote.status == status)
    
    quotes = query.order_by(Quote.created_at.desc()).limit(limit).all()
    
    now = datetime.utcnow()
    soon_threshold = now + timedelta(hours=48)
    
    result = []
    for q in quotes:
        # Extract data from JSON fields
        origin = ""
        destination = ""
        cargo_type = ""
        cargo_value = 0.0
        premium = 0.0
        rate_per_mille = 0.0
        risk_grade = "C"
        
        if q.coverage_terms_json and isinstance(q.coverage_terms_json, dict):
            origin = q.coverage_terms_json.get("origin_port", "")
            destination = q.coverage_terms_json.get("destination_port", "")
            cargo_type = q.coverage_terms_json.get("cargo_type", "")
        
        if q.pricing_snapshot_json and isinstance(q.pricing_snapshot_json, dict):
            cargo_value = float(q.pricing_snapshot_json.get("cargo_value", 0))
            premium = float(q.pricing_snapshot_json.get("total_premium", 0))
            rate_per_mille = float(q.pricing_snapshot_json.get("rate_per_mille", 0))
        
        if q.risk_summary_json and isinstance(q.risk_summary_json, dict):
            risk_grade = q.risk_summary_json.get("risk_grade", "C")
        
        is_expiring_soon = q.valid_until and q.valid_until <= soon_threshold
        
        result.append(QuoteSummary(
            quote_id=str(q.id),
            quote_number=q.quote_number,
            status=q.status,
            origin=origin,
            destination=destination,
            cargo_type=cargo_type,
            cargo_value_usd=cargo_value,
            premium_usd=premium,
            rate_per_mille=rate_per_mille,
            risk_grade=risk_grade,
            created_at=q.created_at,
            valid_until=q.valid_until,
            is_expiring_soon=is_expiring_soon
        ))
    
    return result


@router.get("/claims", response_model=List[ClaimSummary])
async def get_claims(
    status: Optional[str] = Query(None, description="Filter by status"),
    include_closed: bool = Query(False, description="Include closed claims"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get customer's claims.
    """
    from app.modules.claims.models import Claim, ClaimStatus
    from app.modules.underwriting.models import Policy
    
    tenant_id = tenant_context.tenant_id
    
    query = db.query(Claim).join(Policy).filter(
        Policy.tenant_id == tenant_id
    )
    
    if status:
        try:
            status_enum = ClaimStatus[status]
            query = query.filter(Claim.status == status_enum)
        except KeyError:
            raise HTTPException(400, f"Invalid status: {status}")
    elif not include_closed:
        query = query.filter(Claim.status.notin_([ClaimStatus.PAID, ClaimStatus.DECLINED, ClaimStatus.CLOSED]))
    
    claims = query.order_by(Claim.created_at.desc()).limit(limit).all()
    
    result = []
    for c in claims:
        # Extract data from JSON fields
        claimed_amount = 0.0
        loss_type = ""
        loss_date = None
        
        if c.fnol_json and isinstance(c.fnol_json, dict):
            claimed_amount = float(c.fnol_json.get("alleged_loss_amount", 0))
            loss_type = c.fnol_json.get("loss_type", "")
            loss_date_str = c.fnol_json.get("incident_date")
            if loss_date_str:
                try:
                    if isinstance(loss_date_str, str):
                        loss_date = datetime.fromisoformat(loss_date_str.replace('Z', '+00:00')).date()
                    else:
                        loss_date = loss_date_str.date() if hasattr(loss_date_str, 'date') else None
                except:
                    pass
        
        approved_amount = float(c.approved_amount_cents) / 100.0 if c.approved_amount_cents else None
        
        # Get paid amount from payouts
        paid_amount = 0.0
        if c.payouts:
            for payout in c.payouts:
                if payout.amount_cents:
                    paid_amount += float(payout.amount_cents) / 100.0
        
        policy_number = c.policy.policy_number if c.policy else ""
        
        result.append(ClaimSummary(
            claim_id=str(c.id),
            claim_number=c.claim_number or "",
            policy_number=policy_number,
            status=c.status.value if hasattr(c.status, 'value') else str(c.status),
            claimed_amount_usd=claimed_amount,
            approved_amount_usd=approved_amount,
            paid_amount_usd=paid_amount if paid_amount > 0 else None,
            loss_type=loss_type,
            loss_date=loss_date,
            filed_at=c.created_at,
            current_stage=_get_claim_stage(c.status.value if hasattr(c.status, 'value') else str(c.status)),
            estimated_resolution=_estimate_resolution(c),
            documents_pending=_get_pending_documents(c)
        ))
    
    return result


@router.get("/risk-profile", response_model=RiskProfile)
async def get_risk_profile(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get customer's detailed risk profile.
    """
    from app.modules.underwriting.models import Policy
    from app.modules.claims.models import Claim
    
    tenant_id = tenant_context.tenant_id
    
    # Calculate risk factors
    risk_factors = _analyze_risk_factors(db, tenant_id)
    
    # Get risk history (monthly scores from quotes/policies)
    risk_history = _get_risk_history(db, tenant_id)
    
    # Loss ratio calculation
    three_years_ago = date.today() - timedelta(days=365*3)
    three_years_ago_dt = datetime.combine(three_years_ago, datetime.min.time())
    
    total_premium_3yr = 0.0
    policies_3yr = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.effective_from >= three_years_ago_dt
    ).all()
    
    for p in policies_3yr:
        if p.premium_json and isinstance(p.premium_json, dict):
            premium = p.premium_json.get("total_premium", 0)
            if premium:
                total_premium_3yr += float(premium)
    
    claims_3yr = db.query(Claim).join(Policy).filter(
        Policy.tenant_id == tenant_id,
        Claim.created_at >= three_years_ago_dt
    ).all()
    
    total_claims_paid = 0.0
    for c in claims_3yr:
        if c.payouts:
            for payout in c.payouts:
                if payout.amount_cents:
                    total_claims_paid += float(payout.amount_cents) / 100.0
    
    loss_ratio = total_claims_paid / total_premium_3yr if total_premium_3yr > 0 else 0
    
    # Claims frequency
    total_shipments = len(policies_3yr)
    total_claims_count = len(claims_3yr)
    
    claims_frequency = total_claims_count / total_shipments if total_shipments > 0 else 0
    
    # Average severity
    avg_severity = total_claims_paid / total_claims_count if total_claims_count > 0 else 0
    
    # Percentile calculation (simplified)
    risk_score = 0.5  # Would come from customer model
    percentile = int((1 - risk_score) * 100)
    
    return RiskProfile(
        customer_id=None,
        overall_risk_score=risk_score,
        risk_grade="C",
        risk_percentile=percentile,
        risk_factors=risk_factors,
        risk_history=risk_history,
        loss_ratio_3yr=loss_ratio,
        claims_frequency=claims_frequency,
        avg_claim_severity=avg_severity,
        industry_avg_loss_ratio=0.35,
        peer_avg_risk_score=0.45
    )


@router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    limit: int = Query(10, le=20),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get personalized recommendations for the customer.
    """
    from app.models.quote import Quote
    from app.modules.underwriting.models import Policy, PolicyStatus
    
    tenant_id = tenant_context.tenant_id
    
    recommendations = []
    
    # Check for expiring quotes
    expiring_quotes = db.query(Quote).filter(
        Quote.tenant_id == tenant_id,
        Quote.status.in_(["PENDING", "ISSUED"]),
        Quote.valid_until <= datetime.utcnow() + timedelta(days=2)
    ).all()
    
    for quote in expiring_quotes:
        origin = ""
        destination = ""
        if quote.coverage_terms_json and isinstance(quote.coverage_terms_json, dict):
            origin = quote.coverage_terms_json.get("origin_port", "")
            destination = quote.coverage_terms_json.get("destination_port", "")
        
        recommendations.append(Recommendation(
            id=f"quote_expiring_{quote.id}",
            type="RENEWAL",
            priority="HIGH",
            title=f"Quote {quote.quote_number} expiring soon",
            description=f"Your quote for {origin} to {destination} expires on {quote.valid_until.strftime('%Y-%m-%d') if quote.valid_until else 'soon'}",
            potential_benefit="Lock in current rates before expiration",
            action_url=f"/quotes/{quote.id}",
            expires_at=quote.valid_until
        ))
    
    # Check for policies nearing renewal
    policies_expiring = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.status == PolicyStatus.ACTIVE,
        Policy.effective_to <= datetime.utcnow() + timedelta(days=30)
    ).all()
    
    for policy in policies_expiring:
        effective_to_date = policy.effective_to.date() if policy.effective_to else date.today()
        recommendations.append(Recommendation(
            id=f"policy_renewal_{policy.id}",
            type="RENEWAL",
            priority="MEDIUM",
            title=f"Policy {policy.policy_number} renewal",
            description=f"Your policy expires on {effective_to_date.strftime('%Y-%m-%d')}. Consider renewing early.",
            potential_benefit="Continuous coverage without gaps",
            action_url=f"/policies/{policy.id}/renew",
            expires_at=datetime.combine(effective_to_date, datetime.min.time())
        ))
    
    # Tier upgrade recommendation (simplified)
    shipment_count = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.effective_from >= datetime.utcnow() - timedelta(days=365)
    ).count()
    
    if shipment_count >= 20:
        recommendations.append(Recommendation(
            id="tier_upgrade",
            type="COST_SAVING",
            priority="MEDIUM",
            title="Eligible for Preferred tier",
            description=f"With {shipment_count} shipments this year, you may qualify for our Preferred tier with 10% discount.",
            potential_benefit="Save 10% on all future premiums",
            action_url="/account/upgrade",
            expires_at=None
        ))
    
    # Sort by priority and limit
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))
    
    return recommendations[:limit]


@router.get("/spending", response_model=SpendingAnalysis)
async def get_spending_analysis(
    period: str = Query(default="YTD", description="YTD, QTD, LAST_12_MONTHS"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get premium spending analysis.
    """
    from app.modules.underwriting.models import Policy
    
    tenant_id = tenant_context.tenant_id
    
    # Determine date range
    today = date.today()
    if period == "YTD":
        start_date = date(today.year, 1, 1)
        prev_start = date(today.year - 1, 1, 1)
        prev_end = date(today.year - 1, today.month, today.day)
    elif period == "QTD":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        start_date = date(today.year, quarter_start_month, 1)
        prev_start = date(today.year - 1, quarter_start_month, 1)
        prev_end = date(today.year - 1, today.month, today.day)
    else:  # LAST_12_MONTHS
        start_date = today - timedelta(days=365)
        prev_start = start_date - timedelta(days=365)
        prev_end = start_date - timedelta(days=1)
    
    start_datetime = datetime.combine(start_date, datetime.min.time())
    
    # Current period spending
    current_policies = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.effective_from >= start_datetime
    ).all()
    
    total_premium = 0.0
    by_cargo = {}
    by_route = {}
    monthly_data = {}
    
    for p in current_policies:
        premium = 0.0
        cargo = "OTHER"
        route = "UNK-UNK"
        
        if p.premium_json and isinstance(p.premium_json, dict):
            premium = float(p.premium_json.get("total_premium", 0))
        
        if p.terms_json and isinstance(p.terms_json, dict):
            cargo = p.terms_json.get("cargo_type", "OTHER")
            origin = p.terms_json.get("origin_port", "UNK")
            dest = p.terms_json.get("destination_port", "UNK")
            route = f"{origin}-{dest}"
        
        total_premium += premium
        by_cargo[cargo] = by_cargo.get(cargo, 0) + premium
        by_route[route] = by_route.get(route, 0) + premium
        
        if p.effective_from:
            month_key = p.effective_from.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"premium": 0, "count": 0}
            monthly_data[month_key]["premium"] += premium
            monthly_data[month_key]["count"] += 1
    
    # Sort and limit routes
    by_route = dict(sorted(by_route.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # By month
    by_month = []
    for month in sorted(monthly_data.keys()):
        by_month.append({
            "month": month,
            "premium": monthly_data[month]["premium"],
            "shipments": monthly_data[month]["count"]
        })
    
    # Previous period comparison
    prev_start_dt = datetime.combine(prev_start, datetime.min.time())
    prev_end_dt = datetime.combine(prev_end, datetime.max.time())
    
    prev_policies = db.query(Policy).filter(
        Policy.tenant_id == tenant_id,
        Policy.effective_from >= prev_start_dt,
        Policy.effective_from <= prev_end_dt
    ).all()
    
    prev_premium = 0.0
    for p in prev_policies:
        if p.premium_json and isinstance(p.premium_json, dict):
            prev_premium += float(p.premium_json.get("total_premium", 0))
    
    vs_previous = ((total_premium - prev_premium) / prev_premium * 100) if prev_premium > 0 else 0
    
    # Average rate
    total_value = 0.0
    for p in current_policies:
        if p.terms_json and isinstance(p.terms_json, dict):
            value = p.terms_json.get("cargo_value_usd", 0)
            if value:
                total_value += float(value)
    
    avg_rate = (total_premium / total_value * 1000) if total_value > 0 else 0
    
    # Discounts (simplified)
    discounts = 0.0
    
    # Potential savings (simplified)
    potential_savings = total_premium * 0.1
    
    # Rate trend
    mid_point = start_datetime + (datetime.utcnow() - start_datetime) / 2
    first_half = [p for p in current_policies if p.effective_from and p.effective_from < mid_point]
    second_half = [p for p in current_policies if p.effective_from and p.effective_from >= mid_point]
    
    first_value = sum(float(p.terms_json.get("cargo_value_usd", 0)) for p in first_half if p.terms_json) if first_half else 1
    first_premium = sum(float(p.premium_json.get("total_premium", 0)) for p in first_half if p.premium_json) if first_half else 0
    first_rate = (first_premium / first_value * 1000) if first_value > 0 else 0
    
    second_value = sum(float(p.terms_json.get("cargo_value_usd", 0)) for p in second_half if p.terms_json) if second_half else 1
    second_premium = sum(float(p.premium_json.get("total_premium", 0)) for p in second_half if p.premium_json) if second_half else 0
    second_rate = (second_premium / second_value * 1000) if second_value > 0 else 0
    
    if second_rate < first_rate * 0.95:
        rate_trend = "DECREASING"
    elif second_rate > first_rate * 1.05:
        rate_trend = "INCREASING"
    else:
        rate_trend = "STABLE"
    
    return SpendingAnalysis(
        period=period,
        total_premium_usd=total_premium,
        by_cargo_type=by_cargo,
        by_route=by_route,
        by_month=by_month,
        vs_previous_period_pct=vs_previous,
        avg_rate_per_mille=avg_rate,
        rate_trend=rate_trend,
        discounts_applied_usd=discounts,
        potential_savings_usd=potential_savings,
        savings_recommendations=[
            "Bundle multiple shipments for volume discount",
            "Consider annual policy for frequent routes",
            "Upgrade to Preferred tier for 10% savings"
        ] if potential_savings > 1000 else []
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _calculate_risk_trend(db: Session, tenant_id: str) -> str:
    """Calculate risk score trend over last 3 months."""
    from app.models.quote import Quote
    
    now = datetime.utcnow()
    
    # Last month average
    last_month_quotes = db.query(Quote).filter(
        Quote.tenant_id == tenant_id,
        Quote.created_at >= now - timedelta(days=30)
    ).all()
    
    last_month_scores = []
    for q in last_month_quotes:
        if q.risk_summary_json and isinstance(q.risk_summary_json, dict):
            score = q.risk_summary_json.get("overall_risk_score")
            if score:
                last_month_scores.append(float(score))
    
    last_month_avg = sum(last_month_scores) / len(last_month_scores) if last_month_scores else 0.5
    
    # Previous 2 months average
    prev_quotes = db.query(Quote).filter(
        Quote.tenant_id == tenant_id,
        Quote.created_at >= now - timedelta(days=90),
        Quote.created_at < now - timedelta(days=30)
    ).all()
    
    prev_scores = []
    for q in prev_quotes:
        if q.risk_summary_json and isinstance(q.risk_summary_json, dict):
            score = q.risk_summary_json.get("overall_risk_score")
            if score:
                prev_scores.append(float(score))
    
    prev_avg = sum(prev_scores) / len(prev_scores) if prev_scores else 0.5
    
    if last_month_avg < prev_avg * 0.9:
        return "IMPROVING"
    elif last_month_avg > prev_avg * 1.1:
        return "WORSENING"
    else:
        return "STABLE"


def _generate_alerts(db: Session, tenant_id: str, policies, quotes) -> List[Dict[str, Any]]:
    """Generate dashboard alerts."""
    alerts = []
    
    # Expiring quotes
    expiring = [q for q in quotes if q.valid_until and q.valid_until <= datetime.utcnow() + timedelta(days=2)]
    if expiring:
        alerts.append({
            "type": "WARNING",
            "title": f"{len(expiring)} quote(s) expiring soon",
            "message": "Review and accept before expiration",
            "action": "/quotes?status=PENDING"
        })
    
    # Unpaid premiums (simplified)
    unpaid = [p for p in policies if not hasattr(p, 'premium_paid') or not p.premium_paid]
    if unpaid:
        alerts.append({
            "type": "INFO",
            "title": f"{len(unpaid)} policy(ies) with unpaid premium",
            "message": "Payment due within 30 days of inception",
            "action": "/payments"
        })
    
    return alerts


def _get_claim_stage(status: str) -> str:
    """Map claim status to user-friendly stage."""
    stages = {
        "FNOL_RECEIVED": "Submitted - Under Initial Review",
        "UNDER_INVESTIGATION": "Documentation Review",
        "AWAITING_EVIDENCE": "Awaiting Additional Documents",
        "APPROVED": "Approved - Pending Payment",
        "AUTHORIZED": "Authorized - Payment Processing",
        "PAID": "Completed - Payment Issued",
        "DECLINED": "Denied",
        "CLOSED": "Closed",
        "WITHDRAWN": "Withdrawn"
    }
    return stages.get(status, status)


def _estimate_resolution(claim) -> Optional[str]:
    """Estimate claim resolution time."""
    from app.modules.claims.models import ClaimStatus
    
    if claim.status in [ClaimStatus.PAID, ClaimStatus.DECLINED, ClaimStatus.CLOSED]:
        return None
    
    # Simple estimate based on status
    if claim.status == ClaimStatus.FNOL_RECEIVED:
        return "5-7 business days"
    elif claim.status in [ClaimStatus.UNDER_INVESTIGATION, ClaimStatus.AWAITING_EVIDENCE]:
        return "3-5 business days"
    elif claim.status == ClaimStatus.APPROVED:
        return "1-2 business days"
    
    return None


def _get_pending_documents(claim) -> List[str]:
    """Get list of pending documents for claim."""
    # Would check claim requirements vs submitted documents
    return []


def _analyze_risk_factors(db: Session, tenant_id: str) -> List[Dict[str, Any]]:
    """Analyze risk factors for customer."""
    from app.modules.underwriting.models import Policy
    from app.modules.claims.models import Claim
    
    factors = []
    
    # Claims history
    claims_count = db.query(Claim).join(Policy).filter(
        Policy.tenant_id == tenant_id
    ).count()
    
    if claims_count == 0:
        factors.append({
            "factor": "Claims History",
            "score": 0.2,
            "impact": "POSITIVE",
            "description": "No claims filed - excellent track record"
        })
    elif claims_count <= 2:
        factors.append({
            "factor": "Claims History",
            "score": 0.4,
            "impact": "NEUTRAL",
            "description": f"{claims_count} claims filed - within normal range"
        })
    else:
        factors.append({
            "factor": "Claims History",
            "score": 0.7,
            "impact": "NEGATIVE",
            "description": f"{claims_count} claims filed - above average"
        })
    
    return factors


def _get_risk_history(db: Session, tenant_id: str) -> List[Dict[str, Any]]:
    """Get monthly risk score history."""
    from app.models.quote import Quote
    
    quotes = db.query(Quote).filter(
        Quote.tenant_id == tenant_id,
        Quote.created_at >= datetime.utcnow() - timedelta(days=365)
    ).all()
    
    monthly_scores = {}
    for q in quotes:
        if q.created_at and q.risk_summary_json and isinstance(q.risk_summary_json, dict):
            month_key = q.created_at.strftime("%Y-%m")
            score = q.risk_summary_json.get("overall_risk_score")
            if score:
                if month_key not in monthly_scores:
                    monthly_scores[month_key] = []
                monthly_scores[month_key].append(float(score))
    
    history = []
    for month in sorted(monthly_scores.keys()):
        avg_score = sum(monthly_scores[month]) / len(monthly_scores[month])
        history.append({
            "month": month,
            "score": avg_score
        })
    
    return history
