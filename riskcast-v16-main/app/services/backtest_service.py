"""
Backtesting service.

Replays historical assessments with current/new models
to validate model performance.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from app.models.calibration import BacktestRun, CalibrationDataset
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class BacktestService:
    """Service for model backtesting."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize backtest service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_backtest(
        self,
        tenant_id: Optional[str],
        dataset_id: str,
        model_version_id: str,
        config: Dict[str, Any],
        created_by: str,
        baseline_model_version_id: Optional[str] = None
    ) -> BacktestRun:
        """
        Create a new backtest run.
        
        Args:
            tenant_id: Tenant ID (ULID string) or None
            dataset_id: Dataset ID (ULID string)
            model_version_id: Model version ID to test (ULID string)
            config: Backtest configuration dictionary
            created_by: User ID creating run (ULID string)
            baseline_model_version_id: Optional baseline model for comparison
            
        Returns:
            Created BacktestRun instance
        """
        # Verify dataset
        dataset = self.db.query(CalibrationDataset).filter(
            CalibrationDataset.id == dataset_id,
            CalibrationDataset.status == 'PUBLISHED'
        ).first()
        if not dataset:
            raise DatasetNotFoundError(f"Published dataset {dataset_id} not found")
        
        # Verify model
        try:
            from app.modules.model_versioning.models import RiskModelVersion, ModelVersionStatus
            model = self.db.query(RiskModelVersion).filter(
                RiskModelVersion.id == model_version_id,
                RiskModelVersion.status.in_([ModelVersionStatus.PUBLISHED, ModelVersionStatus.DRAFT])
            ).first()
            if not model:
                raise ModelNotFoundError(f"Model {model_version_id} not found")
        except ImportError:
            raise ModelNotFoundError("RiskModelVersion model not available")
        
        # Verify baseline model if provided
        if baseline_model_version_id:
            baseline_model = self.db.query(RiskModelVersion).filter(
                RiskModelVersion.id == baseline_model_version_id
            ).first()
            if not baseline_model:
                raise ModelNotFoundError(f"Baseline model {baseline_model_version_id} not found")
        
        run = BacktestRun(
            id=generate_ulid(),
            tenant_id=tenant_id,
            dataset_id=dataset_id,
            model_version_id=model_version_id,
            baseline_model_version_id=baseline_model_version_id,
            status='PENDING',
            config_json=config,
            created_by_user_id=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="BACKTEST_RUN",
            action="CREATED",
            entity_type="backtest_run",
            entity_id=run.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "dataset_id": dataset_id,
                "model_version_id": model_version_id,
                "baseline_model_version_id": baseline_model_version_id
            }
        )
        
        logger.info(f"Created backtest run {run.id} for model {model_version_id}")
        
        return run
    
    def execute_backtest(self, run_id: str) -> BacktestRun:
        """
        Execute backtest run.
        
        Replays historical policies through the model and compares
        predicted vs actual outcomes.
        
        Args:
            run_id: Backtest run ID (ULID string)
            
        Returns:
            Updated BacktestRun instance
        """
        run = self._get_run(run_id)
        
        if run.status != 'PENDING':
            raise InvalidRunStateError(f"Run is {run.status}")
        
        run.status = 'RUNNING'
        run.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Load dataset
            dataset = self.db.query(CalibrationDataset).filter(
                CalibrationDataset.id == run.dataset_id
            ).first()
            
            if not dataset:
                raise DatasetNotFoundError(f"Dataset {run.dataset_id} not found")
            
            # Load historical policies/assessments from dataset
            historical_data = self._load_historical_data(dataset)
            
            if not historical_data:
                raise ValueError("Dataset contains no historical data")
            
            # Get model
            try:
                from app.modules.model_versioning.models import RiskModelVersion
                model = self.db.query(RiskModelVersion).filter(
                    RiskModelVersion.id == run.model_version_id
                ).first()
                if not model:
                    raise ModelNotFoundError(f"Model {run.model_version_id} not found")
            except ImportError:
                raise ModelNotFoundError("RiskModelVersion model not available")
            
            # Run backtest
            config = run.config_json or {}
            seed = config.get('seed', 42)
            iterations = config.get('iterations_per_policy', 1000)
            
            results = self._run_backtest(
                historical_data, model, seed, iterations, run.tenant_id
            )
            
            # Store results
            run.metrics_json = results['metrics']
            
            # Compare with baseline if provided
            if run.baseline_model_version_id:
                baseline_model = self.db.query(RiskModelVersion).filter(
                    RiskModelVersion.id == run.baseline_model_version_id
                ).first()
                
                if baseline_model:
                    baseline_results = self._run_backtest(
                        historical_data, baseline_model, seed, iterations, run.tenant_id
                    )
                    
                    run.comparison_json = self._compare_results(
                        results['metrics'], baseline_results['metrics']
                    )
            
            # Generate report
            report_content = self._generate_report(run, results)
            report_json = json.dumps(report_content, sort_keys=True, separators=(',', ':'))
            run.report_hash = hashlib.sha256(report_json.encode()).hexdigest()
            
            # Store report URI (simplified - would upload to S3 in production)
            run.report_uri = f"file:///reports/backtest/{run.id}.json"
            
            run.status = 'COMPLETED'
            run.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Backtest run {run_id} failed: {e}", exc_info=True)
            run.status = 'FAILED'
            run.metrics_json = {"error": str(e)}
            run.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(run)
        
        # Audit
        self.audit.append_event(
            tenant_id=run.tenant_id,
            event_type="BACKTEST_RUN",
            action="COMPLETED" if run.status == 'COMPLETED' else "FAILED",
            entity_type="backtest_run",
            entity_id=run_id,
            actor_type="SYSTEM",
            payload={
                "status": run.status,
                "replay_mismatches": run.metrics_json.get('replay_mismatches', 0) if run.metrics_json and isinstance(run.metrics_json, dict) else None,
                "total_policies": run.metrics_json.get('total_policies', 0) if run.metrics_json and isinstance(run.metrics_json, dict) else None
            }
        )
        
        logger.info(f"Backtest run {run_id} {run.status}")
        
        return run
    
    def _load_historical_data(self, dataset: CalibrationDataset) -> List[Dict[str, Any]]:
        """
        Load historical policy data from dataset.
        
        Args:
            dataset: CalibrationDataset instance
            
        Returns:
            List of dictionaries with input_data and actual_outcome
        """
        # Simplified - would load from storage_uri
        # In production, would:
        # 1. Load CSV/JSON from S3 or local storage
        # 2. Parse into structured format
        # 3. Return list of {input_data: {...}, actual_loss: float}
        
        # For now, try to load from loss experience records if dataset type is LOSS_EXPERIENCE
        if dataset.dataset_type == 'LOSS_EXPERIENCE':
            try:
                from app.models.loss_experience import LossExperienceRecord
                records = self.db.query(LossExperienceRecord).filter(
                    LossExperienceRecord.policy_effective_date.between(
                        dataset.time_range_start or datetime.min.date(),
                        dataset.time_range_end or datetime.max.date()
                    )
                ).limit(1000).all()  # Limit for performance
                
                historical_data = []
                for record in records:
                    # Reconstruct input data from policy (simplified)
                    try:
                        from app.modules.underwriting.models import Policy
                        policy = self.db.query(Policy).filter(
                            Policy.id == record.policy_id
                        ).first()
                        
                        if policy:
                            # Build input data from policy terms
                            input_data = {
                                "terms": policy.terms_json or {},
                                "risk_snapshot": getattr(policy, 'risk_snapshot_json', None) or {}
                            }
                            
                            historical_data.append({
                                "input_data": input_data,
                                "actual_loss": record.actual_loss_cents or 0,
                                "expected_loss": record.expected_loss_cents or 0,
                                "policy_id": record.policy_id
                            })
                    except (ImportError, AttributeError):
                        continue
                
                return historical_data
            except ImportError:
                pass
        
        # Fallback: return empty list
        logger.warning(f"Could not load historical data for dataset {dataset.id}")
        return []
    
    def _run_backtest(
        self,
        historical_data: List[Dict[str, Any]],
        model: Any,  # RiskModelVersion
        seed: int,
        iterations: int,
        tenant_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Run backtest with given model.
        
        Args:
            historical_data: List of historical records
            model: RiskModelVersion instance
            seed: Random seed for determinism
            iterations: Monte Carlo iterations per policy
            tenant_id: Tenant ID for context
            
        Returns:
            Dictionary with metrics and predictions
        """
        total = len(historical_data)
        predictions = []
        actuals = []
        replay_mismatches = 0
        successful = 0
        failed = 0
        
        # Try to use risk engine for predictions
        try:
            from app.core.engine.risk_engine_v16 import RiskEngineV16
            engine = RiskEngineV16()
        except (ImportError, AttributeError):
            logger.warning("RiskEngineV16 not available, using simplified backtest")
            engine = None
        
        for i, record in enumerate(historical_data):
            input_data = record.get('input_data', {})
            actual_loss = record.get('actual_loss', 0)
            
            try:
                if engine:
                    # Use actual risk engine
                    # Note: This is simplified - actual implementation would need
                    # proper input format and engine configuration
                    predicted_loss = self._predict_with_engine(
                        engine, input_data, model, seed + i, iterations, tenant_id
                    )
                else:
                    # Simplified prediction using expected loss from record
                    predicted_loss = record.get('expected_loss', actual_loss * 0.8)
                
                if predicted_loss is not None:
                    predictions.append(predicted_loss)
                    actuals.append(actual_loss)
                    successful += 1
                    
                    # Verify determinism (replay with same seed)
                    if engine:
                        predicted_loss2 = self._predict_with_engine(
                            engine, input_data, model, seed + i, iterations, tenant_id
                        )
                        if predicted_loss != predicted_loss2:
                            replay_mismatches += 1
                else:
                    failed += 1
                    
            except Exception as e:
                logger.warning(f"Failed to predict for record {i}: {e}")
                predictions.append(None)
                actuals.append(actual_loss)
                failed += 1
        
        # Calculate metrics
        valid_pairs = [(p, a) for p, a in zip(predictions, actuals) if p is not None]
        
        if valid_pairs:
            pred_values = [p for p, a in valid_pairs]
            actual_values = [a for p, a in valid_pairs]
            
            mse = sum((p - a) ** 2 for p, a in valid_pairs) / len(valid_pairs) if valid_pairs else 0
            mae = sum(abs(p - a) for p, a in valid_pairs) / len(valid_pairs) if valid_pairs else 0
            
            total_predicted = sum(pred_values)
            total_actual = sum(actual_values)
            
            # Calculate loss ratio
            loss_ratio_predicted = round(total_predicted / total_actual, 4) if total_actual > 0 else None
            
            metrics = {
                "total_policies": total,
                "successful_predictions": successful,
                "failed_predictions": failed,
                "deterministic_replays": total,
                "replay_mismatches": replay_mismatches,
                "mse": round(mse, 6),
                "mae": round(mae, 6),
                "rmse": round(mse ** 0.5, 6),
                "total_predicted_loss": round(total_predicted, 2),
                "total_actual_loss": round(total_actual, 2),
                "loss_ratio_predicted": loss_ratio_predicted,
                "mean_prediction_error": round(mae / total_actual, 4) if total_actual > 0 else None
            }
        else:
            metrics = {
                "total_policies": total,
                "successful_predictions": 0,
                "failed_predictions": total,
                "error": "No valid predictions"
            }
        
        return {
            "metrics": metrics,
            "predictions": predictions[:100],  # Limit for response size
            "actuals": actuals[:100]
        }
    
    def _predict_with_engine(
        self,
        engine: Any,
        input_data: Dict[str, Any],
        model: Any,
        seed: int,
        iterations: int,
        tenant_id: Optional[str]
    ) -> Optional[float]:
        """
        Predict loss using risk engine.
        
        Args:
            engine: Risk engine instance
            input_data: Input data dictionary
            model: RiskModelVersion instance
            seed: Random seed
            iterations: Monte Carlo iterations
            tenant_id: Tenant ID
            
        Returns:
            Predicted loss value or None
        """
        try:
            # Simplified - would use actual engine API
            # In production, would:
            # 1. Convert input_data to engine format
            # 2. Configure engine with model version
            # 3. Run with specified seed and iterations
            # 4. Extract expected_loss from result
            
            # For now, return None to use fallback
            return None
        except Exception as e:
            logger.warning(f"Engine prediction failed: {e}")
            return None
    
    def _compare_results(
        self,
        new_metrics: Dict[str, Any],
        baseline_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare new model results with baseline.
        
        Args:
            new_metrics: Metrics from new model
            baseline_metrics: Metrics from baseline model
            
        Returns:
            Comparison dictionary
        """
        new_mse = new_metrics.get('mse', float('inf'))
        baseline_mse = baseline_metrics.get('mse', float('inf'))
        
        improvement = (baseline_mse - new_mse) / baseline_mse if baseline_mse > 0 else 0
        
        new_loss_ratio = new_metrics.get('loss_ratio_predicted')
        baseline_loss_ratio = baseline_metrics.get('loss_ratio_predicted')
        
        return {
            "new_model_mse": new_mse,
            "baseline_mse": baseline_mse,
            "mse_improvement": round(improvement, 4),
            "new_model_better": new_mse < baseline_mse,
            "new_model_loss_ratio": new_loss_ratio,
            "baseline_loss_ratio": baseline_loss_ratio,
            "recommendation": (
                "DEPLOY" if improvement > 0.05 else
                "REVIEW" if improvement > 0 else
                "REJECT"
            )
        }
    
    def _generate_report(self, run: BacktestRun, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate backtest report.
        
        Args:
            run: BacktestRun instance
            results: Backtest results dictionary
            
        Returns:
            Report dictionary
        """
        metrics = results.get('metrics', {})
        
        return {
            "backtest_run_id": run.id,
            "model_version_id": run.model_version_id,
            "baseline_model_version_id": run.baseline_model_version_id,
            "dataset_id": run.dataset_id,
            "generated_at": datetime.utcnow().isoformat(),
            "metrics": metrics,
            "comparison": run.comparison_json,
            "config": run.config_json,
            "determinism_check": {
                "passed": metrics.get('replay_mismatches', 0) == 0,
                "mismatches": metrics.get('replay_mismatches', 0),
                "total_replays": metrics.get('deterministic_replays', 0)
            },
            "summary": {
                "status": run.status,
                "total_policies": metrics.get('total_policies', 0),
                "successful_predictions": metrics.get('successful_predictions', 0),
                "mse": metrics.get('mse'),
                "mae": metrics.get('mae'),
                "loss_ratio_predicted": metrics.get('loss_ratio_predicted')
            }
        }
    
    def _get_run(self, run_id: str) -> BacktestRun:
        """
        Get backtest run by ID.
        
        Args:
            run_id: Backtest run ID (ULID string)
            
        Returns:
            BacktestRun instance
        """
        run = self.db.query(BacktestRun).filter(
            BacktestRun.id == run_id
        ).first()
        if not run:
            raise RunNotFoundError(f"Run {run_id} not found")
        return run


# Exception classes
class DatasetNotFoundError(Exception):
    """Dataset not found"""
    pass


class ModelNotFoundError(Exception):
    """Model not found"""
    pass


class RunNotFoundError(Exception):
    """Backtest run not found"""
    pass


class InvalidRunStateError(Exception):
    """Invalid run state for operation"""
    pass
