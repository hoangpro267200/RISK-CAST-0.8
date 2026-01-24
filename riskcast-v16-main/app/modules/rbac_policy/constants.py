"""
RBAC Permission Constants
Permission keys and default role-permission mappings
RISKCAST V3 - Modular Monolith
"""


class Permissions:
    """Permission constants for RBAC"""
    
    # Risk permissions
    RISK_READ = "risk:read"
    RISK_WRITE = "risk:write"
    RISK_RUN = "risk:run"
    RISK_EXPORT = "risk:export"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    AUDIT_EXPORT = "audit:export"
    
    # Evidence permissions
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_WRITE = "evidence:write"
    EVIDENCE_DELETE = "evidence:delete"
    EVIDENCE_EXPORT = "evidence:export"
    
    # Model versioning permissions
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_PUBLISH = "model:publish"
    MODEL_ACTIVATE = "model:activate"
    
    # Underwriting permissions
    UNDERWRITING_READ = "underwriting:read"
    UNDERWRITING_WRITE = "underwriting:write"
    UNDERWRITING_DECIDE = "underwriting:decide"
    POLICY_BIND = "policy:bind"
    
    # Claims permissions
    CLAIMS_READ = "claims:read"
    CLAIMS_WRITE = "claims:write"
    CLAIMS_ACT = "claims:act"
    PAYOUT_APPROVE = "payout:approve"
    
    # Parametric permissions
    PARAMETRIC_READ = "parametric:read"
    PARAMETRIC_WRITE = "parametric:write"
    PARAMETRIC_MONITOR = "parametric:monitor"
    
    # Tenant management permissions
    TENANT_READ = "tenant:read"
    TENANT_MANAGE = "tenant:manage"
    TENANT_USERS = "tenant:users"
    TENANT_ADMIN = "tenant:admin"
    
    # User management permissions
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"
    USER_INVITE = "user:invite"
    
    # Role management permissions
    ROLE_READ = "role:read"
    ROLE_MANAGE = "role:manage"
    
    # Platform permissions
    PLATFORM_ADMIN = "platform:admin"
    
    # Wildcard for all permissions
    ALL = "*"


# Default role-permission mappings
# These are used as templates when creating roles
DEFAULT_ROLE_PERMISSIONS = {
    "viewer": [
        Permissions.RISK_READ,
        Permissions.AUDIT_READ,
        Permissions.EVIDENCE_READ,
        Permissions.CLAIMS_READ,
        Permissions.PARAMETRIC_READ,
    ],
    "operator": [
        Permissions.RISK_READ,
        Permissions.RISK_WRITE,
        Permissions.RISK_RUN,
        Permissions.AUDIT_READ,
        Permissions.EVIDENCE_READ,
        Permissions.EVIDENCE_WRITE,
        Permissions.CLAIMS_READ,
        Permissions.CLAIMS_WRITE,
        Permissions.PARAMETRIC_READ,
    ],
    "tenant_admin": [
        Permissions.ALL,  # All tenant permissions
    ],
    "underwriter": [
        Permissions.RISK_READ,
        Permissions.RISK_EXPORT,
        Permissions.AUDIT_READ,
        Permissions.EVIDENCE_READ,
        Permissions.EVIDENCE_EXPORT,
        Permissions.UNDERWRITING_READ,
        Permissions.UNDERWRITING_WRITE,
        Permissions.UNDERWRITING_DECIDE,
        Permissions.POLICY_BIND,
        Permissions.MODEL_READ,
    ],
    "claims_adjuster": [
        Permissions.RISK_READ,
        Permissions.AUDIT_READ,
        Permissions.EVIDENCE_READ,
        Permissions.EVIDENCE_WRITE,
        Permissions.CLAIMS_READ,
        Permissions.CLAIMS_WRITE,
        Permissions.CLAIMS_ACT,
        Permissions.PAYOUT_APPROVE,
    ],
    "broker": [
        Permissions.RISK_READ,
        Permissions.RISK_EXPORT,
        Permissions.AUDIT_READ,
        Permissions.EVIDENCE_READ,
        Permissions.UNDERWRITING_READ,
        Permissions.CLAIMS_READ,
    ],
    "compliance_officer": [
        Permissions.RISK_READ,
        Permissions.AUDIT_READ,
        Permissions.AUDIT_EXPORT,
        Permissions.EVIDENCE_READ,
        Permissions.CLAIMS_READ,
    ],
    "platform_admin": [
        Permissions.PLATFORM_ADMIN,  # Full platform access
    ],
}


def get_permissions_for_role(role_name: str) -> list[str]:
    """
    Get default permissions for a role.
    
    Args:
        role_name: Role name
        
    Returns:
        List of permission keys
    """
    permissions = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
    
    # Handle wildcard
    if Permissions.ALL in permissions:
        # Return all permissions except platform_admin
        return [
            getattr(Permissions, attr)
            for attr in dir(Permissions)
            if not attr.startswith("_") and attr != "ALL" and attr != "PLATFORM_ADMIN"
        ]
    
    return permissions


def has_permission(user_permissions: set[str], required_permission: str) -> bool:
    """
    Check if user has required permission.
    
    Handles wildcard (*) permission which grants all permissions.
    
    Args:
        user_permissions: Set of user's permissions
        required_permission: Required permission key
        
    Returns:
        True if user has permission
    """
    # Wildcard grants all permissions
    if Permissions.ALL in user_permissions or Permissions.PLATFORM_ADMIN in user_permissions:
        return True
    
    return required_permission in user_permissions


def has_any_permission(user_permissions: set[str], required_permissions: list[str]) -> bool:
    """
    Check if user has any of the required permissions.
    
    Args:
        user_permissions: Set of user's permissions
        required_permissions: List of required permission keys
        
    Returns:
        True if user has at least one permission
    """
    # Wildcard grants all permissions
    if Permissions.ALL in user_permissions or Permissions.PLATFORM_ADMIN in user_permissions:
        return True
    
    return any(perm in user_permissions for perm in required_permissions)


def has_all_permissions(user_permissions: set[str], required_permissions: list[str]) -> bool:
    """
    Check if user has all required permissions.
    
    Args:
        user_permissions: Set of user's permissions
        required_permissions: List of required permission keys
        
    Returns:
        True if user has all permissions
    """
    # Wildcard grants all permissions
    if Permissions.ALL in user_permissions or Permissions.PLATFORM_ADMIN in user_permissions:
        return True
    
    return all(perm in user_permissions for perm in required_permissions)
