"""
Tenant Middleware
Extracts tenant ID from request and sets tenant context for automatic query scoping.
"""
from __future__ import annotations

from typing import Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.tenancy.context import tenant_context, TenantNotSetError
from app.shared.dependencies import resolve_tenant_context, TenantContext


def extract_tenant_id(request: Request) -> Optional[str]:
    """
    Extract tenant ID from request.
    
    Checks in order:
    1. JWT claims (if available)
    2. API key tenant (from request.state.api_key_tenant)
    3. X-Tenant-ID header (for internal services)
    4. request.state.tenant_id (from resolve_tenant_context)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Tenant ID (UUID string) or None if not found
    """
    # 1. Check request.state.tenant_id (set by resolve_tenant_context)
    tenant_id = getattr(request.state, 'tenant_id', None)
    if tenant_id:
        return tenant_id
    
    # 2. Check API key tenant
    api_key_tenant = getattr(request.state, 'api_key_tenant', None)
    if api_key_tenant and hasattr(api_key_tenant, 'id'):
        return api_key_tenant.id
    
    # 3. Check X-Tenant-ID header (for internal services)
    x_tenant_id = request.headers.get("X-Tenant-ID")
    if x_tenant_id:
        return x_tenant_id
    
    # 4. Check X-Tenant-Id header (alternative format)
    x_tenant_id_alt = request.headers.get("X-Tenant-Id")
    if x_tenant_id_alt:
        return x_tenant_id_alt
    
    # 5. Try to get from JWT claims (if available)
    # This would require JWT decoding - for now, return None
    # In a full implementation, you'd decode JWT and extract tenant_id claim
    
    return None


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that sets tenant context for automatic query scoping.
    
    Extracts tenant ID from request and sets it in context using tenant_context().
    All database queries within the request will be automatically scoped to this tenant.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with tenant context.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Extract tenant ID
        tenant_id = extract_tenant_id(request)
        
        # If tenant ID found, set context
        if tenant_id:
            with tenant_context(tenant_id):
                response = await call_next(request)
                return response
        else:
            # No tenant ID - proceed without context
            # Some endpoints may not require tenant context (e.g., public endpoints)
            response = await call_next(request)
            return response


# Alternative: Dependency-based approach (more explicit)
async def set_tenant_context_from_request(
    request: Request,
    tenant_context: Optional[TenantContext] = None
) -> Optional[str]:
    """
    Set tenant context from request (for use as FastAPI dependency).
    
    This is an alternative to middleware - can be used as a dependency
    for routes that require tenant context.
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            tenant_id: str = Depends(set_tenant_context_from_request)
        ):
            # Tenant context is now set
            assessments = db.query(RiskAssessment).all()
    
    Args:
        request: FastAPI request
        tenant_context: Optional TenantContext (from resolve_tenant_context dependency)
        
    Returns:
        Tenant ID (UUID string) or None
    """
    # Try to get from resolved tenant context first
    if tenant_context:
        from app.core.tenancy.context import set_tenant_context
        set_tenant_context(tenant_context.tenant_id)
        return tenant_context.tenant_id
    
    # Fall back to extraction
    tenant_id = extract_tenant_id(request)
    if tenant_id:
        from app.core.tenancy.context import set_tenant_context
        set_tenant_context(tenant_id)
    
    return tenant_id
