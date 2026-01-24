"""
Claims API endpoints.

Full CRUD API for claims management with state machine workflow.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.database import get_db, get_tenant_scoped_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.claims_service import (
    ClaimsService,
    ClaimNotFoundError,
    PolicyNotFoundError,
    InvalidTransitionError,
    InvalidClaimStateError,
    EvidenceRequiredError
)
from app.schemas.claim import (
    FNOLRequest,
    ClaimResponse,
    ClaimDetailResponse,
    ClaimEventResponse,
    AdjudicationRequest
)
from app.core.audit_ledger.ledger import AuditLedger

router = APIRouter(prefix="/claims", tags=["Claims"])


def get_claims_service(
    request: Request,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> ClaimsService:
    """Dependency to get ClaimsService."""
    tenant_db = get_tenant_scoped_db(request, db)
    audit = AuditLedger(db)
    return ClaimsService(tenant_db, audit)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClaimResponse)
async def file_claim(
    policy_id: str,
    fnol: FNOLRequest,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:write"))
) -> ClaimResponse:
    """File a new claim (FNOL)."""
    try:
        claim = service.file_claim(
            tenant_id=context.tenant_id,
            policy_id=policy_id,
            fnol=fnol.dict(),
            filed_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except PolicyNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ClaimResponse])
async def list_claims(
    policy_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:read"))
) -> List[ClaimResponse]:
    """List claims with filters."""
    claims = service.list_claims(
        tenant_id=context.tenant_id,
        policy_id=policy_id,
        status=status,
        assigned_to=assigned_to,
        limit=limit,
        offset=offset
    )
    return [ClaimResponse.from_orm(c) for c in claims]


@router.get("/{claim_id}", response_model=ClaimDetailResponse)
async def get_claim(
    claim_id: str,
    service: ClaimsService = Depends(get_claims_service),
    _: None = Depends(PermissionChecker("claim:read"))
) -> ClaimDetailResponse:
    """Get claim details."""
    try:
        claim = service.get_claim_detail(claim_id)
        return ClaimDetailResponse.from_orm(claim)
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{claim_id}/history", response_model=List[ClaimEventResponse])
async def get_claim_history(
    claim_id: str,
    service: ClaimsService = Depends(get_claims_service),
    _: None = Depends(PermissionChecker("claim:read"))
) -> List[ClaimEventResponse]:
    """Get full claim history."""
    try:
        events = service.get_claim_history(claim_id)
        return [ClaimEventResponse.from_orm(e) for e in events]
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/assign", response_model=ClaimResponse)
async def assign_adjuster(
    claim_id: str,
    adjuster_id: str,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:assign"))
) -> ClaimResponse:
    """Assign an adjuster to a claim."""
    try:
        claim = service.assign_adjuster(
            claim_id=claim_id,
            adjuster_id=adjuster_id,
            assigned_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/investigate", response_model=ClaimResponse)
async def begin_investigation(
    claim_id: str,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:investigate"))
) -> ClaimResponse:
    """Begin claim investigation."""
    try:
        claim = service.begin_investigation(
            claim_id=claim_id,
            started_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/evidence/request")
async def request_evidence(
    claim_id: str,
    evidence_request: str,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:write"))
) -> ClaimResponse:
    """Request additional evidence from claimant."""
    try:
        claim = service.request_evidence(
            claim_id=claim_id,
            evidence_request=evidence_request,
            requested_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/{claim_id}/evidence", response_model=ClaimResponse)
async def submit_evidence(
    claim_id: str,
    evidence_bundle_id: str,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:write"))
) -> ClaimResponse:
    """Submit evidence for a claim."""
    try:
        claim = service.submit_evidence(
            claim_id=claim_id,
            evidence_bundle_id=evidence_bundle_id,
            submitted_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{claim_id}/adjudicate", response_model=ClaimResponse)
async def adjudicate_claim(
    claim_id: str,
    adjudication: AdjudicationRequest,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:adjudicate"))
) -> ClaimResponse:
    """Adjudicate a claim (approve or decline)."""
    try:
        claim = service.adjudicate(
            claim_id=claim_id,
            adjudication=adjudication.dict(),
            adjudicated_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except EvidenceRequiredError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/authorize", response_model=ClaimResponse)
async def authorize_payout(
    claim_id: str,
    notes: Optional[str] = None,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:authorize"))
) -> ClaimResponse:
    """Authorize payout for an approved claim."""
    try:
        claim = service.authorize_payout(
            claim_id=claim_id,
            authorized_by=context.user_id or context.actor_id,
            authorization_notes=notes
        )
        return ClaimResponse.from_orm(claim)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidClaimStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/payment", response_model=ClaimResponse)
async def record_payment(
    claim_id: str,
    payout_id: str,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:write"))
) -> ClaimResponse:
    """Record that payment has been made."""
    try:
        claim = service.record_payment(
            claim_id=claim_id,
            payout_id=payout_id,
            recorded_by=context.user_id or context.actor_id
        )
        return ClaimResponse.from_orm(claim)
    except InvalidClaimStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{claim_id}/close", response_model=ClaimResponse)
async def close_claim(
    claim_id: str,
    notes: Optional[str] = None,
    service: ClaimsService = Depends(get_claims_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("claim:write"))
) -> ClaimResponse:
    """Close a claim."""
    try:
        claim = service.close_claim(
            claim_id=claim_id,
            closed_by=context.user_id or context.actor_id,
            closing_notes=notes
        )
        return ClaimResponse.from_orm(claim)
    except InvalidTransitionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidClaimStateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ClaimNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
