"""
DataLoaders for N+1 Query Prevention

Features:
1. Batch loading
2. Caching within request
3. Deduplication
"""

import asyncio
from typing import Dict, List, Optional, Any
from collections import defaultdict

from strawberry.dataloader import DataLoader
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.graphql.types.quote import Quote, RiskBreakdown, PremiumBreakdown, QuoteStatus, RiskGrade
from app.graphql.types.policy import Policy, PolicyCoverage, PolicyPremium, PolicyStatus
from app.graphql.types.claim import Claim, ClaimStatus, ClaimAssessment, ClaimDocument, ClaimTimeline
from app.graphql.types.customer import Customer


def _run_sync(sync_fn, *args, **kwargs):
    """Run sync function in thread pool for async compatibility."""
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: sync_fn(*args, **kwargs))


# =============================================================================
# Sync batch loaders (run in executor)
# =============================================================================


def _batch_load_quotes(session: Session, ids: List[str]) -> List[Optional[Quote]]:
    from app.models.quote import Quote as QuoteModel
    from sqlalchemy.orm import selectinload

    result = session.execute(
        select(QuoteModel)
        .where(QuoteModel.id.in_(ids))
        .options(selectinload(QuoteModel.submission))
    )
    rows = result.scalars().all()
    by_id = {str(r.id): r for r in rows}
    return [_quote_model_to_type(by_id.get(i)) for i in ids]


def _batch_load_policies(session: Session, ids: List[str]) -> List[Optional[Policy]]:
    from app.modules.underwriting.models import Policy as PolicyModel

    result = session.execute(select(PolicyModel).where(PolicyModel.id.in_(ids)))
    rows = result.scalars().all()
    by_id = {str(r.id): r for r in rows}
    return [_policy_model_to_type(by_id.get(i)) for i in ids]


def _batch_load_policies_by_quote(session: Session, quote_ids: List[str]) -> List[Optional[Policy]]:
    from app.modules.underwriting.models import Policy as PolicyModel

    result = session.execute(
        select(PolicyModel).where(PolicyModel.quote_id.in_(quote_ids))
    )
    rows = result.scalars().all()
    by_quote = {str(r.quote_id): r for r in rows if r.quote_id}
    return [_policy_model_to_type(by_quote.get(qid)) for qid in quote_ids]


def _batch_load_claims(session: Session, ids: List[str]) -> List[Optional[Claim]]:
    from app.modules.claims.models import Claim as ClaimModel

    result = session.execute(select(ClaimModel).where(ClaimModel.id.in_(ids)))
    rows = result.scalars().all()
    by_id = {str(r.id): r for r in rows}
    return [_claim_model_to_type(by_id.get(i)) for i in ids]


def _batch_load_claims_by_policy(session: Session, policy_ids: List[str]) -> List[List[Claim]]:
    from app.modules.claims.models import Claim as ClaimModel

    result = (
        session.execute(
            select(ClaimModel)
            .where(ClaimModel.policy_id.in_(policy_ids))
            .order_by(ClaimModel.created_at.desc())
        )
    )
    rows = result.scalars().all()
    by_policy: Dict[str, List[Claim]] = defaultdict(list)
    for r in rows:
        c = _claim_model_to_type(r)
        if c:
            by_policy[str(r.policy_id)].append(c)
    return [by_policy.get(pid, []) for pid in policy_ids]


def _batch_load_customers(session: Session, ids: List[str]) -> List[Optional[Customer]]:
    from app.models.customer import Customer as CustomerModel

    result = session.execute(select(CustomerModel).where(CustomerModel.id.in_(ids)))
    rows = result.scalars().all()
    by_id = {str(r.id): r for r in rows}
    return [_customer_model_to_type(by_id.get(i)) for i in ids]


# =============================================================================
# DataLoader factories
# =============================================================================


def create_quote_loader(session: Session) -> DataLoader[str, Optional[Quote]]:
    async def load_fn(ids: List[str]) -> List[Optional[Quote]]:
        return await _run_sync(_batch_load_quotes, session, ids)

    return DataLoader(load_fn=load_fn)


def create_policy_loader(session: Session) -> DataLoader[str, Optional[Policy]]:
    async def load_fn(ids: List[str]) -> List[Optional[Policy]]:
        return await _run_sync(_batch_load_policies, session, ids)

    return DataLoader(load_fn=load_fn)


def create_policy_by_quote_loader(session: Session) -> DataLoader[str, Optional[Policy]]:
    async def load_fn(quote_ids: List[str]) -> List[Optional[Policy]]:
        return await _run_sync(_batch_load_policies_by_quote, session, quote_ids)

    return DataLoader(load_fn=load_fn)


def create_claim_loader(session: Session) -> DataLoader[str, Optional[Claim]]:
    async def load_fn(ids: List[str]) -> List[Optional[Claim]]:
        return await _run_sync(_batch_load_claims, session, ids)

    return DataLoader(load_fn=load_fn)


def create_claims_by_policy_loader(session: Session) -> DataLoader[str, List[Claim]]:
    async def load_fn(policy_ids: List[str]) -> List[List[Claim]]:
        return await _run_sync(_batch_load_claims_by_policy, session, policy_ids)

    return DataLoader(load_fn=load_fn)


def create_customer_loader(session: Session) -> DataLoader[str, Optional[Customer]]:
    async def load_fn(ids: List[str]) -> List[Optional[Customer]]:
        return await _run_sync(_batch_load_customers, session, ids)

    return DataLoader(load_fn=load_fn)


class DataLoaders:
    """Container for all dataloaders."""

    def __init__(self, session: Session):
        self.quote_loader = create_quote_loader(session)
        self.policy_loader = create_policy_loader(session)
        self.policy_by_quote_loader = create_policy_by_quote_loader(session)
        self.claim_loader = create_claim_loader(session)
        self.claims_by_policy_loader = create_claims_by_policy_loader(session)
        self.customer_loader = create_customer_loader(session)


# =============================================================================
# Model to GraphQL type mappers
# =============================================================================

import strawberry
from decimal import Decimal
from datetime import datetime, date


def _quote_model_to_type(model: Any) -> Optional[Quote]:
    """Map Quote model to GraphQL type. Adapts to app.models.quote.Quote schema."""
    if not model:
        return None
    # Quote has: id, quote_number, status, pricing_snapshot_json, coverage_terms_json,
    # risk_summary_json, valid_from, valid_until, submission_id, etc.
    pricing = model.pricing_snapshot_json or {}
    coverage = model.coverage_terms_json or {}
    risk_summary = model.risk_summary_json or {}
    cov = coverage.get("coverage_type") or "ALL_RISKS"
    limit = Decimal(str(coverage.get("limit_usd") or pricing.get("total_premium_usd") or 0))
    risk_breakdown = None
    if risk_summary:
        risk_breakdown = RiskBreakdown(
            weather_risk=float(risk_summary.get("weather_risk", 0)),
            port_risk=float(risk_summary.get("port_risk", 0)),
            cargo_risk=float(risk_summary.get("cargo_risk", 0)),
            route_risk=float(risk_summary.get("route_risk", 0)),
            carrier_risk=float(risk_summary.get("carrier_risk", 0)),
            overall_score=float(risk_summary.get("overall_score", 0)),
            risk_grade=(RiskGrade(risk_summary["risk_grade"]) if risk_summary.get("risk_grade") in ("A","B","C","D","F") else RiskGrade.C),
        )
    premium_breakdown = None
    if pricing:
        total = Decimal(str(pricing.get("total_premium_usd") or 0))
        premium_breakdown = PremiumBreakdown(
            base_premium=Decimal(str(pricing.get("base_premium_usd") or 0)),
            risk_loading=Decimal(str(pricing.get("risk_loading_usd") or 0)),
            war_risk_premium=Decimal(str(p)) if (p := pricing.get("war_risk_premium_usd")) is not None else None,
            strikes_premium=Decimal(str(s)) if (s := pricing.get("strikes_premium_usd")) is not None else None,
            extensions_premium=Decimal(str(pricing.get("extensions_premium_usd") or 0)),
            discounts=Decimal(str(pricing.get("discounts_usd") or 0)),
            taxes=Decimal(str(pricing.get("taxes_usd") or 0)),
            total_premium=total,
            rate_per_mille=float(pricing.get("rate_per_mille") or 0),
        )
    customer_id = str(model.submission_id)
    req_cov = {}
    if getattr(model, "submission", None):
        sub = model.submission
        app_json = getattr(sub, "applicant_json", None) or {}
        customer_id = str(app_json.get("customer_id") or app_json.get("id") or model.submission_id)
        req_cov = getattr(sub, "requested_coverage_json", None) or {}
    cargo_type = str(coverage.get("cargo_type") or req_cov.get("cargo_type") or "GENERAL")
    origin = str(coverage.get("origin_port") or req_cov.get("origin_port") or "")
    dest = str(coverage.get("destination_port") or req_cov.get("destination_port") or "")

    return Quote(
        id=strawberry.ID(str(model.id)),
        quote_number=model.quote_number or "",
        status=QuoteStatus(model.status) if model.status else QuoteStatus.DRAFT,
        cargo_type=cargo_type,
        cargo_description=coverage.get("cargo_description"),
        cargo_value_usd=Decimal(str(coverage.get("cargo_value_usd") or pricing.get("sum_insured_usd") or 0)),
        container_count=int(coverage.get("container_count") or 1),
        origin_port=origin,
        origin_port_name=None,
        destination_port=dest,
        destination_port_name=None,
        departure_date=model.valid_from,
        arrival_date=None,
        valid_until=model.valid_until,
        risk_breakdown=risk_breakdown,
        premium_breakdown=premium_breakdown,
        coverage_details=None,
        created_at=model.created_at,
        updated_at=getattr(model, "updated_at", None),
        created_by=None,
        updated_by=None,
        customer_id=customer_id,
    )


def _policy_model_to_type(model: Any) -> Optional[Policy]:
    """Map Policy model to GraphQL type."""
    if not model:
        return None
    terms = model.terms_json or {}
    premium = model.premium_json or {}
    eff_from = model.effective_from
    eff_to = model.effective_to
    if isinstance(eff_from, datetime):
        eff_from = eff_from.date()
    if isinstance(eff_to, datetime):
        eff_to = eff_to.date()
    total = Decimal(str(premium.get("total_premium_usd") or 0))
    paid = Decimal(str(premium.get("paid_premium_usd") or 0))

    coverage = PolicyCoverage(
        coverage_type=terms.get("coverage_type") or "ALL_RISKS",
        coverage_limit=Decimal(str(terms.get("coverage_limit_usd") or 0)),
        deductible=Decimal(str(terms.get("deductible_usd") or 0)),
        extensions=terms.get("extensions") or [],
        territories=terms.get("territories") or ["WORLDWIDE"],
        conveyances=terms.get("conveyances") or ["VESSEL", "TRUCK"],
    )
    premium_obj = PolicyPremium(
        total_premium=total,
        paid_premium=paid,
        outstanding_premium=total - paid,
        payment_status=premium.get("payment_status") or "PENDING",
        next_payment_date=premium.get("next_payment_date"),
    )
    ph = model.policyholder_json or {}
    cargo_type = str(terms.get("cargo_type") or ph.get("cargo_type") or "GENERAL")
    origin = str(terms.get("origin_port") or ph.get("origin") or "")
    dest = str(terms.get("destination_port") or ph.get("destination") or "")

    return Policy(
        id=strawberry.ID(str(model.id)),
        policy_number=model.policy_number or "",
        status=PolicyStatus(model.status.value) if hasattr(model.status, "value") else PolicyStatus.ACTIVE,
        effective_from=eff_from,
        effective_to=eff_to,
        issue_date=model.bound_at.date() if model.bound_at else (eff_from or date.today()),
        coverage=coverage,
        premium=premium_obj,
        cargo_type=cargo_type,
        cargo_description=terms.get("cargo_description"),
        cargo_value_usd=Decimal(str(terms.get("cargo_value_usd") or 0)),
        origin_port=origin,
        destination_port=dest,
        carrier_name=terms.get("carrier_name"),
        vessel_name=terms.get("vessel_name"),
        voyage_number=terms.get("voyage_number"),
        created_at=model.created_at,
        updated_at=getattr(model, "updated_at", None),
        created_by=None,
        updated_by=None,
        customer_id=str(ph.get("customer_id") or ph.get("id") or ""),
        quote_id=str(model.quote_id) if model.quote_id else None,
    )


def _claim_model_to_type(model: Any) -> Optional[Claim]:
    """Map Claim model to GraphQL type."""
    if not model:
        return None
    fnol = model.fnol_json or {}
    adj = model.adjudication_json or {}
    loss_d = fnol.get("loss_date") or fnol.get("incident_date")
    if isinstance(loss_d, str):
        try:
            loss_d = datetime.fromisoformat(loss_d.replace("Z", "+00:00")).date()
        except Exception:
            loss_d = date.today()
    elif not loss_d:
        loss_d = date.today()

    assessed = None
    if adj:
        at = adj.get("assessed_at")
        if isinstance(at, str):
            try:
                at = datetime.fromisoformat(at.replace("Z", "+00:00"))
            except Exception:
                at = datetime.utcnow()
        elif not at:
            at = datetime.utcnow()
        assessed = ClaimAssessment(
            assessed_by=adj.get("assessed_by") or "",
            assessed_at=at,
            assessed_amount=Decimal(str(adj.get("assessed_amount") or 0)),
            assessment_notes=adj.get("notes") or "",
            recommendation=adj.get("recommendation") or "",
        )
    approved_cents = model.approved_amount_cents or 0
    approved_amount = Decimal(approved_cents) / 100 if approved_cents else None
    claimed = Decimal(str(fnol.get("claimed_amount_usd") or fnol.get("alleged_loss_usd") or 0))
    docs = []
    timeline = [
        ClaimTimeline(
            event_type="FILED",
            description="Claim filed",
            timestamp=model.created_at,
            actor=model.created_by_user_id,
        )
    ]

    _status = getattr(model.status, "value", str(model.status))
    _map = {
        "FNOL_RECEIVED": ClaimStatus.FILED,
        "UNDER_INVESTIGATION": ClaimStatus.IN_REVIEW,
        "AWAITING_EVIDENCE": ClaimStatus.IN_REVIEW,
        "APPROVED": ClaimStatus.APPROVED,
        "AUTHORIZED": ClaimStatus.APPROVED,
        "DENIED": ClaimStatus.DENIED,
        "PAID": ClaimStatus.PAID,
        "CLOSED": ClaimStatus.PAID,
        "WITHDRAWN": ClaimStatus.DENIED,
    }
    claim_status = _map.get(_status, ClaimStatus.FILED)
    return Claim(
        id=strawberry.ID(str(model.id)),
        claim_number=model.claim_number or "",
        status=claim_status,
        loss_date=loss_d,
        loss_type=fnol.get("loss_type") or "THEFT",
        loss_location=fnol.get("loss_location"),
        loss_description=fnol.get("loss_description") or fnol.get("incident_summary") or "",
        claimed_amount=claimed,
        assessed_amount=Decimal(str(adj.get("assessed_amount") or 0)) if adj else None,
        approved_amount=approved_amount,
        paid_amount=None,
        assessment=assessed,
        denial_reason=model.decision_reason if (model.decision == "DECLINED") else None,
        documents=docs,
        timeline=timeline,
        filed_at=model.created_at,
        created_at=model.created_at,
        updated_at=getattr(model, "updated_at", None),
        created_by=model.created_by_user_id,
        updated_by=None,
        policy_id=str(model.policy_id),
    )


def _customer_model_to_type(model: Any) -> Optional[Customer]:
    """Map Customer model to GraphQL type."""
    if not model:
        return None
    return Customer(
        id=strawberry.ID(str(model.id)),
        customer_number=model.registration_number or str(model.id),
        name=model.primary_contact_name or "",
        email=model.primary_contact_email or "",
        company_name=model.company_name or "",
        tier=model.pricing_tier,
        created_at=model.created_at,
        updated_at=getattr(model, "updated_at", None),
    )
