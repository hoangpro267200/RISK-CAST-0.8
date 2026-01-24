"""
Model Version Service

Service for managing model versions, including creation from calibration runs.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from app.modules.model_versioning.models import (
    RiskModelVersion,
    RiskModelActivation,
    ModelVersionStatus,
    ActivationStatus,
)
from app.core.audit_ledger.ledger import AuditLedger
from app.calibration.calibration_pipeline import CalibrationRunResult
from app.shared.utils import generate_ulid

logger = __import__('logging').getLogger(__name__)


class ModelVersionService:
    """Service for managing model versions."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        self.db = db
        self.audit = audit
    
    async def create_from_calibration(
        self,
        calibration_result: CalibrationRunResult,
        name: str,
        version: str,
        tenant_id: Optional[str] = None,
        created_by_user_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> RiskModelVersion:
        """
        Create a new model version from calibration results.
        
        Args:
            calibration_result: Result from calibration pipeline
            name: Model name
            version: Semantic version (e.g., "1.0.0")
            tenant_id: Tenant ID (optional, for tenant-specific models)
            created_by_user_id: User ID who created the model
            description: Model description
            
        Returns:
            Created RiskModelVersion
        """
        # Build parameters from calibration
        base_weights = {}
        correlation_matrix = {}
        loss_transform_params = {}
        
        # Layer weights
        if calibration_result.weight_result:
            base_weights = {
                layer.layer_name: layer.calibrated_weight
                for layer in calibration_result.weight_result.layer_weights.values()
            }
        
        # Correlations
        if calibration_result.correlation_result:
            from app.calibration.correlation_calibrator import CorrelationCalibrator
            calibrator = CorrelationCalibrator(self.audit)
            corr_dict = calibrator.get_correlation_matrix_dict(
                calibration_result.correlation_result
            )
            # Store in "layer1:layer2" format
            correlation_matrix = {
                f"{k[0]}:{k[1]}": v for k, v in corr_dict.items()
            }
        
        # Loss function
        if calibration_result.loss_function_result:
            loss_params = calibration_result.loss_function_result.params.parameters
            function_type = calibration_result.loss_function_result.function_type.value
            
            # Build engine-ready format
            if function_type == "POWER":
                loss_transform_params = {
                    "type": "POWER",
                    "parameters": loss_params,
                    "formula": calibration_result.loss_function_result.function_formula,
                    "base_loss_rate": 0.0,
                    "risk_score_exponent": float(loss_params.get("b", 1.8)),
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 1.0,
                    "multiplier": float(loss_params.get("a", 1.0))
                }
            elif function_type == "EXPONENTIAL":
                loss_transform_params = {
                    "type": "EXPONENTIAL",
                    "parameters": loss_params,
                    "formula": calibration_result.loss_function_result.function_formula,
                    "base_loss_rate": float(loss_params.get("a", 0.01)),
                    "risk_score_exponent": float(loss_params.get("b", 3.0)),
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 1.0
                }
            elif function_type == "LOGISTIC":
                loss_transform_params = {
                    "type": "LOGISTIC",
                    "parameters": loss_params,
                    "formula": calibration_result.loss_function_result.function_formula,
                    "base_loss_rate": float(loss_params.get("L", 1.0)),
                    "risk_score_exponent": float(loss_params.get("k", 5.0)),
                    "min_loss_pct": 0.001,
                    "max_loss_pct": float(loss_params.get("L", 1.0)),
                    "inflection_point": float(loss_params.get("x0", 0.5))
                }
            else:
                loss_transform_params = {
                    "type": function_type,
                    "parameters": loss_params,
                    "formula": calibration_result.loss_function_result.function_formula,
                    "base_loss_rate": 0.0,
                    "risk_score_exponent": 1.8,
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 1.0
                }
        
        # Build calibration metadata
        calibration_json = {
            "run_id": calibration_result.run_id,
            "dataset_hash": calibration_result.dataset_hash,
            "dataset_size": calibration_result.dataset_size,
            "calibrated_at": calibration_result.completed_at.isoformat() if calibration_result.completed_at else None,
            "validation_passed": calibration_result.validation_passed,
            "validation_metrics": calibration_result.validation_metrics,
            "weight_method": calibration_result.config.weight_method.value if calibration_result.weight_result else None,
            "correlation_method": calibration_result.config.correlation_method.value if calibration_result.correlation_result else None,
            "loss_function_type": calibration_result.config.loss_function_type.value if calibration_result.loss_function_result else None,
        }
        
        # Create model version
        model = RiskModelVersion(
            id=generate_ulid(),
            tenant_id=tenant_id,
            scope="TENANT" if tenant_id else "GLOBAL",
            name=name,
            status=ModelVersionStatus.DRAFT,
            model_schema_version="risk_model_v1.0",
            version=version,
            description=description or f"Calibrated model from run {calibration_result.run_id}",
            base_weights_json=base_weights if base_weights else None,
            correlation_matrix_json=correlation_matrix if correlation_matrix else None,
            loss_transform_params_json=loss_transform_params if loss_transform_params else None,
            calibration_json=calibration_json,
            calibration_run_id=calibration_result.run_id,
            calibration_dataset_id=None,  # Can be set if dataset_id is available
            created_by_user_id=created_by_user_id
        )
        
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        
        # Audit
        if self.audit:
            try:
                tenant_id_audit = tenant_id or "system"
                self.audit.append_event(
                    tenant_id=tenant_id_audit,
                    event_type="MODEL_VERSION",
                    action="CREATED_FROM_CALIBRATION",
                    entity_type="model_version",
                    entity_id=model.id,
                    actor_type="SYSTEM",
                    payload={
                        "name": name,
                        "version": version,
                        "calibration_run_id": calibration_result.run_id,
                        "is_calibrated": True
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to audit model creation: {e}")
        
        return model

    async def create_draft_detailed(
        self,
        request: Any,
        user_id: Optional[str] = None,
        context: Optional[Any] = None,
    ) -> RiskModelVersion:
        """Create a new draft model version from detailed request."""
        from app.modules.model_versioning.models import ModelScope

        tenant_id = getattr(context, "tenant_id", None) if context else None
        base_weights = getattr(request, "base_weights", None)
        base_weights = _to_dict(base_weights)
        correlation_matrix = getattr(request, "correlation_matrix", None) or {}
        tail_params = _to_dict(getattr(request, "tail_parameters", None))
        interaction = getattr(request, "interaction_multipliers", None) or {}
        loss_params = _to_dict(getattr(request, "loss_transform_params", None))
        mc_defaults = _to_dict(getattr(request, "monte_carlo_defaults", None))

        model = RiskModelVersion(
            id=generate_ulid(),
            tenant_id=tenant_id,
            scope=ModelScope.TENANT if tenant_id else ModelScope.GLOBAL,
            name=request.name,
            version=request.version,
            description=getattr(request, "description", None),
            status=ModelVersionStatus.DRAFT,
            model_schema_version="risk_model_v1.0",
            base_weights_json=base_weights or {},
            correlation_matrix_json=correlation_matrix,
            tail_parameters_json=tail_params or {},
            interaction_multipliers_json=interaction,
            loss_transform_params_json=loss_params or {},
            monte_carlo_defaults_json=mc_defaults,
            parent_version_id=getattr(request, "parent_version_id", None),
            created_by_user_id=user_id,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    async def publish(
        self,
        model_id: str,
        user_id: Optional[str] = None
    ) -> RiskModelVersion:
        """
        Publish a model version.
        
        Args:
            model_id: Model version ID
            user_id: User ID who is publishing
            
        Returns:
            Published RiskModelVersion
            
        Raises:
            ValueError: If model not found or already published
        """
        model = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.id == model_id
        ).first()
        
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        if model.status == ModelVersionStatus.PUBLISHED:
            raise ValueError("Model already published")
        
        # Compute immutable hash
        model.immutable_hash = model.compute_immutable_hash()
        model.status = ModelVersionStatus.PUBLISHED
        model.published_at = datetime.utcnow()
        model.published_by_user_id = user_id
        
        self.db.commit()
        self.db.refresh(model)
        
        # Audit
        if self.audit:
            try:
                tenant_id = model.tenant_id or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="MODEL_VERSION",
                    action="PUBLISHED",
                    entity_type="model_version",
                    entity_id=model.id,
                    actor_type="USER" if user_id else "SYSTEM",
                    actor_id=user_id or "system",
                    payload={
                        "name": model.name,
                        "version": model.version,
                        "immutable_hash": model.immutable_hash,
                        "is_calibrated": model.is_calibrated()
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to audit model publish: {e}")
        
        return model

    async def deprecate(
        self,
        model_id: str,
        user_id: Optional[str] = None,
        reason: str = "",
        replacement_version_id: Optional[str] = None,
    ) -> RiskModelVersion:
        """Deprecate a published model. Sets status DEPRECATED, deprecated_at, deprecated_reason, replacement_version_id."""
        from app.modules.model_versioning.exceptions import ModelVersionNotFoundError, InvalidModelStateError

        model = self.db.query(RiskModelVersion).filter(RiskModelVersion.id == model_id).first()
        if not model:
            raise ModelVersionNotFoundError(model_id)
        if model.status == ModelVersionStatus.DEPRECATED:
            raise InvalidModelStateError("Version already deprecated")
        model.status = ModelVersionStatus.DEPRECATED
        model.deprecated_at = datetime.utcnow()
        model.deprecated_reason = reason or None
        model.replacement_version_id = replacement_version_id
        self.db.commit()
        self.db.refresh(model)
        if self.audit:
            try:
                tid = model.tenant_id or "system"
                self.audit.append_event(
                    tenant_id=tid,
                    event_type="MODEL_VERSION",
                    action="DEPRECATED",
                    entity_type="model_version",
                    entity_id=model_id,
                    actor_type="USER" if user_id else "SYSTEM",
                    actor_id=user_id or "system",
                    payload={
                        "reason": reason,
                        "replacement_version_id": replacement_version_id,
                    },
                )
            except Exception as e:
                logger.warning(f"Failed to audit model deprecate: {e}")
        return model

    def list_activations(
        self,
        skip: int = 0,
        limit: int = 50,
        model_version_id: Optional[str] = None,
        product_type: Optional[str] = None,
    ) -> list:
        """List model activations."""
        q = self.db.query(RiskModelActivation)
        if model_version_id is not None:
            q = q.filter(RiskModelActivation.model_version_id == model_version_id)
        if product_type is not None:
            q = q.filter(RiskModelActivation.product_type == product_type)
        q = q.order_by(RiskModelActivation.effective_from.desc())
        return q.offset(skip).limit(limit).all()

    async def create_activation_detailed(
        self,
        request: "ModelActivationCreateRequest",
        user_id: Optional[str] = None,
        context: Optional[Any] = None,
    ) -> RiskModelActivation:
        """Create a model activation."""
        from app.modules.model_versioning.exceptions import (
            ModelVersionNotFoundError,
            InvalidModelStateError,
        )

        model = self.get_model(request.model_version_id)
        if model.status != ModelVersionStatus.PUBLISHED:
            raise InvalidModelStateError(
                f"Only published models can be activated. Current status: {model.status}"
            )
        tenant_id = getattr(context, "tenant_id", None) if context else None
        now = datetime.utcnow()
        act = RiskModelActivation(
            id=generate_ulid(),
            tenant_id=tenant_id,
            model_version_id=request.model_version_id,
            scope_type=request.scope_type,
            scope_id=request.scope_id,
            effective_from=request.effective_from,
            effective_to=request.effective_to,
            status=ActivationStatus.ACTIVE,
            activated_by_user_id=user_id,
            activated_at=now,
        )
        self.db.add(act)
        self.db.commit()
        self.db.refresh(act)
        return act

    async def deactivate_activation(
        self,
        activation_id: str,
        user_id: Optional[str] = None,
        context: Optional[Any] = None,
        reason: str = "",
    ) -> RiskModelActivation:
        """Deactivate a model activation."""
        from app.modules.model_versioning.exceptions import ActivationNotFoundError

        act = (
            self.db.query(RiskModelActivation)
            .filter(RiskModelActivation.id == activation_id)
            .first()
        )
        if not act:
            raise ActivationNotFoundError(activation_id)
        act.status = ActivationStatus.DISABLED
        act.deactivated_at = datetime.utcnow()
        act.deactivation_reason = reason or None
        self.db.commit()
        self.db.refresh(act)
        return act

    async def get_current_published(
        self,
        tenant_id: Optional[str] = None
    ) -> Optional[RiskModelVersion]:
        """
        Get the current published model version.

        Args:
            tenant_id: Tenant ID (optional, for tenant-specific models)

        Returns:
            Current published RiskModelVersion or None
        """
        query = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.status == ModelVersionStatus.PUBLISHED
        )

        if tenant_id:
            query = query.filter(RiskModelVersion.tenant_id == tenant_id)
        else:
            query = query.filter(RiskModelVersion.tenant_id.is_(None))

        return query.order_by(
            RiskModelVersion.published_at.desc()
        ).first()

    async def compare_versions(
        self,
        version_1_id: str,
        version_2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two model versions.
        
        Args:
            version_1_id: First model version ID
            version_2_id: Second model version ID
            
        Returns:
            Dictionary with comparison results
            
        Raises:
            ValueError: If versions not found
        """
        v1 = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.id == version_1_id
        ).first()
        v2 = self.db.query(RiskModelVersion).filter(
            RiskModelVersion.id == version_2_id
        ).first()
        
        if not v1 or not v2:
            raise ValueError("Version not found")
        
        # Compare weights
        weight_changes = {}
        all_layers = set()
        
        if v1.base_weights_json:
            all_layers.update(v1.base_weights_json.keys())
        if v2.base_weights_json:
            all_layers.update(v2.base_weights_json.keys())
        
        for layer in all_layers:
            w1 = v1.get_layer_weight(layer)
            w2 = v2.get_layer_weight(layer)
            change = w2 - w1
            change_pct = (change / w1 * 100) if w1 > 0 else 0
            weight_changes[layer] = {
                "v1": w1,
                "v2": w2,
                "change": change,
                "change_pct": change_pct
            }
        
        # Compare loss functions
        lf1 = v1.get_loss_function_params()
        lf2 = v2.get_loss_function_params()
        
        loss_function_changes = {
            "v1_type": lf1.get("type"),
            "v2_type": lf2.get("type"),
            "v1_params": lf1.get("parameters"),
            "v2_params": lf2.get("parameters"),
            "v1_exponent": lf1.get("risk_score_exponent"),
            "v2_exponent": lf2.get("risk_score_exponent"),
            "exponent_change": lf2.get("risk_score_exponent", 0) - lf1.get("risk_score_exponent", 0)
        }
        
        return {
            "version_1": {
                "id": v1.id,
                "name": v1.name,
                "version": v1.version,
                "is_calibrated": v1.is_calibrated()
            },
            "version_2": {
                "id": v2.id,
                "name": v2.name,
                "version": v2.version,
                "is_calibrated": v2.is_calibrated()
            },
            "weight_changes": weight_changes,
            "loss_function_changes": loss_function_changes,
        }


def create_model_version_service(db: Session, audit: Optional[AuditLedger] = None) -> ModelVersionService:
    """Create model version service instance."""
    return ModelVersionService(db, audit)
