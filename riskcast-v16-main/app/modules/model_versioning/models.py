"""
Model Versioning Models
SQLAlchemy models for risk model version management
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    Index
)
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin
from app.shared.utils import generate_ulid


class ModelVersionStatus(str, enum.Enum):
    """Model version status"""
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class ModelScope(str, enum.Enum):
    """Model scope"""
    GLOBAL = "GLOBAL"  # Available to all tenants
    TENANT = "TENANT"  # Tenant-specific model


class RiskModelVersion(Base, BaseMixin):
    """
    Risk Model Version model.
    
    Represents a versioned risk model with weights, calibration, and constraints.
    Models can be GLOBAL (available to all tenants) or TENANT-specific.
    """
    __tablename__ = 'risk_model_versions'
    
    # ID is inherited from BaseMixin (ULID String(26))
    # created_at, updated_at are inherited from BaseMixin
    
    # Tenant ID (NULL for global models, set for tenant-specific models)
    tenant_id = Column(
        String(26),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=True,
        index=True
    )
    
    # Scope
    scope = Column(
        SQLEnum(ModelScope, native_enum=False),
        nullable=False,
        index=True
    )
    
    # Model metadata
    name = Column(String(255), nullable=False, index=True)
    status = Column(
        SQLEnum(ModelVersionStatus, native_enum=False),
        default=ModelVersionStatus.DRAFT,
        nullable=False,
        index=True
    )
    
    # Model schema and data
    model_schema_version = Column(String(50), nullable=False)  # e.g., 'risk_model_v1.0'
    version = Column(String(50), nullable=False, index=True)  # Semantic versioning: 1.0.0, 1.1.0
    description = Column(String(1000), nullable=True)  # Model description
    
    # Legacy fields (kept for backward compatibility)
    weights_json = Column(JSON, nullable=True)  # Model weights/parameters (deprecated, use base_weights_json)
    calibration_json = Column(JSON, nullable=True)  # Calibration parameters
    constraints_json = Column(JSON, nullable=True)  # Model constraints
    metrics_json = Column(JSON, nullable=True)  # Performance/drift metrics
    
    # Detailed parameter fields
    base_weights_json = Column(JSON, nullable=True)  # Base risk weights
    correlation_matrix_json = Column(JSON, nullable=True)  # Correlation matrix
    tail_parameters_json = Column(JSON, nullable=True)  # Tail distribution parameters
    interaction_multipliers_json = Column(JSON, nullable=True)  # Interaction multipliers
    loss_transform_params_json = Column(JSON, nullable=True)  # Loss transformation parameters
    monte_carlo_defaults_json = Column(JSON, nullable=True)  # Monte Carlo simulation defaults
    
    # Lineage
    parent_version_id = Column(
        String(26),
        ForeignKey('risk_model_versions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    calibration_run_id = Column(String(26), nullable=True)  # FK to calibration runs (when available)
    calibration_dataset_id = Column(String(26), nullable=True)  # FK to calibration datasets (when available)
    
    # Audit fields
    created_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    published_at = Column(DateTime, nullable=True, index=True)
    published_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    approved_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(String(2000), nullable=True)
    
    # Deprecation (when status = DEPRECATED)
    deprecated_at = Column(DateTime, nullable=True, index=True)
    deprecated_reason = Column(String(2000), nullable=True)
    replacement_version_id = Column(
        String(26),
        ForeignKey('risk_model_versions.id', ondelete='SET NULL'),
        nullable=True,
        index=True
    )
    
    # Immutability
    immutable_hash = Column(String(64), nullable=True, unique=True, index=True)  # Set on publish (SHA256 of all parameters)
    
    # Relationships
    activations = relationship(
        'RiskModelActivation',
        back_populates='model_version',
        cascade='all, delete-orphan',
        lazy='dynamic'
    )
    parent_version = relationship(
        'RiskModelVersion',
        remote_side='RiskModelVersion.id',
        foreign_keys=[parent_version_id],
        lazy='select'
    )
    created_by_user = relationship(
        'User',
        foreign_keys=[created_by_user_id],
        lazy='select'
    )
    published_by_user = relationship(
        'User',
        foreign_keys=[published_by_user_id],
        lazy='select'
    )
    approved_by_user = relationship(
        'User',
        foreign_keys=[approved_by_user_id],
        lazy='select'
    )
    tenant = relationship(
        'Tenant',
        foreign_keys=[tenant_id],
        lazy='select'
    )
    
    __table_args__ = (
        Index('ix_model_versions_status_published', 'status', 'published_at'),
        Index('ix_model_versions_tenant_status', 'tenant_id', 'status'),
        Index('ix_model_versions_scope_status', 'scope', 'status'),
        Index('ix_model_versions_tenant_name_version', 'tenant_id', 'name', 'version', unique=True),
    )
    
    def __repr__(self):
        return f"<RiskModelVersion(id={self.id}, name={self.name}, status={self.status.value}, scope={self.scope.value})>"
    
    def get_layer_weight(self, layer_name: str) -> float:
        """
        Get weight for a specific layer.
        
        Returns calibrated weight if available, otherwise default.
        
        Args:
            layer_name: Name of the risk layer
            
        Returns:
            Weight value (0.0 if not found)
        """
        # Try base_weights_json first (calibrated)
        if self.base_weights_json and layer_name in self.base_weights_json:
            return float(self.base_weights_json[layer_name])
        
        # Fallback to legacy weights_json
        if self.weights_json and layer_name in self.weights_json:
            return float(self.weights_json[layer_name])
        
        # Fallback to default weights
        return self._get_default_weight(layer_name)
    
    def get_correlation(self, layer_1: str, layer_2: str) -> float:
        """
        Get correlation between two layers.
        
        Returns calibrated correlation if available, otherwise default.
        
        Args:
            layer_1: First layer name
            layer_2: Second layer name
            
        Returns:
            Correlation value (0.0 if not found)
        """
        # Ensure consistent key ordering
        key1 = f"{min(layer_1, layer_2)}:{max(layer_1, layer_2)}"
        key2 = f"{layer_1}_{layer_2}"
        key3 = f"{layer_2}_{layer_1}"
        
        # Try correlation_matrix_json first (calibrated)
        if self.correlation_matrix_json:
            if key1 in self.correlation_matrix_json:
                return float(self.correlation_matrix_json[key1])
            if key2 in self.correlation_matrix_json:
                return float(self.correlation_matrix_json[key2])
            if key3 in self.correlation_matrix_json:
                return float(self.correlation_matrix_json[key3])
        
        # Fallback to default correlation
        return self._get_default_correlation(layer_1, layer_2)
    
    def get_loss_function_params(self) -> dict:
        """
        Get loss function parameters.
        
        Returns calibrated parameters if available, otherwise default.
        
        Returns:
            Dictionary with loss function parameters
        """
        # Try loss_transform_params_json first (calibrated)
        if self.loss_transform_params_json:
            params = self.loss_transform_params_json
            
            # If it's stored as a dict with 'type', 'parameters', 'formula'
            if isinstance(params, dict) and 'parameters' in params:
                # Extract parameters for risk engine
                loss_params = params.get('parameters', {})
                function_type = params.get('type', 'POWER')
                
                # Convert to format expected by risk engine
                if function_type == 'POWER':
                    # loss = a * (risk/10)^b
                    a = loss_params.get('a', 1.0)
                    b = loss_params.get('b', 1.8)
                    return {
                        'base_loss_rate': 0.0,  # Not used for power function
                        'risk_score_exponent': float(b),
                        'min_loss_pct': 0.001,
                        'max_loss_pct': 1.0,
                        'function_type': 'POWER',
                        'multiplier': float(a)
                    }
                elif function_type == 'EXPONENTIAL':
                    # loss = a * exp(b * risk/10)
                    a = loss_params.get('a', 0.01)
                    b = loss_params.get('b', 3.0)
                    return {
                        'base_loss_rate': float(a),
                        'risk_score_exponent': float(b),
                        'min_loss_pct': 0.001,
                        'max_loss_pct': 1.0,
                        'function_type': 'EXPONENTIAL'
                    }
                elif function_type == 'LOGISTIC':
                    # loss = L / (1 + exp(-k * (risk/10 - x0)))
                    L = loss_params.get('L', 1.0)
                    k = loss_params.get('k', 5.0)
                    x0 = loss_params.get('x0', 0.5)
                    return {
                        'base_loss_rate': float(L),
                        'risk_score_exponent': float(k),
                        'min_loss_pct': 0.001,
                        'max_loss_pct': float(L),
                        'function_type': 'LOGISTIC',
                        'inflection_point': float(x0)
                    }
                else:
                    # Default to power function
                    return self._get_default_loss_params()
            
            # If it's already in the expected format
            return params
        
        # Fallback to default
        return self._get_default_loss_params()
    
    def is_calibrated(self) -> bool:
        """Check if this model version was created from calibration."""
        return self.calibration_run_id is not None
    
    def compute_immutable_hash(self) -> str:
        """
        Compute hash of all parameters for immutability verification.
        
        Returns:
            SHA256 hash as hex string
        """
        import hashlib
        import json
        
        data = {
            "name": self.name,
            "version": self.version,
            "base_weights": self.base_weights_json or {},
            "correlation_matrix": self.correlation_matrix_json or {},
            "loss_transform_params": self.loss_transform_params_json or {},
            "tail_parameters": self.tail_parameters_json or {},
        }
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    @staticmethod
    def _get_default_weight(layer_name: str) -> float:
        """Get default weight for a layer."""
        defaults = {
            "route_risk": 0.15,
            "cargo_risk": 0.12,
            "transport_risk": 0.10,
            "commercial_risk": 0.08,
            "infrastructure_risk": 0.08,
            "weather_risk": 0.10,
            "geopolitical_risk": 0.07,
            "seasonal_risk": 0.06,
            "documentation_risk": 0.05,
            "handling_risk": 0.07,
            "security_risk": 0.05,
            "regulatory_risk": 0.04,
            "financial_risk": 0.03,
        }
        return defaults.get(layer_name, 0.05)
    
    @staticmethod
    def _get_default_correlation(layer_1: str, layer_2: str) -> float:
        """Get default correlation between two layers."""
        # Default correlations (can be enhanced)
        defaults = {
            ("weather_risk", "route_risk"): 0.42,
            ("cargo_risk", "transport_risk"): 0.38,
            ("geopolitical_risk", "route_risk"): 0.35,
            # Add more defaults as needed
        }
        
        key1 = (layer_1, layer_2)
        key2 = (layer_2, layer_1)
        
        return defaults.get(key1) or defaults.get(key2) or 0.0
    
    @staticmethod
    def _get_default_loss_params() -> dict:
        """Get default loss function parameters."""
        return {
            'base_loss_rate': 0.0,
            'risk_score_exponent': 1.8,  # Original hardcoded value
            'min_loss_pct': 0.001,
            'max_loss_pct': 1.0,
            'function_type': 'POWER',
            'multiplier': 1.0
        }


class ActivationScopeType(str, enum.Enum):
    """Activation scope type"""
    DEFAULT = "DEFAULT"  # Default activation for all contexts
    CORRIDOR = "CORRIDOR"  # Specific corridor
    PRODUCT = "PRODUCT"  # Specific product type
    CARRIER = "CARRIER"  # Specific carrier


class ActivationStatus(str, enum.Enum):
    """Activation status"""
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DISABLED = "DISABLED"


class RiskModelActivation(Base, BaseMixin):
    """
    Risk Model Activation model.
    
    Links a model version to a tenant (and optionally scope_type/scope_id)
    for active use in risk calculations.
    """
    __tablename__ = 'risk_model_activations'
    
    # ID is inherited from BaseMixin (ULID String(26))
    # created_at, updated_at are inherited from BaseMixin
    
    # Tenant ID (nullable for default/system activations)
    tenant_id = Column(
        String(26),
        ForeignKey('tenants.id', ondelete='CASCADE'),
        nullable=True,  # NULL = default activation
        index=True
    )
    
    # Model reference
    model_version_id = Column(
        String(26),
        ForeignKey('risk_model_versions.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    
    # Activation scope (new structure)
    scope_type = Column(
        SQLEnum(ActivationScopeType, native_enum=False),
        nullable=False,
        default=ActivationScopeType.DEFAULT,
        index=True
    )
    scope_id = Column(String(26), nullable=True, index=True)  # corridor_id, product_id, etc.
    
    # Legacy fields (kept for backward compatibility)
    corridor_id = Column(String(100), nullable=True, index=True)  # NULL = all corridors
    product_type = Column(String(100), nullable=True, index=True)  # Optional
    
    # Effective period
    effective_from = Column(DateTime, nullable=False, index=True)
    effective_to = Column(DateTime, nullable=True, index=True)  # NULL = indefinite
    
    # Status
    status = Column(
        SQLEnum(ActivationStatus, native_enum=False),
        nullable=False,
        default=ActivationStatus.ACTIVE,
        index=True
    )
    
    # Audit fields
    activated_by_user_id = Column(
        String(26),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    activated_at = Column(DateTime, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    deactivation_reason = Column(String(1000), nullable=True)
    
    # Relationships
    model_version = relationship(
        'RiskModelVersion',
        foreign_keys=[model_version_id],
        back_populates='activations',
        lazy='select'
    )
    activated_by_user = relationship(
        'User',
        foreign_keys=[activated_by_user_id],
        lazy='select'
    )
    
    __table_args__ = (
        Index('ix_activations_lookup', 'tenant_id', 'corridor_id', 'product_type', 'effective_from'),
        Index('ix_activations_tenant_model', 'tenant_id', 'model_version_id'),
        Index('ix_activations_effective', 'effective_from', 'effective_to'),
        Index('ix_activations_scope', 'scope_type', 'scope_id'),
    )
    
    def __repr__(self):
        return f"<RiskModelActivation(id={self.id}, tenant_id={self.tenant_id}, model_version_id={self.model_version_id}, product_type={self.product_type})>"
