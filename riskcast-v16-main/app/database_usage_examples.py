"""
Tenant-Scoped Database Session Usage Examples

This file demonstrates how to use TenantScopedSession in FastAPI routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db, get_tenant_scoped_db, TenantScopedSession
from app.shared.dependencies import TenantContext, resolve_tenant_context, require_tenant
from app.modules.risk_assessments.models import RiskAssessment

router = APIRouter()


# Example 1: Basic usage with resolve_tenant_context
@router.get("/risk-assessments")
async def get_risk_assessments(
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Get all risk assessments for the current tenant.
    
    The query is automatically filtered by tenant_id - no need to
    manually add .filter(RiskAssessment.tenant_id == context.tenant_id)
    """
    # This query is automatically filtered by tenant_id
    assessments = db.query(RiskAssessment).all()
    return {"assessments": [a.id for a in assessments]}


# Example 2: Using require_tenant() (recommended)
@router.post("/risk-assessments")
async def create_risk_assessment(
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Create a new risk assessment.
    
    The tenant_id is automatically set when adding the instance.
    """
    # Create new assessment - tenant_id will be auto-assigned
    assessment = RiskAssessment(
        assessment_id="ASSESS-001",
        input_data={"route": "..."},
        risk_score=0.75,
        # tenant_id is automatically set to context.tenant_id
    )
    
    db.add(assessment)  # tenant_id auto-assigned here
    db.commit()
    
    return {"assessment_id": assessment.id}


# Example 3: Query with filters (tenant filter is automatic)
@router.get("/risk-assessments/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Get a specific risk assessment.
    
    The query is automatically filtered by tenant_id, so users can only
    access assessments from their own tenant.
    """
    # This query is automatically filtered by tenant_id
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.id == assessment_id
    ).first()
    
    if not assessment:
        return {"error": "Assessment not found"}
    
    return {"assessment": assessment.id}


# Example 4: Using get() method (with tenant validation)
@router.get("/risk-assessments/{assessment_id}/simple")
async def get_assessment_simple(
    assessment_id: str,
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Get assessment using get() method.
    
    WARNING: get() validates tenant_id but doesn't filter automatically.
    If tenant_id doesn't match, returns None.
    Prefer query() for better safety.
    """
    assessment = db.get(RiskAssessment, assessment_id)
    
    if not assessment:
        return {"error": "Assessment not found or not accessible"}
    
    return {"assessment": assessment.id}


# Example 5: Adding instance with explicit tenant_id (validated)
@router.put("/risk-assessments/{assessment_id}")
async def update_assessment(
    assessment_id: str,
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Update risk assessment.
    
    If you explicitly set tenant_id, it will be validated to match
    the session's tenant_id.
    """
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.id == assessment_id
    ).first()
    
    if not assessment:
        return {"error": "Assessment not found"}
    
    # Update fields
    assessment.risk_score = 0.85
    
    # If you try to change tenant_id, it will raise ValueError
    # assessment.tenant_id = "different_tenant_id"  # Would raise ValueError
    
    db.commit()
    
    return {"assessment_id": assessment.id}


# Example 6: Using raw session for non-tenant-scoped models
@router.get("/admin/tenants")
async def list_all_tenants(
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    List all tenants (admin only).
    
    For non-tenant-scoped models (like Tenant itself), use _raw_session.
    WARNING: This bypasses tenant scoping - use with caution!
    """
    from app.modules.tenancy.models import Tenant
    
    # Use raw session for non-tenant-scoped models
    tenants = db._raw_session.query(Tenant).all()
    
    return {"tenants": [t.name for t in tenants]}


# Example 7: Context manager usage
@router.post("/risk-assessments/batch")
async def create_batch_assessments(
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Create multiple assessments in a transaction.
    
    Using context manager ensures proper commit/rollback.
    """
    assessments = []
    
    try:
        with db:
            for i in range(5):
                assessment = RiskAssessment(
                    assessment_id=f"ASSESS-{i:03d}",
                    input_data={"route": f"route_{i}"},
                    risk_score=0.5 + (i * 0.1),
                )
                db.add(assessment)
                assessments.append(assessment.id)
        
        # Context manager commits automatically on success
        return {"created": assessments}
    
    except Exception as e:
        # Context manager rolls back on exception
        return {"error": str(e)}


# Example 8: Error handling for tenant mismatch
@router.post("/risk-assessments/transfer")
async def transfer_assessment(
    assessment_id: str,
    target_tenant_id: str,
    context: TenantContext = Depends(require_tenant()),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    """
    Attempt to transfer assessment (will fail with tenant validation).
    
    This demonstrates the tenant guardrail in action.
    """
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.id == assessment_id
    ).first()
    
    if not assessment:
        return {"error": "Assessment not found"}
    
    # Try to change tenant_id - this will raise ValueError
    try:
        assessment.tenant_id = target_tenant_id
        db.commit()
        return {"success": True}
    except ValueError as e:
        return {"error": str(e)}  # "Cannot add ... with tenant_id=... to session scoped to tenant_id=..."
