"""
Calibration API Endpoints

Endpoints for triggering, monitoring, and managing model calibration.
"""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import get_current_user, TenantContext, resolve_tenant_context
from app.modules.rbac_policy.service import require_permission
from app.modules.rbac_policy.constants import Permissions
from app.calibration.calibration_pipeline import (
    CalibrationPipeline,
    CalibrationConfig,
    CalibrationRunResult,
    CalibrationStatus,
    CalibrationStage
)
from app.calibration.weight_calibrator import CalibrationMethod, CalibrationObjective
from app.calibration.correlation_calibrator import CorrelationMethod
from app.calibration.loss_function_calibrator import LossFunctionType
from app.core.audit_ledger.ledger import AuditLedger
from app.modules.model_versioning.models import RiskModelVersion, ModelVersionStatus

router = APIRouter(prefix="/calibration", tags=["Calibration"])


# ============================================================================
# Schemas
# ============================================================================

class CalibrationRequest(BaseModel):
    """Request to start a calibration run."""
    start_date: date = Field(..., description="Start date for historical data")
    end_date: date = Field(..., description="End date for historical data")
    min_completeness: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum data completeness score"
    )
    
    # Method selection
    weight_method: str = Field(
        default="ENSEMBLE",
        description="Weight calibration method"
    )
    weight_objective: str = Field(
        default="BALANCED",
        description="Weight optimization objective"
    )
    correlation_method: str = Field(
        default="SHRINKAGE",
        description="Correlation calibration method"
    )
    loss_function_type: str = Field(
        default="POWER",
        description="Loss function type to calibrate"
    )
    
    # Validation
    min_improvement_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="Minimum required improvement"
    )
    
    # Output
    auto_publish: bool = Field(
        default=False,
        description="Auto-publish if validation passes"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Name for the calibrated model version"
    )
    
    # Filters
    cargo_type: Optional[str] = None
    origin_port: Optional[str] = None
    destination_port: Optional[str] = None


class CalibrationRunResponse(BaseModel):
    """Response for calibration run."""
    run_id: str
    status: str
    current_stage: str
    dataset_size: int
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    validation_passed: Optional[bool]
    output_model_version_id: Optional[str]
    error_count: int
    warning_count: int


class CalibrationRunDetailResponse(BaseModel):
    """Detailed response for calibration run."""
    run_id: str
    status: str
    current_stage: str
    
    # Config
    start_date: date
    end_date: date
    
    # Dataset
    dataset_size: int
    dataset_hash: str
    
    # Results summaries
    weight_calibration: Optional[dict]
    correlation_calibration: Optional[dict]
    loss_function_calibration: Optional[dict]
    
    # Validation
    validation_passed: bool
    validation_metrics: dict
    
    # Output
    output_model_version_id: Optional[str]
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Issues
    errors: List[dict]
    warnings: List[str]
    recommendations: List[str]


class CalibrationMethodsResponse(BaseModel):
    """Available calibration methods."""
    weight_methods: List[str]
    weight_objectives: List[str]
    correlation_methods: List[str]
    loss_function_types: List[str]


# ============================================================================
# Background task storage (in production, use Redis or database)
# ============================================================================
calibration_runs: dict = {}


# ============================================================================
# Helper Functions
# ============================================================================

def get_audit_ledger(db: Session = Depends(get_db)) -> AuditLedger:
    """Get audit ledger instance."""
    return AuditLedger(db)


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/methods", response_model=CalibrationMethodsResponse)
async def get_calibration_methods(
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """
    Get available calibration methods.
    
    Use these values in calibration requests.
    """
    return CalibrationMethodsResponse(
        weight_methods=[m.value for m in CalibrationMethod],
        weight_objectives=[o.value for o in CalibrationObjective],
        correlation_methods=[m.value for m in CorrelationMethod],
        loss_function_types=[t.value for t in LossFunctionType]
    )


@router.post("/runs", response_model=CalibrationRunResponse)
async def start_calibration_run(
    request: CalibrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    audit: AuditLedger = Depends(get_audit_ledger),
    context: TenantContext = Depends(require_permission(Permissions.RISK_WRITE))
):
    """
    Start a new calibration run.
    
    This triggers the full calibration pipeline in the background.
    Use GET /runs/{run_id} to monitor progress.
    """
    # Validate date range
    if request.end_date < request.start_date:
        raise HTTPException(400, "end_date must be after start_date")
    
    # Build config
    filters = {}
    if request.cargo_type:
        filters["cargo_type"] = request.cargo_type
    if request.origin_port:
        filters["origin_port"] = request.origin_port
    if request.destination_port:
        filters["destination_port"] = request.destination_port
    
    try:
        weight_method = CalibrationMethod(request.weight_method)
        weight_objective = CalibrationObjective(request.weight_objective)
        correlation_method = CorrelationMethod(request.correlation_method)
        loss_function_type = LossFunctionType(request.loss_function_type)
    except ValueError as e:
        raise HTTPException(400, f"Invalid method: {e}")
    
    config = CalibrationConfig(
        start_date=request.start_date,
        end_date=request.end_date,
        min_completeness=request.min_completeness,
        filters=filters if filters else None,
        weight_method=weight_method,
        weight_objective=weight_objective,
        correlation_method=correlation_method,
        loss_function_type=loss_function_type,
        min_improvement_threshold=request.min_improvement_threshold,
        auto_publish=request.auto_publish,
        model_name=request.model_name,
        tenant_id=context.tenant_id
    )
    
    # Create pipeline
    pipeline = CalibrationPipeline(db, audit)
    
    # Generate run ID early for response
    run_id = pipeline._generate_run_id()
    
    # Store initial state
    calibration_runs[run_id] = {
        "status": CalibrationStatus.PENDING.value,
        "stage": CalibrationStage.DATA_LOADING.value,
        "started_at": datetime.utcnow(),
        "result": None,
        "config": config
    }
    
    # Run calibration in background
    async def run_calibration():
        try:
            calibration_runs[run_id]["status"] = CalibrationStatus.RUNNING.value
            result = await pipeline.run(config)
            calibration_runs[run_id]["result"] = result
            calibration_runs[run_id]["status"] = result.status.value
            calibration_runs[run_id]["stage"] = result.current_stage.value
        except Exception as e:
            import traceback
            calibration_runs[run_id]["status"] = CalibrationStatus.FAILED.value
            calibration_runs[run_id]["error"] = str(e)
            calibration_runs[run_id]["traceback"] = traceback.format_exc()
    
    background_tasks.add_task(run_calibration)
    
    return CalibrationRunResponse(
        run_id=run_id,
        status=CalibrationStatus.PENDING.value,
        current_stage=CalibrationStage.DATA_LOADING.value,
        dataset_size=0,
        started_at=datetime.utcnow(),
        completed_at=None,
        duration_seconds=None,
        validation_passed=None,
        output_model_version_id=None,
        error_count=0,
        warning_count=0
    )


@router.get("/runs", response_model=List[CalibrationRunResponse])
async def list_calibration_runs(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100),
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """
    List calibration runs.
    """
    # In production, query from database
    # For now, return from in-memory storage
    runs = []
    
    for run_id, run_data in calibration_runs.items():
        if status and run_data.get("status") != status:
            continue
        
        result = run_data.get("result")
        
        runs.append(CalibrationRunResponse(
            run_id=run_id,
            status=run_data.get("status", "UNKNOWN"),
            current_stage=run_data.get("stage", "UNKNOWN"),
            dataset_size=result.dataset_size if result else 0,
            started_at=run_data.get("started_at"),
            completed_at=result.completed_at if result else None,
            duration_seconds=result.duration_seconds if result else None,
            validation_passed=result.validation_passed if result else None,
            output_model_version_id=result.output_model_version_id if result else None,
            error_count=len(result.errors) if result else 0,
            warning_count=len(result.warnings) if result else 0
        ))
    
    # Sort by started_at descending
    runs.sort(key=lambda x: x.started_at, reverse=True)
    
    return runs[:limit]


@router.get("/runs/{run_id}", response_model=CalibrationRunDetailResponse)
async def get_calibration_run(
    run_id: str,
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """
    Get detailed status of a calibration run.
    """
    if run_id not in calibration_runs:
        raise HTTPException(404, f"Calibration run {run_id} not found")
    
    run_data = calibration_runs[run_id]
    result = run_data.get("result")
    
    if not result:
        # Still running or failed early
        config = run_data.get("config")
        return CalibrationRunDetailResponse(
            run_id=run_id,
            status=run_data.get("status", "UNKNOWN"),
            current_stage=run_data.get("stage", "UNKNOWN"),
            start_date=config.start_date if config else date.today(),
            end_date=config.end_date if config else date.today(),
            dataset_size=0,
            dataset_hash="",
            weight_calibration=None,
            correlation_calibration=None,
            loss_function_calibration=None,
            validation_passed=False,
            validation_metrics={},
            output_model_version_id=None,
            started_at=run_data.get("started_at"),
            completed_at=None,
            duration_seconds=None,
            errors=[{"error": run_data.get("error")}] if run_data.get("error") else [],
            warnings=[],
            recommendations=[]
        )
    
    # Build response from result
    weight_summary = None
    if result.weight_result:
        weight_summary = {
            "method": result.weight_result.method.value,
            "before_mse": result.weight_result.before_mse,
            "after_mse": result.weight_result.after_mse,
            "improvement_pct": result.weight_result.mse_improvement_pct,
            "overfitting_risk": result.weight_result.overfitting_risk,
            "top_layers": [
                {"layer": l.layer_name, "weight": l.calibrated_weight, "change": l.weight_change}
                for l in sorted(
                    result.weight_result.layer_weights.values(),
                    key=lambda x: x.calibrated_weight,
                    reverse=True
                )[:5]
            ]
        }
    
    correlation_summary = None
    if result.correlation_result:
        correlation_summary = {
            "method": result.correlation_result.method.value,
            "is_positive_definite": result.correlation_result.is_positive_definite,
            "significant_changes": result.correlation_result.significant_changes,
            "temporal_stability": result.correlation_result.temporal_stability,
            "bootstrap_stability": result.correlation_result.bootstrap_stability
        }
    
    loss_summary = None
    if result.loss_function_result:
        loss_summary = {
            "function_type": result.loss_function_result.function_type.value,
            "formula": result.loss_function_result.function_formula,
            "before_r2": result.loss_function_result.before_r2,
            "after_r2": result.loss_function_result.after_r2,
            "improvement_pct": result.loss_function_result.r2_improvement_pct,
            "calibrated_exponent": result.loss_function_result.params.parameters.get("b")
        }
    
    return CalibrationRunDetailResponse(
        run_id=run_id,
        status=result.status.value,
        current_stage=result.current_stage.value,
        start_date=result.config.start_date,
        end_date=result.config.end_date,
        dataset_size=result.dataset_size,
        dataset_hash=result.dataset_hash,
        weight_calibration=weight_summary,
        correlation_calibration=correlation_summary,
        loss_function_calibration=loss_summary,
        validation_passed=result.validation_passed,
        validation_metrics=result.validation_metrics,
        output_model_version_id=result.output_model_version_id,
        started_at=result.started_at,
        completed_at=result.completed_at,
        duration_seconds=result.duration_seconds,
        errors=result.errors,
        warnings=result.warnings,
        recommendations=result.recommendations
    )


@router.post("/runs/{run_id}/publish")
async def publish_calibration_result(
    run_id: str,
    db: Session = Depends(get_db),
    audit: AuditLedger = Depends(get_audit_ledger),
    context: TenantContext = Depends(require_permission(Permissions.RISK_WRITE))
):
    """
    Publish the model version from a calibration run.
    
    Only works if calibration was successful and created a model version.
    """
    if run_id not in calibration_runs:
        raise HTTPException(404, f"Calibration run {run_id} not found")
    
    run_data = calibration_runs[run_id]
    result = run_data.get("result")
    
    if not result:
        raise HTTPException(400, "Calibration not complete")
    
    if result.status != CalibrationStatus.SUCCESS:
        raise HTTPException(400, f"Cannot publish: calibration status is {result.status.value}")
    
    if not result.output_model_version_id:
        raise HTTPException(400, "No model version created")
    
    # Publish the model version
    model = db.query(RiskModelVersion).filter(
        RiskModelVersion.id == result.output_model_version_id
    ).first()
    
    if not model:
        raise HTTPException(404, "Model version not found")
    
    if model.status == ModelVersionStatus.PUBLISHED:
        raise HTTPException(400, "Model already published")
    
    model.status = ModelVersionStatus.PUBLISHED
    model.published_at = datetime.utcnow()
    
    # Compute immutable hash if not already set
    if not model.immutable_hash:
        from app.calibration.calibration_pipeline import CalibrationPipeline
        pipeline = CalibrationPipeline(db, audit)
        all_params = {
            "base_weights": model.base_weights_json or {},
            "correlation_matrix": model.correlation_matrix_json or {},
            "loss_transform_params": model.loss_transform_params_json or {},
        }
        model.immutable_hash = pipeline._compute_model_hash(all_params)
    
    db.commit()
    
    # Audit
    if audit:
        try:
            tenant_id = context.tenant_id or "system"
            audit.append_event(
                tenant_id=tenant_id,
                event_type="MODEL_CALIBRATION",
                action="CALIBRATED_MODEL_PUBLISHED",
                entity_type="model_version",
                entity_id=str(model.id),
                actor_type="USER",
                actor_id=context.user_id or "system",
                payload={
                    "calibration_run_id": run_id,
                    "model_name": model.name,
                    "version": model.version
                }
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to audit model publish: {e}")
    
    return {
        "status": "published",
        "model_version_id": str(model.id),
        "model_name": model.name,
        "version": model.version
    }


@router.get("/data-summary")
async def get_calibration_data_summary(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db),
    context: TenantContext = Depends(require_permission(Permissions.RISK_READ))
):
    """
    Get summary of available calibration data.
    
    Use this to understand data availability before starting calibration.
    """
    from app.data.historical.loss_data_repository import HistoricalLossDataRepository, HistoricalShipment
    
    if end_date < start_date:
        raise HTTPException(400, "end_date must be after start_date")
    
    audit = AuditLedger(db)
    repo = HistoricalLossDataRepository(db, audit)
    
    # Query basic stats
    query = db.query(HistoricalShipment).filter(
        HistoricalShipment.shipment_date >= start_date,
        HistoricalShipment.shipment_date <= end_date
    )
    
    total = query.count()
    
    loss_query = query.filter(HistoricalShipment.loss_occurred == True)
    loss_count = loss_query.count()
    
    # Completeness distribution
    high_completeness = query.filter(
        HistoricalShipment.data_completeness_score >= 0.8
    ).count()
    
    medium_completeness = query.filter(
        HistoricalShipment.data_completeness_score >= 0.5,
        HistoricalShipment.data_completeness_score < 0.8
    ).count()
    
    low_completeness = query.filter(
        HistoricalShipment.data_completeness_score < 0.5
    ).count()
    
    return {
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "total_shipments": total,
        "shipments_with_loss": loss_count,
        "loss_rate": loss_count / total if total > 0 else 0,
        "completeness_distribution": {
            "high": high_completeness,
            "medium": medium_completeness,
            "low": low_completeness
        },
        "recommendations": {
            "sufficient_data": total >= 100,
            "sufficient_losses": loss_count >= 20,
            "message": (
                "Sufficient data for calibration" if total >= 100 and loss_count >= 20
                else f"Need more data: {total} shipments, {loss_count} losses. "
                     f"Recommend minimum 100 shipments and 20 loss events."
            )
        }
    }
