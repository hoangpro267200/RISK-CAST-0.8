"""
Tenancy Router
FastAPI routes for tenant management
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.shared.dependencies import require_user
from app.shared.schemas import StandardResponse, PaginationParams
from app.modules.tenancy.service import TenancyService
from app.modules.tenancy.schemas import TenantCreate, TenantUpdate, TenantResponse

router = APIRouter(prefix="/tenants", tags=["Tenancy"])


@router.post("", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """Create a new tenant"""
    service = TenancyService(db)
    tenant = service.create_tenant(tenant_data)
    return StandardResponse(
        success=True,
        data=tenant.dict(),
        message="Tenant created successfully"
    )


@router.get("/{tenant_id}", response_model=StandardResponse)
async def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """Get tenant by ID"""
    service = TenancyService(db)
    tenant = service.get_tenant(tenant_id)
    return StandardResponse(
        success=True,
        data=tenant.dict(),
        message="Tenant retrieved"
    )


@router.get("", response_model=StandardResponse)
async def list_tenants(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """List all tenants"""
    service = TenancyService(db)
    tenants = service.list_tenants(
        skip=pagination.offset,
        limit=pagination.limit
    )
    return StandardResponse(
        success=True,
        data={
            "tenants": [t.dict() for t in tenants],
            "pagination": pagination.dict()
        },
        message="Tenants retrieved"
    )


@router.patch("/{tenant_id}", response_model=StandardResponse)
async def update_tenant(
    tenant_id: str,
    update_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """Update tenant"""
    service = TenancyService(db)
    tenant = service.update_tenant(tenant_id, update_data)
    return StandardResponse(
        success=True,
        data=tenant.dict(),
        message="Tenant updated"
    )


@router.delete("/{tenant_id}", response_model=StandardResponse)
async def delete_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_user)
):
    """Delete tenant (soft delete)"""
    service = TenancyService(db)
    service.delete_tenant(tenant_id)
    return StandardResponse(
        success=True,
        message="Tenant deleted"
    )
