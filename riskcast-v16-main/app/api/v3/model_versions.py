"""
Model Version Management API

Endpoints for managing model versions:
- List all versions
- Get version details
- Compare versions
- Publish/deprecate versions
- Set active version
- View calibration history
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context, require_user
from app.api.deps.rbac import PermissionChecker
from app.core.audit_ledger.ledger import AuditLedger
from app.modules.model_versioning.service import ModelVersionService
from app.modules.model_versioning.exceptions import (
    ModelVersionNotFoundError,
    ModelVersionExistsError,
    DuplicateModelError,
    InvalidModelStateError,
    ActivationNotFoundError,
)
from app.modules.model_versioning.schemas import (
    ModelVersionCreateRequest,
    ModelVersionResponse,
    ModelVersionDetailResponse,
    ModelActivationCreateRequest,
    ModelActivationResponse,
    ModelVersionStatus,
)
from app.modules.model_versioning.models import (
    ActivationScopeType,
    RiskModelVersion,
    ModelVersionStatus as ModelVersionStatusEnum,
)
from app.modules.audit_ledger.schemas import AuditContext
from app.core.model_versioning.selector import ModelSelector, ModelSelectionContext
from app.models.calibration import CalibrationRun
from app.models.system_config import SystemConfig

router = APIRouter(prefix="/models", tags=["Model Versions"])


# ---------- Schemas ----------


class DeprecateRequest(BaseModel):
    """Request to deprecate a model version."""

    reason: str = Field(..., description="Reason for deprecation")
    replacement_version_id: Optional[str] = Field(None, description="Replacement model version ID")


class SetActiveRequest(BaseModel):
    """Request to set active model version."""

    model_version_id: str = Field(..., description="Model version ID to set as active")


# ---------- Dependencies ----------


async def get_model_service(
    request: Request,
    db_session: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context),
) -> ModelVersionService:
    """Get model version service with tenant-scoped session."""
    from app.database import get_tenant_scoped_db

    db = await get_tenant_scoped_db(request, db_session)
    return ModelVersionService(db)


def get_audit(db: Session = Depends(get_db)) -> AuditLedger:
    """Get audit ledger for logging model version actions."""
    return AuditLedger(db)


async def get_model_service_with_audit(
    request: Request,
    db_session: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context),
    audit: AuditLedger = Depends(get_audit),
) -> ModelVersionService:
    """Get model version service with audit (for publish, deprecate, set-active)."""
    from app.database import get_tenant_scoped_db

    db = await get_tenant_scoped_db(request, db_session)
    return ModelVersionService(db, audit)


@router.post(
    "/versions",
    response_model=ModelVersionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create model version",
    description="Create a new model version in DRAFT status"
)
async def create_model_version(
    request_data: ModelVersionCreateRequest,
    http_request: Request,
    service: ModelVersionService = Depends(get_model_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user=Depends(require_user),
    _: None = Depends(PermissionChecker("model:write")),
) -> ModelVersionDetailResponse:
    """
    Create a new model version.

    The model is created in DRAFT status and must be published
    before it can be activated for risk assessments.
    """
    try:
        model = await service.create_draft_detailed(
            request=request_data,
            user_id=user.id,
            context=context,
        )
        
        return ModelVersionDetailResponse(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            version=model.version,
            description=model.description,
            status=model.status,
            immutable_hash=model.immutable_hash if model.immutable_hash else "",
            parent_version_id=model.parent_version_id,
            published_at=model.published_at,
            approved_at=model.approved_at,
            created_at=model.created_at,
            base_weights=model.base_weights_json or {},
            correlation_matrix=model.correlation_matrix_json or {},
            tail_parameters=model.tail_parameters_json or {},
            interaction_multipliers=model.interaction_multipliers_json or {},
            loss_transform_params=model.loss_transform_params_json or {},
            monte_carlo_defaults=model.monte_carlo_defaults_json,
            calibration_run_id=model.calibration_run_id,
            approved_by_user_id=model.approved_by_user_id
        )
    except ModelVersionExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except DuplicateModelError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/versions",
    response_model=List[ModelVersionResponse],
    summary="List model versions",
    description="List model versions for the tenant",
)
async def list_model_versions(
    http_request: Request,
    status_filter: Optional[ModelVersionStatus] = Query(None, alias="status"),
    include_deprecated: bool = Query(False, description="Include deprecated versions"),
    include_system: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    service: ModelVersionService = Depends(get_model_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("model:read")),
) -> List[ModelVersionResponse]:
    """List model versions for the tenant."""
    models = service.list_models(
        skip=skip,
        limit=limit,
        status=status_filter,
        include_deprecated=include_deprecated,
        tenant_id=getattr(context, "tenant_id", None),
    )
    return [
        ModelVersionResponse(
            id=m.id,
            tenant_id=m.tenant_id,
            name=m.name,
            version=m.version,
            description=m.description,
            status=m.status,
            immutable_hash=m.immutable_hash,
            parent_version_id=m.parent_version_id,
            published_at=m.published_at,
            created_at=m.created_at,
        )
        for m in models
    ]


@router.get(
    "/versions/{model_id}",
    response_model=ModelVersionDetailResponse,
    summary="Get model version",
    description="Get model version details",
)
async def get_model_version(
    model_id: str,
    http_request: Request,
    service: ModelVersionService = Depends(get_model_service),
    _: None = Depends(PermissionChecker("model:read")),
) -> ModelVersionDetailResponse:
    """Get model version details."""
    try:
        model = service.get_model(model_id)
        return ModelVersionDetailResponse(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            version=model.version,
            description=model.description,
            status=model.status,
            immutable_hash=model.immutable_hash or "",
            parent_version_id=model.parent_version_id,
            published_at=model.published_at,
            approved_at=model.approved_at,
            created_at=model.created_at,
            base_weights=model.base_weights_json or {},
            correlation_matrix=model.correlation_matrix_json or {},
            tail_parameters=model.tail_parameters_json or {},
            interaction_multipliers=model.interaction_multipliers_json or {},
            loss_transform_params=model.loss_transform_params_json or {},
            monte_carlo_defaults=model.monte_carlo_defaults_json,
            calibration_run_id=model.calibration_run_id,
            approved_by_user_id=model.approved_by_user_id,
        )
    except ModelVersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/versions/{model_id}/publish",
    response_model=ModelVersionResponse,
    summary="Publish model version",
    description="Publish a model version (DRAFT -> PUBLISHED). After publishing, the model parameters are immutable.",
)
async def publish_model_version(
    model_id: str,
    http_request: Request,
    approval_notes: Optional[str] = Query(None),
    service: ModelVersionService = Depends(get_model_service_with_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    user=Depends(require_user),
    _: None = Depends(PermissionChecker("model:publish")),
) -> ModelVersionResponse:
    """
    Publish a model version.

    After publishing, the model parameters are immutable.
    Only published models can be activated.
    """
    try:
        model = await service.publish(model_id=model_id, user_id=user.id)
        return ModelVersionResponse.model_validate(model)
    except ModelVersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidModelStateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post(
    "/versions/{model_id}/deprecate",
    response_model=ModelVersionResponse,
    summary="Deprecate model version",
    description="Deprecate a model version (PUBLISHED -> DEPRECATED). Optional replacement_version_id.",
)
async def deprecate_model_version(
    model_id: str,
    body: DeprecateRequest,
    http_request: Request,
    service: ModelVersionService = Depends(get_model_service_with_audit),
    context: TenantContext = Depends(resolve_tenant_context),
    user=Depends(require_user),
    _: None = Depends(PermissionChecker("model:write")),
) -> ModelVersionResponse:
    """
    Deprecate a model version.

    Deprecated models can still be referenced by existing policies
    but cannot be activated for new assessments.
    """
    try:
        model = await service.deprecate(
            model_id=model_id,
            user_id=user.id,
            reason=body.reason,
            replacement_version_id=body.replacement_version_id,
        )
        return ModelVersionResponse.model_validate(model)
    except ModelVersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidModelStateError as e:
        raise HTTPException(status_code=409, detail=str(e))


# Activations

@router.post(
    "/activations",
    response_model=ModelActivationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create model activation",
    description="Activate a model version for a specific scope. Existing activations for the same scope are automatically superseded.",
)
async def create_activation(
    request: ModelActivationCreateRequest,
    service: ModelVersionService = Depends(get_model_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user=Depends(require_user),
    _: None = Depends(PermissionChecker("model:activate")),
) -> ModelActivationResponse:
    """
    Activate a model version for a specific scope.

    Existing activations for the same scope are automatically superseded.
    """
    try:
        activation = await service.create_activation_detailed(
            request=request,
            user_id=user.id,
            context=context,
        )
        return ModelActivationResponse.model_validate({
            **{k: v for k, v in vars(activation).items() if not k.startswith("_")},
            "activated_at": activation.activated_at or activation.created_at or datetime.utcnow(),
        })
    except ModelVersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidModelStateError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get(
    "/activations",
    response_model=List[ModelActivationResponse],
    summary="List model activations",
    description="List model activations",
)
async def list_activations(
    scope_type: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: ModelVersionService = Depends(get_model_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("model:read")),
) -> List[ModelActivationResponse]:
    """List model activations."""
    activations = service.list_activations(
        skip=skip,
        limit=limit,
        model_version_id=None,
        product_type=None,
    )
    if scope_type:
        activations = [a for a in activations if getattr(a.scope_type, "value", a.scope_type) == scope_type]
    if active_only:
        activations = [a for a in activations if getattr(a.status, "value", a.status) == "ACTIVE"]
    return [
        ModelActivationResponse.model_validate({
            **{k: v for k, v in vars(a).items() if not k.startswith("_")},
            "activated_at": a.activated_at or a.created_at,
        })
        for a in activations
    ]


@router.post(
    "/activations/{activation_id}/deactivate",
    response_model=ModelActivationResponse,
    summary="Deactivate model activation",
    description="Deactivate a model activation"
)
async def deactivate_activation(
    activation_id: str,
    http_request: Request,
    reason: str = Query(..., description="Reason for deactivation"),
    service: ModelVersionService = Depends(get_model_service),
    context: TenantContext = Depends(resolve_tenant_context),
    user = Depends(require_user),
    _: None = Depends(PermissionChecker("model:activate"))
) -> ModelActivationResponse:
    """Deactivate a model activation."""
    try:
        audit_context = AuditContext(
            request_id=None,
            user_agent=None,
            ip_address=None
        )
        
        activation = await service.deactivate_activation(
            activation_id=activation_id,
            user_id=user.id,
            context=audit_context,
            reason=reason
        )
        
        return ModelActivationResponse.model_validate({
            **activation.__dict__,
            'activated_at': activation.activated_at or activation.created_at
        })
    except ActivationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------- Active version & set-active ----------


def _get_active_version(db: Session) -> Optional[RiskModelVersion]:
    """Resolve active model version: SystemConfig key else latest published."""
    config = db.query(SystemConfig).filter(SystemConfig.key == "active_model_version_id").first()
    if config and config.value:
        m = db.query(RiskModelVersion).filter(RiskModelVersion.id == config.value).first()
        if m:
            return m
    return (
        db.query(RiskModelVersion)
        .filter(RiskModelVersion.status == ModelVersionStatusEnum.PUBLISHED)
        .order_by(RiskModelVersion.published_at.desc())
        .first()
    )


@router.get(
    "/active",
    response_model=ModelVersionDetailResponse,
    summary="Get active model version",
    description="Currently active model version used for new risk assessments.",
)
async def get_active_model_version(
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("model:read")),
) -> ModelVersionDetailResponse:
    """Get the currently active model version."""
    version = _get_active_version(db)
    if not version:
        raise HTTPException(status_code=404, detail="No active model version found")
    return ModelVersionDetailResponse(
        id=version.id,
        tenant_id=version.tenant_id,
        name=version.name,
        version=version.version,
        description=version.description,
        status=version.status,
        immutable_hash=version.immutable_hash or "",
        parent_version_id=version.parent_version_id,
        published_at=version.published_at,
        approved_at=version.approved_at,
        created_at=version.created_at,
        base_weights=version.base_weights_json or {},
        correlation_matrix=version.correlation_matrix_json or {},
        tail_parameters=version.tail_parameters_json or {},
        interaction_multipliers=version.interaction_multipliers_json or {},
        loss_transform_params=version.loss_transform_params_json or {},
        monte_carlo_defaults=version.monte_carlo_defaults_json,
        calibration_run_id=version.calibration_run_id,
        approved_by_user_id=version.approved_by_user_id,
    )


@router.get(
    "/versions/{model_id}/parameters",
    summary="Get model parameters",
    description="Full parameters: layer weights, correlation matrix, loss function.",
)
async def get_model_parameters(
    model_id: str,
    service: ModelVersionService = Depends(get_model_service),
    _: None = Depends(PermissionChecker("model:read")),
) -> dict:
    """Get full parameters of a model version."""
    try:
        version = service.get_model(model_id)
    except ModelVersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {
        "version_id": version.id,
        "name": version.name,
        "version": version.version,
        "parameters": version.weights_json or version.base_weights_json,
        "layer_weights": version.base_weights_json or {},
        "correlations": version.correlation_matrix_json or {},
        "loss_function": version.loss_transform_params_json or {},
        "immutable_hash": version.immutable_hash,
    }


@router.get(
    "/versions/{model_id}/calibration",
    summary="Get calibration info",
    description="Calibration run and dataset details for this model.",
)
async def get_calibration_info(
    model_id: str,
    db: Session = Depends(get_db),
    service: ModelVersionService = Depends(get_model_service),
    _: None = Depends(PermissionChecker("model:read")),
) -> dict:
    """Get calibration information for a model version."""
    try:
        version = service.get_model(model_id)
    except ModelVersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not version.is_calibrated():
        return {"is_calibrated": False, "message": "This model uses default (uncalibrated) parameters"}
    run = (
        db.query(CalibrationRun)
        .filter(CalibrationRun.id == version.calibration_run_id)
        .first()
    )
    if not run:
        return {
            "is_calibrated": True,
            "calibration_run_id": str(version.calibration_run_id),
            "message": "Calibration run details not available",
        }
    return {
        "is_calibrated": True,
        "calibration_run_id": str(run.id),
        "calibration_data": {
            "start_date": run.dataset_start_date.isoformat() if run.dataset_start_date else None,
            "end_date": run.dataset_end_date.isoformat() if run.dataset_end_date else None,
            "dataset_size": run.dataset_size,
            "dataset_hash": run.dataset_hash,
        },
        "weight_calibration": {
            "method": run.weight_method,
            "before_mse": run.weight_before_mse,
            "after_mse": run.weight_after_mse,
            "improvement_pct": run.weight_improvement_pct,
        },
        "correlation_calibration": {
            "method": run.correlation_method,
            "stability": run.correlation_stability,
        },
        "loss_function_calibration": {
            "type": run.loss_function_type,
            "before_r2": run.loss_function_before_r2,
            "after_r2": run.loss_function_after_r2,
        },
        "validation_passed": run.validation_passed,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get(
    "/compare/{version_1_id}/{version_2_id}",
    summary="Compare model versions",
    description="Compare weights, loss function, and calibration.",
)
async def compare_model_versions(
    version_1_id: str,
    version_2_id: str,
    service: ModelVersionService = Depends(get_model_service),
    _: None = Depends(PermissionChecker("model:read")),
) -> dict:
    """Compare two model versions."""
    try:
        comparison = await service.compare_versions(version_1_id, version_2_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    weight_changes = comparison.get("weight_changes", {})
    total_change = sum(abs(w.get("change", 0)) for w in weight_changes.values())
    max_change = max((abs(w.get("change", 0)) for w in weight_changes.values()), default=0)
    summary = {
        "total_weight_change": total_change,
        "max_weight_change": max_change,
        "significant_changes": sum(1 for w in weight_changes.values() if abs(w.get("change_pct", 0)) > 10),
        "v1_is_calibrated": comparison.get("version_1", {}).get("is_calibrated"),
        "v2_is_calibrated": comparison.get("version_2", {}).get("is_calibrated"),
    }
    return {
        "version_1": comparison.get("version_1"),
        "version_2": comparison.get("version_2"),
        "weight_changes": weight_changes,
        "loss_function_changes": comparison.get("loss_function_changes", {}),
        "summary": summary,
    }


@router.post(
    "/set-active",
    summary="Set active model version",
    description="Set the model version used for new risk assessments. Only published versions.",
)
async def set_active_model_version(
    body: SetActiveRequest,
    db: Session = Depends(get_db),
    audit: AuditLedger = Depends(get_audit),
    user=Depends(require_user),
    _: None = Depends(PermissionChecker("model:activate")),
) -> dict:
    """Set the active model version."""
    version = db.query(RiskModelVersion).filter(RiskModelVersion.id == body.model_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail=f"Model version {body.model_version_id} not found")
    if version.status != ModelVersionStatusEnum.PUBLISHED:
        raise HTTPException(
            status_code=400,
            detail=f"Only published versions can be set as active. Current status: {version.status}",
        )
    config = db.query(SystemConfig).filter(SystemConfig.key == "active_model_version_id").first()
    old_version_id = None
    if config:
        old_version_id = config.value
        config.value = str(version.id)
        config.updated_at = datetime.utcnow()
    else:
        config = SystemConfig(key="active_model_version_id", value=str(version.id))
        db.add(config)
    db.commit()
    try:
        audit.append_event(
            tenant_id=version.tenant_id or "system",
            event_type="MODEL_VERSION",
            action="SET_ACTIVE",
            entity_type="model_version",
            entity_id=str(version.id),
            actor_type="USER",
            actor_id=str(user.id),
            payload={
                "previous_active_version_id": old_version_id,
                "new_active_version_id": str(version.id),
                "version_name": version.name,
            },
        )
    except Exception:
        pass
    return {
        "status": "success",
        "active_version_id": str(version.id),
        "active_version_name": version.name,
        "previous_version_id": old_version_id,
    }


@router.get(
    "/versions/{model_id}/usage-stats",
    summary="Version usage statistics",
    description="Risk run counts per day for this model version.",
)
async def get_version_usage_stats(
    model_id: str,
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    _: None = Depends(PermissionChecker("model:read")),
) -> dict:
    """Get usage statistics for a model version."""
    start_date = datetime.utcnow() - timedelta(days=days)
    try:
        from app.modules.risk_runs.models import RiskRun as RRun
    except Exception:
        from app.models.risk_run import RiskRun as RRun
    total = db.query(func.count(RRun.id)).filter(
        RRun.model_version_id == model_id,
        RRun.created_at >= start_date,
    ).scalar() or 0
    rows = (
        db.query(func.date(RRun.created_at).label("date"), func.count(RRun.id).label("count"))
        .filter(RRun.model_version_id == model_id, RRun.created_at >= start_date)
        .group_by(func.date(RRun.created_at))
        .all()
    )
    return {
        "version_id": model_id,
        "period_days": days,
        "total_risk_runs": total,
        "daily_counts": [{"date": str(r.date), "count": r.count} for r in rows],
    }


# Selection preview

@router.get(
    "/selection/preview",
    summary="Preview model selection",
    description="Preview which model would be selected for a given context. Useful for testing activation rules before running assessments."
)
async def preview_model_selection(
    http_request: Request,
    corridor_id: Optional[str] = Query(None),
    product_id: Optional[str] = Query(None),
    carrier_id: Optional[str] = Query(None),
    as_of: Optional[datetime] = Query(None),
    db_session: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("model:read"))
) -> dict:
    """
    Preview which model would be selected for a given context.
    
    Useful for testing activation rules before running assessments.
    """
    selector = ModelSelector(db_session)
    selection_context = ModelSelectionContext(
        tenant_id=context.tenant_id,
        corridor_id=corridor_id,
        product_id=product_id,
        carrier_id=carrier_id,
        as_of=as_of
    )
    
    try:
        result = selector.select(selection_context)
        return {
            "model_version_id": result.model_version_id,
            "model_name": result.model_version.name,
            "model_version": result.model_version.version,
            "immutable_hash": result.immutable_hash,
            "selection_reason": result.selection_reason,
            "activation_id": str(result.activation.id) if result.activation else None
        }
    except Exception as e:
        return {
            "error": str(e),
            "model_version_id": None
        }
