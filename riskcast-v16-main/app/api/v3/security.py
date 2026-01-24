"""
Security compliance API endpoints.

Security controls, assessments, and remediation plans.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.security_compliance_service import (
    SecurityComplianceService,
    ControlNotFoundError,
    ControlExistsError,
    InvalidFrameworkError,
    RemediationPlanNotFoundError
)
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security Compliance"])


def get_security_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> SecurityComplianceService:
    """Dependency to get SecurityComplianceService."""
    audit = AuditLedger(db)
    return SecurityComplianceService(db, audit)


# ==================== Security Controls ====================

@router.post("/controls", status_code=status.HTTP_201_CREATED)
async def create_control(
    control_id: str = Query(..., description="Unique control identifier"),
    name: str = Query(...),
    framework: str = Query(..., description="SOC2, ISO27001, GDPR, PCI_DSS, NIST"),
    description: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    subcategory: Optional[str] = Query(None),
    control_type: Optional[str] = Query(None, description="PREVENTIVE, DETECTIVE, CORRECTIVE"),
    implementation_type: Optional[str] = Query(None, description="TECHNICAL, ADMINISTRATIVE, PHYSICAL"),
    evidence_requirements: Optional[Dict[str, Any]] = Body(None),
    owner_user_id: Optional[str] = Query(None),
    owner_role: Optional[str] = Query(None),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:write"))
) -> dict:
    """
    Create a new security control.
    """
    created_by = context.user_id or context.actor_id
    
    if not created_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        control = service.create_control(
            control_id=control_id,
            name=name,
            framework=framework,
            created_by=created_by,
            description=description,
            category=category,
            subcategory=subcategory,
            control_type=control_type,
            implementation_type=implementation_type,
            evidence_requirements=evidence_requirements,
            owner_user_id=owner_user_id,
            owner_role=owner_role
        )
        
        return {
            "id": control.id,
            "control_id": control.control_id,
            "name": control.name,
            "framework": control.framework,
            "status": control.status,
            "created_at": control.created_at.isoformat() if control.created_at else None
        }
    except (ControlExistsError, InvalidFrameworkError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/controls")
async def list_controls(
    framework: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> List[dict]:
    """
    List security controls with filters.
    """
    controls = service.list_controls(
        framework=framework,
        status=status,
        category=category
    )
    
    return [
        {
            "id": c.id,
            "control_id": c.control_id,
            "name": c.name,
            "framework": c.framework,
            "category": c.category,
            "status": c.status,
            "control_type": c.control_type,
            "owner_user_id": c.owner_user_id
        }
        for c in controls
    ]


@router.get("/controls/{control_id}")
async def get_control(
    control_id: str,
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> dict:
    """
    Get security control details.
    """
    try:
        control = service.get_control(control_id)
        return {
            "id": control.id,
            "control_id": control.control_id,
            "name": control.name,
            "description": control.description,
            "framework": control.framework,
            "category": control.category,
            "subcategory": control.subcategory,
            "control_type": control.control_type,
            "implementation_type": control.implementation_type,
            "status": control.status,
            "evidence_requirements": control.evidence_requirements_json,
            "owner_user_id": control.owner_user_id,
            "owner_role": control.owner_role,
            "created_at": control.created_at.isoformat() if control.created_at else None,
            "updated_at": control.updated_at.isoformat() if control.updated_at else None
        }
    except ControlNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/controls/{control_id}/status")
async def update_control_status(
    control_id: str,
    status: str = Body(..., description="NOT_IMPLEMENTED, IMPLEMENTED, PARTIALLY_IMPLEMENTED, NOT_APPLICABLE"),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:write"))
) -> dict:
    """
    Update control implementation status.
    """
    updated_by = context.user_id or context.actor_id
    
    if not updated_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        control = service.update_control_status(
            control_id=control_id,
            status=status,
            updated_by=updated_by
        )
        
        return {
            "id": control.id,
            "control_id": control.control_id,
            "status": control.status,
            "updated_at": control.updated_at.isoformat() if control.updated_at else None
        }
    except ControlNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/frameworks/{framework}/compliance")
async def get_framework_compliance(
    framework: str,
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> dict:
    """
    Get compliance summary for a framework.
    """
    try:
        summary = service.get_framework_compliance_summary(framework)
        return summary
    except Exception as e:
        logger.error(f"Failed to get framework compliance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance summary: {str(e)}"
        )


# ==================== Assessments ====================

@router.post("/assessments", status_code=status.HTTP_201_CREATED)
async def create_assessment(
    control_id: str = Query(...),
    assessment_date: date = Query(...),
    effectiveness: str = Query(..., description="EFFECTIVE, PARTIALLY_EFFECTIVE, INEFFECTIVE"),
    maturity_level: Optional[int] = Query(None, ge=1, le=5),
    risk_rating: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    assessment_type: str = Query("INTERNAL", description="INTERNAL, EXTERNAL, SELF"),
    findings: Optional[Dict[str, Any]] = Body(None),
    evidence_bundle_id: Optional[str] = Query(None),
    evidence_summary: Optional[str] = Body(None),
    next_assessment_date: Optional[date] = Query(None),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:write"))
) -> dict:
    """
    Create a control assessment.
    
    Automatically creates remediation plan if control is not effective.
    """
    assessor_id = context.user_id or context.actor_id
    
    if not assessor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        assessment = service.create_assessment(
            control_id=control_id,
            assessment_date=assessment_date,
            effectiveness=effectiveness,
            assessor_id=assessor_id,
            assessment_type=assessment_type,
            maturity_level=maturity_level,
            risk_rating=risk_rating,
            findings=findings,
            evidence_bundle_id=evidence_bundle_id,
            evidence_summary=evidence_summary,
            next_assessment_date=next_assessment_date
        )
        
        return {
            "id": assessment.id,
            "control_id": assessment.control_id,
            "assessment_date": assessment.assessment_date.isoformat(),
            "effectiveness": assessment.effectiveness,
            "maturity_level": assessment.maturity_level,
            "risk_rating": assessment.risk_rating,
            "next_assessment_date": assessment.next_assessment_date.isoformat() if assessment.next_assessment_date else None,
            "created_at": assessment.created_at.isoformat() if assessment.created_at else None
        }
    except ControlNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/controls/{control_id}/assessments")
async def get_assessment_history(
    control_id: str,
    limit: int = Query(10, ge=1, le=50),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> List[dict]:
    """
    Get assessment history for a control.
    """
    try:
        assessments = service.get_assessment_history(control_id, limit=limit)
        
        return [
            {
                "id": a.id,
                "assessment_date": a.assessment_date.isoformat(),
                "effectiveness": a.effectiveness,
                "maturity_level": a.maturity_level,
                "risk_rating": a.risk_rating,
                "assessment_type": a.assessment_type,
                "next_assessment_date": a.next_assessment_date.isoformat() if a.next_assessment_date else None,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in assessments
        ]
    except ControlNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/assessments/overdue")
async def get_overdue_assessments(
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> List[dict]:
    """
    Get controls with overdue assessments.
    """
    overdue = service.get_overdue_assessments()
    return overdue


# ==================== Remediation Plans ====================

@router.post("/remediation-plans", status_code=status.HTTP_201_CREATED)
async def create_remediation_plan(
    control_id: str = Query(...),
    title: str = Query(...),
    description: str = Body(...),
    target_date: date = Query(...),
    priority: str = Query("MEDIUM", description="LOW, MEDIUM, HIGH, CRITICAL"),
    assessment_id: Optional[str] = Query(None),
    actions: Optional[List[Dict[str, Any]]] = Body(None),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:write"))
) -> dict:
    """
    Create a remediation plan.
    """
    owner_id = context.user_id or context.actor_id
    
    if not owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        plan = service.create_remediation_plan(
            control_id=control_id,
            title=title,
            description=description,
            target_date=target_date,
            owner_id=owner_id,
            priority=priority,
            assessment_id=assessment_id,
            actions=actions
        )
        
        return {
            "id": plan.id,
            "control_id": plan.control_id,
            "title": plan.title,
            "priority": plan.priority,
            "status": plan.status,
            "target_date": plan.target_date.isoformat() if plan.target_date else None,
            "created_at": plan.created_at.isoformat() if plan.created_at else None
        }
    except ControlNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/remediation-plans/{plan_id}/status")
async def update_remediation_status(
    plan_id: str,
    status: str = Body(..., description="PLANNED, IN_PROGRESS, COMPLETED, CANCELLED"),
    completion_date: Optional[date] = Body(None),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:write"))
) -> dict:
    """
    Update remediation plan status.
    """
    updated_by = context.user_id or context.actor_id
    
    if not updated_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        plan = service.update_remediation_status(
            plan_id=plan_id,
            status=status,
            updated_by=updated_by,
            completion_date=completion_date
        )
        
        return {
            "id": plan.id,
            "status": plan.status,
            "completion_date": plan.completion_date.isoformat() if plan.completion_date else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
        }
    except RemediationPlanNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/remediation-plans")
async def list_remediation_plans(
    priority: Optional[str] = Query(None, description="LOW, MEDIUM, HIGH, CRITICAL"),
    status: Optional[str] = Query(None, description="PLANNED, IN_PROGRESS, COMPLETED, CANCELLED"),
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> List[dict]:
    """
    List remediation plans.
    """
    if status and status in ['PLANNED', 'IN_PROGRESS']:
        plans = service.get_open_remediations(priority=priority)
    else:
        from app.models.security import ControlRemediationPlan
        query = service.db.query(ControlRemediationPlan)
        if priority:
            query = query.filter(ControlRemediationPlan.priority == priority)
        if status:
            query = query.filter(ControlRemediationPlan.status == status)
        plans = query.order_by(ControlRemediationPlan.target_date).all()
    
    return [
        {
            "id": p.id,
            "control_id": p.control_id,
            "title": p.title,
            "priority": p.priority,
            "status": p.status,
            "target_date": p.target_date.isoformat() if p.target_date else None,
            "completion_date": p.completion_date.isoformat() if p.completion_date else None,
            "owner_user_id": p.owner_user_id
        }
        for p in plans
    ]


# ==================== Reporting ====================

@router.get("/compliance-report")
async def generate_compliance_report(
    service: SecurityComplianceService = Depends(get_security_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("security:read"))
) -> dict:
    """
    Generate comprehensive compliance report.
    
    Returns overall statistics and framework breakdowns.
    """
    try:
        report = service.generate_compliance_report()
        return report
    except Exception as e:
        logger.error(f"Failed to generate compliance report: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
