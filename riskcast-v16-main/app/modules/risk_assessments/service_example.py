"""
Risk Assessment Service Usage Examples

This file demonstrates how to use RiskAssessmentService.
"""
from app.modules.risk_assessments.service import RiskAssessmentService
from app.modules.risk_assessments.schemas import RiskAssessmentCreate, RiskAssessmentInputV3
from app.modules.audit_ledger.schemas import AuditContext
from app.database import get_tenant_scoped_db
from app.shared.dependencies import resolve_tenant_context, TenantContext
from fastapi import Depends


# Example 1: Create a risk assessment
async def create_assessment_example(
    data: RiskAssessmentCreate,
    context: TenantContext = Depends(resolve_tenant_context),
    db = Depends(get_tenant_scoped_db)
):
    """Create a new risk assessment"""
    service = RiskAssessmentService(db)
    
    # Create audit context
    audit_context = AuditContext(
        request_id="req-123",
        trace_id="trace-456",
        ip="192.168.1.1",
        user_agent="Mozilla/5.0",
        route="/api/v3/risk-assessments",
        method="POST"
    )
    
    # Create assessment
    assessment = await service.create_assessment(
        data=data,
        user_id=context.user_id,
        context=audit_context
    )
    
    return assessment


# Example 2: Get an assessment
async def get_assessment_example(
    assessment_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db = Depends(get_tenant_scoped_db)
):
    """Get a risk assessment by ID"""
    service = RiskAssessmentService(db)
    
    assessment = await service.get_assessment(assessment_id)
    
    return assessment


# Example 3: List assessments
async def list_assessments_example(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    context: TenantContext = Depends(resolve_tenant_context),
    db = Depends(get_tenant_scoped_db)
):
    """List risk assessments"""
    service = RiskAssessmentService(db)
    
    assessments = await service.list_assessments(
        skip=skip,
        limit=limit,
        status=status
    )
    
    return assessments


# Example 4: Update assessment status
async def update_status_example(
    assessment_id: str,
    new_status: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db = Depends(get_tenant_scoped_db)
):
    """Update assessment status"""
    service = RiskAssessmentService(db)
    
    audit_context = AuditContext(
        request_id="req-789",
        route="/api/v3/risk-assessments/{assessment_id}/status",
        method="PATCH"
    )
    
    assessment = await service.update_assessment_status(
        assessment_id=assessment_id,
        new_status=new_status,
        user_id=context.user_id,
        context=audit_context
    )
    
    return assessment


# Example 5: Archive assessment
async def archive_assessment_example(
    assessment_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db = Depends(get_tenant_scoped_db)
):
    """Archive a risk assessment"""
    service = RiskAssessmentService(db)
    
    audit_context = AuditContext(
        request_id="req-999",
        route="/api/v3/risk-assessments/{assessment_id}/archive",
        method="POST"
    )
    
    assessment = await service.archive_assessment(
        assessment_id=assessment_id,
        user_id=context.user_id,
        context=audit_context
    )
    
    return assessment


# Example 6: Find by input hash (deduplication)
async def find_duplicate_example(
    input_data: RiskAssessmentInputV3,
    context: TenantContext = Depends(resolve_tenant_context),
    db = Depends(get_tenant_scoped_db)
):
    """Find existing assessment with same input hash"""
    service = RiskAssessmentService(db)
    
    # Compute hash
    input_dict = input_data.model_dump(exclude_none=True, mode='json')
    canonical_input = service._canonicalize_input(input_dict)
    input_hash = service._compute_input_hash(canonical_input)
    
    # Find existing
    existing = service.find_by_input_hash(input_hash)
    
    if existing:
        return {"duplicate": True, "assessment_id": existing.id}
    else:
        return {"duplicate": False}
