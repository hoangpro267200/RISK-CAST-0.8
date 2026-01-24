"""
Underwriting API Endpoints
API v3 endpoints for underwriting
RISKCAST V3 - Modular Monolith
"""
from fastapi import APIRouter, Depends, Request, status
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
import logging

# Import dependencies
from app.shared.dependencies import TenantContext
from app.shared.utils import build_audit_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.modules.underwriting.service import UnderwritingService
from app.modules.underwriting.models import (
    UnderwritingSubmission,
    UnderwritingDecision,
    Policy,
    SubmissionStatus,
    DecisionType
)

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession, get_tenant_scoped_db

logger = logging.getLogger(__name__)

# Underwriting router
router = APIRouter(prefix="/underwriting", tags=["underwriting"])


# Schemas
class SubmissionCreate(BaseModel):
    """Schema for creating underwriting submission"""
    risk_assessment_id: str = Field(..., description="Risk assessment ID")
    risk_run_id: Optional[str] = Field(None, description="Risk run ID")
    evidence_bundle_id: Optional[str] = Field(None, description="Evidence bundle ID")
    requested_coverage_json: Optional[Dict[str, Any]] = Field(None, description="Coverage request")
    corridor_id: Optional[str] = Field(None, description="Corridor ID")
    product_type: Optional[str] = Field(None, description="Product type")


class SubmissionResponse(BaseModel):
    """Schema for submission response"""
    id: str
    tenant_id: str
    status: str
    risk_assessment_id: str
    risk_run_id: Optional[str]
    evidence_bundle_id: Optional[str]
    created_by_user_id: Optional[str]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class DecisionCreate(BaseModel):
    """Schema for creating underwriting decision"""
    decision: DecisionType = Field(..., description="Decision type")
    terms_json: Optional[Dict[str, Any]] = Field(None, description="Terms for quote")
    evidence_bundle_id: Optional[str] = Field(None, description="Evidence bundle to pin")
    risk_run_id: Optional[str] = Field(None, description="Risk run to pin")
    model_version_id: Optional[str] = Field(None, description="Model version to pin")
    notes: Optional[str] = Field(None, description="Decision notes")


class DecisionResponse(BaseModel):
    """Schema for decision response"""
    id: str
    tenant_id: str
    submission_id: str
    decided_by_user_id: Optional[str]
    decision: str
    terms_json: Optional[Dict[str, Any]]
    notes: Optional[str]
    model_version_id: Optional[str]
    risk_run_id: Optional[str]
    evidence_bundle_id: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True


class PolicyBindRequest(BaseModel):
    """Schema for binding policy"""
    submission_id: str = Field(..., description="Submission ID")
    effective_from: datetime = Field(..., description="Policy effective start date")
    effective_to: datetime = Field(..., description="Policy effective end date")
    policy_number: str = Field(..., description="Policy number")


class PolicyResponse(BaseModel):
    """Schema for policy response"""
    id: str
    tenant_id: str
    policy_number: str
    status: str
    submission_id: Optional[str]
    bound_by_user_id: Optional[str]
    bound_at: Optional[str]
    effective_from: str
    effective_to: str
    model_version_id: str
    risk_run_id: str
    created_at: str
    
    class Config:
        from_attributes = True


@router.post(
    "/submissions",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create submission",
    description="Create a new underwriting submission"
)
async def create_submission(
    data: SubmissionCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.UNDERWRITING_WRITE))
):
    """Create a new underwriting submission"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = UnderwritingService(db)
        submission = await service.create_submission(
            data=data.dict(),
            user_id=context.user_id,
            context=audit_context
        )
        
        return SubmissionResponse(
            id=submission.id,
            tenant_id=submission.tenant_id,
            status=submission.status.value,
            risk_assessment_id=submission.risk_assessment_id,
            risk_run_id=submission.risk_run_id,
            evidence_bundle_id=submission.evidence_bundle_id,
            created_by_user_id=submission.created_by_user_id,
            created_at=submission.created_at.isoformat() + 'Z',
            updated_at=submission.updated_at.isoformat() + 'Z'
        )
    finally:
        db_session.close()


@router.post(
    "/submissions/{id}/decisions",
    response_model=DecisionResponse,
    summary="Make decision",
    description="Make underwriting decision (QUOTE, DECLINE, REQUEST_INFO)"
)
async def make_decision(
    id: str,
    data: DecisionCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.UNDERWRITING_DECIDE))
):
    """Make underwriting decision"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = UnderwritingService(db)
        decision, submission = await service.make_decision(
            submission_id=id,
            decision=data.decision,
            user_id=context.user_id,
            context=audit_context,
            terms_json=data.terms_json,
            evidence_bundle_id=data.evidence_bundle_id,
            risk_run_id=data.risk_run_id,
            model_version_id=data.model_version_id,
            notes=data.notes
        )
        
        return DecisionResponse(
            id=decision.id,
            tenant_id=decision.tenant_id,
            submission_id=decision.submission_id,
            decided_by_user_id=decision.decided_by_user_id,
            decision=decision.decision.value,
            terms_json=decision.terms_json,
            notes=decision.notes,
            model_version_id=decision.model_version_id,
            risk_run_id=decision.risk_run_id,
            evidence_bundle_id=decision.evidence_bundle_id,
            created_at=decision.created_at.isoformat() + 'Z'
        )
    finally:
        db_session.close()


@router.post(
    "/policies",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bind policy",
    description="Bind policy from quoted submission"
)
async def bind_policy(
    data: PolicyBindRequest,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.POLICY_BIND))
):
    """Bind policy from quoted submission"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = UnderwritingService(db)
        policy = await service.bind_policy(
            submission_id=data.submission_id,
            user_id=context.user_id,
            context=audit_context,
            effective_from=data.effective_from,
            effective_to=data.effective_to,
            policy_number=data.policy_number
        )
        
        return PolicyResponse(
            id=policy.id,
            tenant_id=policy.tenant_id,
            policy_number=policy.policy_number,
            status=policy.status.value,
            submission_id=policy.submission_id,
            bound_by_user_id=policy.bound_by_user_id,
            bound_at=policy.bound_at.isoformat() + 'Z' if policy.bound_at else None,
            effective_from=policy.effective_from.isoformat() + 'Z',
            effective_to=policy.effective_to.isoformat() + 'Z',
            model_version_id=policy.model_version_id,
            risk_run_id=policy.risk_run_id,
            created_at=policy.created_at.isoformat() + 'Z'
        )
    finally:
        db_session.close()
