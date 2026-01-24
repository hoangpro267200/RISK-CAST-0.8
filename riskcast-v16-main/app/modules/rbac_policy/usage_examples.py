"""
RBAC Permission Checking Usage Examples

This file demonstrates different ways to use permission checking in FastAPI routes.
"""
from fastapi import APIRouter, Request, Depends
from app.shared.dependencies import TenantContext
from app.modules.rbac_policy.service import require_permission, require_any_permission
from app.modules.rbac_policy.decorators import permissions_required, require_all_permissions
from app.modules.rbac_policy.constants import Permissions

router = APIRouter()


# Example 1: Using dependency injection (recommended)
@router.get("/risk-assessments")
async def get_risk_assessments(
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """Endpoint requiring risk:read permission"""
    return {
        "message": "Access granted",
        "tenant_id": context.tenant_id,
        "permissions": list(context.permissions)
    }


# Example 2: Requiring multiple permissions (ALL required)
@router.post("/risk-assessments")
async def create_risk_assessment(
    context: TenantContext = Depends(require_permission(
        Permissions.RISK_READ,
        Permissions.RISK_WRITE
    ))
):
    """Endpoint requiring both risk:read and risk:write"""
    return {"message": "Assessment created"}


# Example 3: Requiring ANY permission (OR logic)
@router.get("/reports")
async def get_reports(
    context: TenantContext = Depends(require_any_permission(
        Permissions.RISK_READ,
        Permissions.AUDIT_READ
    ))
):
    """Endpoint requiring risk:read OR audit:read"""
    return {"message": "Reports accessed"}


# Example 4: Using decorator approach
@router.get("/evidence")
@permissions_required(Permissions.EVIDENCE_READ)
async def get_evidence(request: Request):
    """Endpoint using decorator for permission check"""
    context = request.state.tenant_context
    return {
        "message": "Evidence accessed",
        "tenant_id": context.tenant_id
    }


# Example 5: Requiring all permissions with decorator
@router.post("/evidence")
@require_all_permissions(Permissions.EVIDENCE_READ, Permissions.EVIDENCE_WRITE)
async def upload_evidence(request: Request):
    """Endpoint requiring both evidence:read and evidence:write"""
    return {"message": "Evidence uploaded"}


# Example 6: Underwriting endpoint with multiple permissions
@router.post("/underwriting/decide")
async def make_underwriting_decision(
    context: TenantContext = Depends(require_permission(
        Permissions.UNDERWRITING_READ,
        Permissions.UNDERWRITING_DECIDE
    ))
):
    """Endpoint for underwriting decisions"""
    return {"message": "Decision made"}


# Example 7: Admin endpoint
@router.get("/admin/tenants")
async def list_tenants(
    context: TenantContext = Depends(require_permission(Permissions.TENANT_ADMIN))
):
    """Admin endpoint requiring tenant:admin permission"""
    return {"message": "Tenants listed"}


# Example 8: Platform admin endpoint
@router.get("/platform/users")
async def list_platform_users(
    context: TenantContext = Depends(require_permission(Permissions.PLATFORM_ADMIN))
):
    """Platform admin endpoint"""
    return {"message": "Platform users listed"}


# Example 9: Combining with other dependencies
@router.delete("/risk-assessments/{assessment_id}")
async def delete_assessment(
    assessment_id: str,
    context: TenantContext = Depends(require_permission(Permissions.RISK_WRITE))
):
    """Endpoint with permission check and path parameter"""
    return {"message": f"Assessment {assessment_id} deleted"}


# Example 10: Using constants for type safety
@router.get("/claims")
async def get_claims(
    context: TenantContext = Depends(require_permission(Permissions.CLAIMS_READ))
):
    """Endpoint using permission constant"""
    return {"message": "Claims accessed"}
