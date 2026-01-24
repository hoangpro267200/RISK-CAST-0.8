"""
Example Usage of Tenant Context Dependencies

This file demonstrates how to use tenant context resolution in FastAPI routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import (
    TenantContext, get_current_user, resolve_tenant_context,
    require_tenant, require_user, require_permission, get_tenant_context
)
from app.modules.tenancy.models import User
from app.database import get_db

router = APIRouter()


# Example 1: Endpoint requiring tenant context
@router.get("/example-1")
async def example_with_tenant_context(
    context: TenantContext = Depends(require_tenant()),
    db: Session = Depends(get_db)
):
    """Endpoint that requires tenant context"""
    return {
        "tenant_id": context.tenant_id,
        "user_id": context.user_id,
        "permissions": list(context.permissions),
        "actor_type": context.actor_type
    }


# Example 2: Endpoint requiring user authentication
@router.get("/example-2")
async def example_with_user(
    user: User = Depends(require_user()),
    db: Session = Depends(get_db)
):
    """Endpoint that requires user authentication"""
    return {
        "user_id": user.id,
        "email": user.email
    }


# Example 3: Endpoint requiring specific permission
@router.get("/example-3")
async def example_with_permission(
    context: TenantContext = Depends(require_permission("risk:read")),
    db: Session = Depends(get_db)
):
    """Endpoint that requires 'risk:read' permission"""
    return {
        "message": "Access granted",
        "tenant_id": context.tenant_id,
        "permissions": list(context.permissions)
    }


# Example 4: Endpoint with optional authentication
@router.get("/example-4")
async def example_optional_auth(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Endpoint with optional authentication"""
    if user:
        return {"authenticated": True, "user_id": user.id}
    else:
        return {"authenticated": False}


# Example 5: Access tenant context from request state
@router.get("/example-5")
async def example_from_request_state(
    request: Request
):
    """Access tenant context from request state"""
    context = get_tenant_context(request)
    if context:
        return {
            "tenant_id": context.tenant_id,
            "permissions": list(context.permissions)
        }
    return {"message": "No tenant context"}
