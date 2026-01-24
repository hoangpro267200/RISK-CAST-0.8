"""
Risk Assessments Router
FastAPI routes for risk assessments
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse, PaginationParams
from app.shared.dependencies import require_user, require_tenant
from app.modules.risk_assessments.service import RiskAssessmentService
from app.modules.risk_assessments.schemas import RiskAssessmentResponse

router = APIRouter(prefix="/risk-assessments", tags=["Risk Assessments"])


@router.get("/{assessment_id}", response_model=StandardResponse)
async def get_assessment(
    assessment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Get risk assessment by ID"""
    service = RiskAssessmentService(db)
    assessment = service.get_assessment(assessment_id, tenant_id)
    return StandardResponse(
        success=True,
        data=assessment.dict(),
        message="Risk assessment retrieved"
    )


@router.get("", response_model=StandardResponse)
async def list_assessments(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """List risk assessments"""
    service = RiskAssessmentService(db)
    assessments = service.list_assessments(
        tenant_id,
        skip=pagination.offset,
        limit=pagination.limit
    )
    return StandardResponse(
        success=True,
        data={
            "assessments": [a.dict() for a in assessments],
            "pagination": pagination.dict()
        },
        message="Risk assessments retrieved"
    )
