"""
Tests for model selection logic.
"""

import pytest
from datetime import datetime, timedelta
from app.shared.utils import generate_ulid
from app.modules.model_versioning.models import (
    RiskModelVersion,
    RiskModelActivation,
    ModelVersionStatus,
    ModelScope,
    ActivationScopeType,
    ActivationStatus
)
from app.core.model_versioning.selector import (
    ModelSelector,
    ModelSelectionContext,
    NoActiveModelError,
    ModelNotFoundError,
    ModelNotPublishedError
)


def create_model(
    db_session,
    name: str = "test_model",
    version: str = "1.0.0",
    tenant_id: str = None,
    status: ModelVersionStatus = ModelVersionStatus.PUBLISHED,
    scope: ModelScope = ModelScope.GLOBAL
) -> RiskModelVersion:
    """Helper to create a test model."""
    model = RiskModelVersion(
        name=name,
        version=version,
        tenant_id=tenant_id,
        status=status,
        scope=scope,
        model_schema_version="risk_model_v1.0",
        base_weights_json={
            "route_risk": 0.25,
            "cargo_risk": 0.20,
            "carrier_risk": 0.20,
            "timing_risk": 0.15,
            "weather_risk": 0.10,
            "geopolitical_risk": 0.10
        },
        correlation_matrix_json={
            "route_cargo": 0.3,
            "weather_timing": 0.5
        },
        tail_parameters_json={
            "degrees_of_freedom": 4,
            "tail_shock_probability": 0.05,
            "extreme_loss_multiplier": 2.5
        },
        interaction_multipliers_json={},
        loss_transform_params_json={
            "base_loss_rate": 0.02,
            "risk_score_exponent": 1.5,
            "min_loss_pct": 0.001,
            "max_loss_pct": 0.15
        },
        monte_carlo_defaults_json={
            "default_iterations": 10000,
            "confidence_levels": [0.95, 0.99]
        },
        immutable_hash="test_hash_" + generate_ulid()[:10]
    )
    db_session.add(model)
    db_session.commit()
    db_session.refresh(model)
    return model


def create_activation(
    db_session,
    model_version_id: str,
    tenant_id: str = None,
    scope_type: ActivationScopeType = ActivationScopeType.DEFAULT,
    scope_id: str = None,
    effective_from: datetime = None,
    effective_to: datetime = None,
    status: ActivationStatus = ActivationStatus.ACTIVE
) -> RiskModelActivation:
    """Helper to create a test activation."""
    if effective_from is None:
        effective_from = datetime.utcnow() - timedelta(days=1)
    
    activation = RiskModelActivation(
        model_version_id=model_version_id,
        tenant_id=tenant_id,
        scope_type=scope_type,
        scope_id=scope_id,
        effective_from=effective_from,
        effective_to=effective_to,
        status=status
    )
    db_session.add(activation)
    db_session.commit()
    db_session.refresh(activation)
    return activation


class TestModelSelector:
    """Tests for ModelSelector."""
    
    @pytest.fixture
    def selector(self, db_session):
        """Create a model selector."""
        return ModelSelector(db_session)
    
    @pytest.fixture
    def setup_models(self, db_session):
        """Create test models and activations."""
        # Create system default model
        system_model = create_model(
            db_session,
            name="system",
            version="1.0.0",
            tenant_id=None,
            scope=ModelScope.GLOBAL
        )
        create_activation(
            db_session,
            model_version_id=system_model.id,
            tenant_id=None,
            scope_type=ActivationScopeType.DEFAULT
        )
        
        # Create tenant default model
        tenant_id = generate_ulid()
        tenant_model = create_model(
            db_session,
            name="tenant",
            version="1.0.0",
            tenant_id=tenant_id,
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=tenant_model.id,
            tenant_id=tenant_id,
            scope_type=ActivationScopeType.DEFAULT
        )
        
        # Create corridor-specific model
        corridor_id = generate_ulid()
        corridor_model = create_model(
            db_session,
            name="corridor",
            version="1.0.0",
            tenant_id=tenant_id,
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=corridor_model.id,
            tenant_id=tenant_id,
            scope_type=ActivationScopeType.CORRIDOR,
            scope_id=corridor_id
        )
        
        return {
            'tenant_id': tenant_id,
            'corridor_id': corridor_id,
            'system_model': system_model,
            'tenant_model': tenant_model,
            'corridor_model': corridor_model
        }
    
    def test_selects_system_default_when_no_tenant(self, selector, setup_models):
        """Should select system default for unknown tenant."""
        context = ModelSelectionContext(tenant_id=generate_ulid())
        result = selector.select(context)
        
        assert result.model_version.name == "system"
        assert "System default" in result.selection_reason
    
    def test_selects_tenant_default_over_system(self, selector, setup_models):
        """Tenant default should override system default."""
        context = ModelSelectionContext(tenant_id=setup_models['tenant_id'])
        result = selector.select(context)
        
        assert result.model_version.name == "tenant"
        assert "Tenant default" in result.selection_reason
    
    def test_selects_corridor_over_tenant_default(self, selector, setup_models):
        """Corridor scope should override tenant default."""
        context = ModelSelectionContext(
            tenant_id=setup_models['tenant_id'],
            corridor_id=setup_models['corridor_id']
        )
        result = selector.select(context)
        
        assert result.model_version.name == "corridor"
        assert "CORRIDOR scope" in result.selection_reason
    
    def test_explicit_model_overrides_all(self, selector, setup_models):
        """Explicit model_version_id should override activation rules."""
        context = ModelSelectionContext(
            tenant_id=setup_models['tenant_id'],
            corridor_id=setup_models['corridor_id']
        )
        result = selector.select(
            context,
            explicit_model_version_id=setup_models['system_model'].id
        )
        
        assert result.model_version.name == "system"
        assert "Explicit" in result.selection_reason
    
    def test_respects_effective_dates(self, selector, db_session, setup_models):
        """Should only select activations within effective dates."""
        # Create future activation
        future_model = create_model(
            db_session,
            name="future",
            version="2.0.0",
            tenant_id=setup_models['tenant_id'],
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=future_model.id,
            tenant_id=setup_models['tenant_id'],
            scope_type=ActivationScopeType.DEFAULT,
            effective_from=datetime.utcnow() + timedelta(days=30)
        )
        
        # Current selection should not use future model
        context = ModelSelectionContext(tenant_id=setup_models['tenant_id'])
        result = selector.select(context)
        
        assert result.model_version.name == "tenant"  # Current default
    
    def test_raises_when_no_model_available(self, selector, db_session):
        """Should raise NoActiveModelError when no model found."""
        # Use tenant with no activations and no system default
        context = ModelSelectionContext(tenant_id=generate_ulid())
        
        with pytest.raises(NoActiveModelError):
            selector.select(context)
    
    def test_raises_when_explicit_model_not_found(self, selector, setup_models):
        """Should raise ModelNotFoundError when explicit model doesn't exist."""
        context = ModelSelectionContext(tenant_id=setup_models['tenant_id'])
        fake_id = generate_ulid()
        
        with pytest.raises(ModelNotFoundError):
            selector.select(context, explicit_model_version_id=fake_id)
    
    def test_raises_when_explicit_model_not_published(self, selector, db_session, setup_models):
        """Should raise ModelNotPublishedError when explicit model is not published."""
        # Create a draft model
        draft_model = create_model(
            db_session,
            name="draft",
            version="1.0.0",
            tenant_id=setup_models['tenant_id'],
            status=ModelVersionStatus.DRAFT
        )
        
        context = ModelSelectionContext(tenant_id=setup_models['tenant_id'])
        
        with pytest.raises(ModelNotPublishedError):
            selector.select(context, explicit_model_version_id=draft_model.id)
    
    def test_product_scope_priority(self, selector, db_session, setup_models):
        """PRODUCT scope should have higher priority than CORRIDOR."""
        product_id = generate_ulid()
        product_model = create_model(
            db_session,
            name="product",
            version="1.0.0",
            tenant_id=setup_models['tenant_id'],
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=product_model.id,
            tenant_id=setup_models['tenant_id'],
            scope_type=ActivationScopeType.PRODUCT,
            scope_id=product_id
        )
        
        context = ModelSelectionContext(
            tenant_id=setup_models['tenant_id'],
            corridor_id=setup_models['corridor_id'],
            product_id=product_id
        )
        result = selector.select(context)
        
        assert result.model_version.name == "product"
        assert "PRODUCT scope" in result.selection_reason
    
    def test_carrier_scope_priority(self, selector, db_session, setup_models):
        """CARRIER scope should have highest priority."""
        carrier_id = generate_ulid()
        carrier_model = create_model(
            db_session,
            name="carrier",
            version="1.0.0",
            tenant_id=setup_models['tenant_id'],
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=carrier_model.id,
            tenant_id=setup_models['tenant_id'],
            scope_type=ActivationScopeType.CARRIER,
            scope_id=carrier_id
        )
        
        context = ModelSelectionContext(
            tenant_id=setup_models['tenant_id'],
            corridor_id=setup_models['corridor_id'],
            carrier_id=carrier_id
        )
        result = selector.select(context)
        
        assert result.model_version.name == "carrier"
        assert "CARRIER scope" in result.selection_reason
    
    def test_respects_effective_to_date(self, selector, db_session, setup_models):
        """Should not select activations that have expired."""
        # Create expired activation
        expired_model = create_model(
            db_session,
            name="expired",
            version="1.0.0",
            tenant_id=setup_models['tenant_id'],
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=expired_model.id,
            tenant_id=setup_models['tenant_id'],
            scope_type=ActivationScopeType.DEFAULT,
            effective_from=datetime.utcnow() - timedelta(days=30),
            effective_to=datetime.utcnow() - timedelta(days=1)  # Expired
        )
        
        # Should fall back to tenant default (not expired)
        context = ModelSelectionContext(tenant_id=setup_models['tenant_id'])
        result = selector.select(context)
        
        assert result.model_version.name == "tenant"
    
    def test_only_selects_active_activations(self, selector, db_session, setup_models):
        """Should only select activations with ACTIVE status."""
        # Create disabled activation
        disabled_model = create_model(
            db_session,
            name="disabled",
            version="1.0.0",
            tenant_id=setup_models['tenant_id'],
            scope=ModelScope.TENANT
        )
        create_activation(
            db_session,
            model_version_id=disabled_model.id,
            tenant_id=setup_models['tenant_id'],
            scope_type=ActivationScopeType.DEFAULT,
            status=ActivationStatus.DISABLED
        )
        
        # Should fall back to tenant default (active)
        context = ModelSelectionContext(tenant_id=setup_models['tenant_id'])
        result = selector.select(context)
        
        assert result.model_version.name == "tenant"
