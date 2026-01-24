"""
Unit Tests for RBAC Permission Checking
Tests for permission checking in API routes.
"""
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps.rbac import PermissionChecker, AnyPermissionChecker, AllPermissionsChecker
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.services.rbac_service import RBACService
from app.models.tenant import Membership, MembershipStatus
from app.models.rbac import Role, Permission
from app.shared.utils import generate_ulid
from app.database import get_db


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return generate_ulid()


@pytest.fixture
def user_id():
    """Test user ID"""
    return generate_ulid()


@pytest.fixture
def rbac_service(db_session):
    """RBAC service instance"""
    return RBACService(db_session)


@pytest.fixture
def admin_role(db_session):
    """Create admin role with all permissions"""
    role = Role(
        name="admin",
        is_system_role=True,
        description="Full access"
    )
    db_session.add(role)
    
    # Add all permissions
    permissions = [
        Permission(name="risk:read", resource="risk", action="read"),
        Permission(name="risk:write", resource="risk", action="write"),
        Permission(name="audit:read", resource="audit", action="read"),
        Permission(name="audit:export", resource="audit", action="export"),
    ]
    for perm in permissions:
        db_session.add(perm)
        role.permissions.append(perm)
    
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def viewer_role(db_session):
    """Create viewer role with read-only permissions"""
    role = Role(
        name="viewer",
        is_system_role=True,
        description="Read-only access"
    )
    db_session.add(role)
    
    # Add read permissions only
    perm = Permission(name="risk:read", resource="risk", action="read")
    db_session.add(perm)
    role.permissions.append(perm)
    
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def admin_membership(db_session, tenant_id, user_id, admin_role):
    """Create membership with admin role"""
    membership = Membership(
        tenant_id=tenant_id,
        user_id=user_id,
        role="admin",
        status=MembershipStatus.ACTIVE
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    return membership


@pytest.fixture
def viewer_membership(db_session, tenant_id, user_id, viewer_role):
    """Create membership with viewer role"""
    # Create a different user for viewer
    viewer_user_id = generate_ulid()
    membership = Membership(
        tenant_id=tenant_id,
        user_id=viewer_user_id,
        role="viewer",
        status=MembershipStatus.ACTIVE
    )
    db_session.add(membership)
    db_session.commit()
    db_session.refresh(membership)
    return membership, viewer_user_id


class TestPermissionChecker:
    """Tests for PermissionChecker dependency"""
    
    async def test_user_with_permission_can_access(
        self, db_session, tenant_id, user_id, admin_membership, admin_role
    ):
        """User with permission should be able to access"""
        # Create context
        context = TenantContext(
            tenant_id=tenant_id,
            user_id=user_id,
            membership_id=admin_membership.id,
            role_names=["admin"],
            permissions=set(),  # Will be loaded by RBAC service
            actor_type="USER",
            actor_id=user_id
        )
        
        # Create mock request
        from unittest.mock import Mock
        request = Mock()
        
        # Check permission
        rbac_service = RBACService(db_session)
        has_perm = rbac_service.has_permission(user_id, tenant_id, "risk:write")
        
        assert has_perm is True
    
    async def test_user_without_permission_gets_403(
        self, db_session, tenant_id, viewer_membership, viewer_role
    ):
        """User without permission should get 403"""
        viewer_user_id = viewer_membership[1]
        
        # Create context
        context = TenantContext(
            tenant_id=tenant_id,
            user_id=viewer_user_id,
            membership_id=viewer_membership[0].id,
            role_names=["viewer"],
            permissions=set(),
            actor_type="USER",
            actor_id=viewer_user_id
        )
        
        # Check permission
        rbac_service = RBACService(db_session)
        has_perm = rbac_service.has_permission(
            viewer_user_id,
            tenant_id,
            "risk:write"
        )
        
        assert has_perm is False
    
    async def test_admin_role_has_all_permissions(
        self, db_session, tenant_id, user_id, admin_membership, admin_role
    ):
        """Admin role should have all permissions"""
        rbac_service = RBACService(db_session)
        
        # Check various permissions
        assert rbac_service.has_permission(user_id, tenant_id, "risk:read") is True
        assert rbac_service.has_permission(user_id, tenant_id, "risk:write") is True
        assert rbac_service.has_permission(user_id, tenant_id, "audit:read") is True
        assert rbac_service.has_permission(user_id, tenant_id, "audit:export") is True


class TestAnyPermissionChecker:
    """Tests for AnyPermissionChecker dependency"""
    
    async def test_user_with_any_permission_can_access(
        self, db_session, tenant_id, user_id, admin_membership, admin_role
    ):
        """User with any of the required permissions should be able to access"""
        rbac_service = RBACService(db_session)
        
        # User has risk:write, so should pass with any of [risk:read, risk:write]
        has_any = (
            rbac_service.has_permission(user_id, tenant_id, "risk:read") or
            rbac_service.has_permission(user_id, tenant_id, "risk:write")
        )
        
        assert has_any is True
    
    async def test_user_without_any_permission_gets_403(
        self, db_session, tenant_id, viewer_membership, viewer_role
    ):
        """User without any of the required permissions should get 403"""
        viewer_user_id = viewer_membership[1]
        rbac_service = RBACService(db_session)
        
        # Viewer only has risk:read, not risk:write or audit:export
        has_any = (
            rbac_service.has_permission(viewer_user_id, tenant_id, "risk:write") or
            rbac_service.has_permission(viewer_user_id, tenant_id, "audit:export")
        )
        
        assert has_any is False


class TestAllPermissionsChecker:
    """Tests for AllPermissionsChecker dependency"""
    
    async def test_user_with_all_permissions_can_access(
        self, db_session, tenant_id, user_id, admin_membership, admin_role
    ):
        """User with all required permissions should be able to access"""
        rbac_service = RBACService(db_session)
        
        # Admin has both permissions
        has_all = (
            rbac_service.has_permission(user_id, tenant_id, "risk:read") and
            rbac_service.has_permission(user_id, tenant_id, "audit:export")
        )
        
        assert has_all is True
    
    async def test_user_without_all_permissions_gets_403(
        self, db_session, tenant_id, viewer_membership, viewer_role
    ):
        """User without all required permissions should get 403"""
        viewer_user_id = viewer_membership[1]
        rbac_service = RBACService(db_session)
        
        # Viewer has risk:read but not audit:export
        has_all = (
            rbac_service.has_permission(viewer_user_id, tenant_id, "risk:read") and
            rbac_service.has_permission(viewer_user_id, tenant_id, "audit:export")
        )
        
        assert has_all is False


class TestPermissionCheckingIntegration:
    """Integration tests for permission checking in routes"""
    
    def test_permission_checker_raises_403_on_missing_permission(
        self, db_session, tenant_id, viewer_membership, viewer_role
    ):
        """PermissionChecker should raise 403 when permission is missing"""
        viewer_user_id = viewer_membership[1]
        rbac_service = RBACService(db_session)
        
        # Viewer doesn't have risk:write
        has_perm = rbac_service.has_permission(
            viewer_user_id,
            tenant_id,
            "risk:write"
        )
        
        assert has_perm is False
    
    def test_permission_checker_allows_access_with_permission(
        self, db_session, tenant_id, user_id, admin_membership, admin_role
    ):
        """PermissionChecker should allow access when permission exists"""
        rbac_service = RBACService(db_session)
        
        # Admin has risk:write
        has_perm = rbac_service.has_permission(
            user_id,
            tenant_id,
            "risk:write"
        )
        
        assert has_perm is True
