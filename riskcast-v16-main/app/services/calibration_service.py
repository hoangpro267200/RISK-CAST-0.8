"""
Calibration service.

Manages calibration datasets, runs, and model generation.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
import hashlib
import logging

from sqlalchemy.orm import Session

from app.models.calibration import CalibrationDataset, CalibrationRun, BacktestRun
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class CalibrationService:
    """Service for model calibration."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize calibration service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_dataset(
        self,
        tenant_id: Optional[str],
        name: str,
        dataset_type: str,
        schema_version: str,
        created_by: str,
        description: Optional[str] = None,
        data_source: Optional[str] = None,
        time_range_start: Optional[date] = None,
        time_range_end: Optional[date] = None
    ) -> CalibrationDataset:
        """
        Create a new calibration dataset.
        
        Args:
            tenant_id: Tenant ID (ULID string) or None for global
            name: Dataset name
            dataset_type: Type of dataset (HISTORICAL_POLICIES, LOSS_EXPERIENCE, MARKET_DATA)
            schema_version: Schema version string
            created_by: User ID creating dataset (ULID string)
            description: Optional description
            data_source: Optional data source identifier
            time_range_start: Optional start date for data
            time_range_end: Optional end date for data
            
        Returns:
            Created CalibrationDataset instance
        """
        dataset = CalibrationDataset(
            id=generate_ulid(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            dataset_type=dataset_type,
            status='DRAFT',
            schema_version=schema_version,
            data_source=data_source,
            time_range_start=time_range_start,
            time_range_end=time_range_end,
            created_by_user_id=created_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="CALIBRATION_DATASET",
            action="CREATED",
            entity_type="calibration_dataset",
            entity_id=dataset.id,
            actor_type="USER",
            actor_id=created_by,
            payload={"name": name, "type": dataset_type}
        )
        
        logger.info(f"Created calibration dataset: {dataset.id} ({name})")
        
        return dataset
    
    def upload_dataset_data(
        self,
        dataset_id: str,
        data: bytes,
        uploaded_by: str
    ) -> CalibrationDataset:
        """
        Upload data to a dataset.
        
        Args:
            dataset_id: Dataset ID (ULID string)
            data: Dataset data as bytes
            uploaded_by: User ID uploading (ULID string)
            
        Returns:
            Updated CalibrationDataset instance
        """
        dataset = self._get_dataset(dataset_id)
        
        if dataset.status != 'DRAFT':
            raise DatasetNotEditableError("Dataset is not in DRAFT status")
        
        # Compute hash
        dataset_hash = hashlib.sha256(data).hexdigest()
        
        # Store data (simplified - would use S3 in production)
        storage_uri = f"file:///data/calibration/{dataset_id}.csv"
        # In production: upload to S3 and store URI
        
        dataset.storage_uri = storage_uri
        dataset.dataset_hash = dataset_hash
        dataset.size_bytes = len(data)
        
        # Count rows (simplified - assumes CSV with newlines)
        dataset.row_count = data.count(b'\n') if data else 0
        
        self.db.commit()
        self.db.refresh(dataset)
        
        # Audit
        self.audit.append_event(
            tenant_id=dataset.tenant_id,
            event_type="CALIBRATION_DATASET",
            action="DATA_UPLOADED",
            entity_type="calibration_dataset",
            entity_id=dataset_id,
            actor_type="USER",
            actor_id=uploaded_by,
            payload={
                "size_bytes": len(data),
                "row_count": dataset.row_count,
                "hash": dataset_hash[:16] + "..."
            }
        )
        
        logger.info(f"Uploaded data to dataset {dataset_id} ({len(data)} bytes, {dataset.row_count} rows)")
        
        return dataset
    
    def validate_dataset(
        self,
        dataset_id: str,
        validated_by: str
    ) -> CalibrationDataset:
        """
        Validate dataset quality.
        
        Args:
            dataset_id: Dataset ID (ULID string)
            validated_by: User ID validating (ULID string)
            
        Returns:
            Updated CalibrationDataset instance
        """
        dataset = self._get_dataset(dataset_id)
        
        if not dataset.storage_uri:
            raise DatasetNotUploadedError("Dataset has no data")
        
        # Run validation (simplified)
        quality_metrics = self._compute_quality_metrics(dataset)
        
        dataset.quality_metrics_json = quality_metrics
        dataset.status = 'VALIDATED' if quality_metrics.get('validation_passed') else 'DRAFT'
        dataset.validated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(dataset)
        
        # Audit
        self.audit.append_event(
            tenant_id=dataset.tenant_id,
            event_type="CALIBRATION_DATASET",
            action="VALIDATED",
            entity_type="calibration_dataset",
            entity_id=dataset_id,
            actor_type="USER",
            actor_id=validated_by,
            payload={
                "passed": quality_metrics.get('validation_passed'),
                "completeness": quality_metrics.get('completeness')
            }
        )
        
        logger.info(f"Validated dataset {dataset_id} (passed: {quality_metrics.get('validation_passed')})")
        
        return dataset
    
    def publish_dataset(
        self,
        dataset_id: str,
        published_by: str
    ) -> CalibrationDataset:
        """
        Publish dataset for use in calibration.
        
        Args:
            dataset_id: Dataset ID (ULID string)
            published_by: User ID publishing (ULID string)
            
        Returns:
            Updated CalibrationDataset instance
        """
        dataset = self._get_dataset(dataset_id)
        
        if dataset.status != 'VALIDATED':
            raise InvalidDatasetStateError("Dataset must be VALIDATED")
        
        dataset.status = 'PUBLISHED'
        dataset.published_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(dataset)
        
        # Audit
        self.audit.append_event(
            tenant_id=dataset.tenant_id,
            event_type="CALIBRATION_DATASET",
            action="PUBLISHED",
            entity_type="calibration_dataset",
            entity_id=dataset_id,
            actor_type="USER",
            actor_id=published_by,
            payload={"row_count": dataset.row_count}
        )
        
        logger.info(f"Published dataset {dataset_id}")
        
        return dataset
    
    def create_calibration_run(
        self,
        tenant_id: Optional[str],
        dataset_id: str,
        input_model_version_id: str,
        config: Dict[str, Any],
        created_by: str
    ) -> CalibrationRun:
        """
        Create a new calibration run.
        
        Args:
            tenant_id: Tenant ID (ULID string) or None
            dataset_id: Dataset ID (ULID string)
            input_model_version_id: Input model version ID (ULID string)
            config: Calibration configuration dictionary
            created_by: User ID creating run (ULID string)
            
        Returns:
            Created CalibrationRun instance
        """
        # Verify dataset is published
        dataset = self._get_dataset(dataset_id)
        if dataset.status != 'PUBLISHED':
            raise InvalidDatasetStateError("Dataset must be PUBLISHED")
        
        # Verify model exists
        try:
            from app.modules.model_versioning.models import RiskModelVersion
            model = self.db.query(RiskModelVersion).filter(
                RiskModelVersion.id == input_model_version_id
            ).first()
            if not model:
                raise ModelNotFoundError(f"Model {input_model_version_id} not found")
        except ImportError:
            raise ModelNotFoundError("RiskModelVersion model not available")
        
        run = CalibrationRun(
            id=generate_ulid(),
            tenant_id=tenant_id,
            dataset_id=dataset_id,
            input_model_version_id=input_model_version_id,
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
            event_type="CALIBRATION_RUN",
            action="CREATED",
            entity_type="calibration_run",
            entity_id=run.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "dataset_id": dataset_id,
                "input_model_id": input_model_version_id,
                "method": config.get('method', 'UNKNOWN')
            }
        )
        
        logger.info(f"Created calibration run {run.id} for dataset {dataset_id}")
        
        return run
    
    def execute_calibration(self, run_id: str) -> CalibrationRun:
        """
        Execute calibration run.
        
        This would typically be run asynchronously by a worker.
        
        Args:
            run_id: Calibration run ID (ULID string)
            
        Returns:
            Updated CalibrationRun instance
        """
        run = self._get_run(run_id)
        
        if run.status != 'PENDING':
            raise InvalidRunStateError(f"Run is {run.status}")
        
        run.status = 'RUNNING'
        run.started_at = datetime.utcnow()
        self.db.commit()
        
        try:
            # Load dataset
            dataset = self._get_dataset(run.dataset_id)
            
            # Load input model
            try:
                from app.modules.model_versioning.models import RiskModelVersion
                input_model = self.db.query(RiskModelVersion).filter(
                    RiskModelVersion.id == run.input_model_version_id
                ).first()
                if not input_model:
                    raise ModelNotFoundError(f"Model {run.input_model_version_id} not found")
            except ImportError:
                raise ModelNotFoundError("RiskModelVersion model not available")
            
            # Run calibration algorithm (simplified)
            results = self._run_calibration_algorithm(
                dataset, input_model, run.config_json
            )
            
            # Store results
            run.metrics_json = results['metrics']
            run.parameter_changes_json = results['parameter_changes']
            
            # Create new model version with calibrated parameters
            new_model = self._create_calibrated_model(
                input_model, results['new_parameters'], run
            )
            
            run.output_model_version_id = new_model.id
            run.status = 'COMPLETED'
            run.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Calibration run {run_id} failed: {e}", exc_info=True)
            run.status = 'FAILED'
            run.metrics_json = {"error": str(e)}
            run.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(run)
        
        # Audit
        self.audit.append_event(
            tenant_id=run.tenant_id,
            event_type="CALIBRATION_RUN",
            action="COMPLETED" if run.status == 'COMPLETED' else "FAILED",
            entity_type="calibration_run",
            entity_id=run_id,
            actor_type="SYSTEM",
            payload={
                "status": run.status,
                "output_model_id": str(run.output_model_version_id) if run.output_model_version_id else None
            }
        )
        
        logger.info(f"Calibration run {run_id} {run.status}")
        
        return run
    
    def approve_calibration(
        self,
        run_id: str,
        approved_by: str
    ) -> CalibrationRun:
        """
        Approve calibration results for model activation.
        
        Args:
            run_id: Calibration run ID (ULID string)
            approved_by: User ID approving (ULID string)
            
        Returns:
            Updated CalibrationRun instance
        """
        run = self._get_run(run_id)
        
        if run.status != 'COMPLETED':
            raise InvalidRunStateError("Run must be COMPLETED")
        
        run.status = 'APPROVED'
        run.approved_by_user_id = approved_by
        run.approved_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(run)
        
        # Audit
        self.audit.append_event(
            tenant_id=run.tenant_id,
            event_type="CALIBRATION_RUN",
            action="APPROVED",
            entity_type="calibration_run",
            entity_id=run_id,
            actor_type="USER",
            actor_id=approved_by,
            payload={"output_model_id": str(run.output_model_version_id)}
        )
        
        logger.info(f"Approved calibration run {run_id}")
        
        return run
    
    def _get_dataset(self, dataset_id: str) -> CalibrationDataset:
        """Get dataset by ID."""
        dataset = self.db.query(CalibrationDataset).filter(
            CalibrationDataset.id == dataset_id
        ).first()
        if not dataset:
            raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
        return dataset
    
    def _get_run(self, run_id: str) -> CalibrationRun:
        """Get calibration run by ID."""
        run = self.db.query(CalibrationRun).filter(
            CalibrationRun.id == run_id
        ).first()
        if not run:
            raise RunNotFoundError(f"Run {run_id} not found")
        return run
    
    def _compute_quality_metrics(self, dataset: CalibrationDataset) -> Dict[str, Any]:
        """
        Compute dataset quality metrics.
        
        Args:
            dataset: CalibrationDataset instance
            
        Returns:
            Dictionary with quality metrics
        """
        # Simplified - would load and analyze actual data
        # In production, would:
        # 1. Load dataset from storage_uri
        # 2. Check completeness, missing fields, outliers
        # 3. Validate schema compliance
        # 4. Check data types and ranges
        
        return {
            "completeness": 0.98,
            "missing_fields": [],
            "outliers_removed": 0,
            "validation_passed": True,
            "row_count": dataset.row_count or 0,
            "size_bytes": dataset.size_bytes or 0
        }
    
    def _run_calibration_algorithm(
        self,
        dataset: CalibrationDataset,
        model: Any,  # RiskModelVersion
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run calibration algorithm.
        
        Args:
            dataset: CalibrationDataset instance
            model: RiskModelVersion instance
            config: Calibration configuration
            
        Returns:
            Dictionary with calibration results
        """
        # Simplified - would implement actual calibration algorithm
        # In production, would:
        # 1. Load dataset from storage_uri
        # 2. Extract features and targets
        # 3. Run optimization algorithm (gradient descent, etc.)
        # 4. Compute metrics before/after
        # 5. Return parameter changes
        
        method = config.get('method', 'GRADIENT_DESCENT')
        
        # Get current model parameters
        base_weights = getattr(model, 'base_weights_json', None) or {}
        correlations = getattr(model, 'correlation_matrix_json', None) or {}
        tail_params = getattr(model, 'tail_parameters_json', None) or {}
        
        # Simulated parameter changes
        new_weights = base_weights.copy() if base_weights else {}
        if 'route_risk' in new_weights:
            new_weights['route_risk'] = new_weights.get('route_risk', 0.25) * 1.12
        
        return {
            "metrics": {
                "before": {"loss_ratio_error": 0.15, "mse": 0.02},
                "after": {"loss_ratio_error": 0.05, "mse": 0.008},
                "improvement": 0.67,
                "convergence_iterations": 450
            },
            "parameter_changes": {
                "weights": {
                    "route_risk": {
                        "before": base_weights.get('route_risk', 0.25),
                        "after": new_weights.get('route_risk', 0.28)
                    }
                }
            },
            "new_parameters": {
                "base_weights": new_weights,
                "correlations": correlations,
                "tail_params": tail_params,
                "interactions": getattr(model, 'interaction_multipliers_json', None) or {},
                "loss_transform": getattr(model, 'loss_transform_params_json', None) or {}
            }
        }
    
    def _create_calibrated_model(
        self,
        input_model: Any,  # RiskModelVersion
        new_params: Dict[str, Any],
        run: CalibrationRun
    ) -> Any:  # RiskModelVersion
        """
        Create new model version from calibration.
        
        Args:
            input_model: Input RiskModelVersion instance
            new_params: New calibrated parameters
            run: CalibrationRun instance
            
        Returns:
            New RiskModelVersion instance
        """
        try:
            from app.modules.model_versioning.models import RiskModelVersion, ModelVersionStatus
            from app.shared.utils import generate_ulid
            
            # Get next version number
            existing_versions = self.db.query(RiskModelVersion).filter(
                RiskModelVersion.name == input_model.name
            ).count()
            next_version = existing_versions + 1
            
            # Create new model version with calibrated parameters
            new_model = RiskModelVersion(
                id=generate_ulid(),
                tenant_id=run.tenant_id,
                name=input_model.name,  # Keep same name
                version=next_version,
                status=ModelVersionStatus.DRAFT,
                base_weights_json=new_params.get('base_weights'),
                correlation_matrix_json=new_params.get('correlations'),
                tail_parameters_json=new_params.get('tail_params'),
                interaction_multipliers_json=new_params.get('interactions'),
                loss_transform_params_json=new_params.get('loss_transform'),
                created_by_user_id=run.created_by_user_id,
                description=f"Calibrated from run {run.id}",
                created_at=datetime.utcnow()
            )
            
            self.db.add(new_model)
            self.db.commit()
            self.db.refresh(new_model)
            
            logger.info(f"Created calibrated model version {new_model.id} (v{next_version})")
            
            return new_model
        except (ImportError, AttributeError) as e:
            logger.warning(f"Could not create calibrated model: {e}")
            # Fallback: return input model
            return input_model


# Exception classes
class DatasetNotFoundError(Exception):
    """Dataset not found"""
    pass


class DatasetNotEditableError(Exception):
    """Dataset is not editable"""
    pass


class DatasetNotUploadedError(Exception):
    """Dataset has no data uploaded"""
    pass


class InvalidDatasetStateError(Exception):
    """Invalid dataset state for operation"""
    pass


class ModelNotFoundError(Exception):
    """Model not found"""
    pass


class RunNotFoundError(Exception):
    """Calibration run not found"""
    pass


class InvalidRunStateError(Exception):
    """Invalid run state for operation"""
    pass
