"""
RBAC & Policy Router
FastAPI routes for role-based access control
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user, get_current_tenant
from app.modules.rbac_policy.service import RBACService
from app.modules.rbac_policy.schemas import RoleCreate, RoleResponse, PermissionCreate, PermissionResponse, AssignRoleRequest

router = APIRouter(prefix="/rbac", tags=["RBAC & Policy"])


@router.post("/roles", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """Create a new role"""
    service = RBACService(db)
    role = service.create_role(role_data)
    return StandardResponse(
        success=True,
        data=role.dict(),
        message="Role created"
    )


@router.get("/roles", response_model=StandardResponse)
async def list_roles(
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(get_current_tenant)
):
    """List roles"""
    service = RBACService(db)
    roles = service.list_roles(tenant_id)
    return StandardResponse(
        success=True,
        data={"roles": [r.dict() for r in roles]},
        message="Roles retrieved"
    )


@router.post("/permissions", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    permission_data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """Create a new permission"""
    service = RBACService(db)
    permission = service.create_permission(permission_data)
    return StandardResponse(
        success=True,
        data=permission.dict(),
        message="Permission created"
    )


@router.get("/permissions", response_model=StandardResponse)
async def list_permissions(
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """List all permissions"""
    service = RBACService(db)
    permissions = service.list_permissions()
    return StandardResponse(
        success=True,
        data={"permissions": [p.dict() for p in permissions]},
        message="Permissions retrieved"
    )
