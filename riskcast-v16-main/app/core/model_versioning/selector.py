"""
Model version selection logic.

Selection priority (highest to lowest):
1. Explicit model_version_id provided
2. Scope-specific activation (CARRIER > PRODUCT > CORRIDOR)
3. Tenant-level DEFAULT activation
4. System-level DEFAULT activation (tenant_id = NULL)
"""

from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.modules.model_versioning.models import (
    RiskModelVersion,
    RiskModelActivation,
    ModelVersionStatus,
    ActivationScopeType,
    ActivationStatus
)


class ModelSelectionContext:
    """Context for model selection."""
    
    def __init__(
        self,
        tenant_id: str,  # ULID string
        corridor_id: Optional[str] = None,  # ULID string
        product_id: Optional[str] = None,  # ULID string
        carrier_id: Optional[str] = None,  # ULID string
        as_of: Optional[datetime] = None
    ):
        self.tenant_id = tenant_id
        self.corridor_id = corridor_id
        self.product_id = product_id
        self.carrier_id = carrier_id
        self.as_of = as_of or datetime.utcnow()


class ModelSelectionResult:
    """Result of model selection."""
    
    def __init__(
        self,
        model_version: RiskModelVersion,
        activation: Optional[RiskModelActivation],
        selection_reason: str
    ):
        self.model_version = model_version
        self.activation = activation
        self.selection_reason = selection_reason
    
    @property
    def model_version_id(self) -> str:
        """Get model version ID (ULID)."""
        return self.model_version.id
    
    @property
    def immutable_hash(self) -> Optional[str]:
        """Get immutable hash of the model."""
        return self.model_version.immutable_hash


class ModelNotFoundError(Exception):
    """Raised when a model is not found."""
    pass


class ModelNotPublishedError(Exception):
    """Raised when trying to use a non-published model."""
    pass


class NoActiveModelError(Exception):
    """Raised when no active model can be found for the context."""
    pass


class ModelSelector:
    """
    Selects the appropriate model version for a given context.
    """
    
    def __init__(self, db: Session):
        """
        Initialize model selector.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def select(
        self,
        context: ModelSelectionContext,
        explicit_model_version_id: Optional[str] = None  # ULID string
    ) -> ModelSelectionResult:
        """
        Select model version based on context and activation rules.
        
        Args:
            context: Selection context with tenant, corridor, etc.
            explicit_model_version_id: If provided, use this model (bypass activation rules)
            
        Returns:
            ModelSelectionResult with selected model and reason
            
        Raises:
            ModelNotFoundError: If explicit model is not found
            ModelNotPublishedError: If explicit model is not published
            NoActiveModelError: If no model can be selected
        """
        # 1. If explicit model_version_id provided, use it
        if explicit_model_version_id:
            model = self._get_model_by_id(explicit_model_version_id)
            if not model:
                raise ModelNotFoundError(f"Model {explicit_model_version_id} not found")
            if model.status != ModelVersionStatus.PUBLISHED:
                raise ModelNotPublishedError(
                    f"Model {explicit_model_version_id} is not published (status: {model.status.value})"
                )
            return ModelSelectionResult(
                model_version=model,
                activation=None,
                selection_reason=f"Explicit model_version_id provided: {explicit_model_version_id}"
            )
        
        # 2. Find best matching activation
        activation = self._find_best_activation(context)
        
        if not activation:
            raise NoActiveModelError(
                f"No active model found for tenant {context.tenant_id} "
                f"as of {context.as_of.isoformat()}"
            )
        
        model = activation.model_version
        
        # Verify model is published
        if model.status != ModelVersionStatus.PUBLISHED:
            raise ModelNotPublishedError(
                f"Model {model.id} in activation {activation.id} is not published (status: {model.status.value})"
            )
        
        reason = self._build_selection_reason(activation, context)
        
        return ModelSelectionResult(
            model_version=model,
            activation=activation,
            selection_reason=reason
        )
    
    def _find_best_activation(
        self,
        context: ModelSelectionContext
    ) -> Optional[RiskModelActivation]:
        """
        Find the best matching activation using scope priority.
        
        Priority order:
        1. CARRIER scope matching carrier_id
        2. PRODUCT scope matching product_id
        3. CORRIDOR scope matching corridor_id
        4. DEFAULT scope for tenant
        5. DEFAULT scope system-wide (tenant_id = NULL)
        
        Args:
            context: Selection context
            
        Returns:
            Best matching activation or None
        """
        # Check CARRIER scope (highest priority)
        if context.carrier_id:
            carrier_activation = self._find_activation(
                tenant_id=context.tenant_id,
                scope_type=ActivationScopeType.CARRIER,
                scope_id=context.carrier_id,
                as_of=context.as_of
            )
            if carrier_activation:
                return carrier_activation
        
        # Check PRODUCT scope
        if context.product_id:
            product_activation = self._find_activation(
                tenant_id=context.tenant_id,
                scope_type=ActivationScopeType.PRODUCT,
                scope_id=context.product_id,
                as_of=context.as_of
            )
            if product_activation:
                return product_activation
        
        # Check CORRIDOR scope
        if context.corridor_id:
            corridor_activation = self._find_activation(
                tenant_id=context.tenant_id,
                scope_type=ActivationScopeType.CORRIDOR,
                scope_id=context.corridor_id,
                as_of=context.as_of
            )
            if corridor_activation:
                return corridor_activation
        
        # Check tenant DEFAULT scope
        tenant_default = self._find_activation(
            tenant_id=context.tenant_id,
            scope_type=ActivationScopeType.DEFAULT,
            scope_id=None,
            as_of=context.as_of
        )
        if tenant_default:
            return tenant_default
        
        # Check system DEFAULT scope (tenant_id = NULL)
        system_default = self._find_activation(
            tenant_id=None,
            scope_type=ActivationScopeType.DEFAULT,
            scope_id=None,
            as_of=context.as_of
        )
        return system_default
    
    def _find_activation(
        self,
        tenant_id: Optional[str],  # ULID string or None
        scope_type: ActivationScopeType,
        scope_id: Optional[str],  # ULID string or None
        as_of: datetime
    ) -> Optional[RiskModelActivation]:
        """
        Find a specific activation matching the criteria.
        
        Args:
            tenant_id: Tenant ID (None for system-wide)
            scope_type: Activation scope type
            scope_id: Scope ID (None for DEFAULT)
            as_of: Point in time for activation lookup
            
        Returns:
            Matching activation or None
        """
        query = self.db.query(RiskModelActivation).join(
            RiskModelVersion,
            RiskModelActivation.model_version_id == RiskModelVersion.id
        ).filter(
            RiskModelActivation.status == ActivationStatus.ACTIVE,
            RiskModelActivation.scope_type == scope_type,
            RiskModelActivation.effective_from <= as_of,
            or_(
                RiskModelActivation.effective_to.is_(None),
                RiskModelActivation.effective_to > as_of
            ),
            RiskModelVersion.status == ModelVersionStatus.PUBLISHED
        )
        
        # Filter by tenant_id
        if tenant_id is None:
            query = query.filter(RiskModelActivation.tenant_id.is_(None))
        else:
            query = query.filter(RiskModelActivation.tenant_id == tenant_id)
        
        # Filter by scope_id
        if scope_id is None:
            query = query.filter(RiskModelActivation.scope_id.is_(None))
        else:
            query = query.filter(RiskModelActivation.scope_id == scope_id)
        
        # Order by effective_from desc to get most recent activation
        return query.order_by(RiskModelActivation.effective_from.desc()).first()
    
    def _get_model_by_id(self, model_id: str) -> Optional[RiskModelVersion]:
        """
        Get model by ID.
        
        Args:
            model_id: Model version ID (ULID)
            
        Returns:
            Model version or None
        """
        return self.db.query(RiskModelVersion).filter(
            RiskModelVersion.id == model_id
        ).first()
    
    def _build_selection_reason(
        self,
        activation: RiskModelActivation,
        context: ModelSelectionContext
    ) -> str:
        """
        Build human-readable selection reason.
        
        Args:
            activation: Selected activation
            context: Selection context
            
        Returns:
            Human-readable reason string
        """
        scope = activation.scope_type
        if scope == ActivationScopeType.DEFAULT:
            if activation.tenant_id:
                return f"Tenant default model (activation {activation.id}, model {activation.model_version.name} v{activation.model_version.version})"
            else:
                return f"System default model (activation {activation.id}, model {activation.model_version.name} v{activation.model_version.version})"
        else:
            scope_name = scope.value
            return f"{scope_name} scope activation for {activation.scope_id} (activation {activation.id}, model {activation.model_version.name} v{activation.model_version.version})"
