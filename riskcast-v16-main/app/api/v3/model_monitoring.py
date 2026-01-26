"""
Model Monitoring API Endpoints
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.dependencies.auth import require_admin
from app.ml.monitoring import DriftDetector, PerformanceTracker, ModelRegistry
from app.ml.monitoring.drift_detector import DriftSeverity
from app.database import get_db, Session
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/model-monitoring", tags=["Model Monitoring"])


# Response Models
class DriftReportResponse(BaseModel):
    report_id: str
    model_name: str
    model_version: str
    drift_detected: bool
    overall_severity: str
    drift_types_detected: List[str]
    drifted_features: List[str]
    prediction_drift_score: float
    recommendations: List[str]
    generated_at: str


class PerformanceSnapshotResponse(BaseModel):
    model_name: str
    total_predictions: int
    avg_latency_ms: float
    p95_latency_ms: float
    predictions_per_second: float
    mae: Optional[float]
    error_rate: float


class ModelInfoResponse(BaseModel):
    model_name: str
    model_version: str
    status: str
    trained_at: str
    deployed_at: Optional[str]
    drift_score: Optional[float]


# Singleton trackers
_drift_detectors: dict = {}
_performance_trackers: dict = {}


def get_drift_detector(model_name: str, model_version: str = "v1") -> DriftDetector:
    key = f"{model_name}:{model_version}"
    if key not in _drift_detectors:
        _drift_detectors[key] = DriftDetector(model_name, model_version)
    return _drift_detectors[key]


def get_performance_tracker(model_name: str, model_version: str = "v1") -> PerformanceTracker:
    key = f"{model_name}:{model_version}"
    if key not in _performance_trackers:
        _performance_trackers[key] = PerformanceTracker(model_name, model_version)
    return _performance_trackers[key]


# Endpoints
@router.post("/drift/detect/{model_name}", response_model=DriftReportResponse)
async def detect_drift(
    model_name: str,
    model_version: str = Query("v1"),
    current_user = Depends(get_current_user)
):
    """
    Run drift detection for a model.
    """
    detector = get_drift_detector(model_name, model_version)
    
    if detector.current_window.size() < 100:
        raise HTTPException(
            400,
            f"Insufficient data for drift detection. Need at least 100 samples, have {detector.current_window.size()}"
        )
    
    report = await detector.detect_drift()
    
    return DriftReportResponse(
        report_id=report.report_id,
        model_name=report.model_name,
        model_version=report.model_version,
        drift_detected=report.drift_detected,
        overall_severity=report.overall_severity.value,
        drift_types_detected=[d.value for d in report.drift_types_detected],
        drifted_features=report.drifted_features,
        prediction_drift_score=report.prediction_drift_score,
        recommendations=report.recommendations,
        generated_at=report.generated_at.isoformat()
    )


@router.get("/performance/{model_name}", response_model=PerformanceSnapshotResponse)
async def get_performance(
    model_name: str,
    model_version: str = Query("v1"),
    current_user = Depends(get_current_user)
):
    """
    Get current performance metrics for a model.
    """
    tracker = get_performance_tracker(model_name, model_version)
    snapshot = tracker.get_current_snapshot()
    
    return PerformanceSnapshotResponse(
        model_name=snapshot.model_name,
        total_predictions=snapshot.total_predictions,
        avg_latency_ms=snapshot.avg_latency_ms,
        p95_latency_ms=snapshot.p95_latency_ms,
        predictions_per_second=snapshot.predictions_per_second,
        mae=snapshot.mae,
        error_rate=snapshot.error_rate
    )


@router.post("/record-prediction/{model_name}")
async def record_prediction(
    model_name: str,
    prediction: float,
    latency_ms: float,
    features: dict,
    actual: Optional[float] = None,
    model_version: str = Query("v1"),
    current_user = Depends(get_current_user)
):
    """
    Record a prediction for monitoring.
    """
    # Record for drift detection
    detector = get_drift_detector(model_name, model_version)
    detector.record_prediction(features, prediction, actual)
    
    # Record for performance tracking
    tracker = get_performance_tracker(model_name, model_version)
    tracker.record_prediction(prediction, latency_ms, actual)
    
    return {"status": "recorded"}


@router.get("/models", response_model=List[ModelInfoResponse])
async def list_models(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List all registered models.
    """
    registry = ModelRegistry(session=db)
    
    status_enum = None
    if status:
        from app.ml.monitoring.model_registry import ModelStatus
        try:
            status_enum = ModelStatus(status.upper())
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    
    models = registry.list_models(status=status_enum)
    
    return [
        ModelInfoResponse(
            model_name=m.model_name,
            model_version=m.model_version,
            status=m.status.value,
            trained_at=m.trained_at.isoformat(),
            deployed_at=m.deployed_at.isoformat() if m.deployed_at else None,
            drift_score=m.drift_score
        )
        for m in models
    ]


@router.post("/models/{model_name}/promote")
async def promote_model(
    model_name: str,
    version: str,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin)
):
    """
    Promote a model to production.
    """
    registry = ModelRegistry(session=db)
    
    try:
        registry.promote_to_production(
            model_name=model_name,
            version=version,
            deployed_by=str(current_user.id) if hasattr(current_user, 'id') else "system"
        )
        return {"status": "promoted", "model": model_name, "version": version}
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/drift/history/{model_name}")
async def get_drift_history(
    model_name: str,
    days: int = Query(30, ge=1, le=90),
    current_user = Depends(get_current_user)
):
    """
    Get drift detection history for a model.
    """
    # Would fetch from Redis/DB
    # For now, return empty list
    return {"model_name": model_name, "history": []}
