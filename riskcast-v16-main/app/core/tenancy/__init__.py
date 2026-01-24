"""
Tenancy Core Module
Automatic tenant scoping for database queries.
"""
from app.core.tenancy.context import (
    get_current_tenant_id,
    set_tenant_context,
    tenant_context,
    TenantNotSetError,
)
from app.core.tenancy.scoped_session import TenantScopedQuery, TenantScopedSession

__all__ = [
    "get_current_tenant_id",
    "set_tenant_context",
    "tenant_context",
    "TenantNotSetError",
    "TenantScopedQuery",
    "TenantScopedSession",
]
