"""
Example: Risk Assessment API with Permission Checks
Demonstrates how to apply permission checking to API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker, AnyPermissionChecker, AllPermissionsChecker
from app.database import get_db
from app.services.risk_assessment_service import RiskAssessmentService
from app.schemas.risk_assessment import RiskAssessmentCreate, RiskAssessmentResponse

router = APIRouter(prefix="/risk/assessments", tags=["risk"])


@router.post(
    "",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create risk assessment",
    description="Create a new risk assessment (requires risk:write permission)"
)
async def create_assessment(
    data: RiskAssessmentCreate,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("risk:write"))  # Permission check
):
    """
    Create a new risk assessment.
    
    Requires: risk:write permission
    """
    service = RiskAssessmentService(db)
    assessment = service.create_assessment(
        tenant_id=context.tenant_id,
        raw_input=data.input_data,
        schema_version=data.schema_version,
        created_by_user_id=context.user_id
    )
    return RiskAssessmentResponse.from_orm(assessment)


@router.get(
    "",
    response_model=list[RiskAssessmentResponse],
    summary="List risk assessments",
    description="List risk assessments (requires risk:read permission)"
)
async def list_assessments(
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("risk:read"))  # Permission check
):
    """
    List risk assessments for the tenant.
    
    Requires: risk:read permission
    """
    service = RiskAssessmentService(db)
    assessments = service.list_assessments(
        tenant_id=context.tenant_id
    )
    return [RiskAssessmentResponse.from_orm(a) for a in assessments]


@router.get(
    "/{assessment_id}",
    response_model=RiskAssessmentResponse,
    summary="Get risk assessment",
    description="Get a specific risk assessment (requires risk:read permission)"
)
async def get_assessment(
    assessment_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    db: Session = Depends(get_db),
    _: None = Depends(AnyPermissionChecker("risk:read", "risk:write"))  # Any of these
):
    """
    Get a specific risk assessment.
    
    Requires: risk:read OR risk:write permission
    """
    service = RiskAssessmentService(db)
    assessment = service.get_assessment(
        tenant_id=context.tenant_id,
        assessment_id=assessment_id
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    return RiskAssessmentResponse.from_orm(assessment)


@router.post(
    "/{assessment_id}/export",
    summary="Export risk assessment",
    description="Export risk assessment with audit trail (requires risk:read AND audit:export)"
)
async def export_assessment(
    assessment_id: str,
    request: Request,
    context: TenantContext = Depends(resolve_tenant_context),
    db: Session = Depends(get_db),
    _: None = Depends(AllPermissionsChecker("risk:read", "audit:export"))  # All of these
):
    """
    Export risk assessment with audit trail.
    
    Requires: risk:read AND audit:export permissions
    """
    service = RiskAssessmentService(db)
    assessment = service.get_assessment(
        tenant_id=context.tenant_id,
        assessment_id=assessment_id
    )
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Export logic here
    return {
        "assessment_id": assessment.id,
        "exported_at": "2024-12-20T00:00:00Z",
        "format": "json"
    }
