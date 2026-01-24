"""
Tenancy Module Exceptions
Custom exceptions for tenancy operations
RISKCAST V3 - Modular Monolith
"""
from fastapi import status
from typing import Optional

from app.shared.exceptions import RISKCASTException, NotFoundError, ConflictError


class TenantNotFoundError(NotFoundError):
    """Tenant not found exception"""
    
    def __init__(self, tenant_id: Optional[str] = None):
        super().__init__("Tenant", tenant_id)
        self.error_code = "TENANT_NOT_FOUND"


class TenantAlreadyExistsError(ConflictError):
    """Tenant already exists exception"""
    
    def __init__(self, name: str):
        super().__init__(
            f"Tenant with name '{name}' already exists",
            resource="tenant"
        )
        self.error_code = "TENANT_ALREADY_EXISTS"


class MembershipNotFoundError(NotFoundError):
    """Membership not found exception"""
    
    def __init__(self, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        detail = "Membership not found"
        if tenant_id and user_id:
            detail = f"Membership not found for tenant {tenant_id} and user {user_id}"
        super().__init__("Membership", f"{tenant_id}:{user_id}" if tenant_id and user_id else None)
        self.error_code = "MEMBERSHIP_NOT_FOUND"


class InvalidMembershipError(RISKCASTException):
    """Invalid membership operation exception"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="INVALID_MEMBERSHIP"
        )


class UserNotFoundError(NotFoundError):
    """User not found exception"""
    
    def __init__(self, user_id: Optional[str] = None):
        super().__init__("User", user_id)
        self.error_code = "USER_NOT_FOUND"


class RoleNotFoundError(NotFoundError):
    """Role not found exception"""
    
    def __init__(self, role_id: Optional[str] = None):
        super().__init__("Role", role_id)
        self.error_code = "ROLE_NOT_FOUND"
