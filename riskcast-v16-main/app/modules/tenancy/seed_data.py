"""
Seed Data for Tenancy Module
Standard roles and permissions for RISKCAST V3
"""
from app.modules.tenancy.models import (
    Role, RoleScope, Permission, RolePermission
)


# Standard roles
STANDARD_ROLES = [
    # Tenant scope roles
    {"name": "tenant_admin", "scope": RoleScope.TENANT},
    {"name": "operator", "scope": RoleScope.TENANT},
    {"name": "viewer", "scope": RoleScope.TENANT},
    {"name": "underwriter", "scope": RoleScope.TENANT},
    {"name": "claims_adjuster", "scope": RoleScope.TENANT},
    {"name": "broker", "scope": RoleScope.TENANT},
    {"name": "compliance_officer", "scope": RoleScope.TENANT},
    # Platform scope roles
    {"name": "platform_admin", "scope": RoleScope.PLATFORM},
]

# Standard permissions
STANDARD_PERMISSIONS = [
    # Risk permissions
    {"key": "risk:read", "description": "Read risk assessments"},
    {"key": "risk:write", "description": "Create and update risk assessments"},
    {"key": "risk:run", "description": "Run risk calculations"},
    {"key": "risk:export", "description": "Export risk data"},
    
    # Audit permissions
    {"key": "audit:read", "description": "Read audit logs"},
    {"key": "audit:export", "description": "Export audit logs"},
    
    # Evidence permissions
    {"key": "evidence:read", "description": "Read evidence"},
    {"key": "evidence:write", "description": "Upload evidence"},
    {"key": "evidence:delete", "description": "Delete evidence"},
    
    # Underwriting permissions
    {"key": "underwriting:read", "description": "Read underwriting decisions"},
    {"key": "underwriting:decide", "description": "Make underwriting decisions"},
    {"key": "underwriting:approve", "description": "Approve policies"},
    
    # Claims permissions
    {"key": "claims:read", "description": "Read claims"},
    {"key": "claims:create", "description": "Create claims"},
    {"key": "claims:process", "description": "Process claims"},
    {"key": "claims:approve", "description": "Approve claim payments"},
    
    # Parametric permissions
    {"key": "parametric:read", "description": "Read parametric triggers"},
    {"key": "parametric:write", "description": "Create parametric triggers"},
    {"key": "parametric:monitor", "description": "Monitor parametric triggers"},
    
    # Tenant management permissions
    {"key": "tenant:read", "description": "Read tenant information"},
    {"key": "tenant:manage", "description": "Manage tenant settings"},
    {"key": "tenant:users", "description": "Manage tenant users"},
    
    # User management permissions
    {"key": "user:read", "description": "Read user information"},
    {"key": "user:manage", "description": "Manage users"},
    {"key": "user:invite", "description": "Invite users"},
    
    # Role management permissions
    {"key": "role:read", "description": "Read roles"},
    {"key": "role:manage", "description": "Manage roles and permissions"},
    
    # Model versioning permissions
    {"key": "model:read", "description": "Read model versions"},
    {"key": "model:manage", "description": "Manage model versions"},
    
    # Platform permissions
    {"key": "platform:admin", "description": "Full platform access"},
]


# Role-Permission mappings
ROLE_PERMISSIONS = {
    "tenant_admin": [
        "risk:read", "risk:write", "risk:run", "risk:export",
        "audit:read", "audit:export",
        "evidence:read", "evidence:write", "evidence:delete",
        "underwriting:read", "underwriting:decide", "underwriting:approve",
        "claims:read", "claims:create", "claims:process", "claims:approve",
        "parametric:read", "parametric:write", "parametric:monitor",
        "tenant:read", "tenant:manage", "tenant:users",
        "user:read", "user:manage", "user:invite",
        "role:read", "role:manage",
        "model:read",
    ],
    "operator": [
        "risk:read", "risk:write", "risk:run",
        "audit:read",
        "evidence:read", "evidence:write",
        "claims:read", "claims:create",
        "parametric:read",
    ],
    "viewer": [
        "risk:read",
        "audit:read",
        "evidence:read",
        "claims:read",
        "parametric:read",
    ],
    "underwriter": [
        "risk:read", "risk:export",
        "audit:read",
        "evidence:read",
        "underwriting:read", "underwriting:decide", "underwriting:approve",
        "model:read",
    ],
    "claims_adjuster": [
        "risk:read",
        "audit:read",
        "evidence:read", "evidence:write",
        "claims:read", "claims:create", "claims:process", "claims:approve",
    ],
    "broker": [
        "risk:read", "risk:export",
        "audit:read",
        "evidence:read",
        "underwriting:read",
        "claims:read",
    ],
    "compliance_officer": [
        "risk:read",
        "audit:read", "audit:export",
        "evidence:read",
        "claims:read",
    ],
    "platform_admin": [
        # All permissions
        *[p["key"] for p in STANDARD_PERMISSIONS],
    ],
}


def seed_roles_and_permissions(db):
    """
    Seed standard roles and permissions.
    
    Args:
        db: Database session
    """
    # Create permissions
    permission_map = {}
    for perm_data in STANDARD_PERMISSIONS:
        permission = db.query(Permission).filter(Permission.key == perm_data["key"]).first()
        if not permission:
            permission = Permission(**perm_data)
            db.add(permission)
        permission_map[perm_data["key"]] = permission
    
    db.commit()
    
    # Create roles and assign permissions
    for role_data in STANDARD_ROLES:
        role = db.query(Role).filter(
            Role.name == role_data["name"],
            Role.scope == role_data["scope"]
        ).first()
        
        if not role:
            role = Role(**role_data)
            db.add(role)
            db.flush()  # Get role.id
        
        # Assign permissions
        permission_keys = ROLE_PERMISSIONS.get(role_data["name"], [])
        for perm_key in permission_keys:
            permission = permission_map.get(perm_key)
            if permission:
                # Check if association exists
                existing = db.query(RolePermission).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id
                ).first()
                
                if not existing:
                    role_perm = RolePermission(
                        role_id=role.id,
                        permission_id=permission.id
                    )
                    db.add(role_perm)
    
    db.commit()
    print("✅ Roles and permissions seeded successfully")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        seed_roles_and_permissions(db)
    finally:
        db.close()
