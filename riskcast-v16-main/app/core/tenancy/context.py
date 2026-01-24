"""
Tenant Context Management
Thread-safe tenant context using ContextVar for automatic query scoping.
"""
from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
from typing import Optional
import uuid

# Context variable for current tenant ID
_tenant_context: ContextVar[Optional[str]] = ContextVar(
    'tenant_id',
    default=None
)


class TenantNotSetError(Exception):
    """Raised when tenant context is required but not set"""
    pass


def get_current_tenant_id() -> str:
    """
    Get the current tenant ID from context.
    
    Returns:
        Tenant ID (UUID string)
        
    Raises:
        TenantNotSetError: If tenant context is not set
    """
    tenant_id = _tenant_context.get()
    if tenant_id is None:
        raise TenantNotSetError(
            "Tenant context not set. Use tenant_context() context manager "
            "or set_tenant_context() to set tenant ID before querying."
        )
    return tenant_id


def set_tenant_context(tenant_id: str) -> None:
    """
    Set the tenant context for the current execution context.
    
    This sets the tenant ID for the current async task/thread.
    Use tenant_context() context manager for automatic cleanup.
    
    Args:
        tenant_id: Tenant ID (UUID string)
    """
    _tenant_context.set(tenant_id)


@contextmanager
def tenant_context(tenant_id: Optional[str]):
    """
    Context manager for setting tenant context.
    
    Automatically resets context when exiting.
    
    Usage:
        with tenant_context("tenant-uuid"):
            # All queries here are scoped to this tenant
            assessments = db.query(RiskAssessment).all()
    
    Args:
        tenant_id: Tenant ID (UUID string) or None to clear context
        
    Yields:
        None
    """
    token = _tenant_context.set(tenant_id)
    try:
        yield
    finally:
        _tenant_context.reset(token)


def clear_tenant_context() -> None:
    """
    Clear the tenant context.
    
    Note: Prefer using tenant_context(None) context manager.
    """
    _tenant_context.set(None)
