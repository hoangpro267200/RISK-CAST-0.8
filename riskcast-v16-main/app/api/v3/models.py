"""
Model Versioning API Endpoints
API v3 endpoints for model versioning
RISKCAST V3 - Modular Monolith
"""
from fastapi import APIRouter, Depends, Request, status, HTTPException
from typing import TYPE_CHECKING
import logging

# Import dependencies
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.shared.utils import build_audit_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.modules.model_versioning.service import ModelVersionService
from app.modules.model_versioning.schemas import (
    ModelVersionCreate,
    ModelVersionResponse,
    ModelVersionUpdate
)

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession, get_tenant_scoped_db

logger = logging.getLogger(__name__)

# Model versioning router
router = APIRouter(prefix="/model-versions", tags=["models"])


@router.post(
    "",
    response_model=ModelVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create model version",
    description="Create a new draft model version"
)
async def create_model_version(
    data: ModelVersionCreate,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.MODEL_WRITE))
):
    """Create a new draft model version"""
    # Get tenant-scoped DB session
    from app.database import get_tenant_scoped_db, get_db
    
    # Get raw DB session
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        # Get tenant-scoped session
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = ModelVersionService(db)
        model = await service.create_draft(
            data=data,
            user_id=context.user_id,
            context=audit_context
        )
        
        return ModelVersionResponse(
            id=model.id,
            tenant_id=model.tenant_id,
            scope=model.scope,
            name=model.name,
            status=model.status,
            model_schema_version=model.model_schema_version,
            weights_json=model.weights_json,
            calibration_json=model.calibration_json,
            constraints_json=model.constraints_json,
            metrics_json=model.metrics_json,
            created_by_user_id=model.created_by_user_id,
            published_at=model.published_at,
            immutable_hash=model.immutable_hash,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    finally:
        db_session.close()


@router.post(
    "/{id}/publish",
    response_model=ModelVersionResponse,
    summary="Publish model version",
    description="Publish a draft model version (makes it immutable)"
)
async def publish_model_version(
    id: str,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.MODEL_PUBLISH))
):
    """Publish a draft model version"""
    from pydantic import BaseModel
    
    class PublishRequest(BaseModel):
        reason: str = ""
    
    # Parse request body if provided (optional)
    publish_data = PublishRequest(reason="")
    try:
        body = await request.json()
        if body:
            publish_data = PublishRequest(**body)
    except:
        pass  # Use default if no body
    
    # Get tenant-scoped DB session
    from app.database import get_tenant_scoped_db, get_db
    
    # Get raw DB session
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        # Get tenant-scoped session
        db = await get_tenant_scoped_db(request, db_session)
        
        audit_context = build_audit_context(request)
        
        service = ModelVersionService(db)
        model = await service.publish(
            model_id=id,
            user_id=context.user_id,
            context=audit_context,
            reason=publish_data.reason if publish_data.reason else None
        )
        
        return ModelVersionResponse(
            id=model.id,
            tenant_id=model.tenant_id,
            scope=model.scope,
            name=model.name,
            status=model.status,
            model_schema_version=model.model_schema_version,
            weights_json=model.weights_json,
            calibration_json=model.calibration_json,
            constraints_json=model.constraints_json,
            metrics_json=model.metrics_json,
            created_by_user_id=model.created_by_user_id,
            published_at=model.published_at,
            immutable_hash=model.immutable_hash,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    finally:
        db_session.close()


@router.get(
    "/{id}",
    response_model=ModelVersionResponse,
    summary="Get model version",
    description="Get model version by ID"
)
async def get_model_version(
    id: str,
    request: Request,
    context: TenantContext = Depends(require_permission(Permissions.MODEL_READ))
):
    """Get model version by ID"""
    from app.database import get_tenant_scoped_db, get_db
    
    db_gen = get_db()
    db_session = next(db_gen)
    
    try:
        db = await get_tenant_scoped_db(request, db_session)
        
        service = ModelVersionService(db)
        model = await service.get_model(id)
        
        return ModelVersionResponse(
            id=model.id,
            tenant_id=model.tenant_id,
            scope=model.scope,
            name=model.name,
            status=model.status,
            model_schema_version=model.model_schema_version,
            weights_json=model.weights_json,
            calibration_json=model.calibration_json,
            constraints_json=model.constraints_json,
            metrics_json=model.metrics_json,
            created_by_user_id=model.created_by_user_id,
            published_at=model.published_at,
            immutable_hash=model.immutable_hash,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    finally:
        db_session.close()
