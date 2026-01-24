"""
Calibration Pipeline

Orchestrates the full calibration cycle:
1. Load historical data
2. Calibrate weights
3. Calibrate correlations
4. Calibrate loss function
5. Validate results
6. Package for deployment

This is the entry point for model calibration.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from enum import Enum
import asyncio
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from app.data.historical.loss_data_repository import (
    HistoricalLossDataRepository,
    CalibrationDataset
)
from app.calibration.weight_calibrator import (
    WeightCalibrator,
    CalibrationMethod,
    CalibrationObjective,
    CalibrationResult
)
from app.calibration.correlation_calibrator import (
    CorrelationCalibrator,
    CorrelationMethod,
    CorrelationMatrixResult
)
from app.calibration.loss_function_calibrator import (
    LossFunctionCalibrator,
    LossFunctionType,
    LossFunctionResult
)
from app.core.audit_ledger.ledger import AuditLedger
from app.modules.model_versioning.models import (
    RiskModelVersion,
    ModelVersionStatus,
    ModelScope
)

logger = logging.getLogger(__name__)


class CalibrationStage(Enum):
    """Stages of calibration pipeline."""
    DATA_LOADING = "DATA_LOADING"
    WEIGHT_CALIBRATION = "WEIGHT_CALIBRATION"
    CORRELATION_CALIBRATION = "CORRELATION_CALIBRATION"
    LOSS_FUNCTION_CALIBRATION = "LOSS_FUNCTION_CALIBRATION"
    VALIDATION = "VALIDATION"
    PACKAGING = "PACKAGING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class CalibrationStatus(Enum):
    """Status of calibration run."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


@dataclass
class CalibrationConfig:
    """Configuration for calibration run."""
    # Data selection
    start_date: date
    end_date: date
    min_completeness: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    
    # Method selection
    weight_method: CalibrationMethod = CalibrationMethod.ENSEMBLE
    weight_objective: CalibrationObjective = CalibrationObjective.BALANCED
    correlation_method: CorrelationMethod = CorrelationMethod.SHRINKAGE
    loss_function_type: LossFunctionType = LossFunctionType.POWER
    
    # Validation
    validation_split: float = 0.2
    min_improvement_threshold: float = 0.05  # 5% minimum improvement
    
    # Output
    auto_publish: bool = False
    model_name: Optional[str] = None
    tenant_id: Optional[str] = None  # For tenant-specific models
    scope: ModelScope = ModelScope.GLOBAL


@dataclass
class CalibrationRunResult:
    """Complete result of calibration run."""
    run_id: str
    config: CalibrationConfig
    status: CalibrationStatus
    current_stage: CalibrationStage
    
    # Dataset info
    dataset_size: int
    dataset_hash: str
    
    # Individual results
    weight_result: Optional[CalibrationResult]
    correlation_result: Optional[CorrelationMatrixResult]
    loss_function_result: Optional[LossFunctionResult]
    
    # Validation results
    validation_passed: bool
    validation_metrics: Dict[str, Any]
    
    # Output model
    output_model_version_id: Optional[str]
    
    # Timing
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    
    # Errors
    errors: List[Dict[str, Any]]
    warnings: List[str]
    
    # Recommendations
    recommendations: List[str]


class CalibrationPipeline:
    """
    Orchestrates the full calibration pipeline.
    
    Usage:
        pipeline = CalibrationPipeline(db, audit)
        result = await pipeline.run(config)
        
        if result.status == CalibrationStatus.SUCCESS:
            # New model version is ready
            print(f"Model version: {result.output_model_version_id}")
    """
    
    def __init__(self, db: Session, audit: AuditLedger):
        self.db = db
        self.audit = audit
        self.logger = logging.getLogger(__name__)
        
        # Initialize calibrators
        self.data_repo = HistoricalLossDataRepository(db, audit)
        self.weight_calibrator = WeightCalibrator(audit)
        self.correlation_calibrator = CorrelationCalibrator(audit)
        self.loss_function_calibrator = LossFunctionCalibrator(audit)
    
    async def run(self, config: CalibrationConfig) -> CalibrationRunResult:
        """
        Run the full calibration pipeline.
        """
        run_id = self._generate_run_id()
        started_at = datetime.utcnow()
        
        self.logger.info(f"Starting calibration run {run_id}")
        
        result = CalibrationRunResult(
            run_id=run_id,
            config=config,
            status=CalibrationStatus.RUNNING,
            current_stage=CalibrationStage.DATA_LOADING,
            dataset_size=0,
            dataset_hash="",
            weight_result=None,
            correlation_result=None,
            loss_function_result=None,
            validation_passed=False,
            validation_metrics={},
            output_model_version_id=None,
            started_at=started_at,
            completed_at=None,
            duration_seconds=None,
            errors=[],
            warnings=[],
            recommendations=[]
        )
        
        try:
            # Stage 1: Load data
            result.current_stage = CalibrationStage.DATA_LOADING
            dataset = await self._load_data(config, result)
            
            # Stage 2: Calibrate weights
            result.current_stage = CalibrationStage.WEIGHT_CALIBRATION
            weight_result = await self._calibrate_weights(dataset, config, result)
            result.weight_result = weight_result
            
            # Stage 3: Calibrate correlations
            result.current_stage = CalibrationStage.CORRELATION_CALIBRATION
            correlation_result = await self._calibrate_correlations(dataset, config, result)
            result.correlation_result = correlation_result
            
            # Stage 4: Calibrate loss function
            result.current_stage = CalibrationStage.LOSS_FUNCTION_CALIBRATION
            loss_result = await self._calibrate_loss_function(dataset, config, result)
            result.loss_function_result = loss_result
            
            # Stage 5: Validation
            result.current_stage = CalibrationStage.VALIDATION
            await self._validate(dataset, config, result)
            
            # Stage 6: Package model
            result.current_stage = CalibrationStage.PACKAGING
            await self._package_model(config, result)
            
            # Complete
            result.current_stage = CalibrationStage.COMPLETE
            result.status = CalibrationStatus.SUCCESS if result.validation_passed else CalibrationStatus.PARTIAL_SUCCESS
            
            # Compile recommendations
            result.recommendations = self._compile_recommendations(result)
            
        except Exception as e:
            result.current_stage = CalibrationStage.FAILED
            result.status = CalibrationStatus.FAILED
            result.errors.append({
                "stage": result.current_stage.value,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            self.logger.error(f"Calibration failed: {e}", exc_info=True)
        
        # Finalize
        result.completed_at = datetime.utcnow()
        result.duration_seconds = (result.completed_at - started_at).total_seconds()
        
        # Audit
        if self.audit:
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or config.tenant_id or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="MODEL_CALIBRATION",
                    action="CALIBRATION_RUN_COMPLETE",
                    entity_type="calibration_run",
                    entity_id=result.run_id,
                    actor_type="SYSTEM",
                    payload={
                        "status": result.status.value,
                        "duration_seconds": result.duration_seconds,
                        "dataset_size": result.dataset_size,
                        "validation_passed": result.validation_passed,
                        "output_model": result.output_model_version_id,
                        "error_count": len(result.errors)
                    }
                )
            except Exception as e:
                self.logger.warning(f"Failed to audit calibration run: {e}")
        
        return result
    
    async def _load_data(
        self,
        config: CalibrationConfig,
        result: CalibrationRunResult
    ) -> CalibrationDataset:
        """Load calibration dataset."""
        self.logger.info(
            f"Loading data from {config.start_date} to {config.end_date}"
        )
        
        dataset = await self.data_repo.get_calibration_dataset(
            start_date=config.start_date,
            end_date=config.end_date,
            min_completeness=config.min_completeness,
            filters=config.filters
        )
        
        result.dataset_size = dataset.total_shipments
        result.dataset_hash = dataset.dataset_hash
        
        self.logger.info(f"Loaded {dataset.total_shipments} shipments")
        
        # Check minimum data requirements
        if dataset.total_shipments < 100:
            result.warnings.append(
                f"Dataset has only {dataset.total_shipments} shipments. "
                f"Minimum recommended is 100 for reliable calibration."
            )
        
        if dataset.loss_rate < 0.01:
            result.warnings.append(
                f"Very low loss rate ({dataset.loss_rate:.2%}). "
                f"May not have enough loss events for accurate calibration."
            )
        
        return dataset
    
    async def _calibrate_weights(
        self,
        dataset: CalibrationDataset,
        config: CalibrationConfig,
        result: CalibrationRunResult
    ) -> CalibrationResult:
        """Calibrate risk layer weights."""
        self.logger.info("Calibrating weights...")
        
        weight_result = await self.weight_calibrator.calibrate(
            dataset=dataset,
            method=config.weight_method,
            objective=config.weight_objective
        )
        
        self.logger.info(
            f"Weight calibration complete. MSE improvement: "
            f"{weight_result.mse_improvement_pct:.1f}%"
        )
        
        # Add warnings
        result.warnings.extend(weight_result.recommendations)
        
        if weight_result.overfitting_risk == "HIGH":
            result.warnings.append(
                "High overfitting risk in weight calibration. "
                "Consider using more data or regularization."
            )
        
        return weight_result
    
    async def _calibrate_correlations(
        self,
        dataset: CalibrationDataset,
        config: CalibrationConfig,
        result: CalibrationRunResult
    ) -> CorrelationMatrixResult:
        """Calibrate correlation matrix."""
        self.logger.info("Calibrating correlation matrix...")
        
        corr_result = await self.correlation_calibrator.calibrate(
            dataset=dataset,
            method=config.correlation_method
        )
        
        self.logger.info(
            f"Correlation calibration complete. "
            f"{corr_result.significant_changes} significant changes."
        )
        
        # Add warnings
        result.warnings.extend(corr_result.warnings)
        
        return corr_result
    
    async def _calibrate_loss_function(
        self,
        dataset: CalibrationDataset,
        config: CalibrationConfig,
        result: CalibrationRunResult
    ) -> LossFunctionResult:
        """Calibrate loss function."""
        self.logger.info("Calibrating loss function...")
        
        loss_result = await self.loss_function_calibrator.calibrate(
            dataset=dataset,
            function_type=config.loss_function_type
        )
        
        self.logger.info(
            f"Loss function calibration complete. "
            f"R² improvement: {loss_result.r2_improvement_pct:.1f}%"
        )
        
        # Add warnings
        result.warnings.extend(loss_result.warnings)
        
        return loss_result
    
    async def _validate(
        self,
        dataset: CalibrationDataset,
        config: CalibrationConfig,
        result: CalibrationRunResult
    ) -> None:
        """Validate calibration results."""
        self.logger.info("Validating calibration...")
        
        validation_metrics = {}
        validation_passed = True
        
        # Check weight calibration improvement
        if result.weight_result:
            weight_improvement = result.weight_result.mse_improvement_pct / 100
            validation_metrics["weight_improvement"] = weight_improvement
            
            if weight_improvement < config.min_improvement_threshold:
                validation_passed = False
                result.warnings.append(
                    f"Weight calibration improvement ({weight_improvement:.1%}) "
                    f"below threshold ({config.min_improvement_threshold:.1%})"
                )
        
        # Check correlation stability
        if result.correlation_result:
            stability = result.correlation_result.bootstrap_stability
            validation_metrics["correlation_stability"] = stability
            
            if stability < 0.7:
                result.warnings.append(
                    f"Correlation stability is low ({stability:.2f}). "
                    f"Results may not be reliable."
                )
        
        # Check loss function fit
        if result.loss_function_result:
            r2 = result.loss_function_result.after_r2
            validation_metrics["loss_function_r2"] = r2
            
            if r2 < 0.3:
                validation_passed = False
                result.warnings.append(
                    f"Loss function R² is low ({r2:.2f}). "
                    f"Model may not predict losses accurately."
                )
        
        # Check for overfitting
        if result.weight_result:
            if result.weight_result.overfitting_risk == "HIGH":
                validation_passed = False
        
        result.validation_passed = validation_passed
        result.validation_metrics = validation_metrics
        
        self.logger.info(
            f"Validation {'passed' if validation_passed else 'failed'}"
        )
    
    async def _package_model(
        self,
        config: CalibrationConfig,
        result: CalibrationRunResult
    ) -> None:
        """Package calibrated parameters into a new model version."""
        self.logger.info("Packaging calibrated model...")
        
        # Build parameters JSON
        base_weights = {}
        correlation_matrix = {}
        loss_transform_params = {}
        
        # Add calibrated weights
        if result.weight_result:
            base_weights = {
                layer.layer_name: layer.calibrated_weight
                for layer in result.weight_result.layer_weights.values()
            }
        
        # Add calibrated correlations
        if result.correlation_result:
            corr_dict = self.correlation_calibrator.get_correlation_matrix_dict(
                result.correlation_result
            )
            # Convert to matrix format for storage
            correlation_matrix = {
                f"{k[0]}:{k[1]}": v for k, v in corr_dict.items()
            }
        
        # Add calibrated loss function
        if result.loss_function_result:
            # Store both the full structure and the engine-ready format
            loss_params = result.loss_function_result.params.parameters
            function_type = result.loss_function_result.function_type.value
            
            # Build engine-ready format
            if function_type == "POWER":
                # loss = a * (risk/10)^b
                loss_transform_params = {
                    "type": "POWER",
                    "parameters": loss_params,
                    "formula": result.loss_function_result.function_formula,
                    # Engine-ready format
                    "base_loss_rate": 0.0,
                    "risk_score_exponent": float(loss_params.get("b", 1.8)),
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 1.0,
                    "multiplier": float(loss_params.get("a", 1.0))
                }
            elif function_type == "EXPONENTIAL":
                # loss = a * exp(b * risk/10)
                loss_transform_params = {
                    "type": "EXPONENTIAL",
                    "parameters": loss_params,
                    "formula": result.loss_function_result.function_formula,
                    # Engine-ready format
                    "base_loss_rate": float(loss_params.get("a", 0.01)),
                    "risk_score_exponent": float(loss_params.get("b", 3.0)),
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 1.0
                }
            elif function_type == "LOGISTIC":
                # loss = L / (1 + exp(-k * (risk/10 - x0)))
                loss_transform_params = {
                    "type": "LOGISTIC",
                    "parameters": loss_params,
                    "formula": result.loss_function_result.function_formula,
                    # Engine-ready format
                    "base_loss_rate": float(loss_params.get("L", 1.0)),
                    "risk_score_exponent": float(loss_params.get("k", 5.0)),
                    "min_loss_pct": 0.001,
                    "max_loss_pct": float(loss_params.get("L", 1.0)),
                    "inflection_point": float(loss_params.get("x0", 0.5))
                }
            else:
                # Default to power function format
                loss_transform_params = {
                    "type": function_type,
                    "parameters": loss_params,
                    "formula": result.loss_function_result.function_formula,
                    "base_loss_rate": 0.0,
                    "risk_score_exponent": 1.8,
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 1.0
                }
        
        # Create model version
        model_name = config.model_name or f"calibrated_{datetime.utcnow().strftime('%Y%m%d')}"
        version = self._get_next_version(config.tenant_id, model_name)
        
        # Build calibration JSON with metadata
        calibration_json = {
            "run_id": result.run_id,
            "dataset_hash": result.dataset_hash,
            "dataset_size": result.dataset_size,
            "calibrated_at": result.completed_at.isoformat() if result.completed_at else None,
            "validation_passed": result.validation_passed,
            "validation_metrics": result.validation_metrics,
            "weight_method": config.weight_method.value,
            "correlation_method": config.correlation_method.value,
            "loss_function_type": config.loss_function_type.value,
        }
        
        model_version = RiskModelVersion(
            tenant_id=config.tenant_id,
            scope=config.scope,
            name=model_name,
            status=ModelVersionStatus.DRAFT,
            model_schema_version="risk_model_v1.0",
            version=version,
            description=f"Calibrated model from run {result.run_id}",
            base_weights_json=base_weights if base_weights else None,
            correlation_matrix_json=correlation_matrix if correlation_matrix else None,
            loss_transform_params_json=loss_transform_params if loss_transform_params else None,
            calibration_json=calibration_json,
            calibration_run_id=result.run_id,
        )
        
        self.db.add(model_version)
        self.db.commit()
        self.db.refresh(model_version)
        
        result.output_model_version_id = str(model_version.id)
        
        # Auto-publish if configured and validation passed
        if config.auto_publish and result.validation_passed:
            model_version.status = ModelVersionStatus.PUBLISHED
            model_version.published_at = datetime.utcnow()
            
            # Compute immutable hash from all parameters
            all_params = {
                "base_weights": base_weights,
                "correlation_matrix": correlation_matrix,
                "loss_transform_params": loss_transform_params,
            }
            model_version.immutable_hash = self._compute_model_hash(all_params)
            
            self.db.commit()
            
            self.logger.info(f"Published model version {model_version.id}")
        
        self.logger.info(f"Created model version {model_version.id}")
    
    def _compile_recommendations(
        self,
        result: CalibrationRunResult
    ) -> List[str]:
        """Compile all recommendations."""
        recommendations = []
        
        # From weight calibration
        if result.weight_result:
            recommendations.extend(result.weight_result.recommendations)
        
        # General recommendations
        if result.dataset_size < 500:
            recommendations.append(
                "Consider collecting more historical data (500+ shipments "
                "recommended for robust calibration)."
            )
        
        if not result.validation_passed:
            recommendations.append(
                "Calibration validation failed. Review warnings and consider "
                "adjusting calibration parameters or collecting more data."
            )
        
        if result.status == CalibrationStatus.SUCCESS:
            recommendations.append(
                f"Calibration successful. New model version "
                f"({result.output_model_version_id}) is ready for testing."
            )
        
        return recommendations
    
    def _generate_run_id(self) -> str:
        """Generate unique run ID."""
        data = f"calibration:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _get_next_version(self, tenant_id: Optional[str], model_name: str) -> str:
        """Get next model version number."""
        query = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.name == model_name
        )
        
        if tenant_id:
            query = query.filter(RiskModelVersion.tenant_id == tenant_id)
        else:
            query = query.filter(RiskModelVersion.tenant_id.is_(None))
        
        latest = query.order_by(
            RiskModelVersion.created_at.desc()
        ).first()
        
        if latest and latest.version:
            try:
                parts = latest.version.split(".")
                if len(parts) >= 2:
                    major, minor = int(parts[0]), int(parts[1])
                    return f"{major}.{minor + 1}.0"
            except (ValueError, IndexError):
                pass
        
        return "1.0.0"
    
    def _compute_model_hash(self, parameters: Dict[str, Any]) -> str:
        """Compute hash of model parameters."""
        canonical = json.dumps(parameters, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()


def create_calibration_pipeline(db: Session, audit: AuditLedger) -> CalibrationPipeline:
    """Create calibration pipeline instance."""
    return CalibrationPipeline(db, audit)
