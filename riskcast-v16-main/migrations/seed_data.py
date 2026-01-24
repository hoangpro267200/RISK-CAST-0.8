"""
Seed Data for Roles and Permissions
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy.orm import Session
from app.modules.tenancy.models import Role, Permission, RolePermission, RoleScope
from app.modules.rbac_policy.constants import Permissions, DEFAULT_ROLE_PERMISSIONS


def seed_roles_and_permissions(session: Session):
    """
    Seed initial roles and permissions.
    
    Creates all permissions from Permissions class and assigns them to roles
    based on DEFAULT_ROLE_PERMISSIONS mapping.
    
    Args:
        session: SQLAlchemy session
    """
    # Get all permission constants from Permissions class
    permission_keys = []
    for attr_name in dir(Permissions):
        if not attr_name.startswith("_") and attr_name not in ["ALL"]:
            perm_value = getattr(Permissions, attr_name)
            if isinstance(perm_value, str) and ":" in perm_value:  # Format: "resource:action"
                # Generate description from permission key
                parts = perm_value.split(":")
                resource = parts[0].replace("_", " ").title()
                action = parts[1].replace("_", " ").title()
                description = f"{action} {resource}"
                
                permission_keys.append((perm_value, description))
    
    # Create permissions (skip if already exists)
    permissions = {}
    for key, description in permission_keys:
        # Check if permission already exists
        existing = session.query(Permission).filter(Permission.key == key).first()
        if existing:
            permissions[key] = existing
        else:
            perm = Permission(key=key, description=description)
            session.add(perm)
            permissions[key] = perm
    
    session.flush()
    
    # Get all tenant permissions (exclude PLATFORM_ADMIN)
    all_tenant_permissions = [
        key for key in permissions.keys()
        if key != Permissions.PLATFORM_ADMIN
    ]
    
    # Create roles
    roles_data = [
        ("viewer", RoleScope.TENANT),
        ("operator", RoleScope.TENANT),
        ("tenant_admin", RoleScope.TENANT),
        ("underwriter", RoleScope.TENANT),
        ("claims_adjuster", RoleScope.TENANT),
        ("broker", RoleScope.TENANT),
        ("compliance_officer", RoleScope.TENANT),
        ("platform_admin", RoleScope.PLATFORM),
    ]
    
    roles = {}
    for name, scope in roles_data:
        # Check if role already exists
        existing = session.query(Role).filter(
            Role.name == name,
            Role.scope == scope
        ).first()
        
        if existing:
            roles[name] = existing
        else:
            role = Role(name=name, scope=scope)
            session.add(role)
            roles[name] = role
    
    session.flush()
    
    # Assign permissions to roles
    for role_name, role in roles.items():
        # Get permissions for this role from DEFAULT_ROLE_PERMISSIONS
        role_perms = DEFAULT_ROLE_PERMISSIONS.get(role_name, [])
        
        # Clear existing role permissions (if reseeding)
        session.query(RolePermission).filter(
            RolePermission.role_id == role.id
        ).delete()
        
        for perm_key in role_perms:
            if perm_key == Permissions.ALL:
                # All tenant permissions (for tenant_admin)
                for perm_key_tenant in all_tenant_permissions:
                    if perm_key_tenant in permissions:
                        # Check if association already exists
                        existing = session.query(RolePermission).filter(
                            RolePermission.role_id == role.id,
                            RolePermission.permission_id == permissions[perm_key_tenant].id
                        ).first()
                        if not existing:
                            session.add(RolePermission(
                                role_id=role.id,
                                permission_id=permissions[perm_key_tenant].id
                            ))
            elif perm_key == Permissions.PLATFORM_ADMIN:
                # Platform admin gets platform_admin permission
                if Permissions.PLATFORM_ADMIN in permissions:
                    existing = session.query(RolePermission).filter(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permissions[Permissions.PLATFORM_ADMIN].id
                    ).first()
                    if not existing:
                        session.add(RolePermission(
                            role_id=role.id,
                            permission_id=permissions[Permissions.PLATFORM_ADMIN].id
                        ))
            elif perm_key in permissions:
                # Regular permission
                existing = session.query(RolePermission).filter(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permissions[perm_key].id
                ).first()
                if not existing:
                    session.add(RolePermission(
                        role_id=role.id,
                        permission_id=permissions[perm_key].id
                    ))
    
    session.commit()
    print(f"✅ Seeded {len(permissions)} permissions and {len(roles)} roles")


def clear_roles_and_permissions(session: Session):
    """
    Clear all roles and permissions (for downgrade).
    
    Args:
        session: SQLAlchemy session
    """
    # Delete role permissions first (due to foreign keys)
    session.query(RolePermission).delete()
    
    # Delete roles
    session.query(Role).delete()
    
    # Delete permissions
    session.query(Permission).delete()
    
    session.commit()
    print("✅ Cleared all roles and permissions")
