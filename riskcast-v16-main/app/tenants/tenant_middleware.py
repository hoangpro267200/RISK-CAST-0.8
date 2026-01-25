"""
Tenant Middleware

Handles tenant resolution and context injection.
"""

from typing import Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import contextvars

from app.tenants.tenant_manager import TenantManager, Tenant


# Context variable for current tenant
_current_tenant: contextvars.ContextVar[Optional[Tenant]] = contextvars.ContextVar(
    "current_tenant", default=None
)


def get_current_tenant() -> Optional[Tenant]:
    """Get current tenant from context."""
    return _current_tenant.get()


def set_current_tenant(tenant: Optional[Tenant]):
    """Set current tenant in context."""
    _current_tenant.set(tenant)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to resolve and inject tenant context.
    
    Resolution order:
    1. X-Tenant-ID header
    2. Custom domain
    3. Subdomain
    4. Default tenant (if configured)
    """
    
    def __init__(self, app, db_session_factory, audit, default_tenant_id: Optional[str] = None):
        super().__init__(app)
        self.db_session_factory = db_session_factory
        self.audit = audit
        self.default_tenant_id = default_tenant_id
    
    async def dispatch(self, request: Request, call_next):
        tenant = None
        
        # Skip tenant resolution for certain paths
        skip_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
        if any(request.url.path.startswith(p) for p in skip_paths):
            return await call_next(request)
        
        db = self.db_session_factory()
        manager = TenantManager(db, self.audit)
        
        try:
            # 1. Check X-Tenant-ID header
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                tenant = await manager.get_tenant(tenant_id)
                if not tenant:
                    raise HTTPException(404, f"Tenant {tenant_id} not found")
            
            # 2. Check custom domain
            if not tenant:
                host = request.headers.get("host", "").split(":")[0]
                tenant = await manager.get_tenant_by_domain(host)
            
            # 3. Check subdomain
            if not tenant:
                host = request.headers.get("host", "").split(":")[0]
                parts = host.split(".")
                if len(parts) >= 3:
                    subdomain = parts[0]
                    tenant = await manager.get_tenant_by_slug(subdomain)
            
            # 4. Default tenant
            if not tenant and self.default_tenant_id:
                tenant = await manager.get_tenant(self.default_tenant_id)
            
            # Validate tenant status
            if tenant:
                from app.tenants.tenant_manager import TenantStatus
                if tenant.status != TenantStatus.ACTIVE:
                    raise HTTPException(403, f"Tenant is {tenant.status.value}")
            
            # Set tenant in context
            set_current_tenant(tenant)
            
            # Add tenant to request state
            request.state.tenant = tenant
            request.state.tenant_id = tenant.id if tenant else None
            
            response = await call_next(request)
            
            # Add tenant header to response
            if tenant:
                response.headers["X-Tenant-ID"] = tenant.id
            
            return response
            
        finally:
            db.close()
            set_current_tenant(None)


class TenantDependency:
    """
    FastAPI dependency for tenant-aware endpoints.
    """
    def __init__(self, required: bool = True):
        self.required = required
    
    async def __call__(self, request: Request) -> Optional[Tenant]:
        tenant = getattr(request.state, "tenant", None)
        
        if self.required and not tenant:
            raise HTTPException(400, "Tenant context required")
        
        return tenant


# Convenience functions for dependency injection
def require_tenant():
    """Dependency that requires tenant context."""
    return TenantDependency(required=True)


def optional_tenant():
    """Dependency that optionally uses tenant context."""
    return TenantDependency(required=False)
