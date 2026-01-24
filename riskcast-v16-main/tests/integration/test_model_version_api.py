"""
Integration tests for model version API.
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


def create_model(
    db_session,
    name: str = "test_model",
    version: str = "1.0.0",
    tenant_id: str = None,
    status: ModelVersionStatus = ModelVersionStatus.DRAFT,
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
        immutable_hash="test_hash_" + generate_ulid()[:10] if status == ModelVersionStatus.PUBLISHED else None
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


class TestModelVersionAPI:
    """Integration tests for model version API."""
    
    @pytest.fixture
    def draft_model(self, db_session):
        """Create a draft model for testing."""
        return create_model(
            db_session,
            name="draft_test",
            version="1.0.0",
            status=ModelVersionStatus.DRAFT
        )
    
    @pytest.fixture
    def published_model(self, db_session):
        """Create a published model for testing."""
        return create_model(
            db_session,
            name="published_test",
            version="1.0.0",
            status=ModelVersionStatus.PUBLISHED
        )
    
    @pytest.fixture
    def existing_activation(self, db_session, published_model):
        """Create an existing activation for testing."""
        return create_activation(
            db_session,
            model_version_id=published_model.id,
            scope_type=ActivationScopeType.DEFAULT
        )
    
    @pytest.fixture
    def setup_activations(self, db_session):
        """Create test models and activations."""
        tenant_id = generate_ulid()
        
        # Create system default model
        system_model = create_model(
            db_session,
            name="system",
            version="1.0.0",
            tenant_id=None,
            scope=ModelScope.GLOBAL,
            status=ModelVersionStatus.PUBLISHED
        )
        create_activation(
            db_session,
            model_version_id=system_model.id,
            tenant_id=None,
            scope_type=ActivationScopeType.DEFAULT
        )
        
        # Create tenant default model
        tenant_model = create_model(
            db_session,
            name="tenant",
            version="1.0.0",
            tenant_id=tenant_id,
            scope=ModelScope.TENANT,
            status=ModelVersionStatus.PUBLISHED
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
            scope=ModelScope.TENANT,
            status=ModelVersionStatus.PUBLISHED
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
    
    def test_create_model_version(self, client, auth_headers):
        """Test creating a new model version."""
        response = client.post(
            "/api/v3/models/versions",
            headers=auth_headers,
            json={
                "name": "test_model",
                "version": "1.0.0",
                "description": "Test model",
                "base_weights": {
                    "route_risk": 0.25,
                    "cargo_risk": 0.20,
                    "carrier_risk": 0.20,
                    "timing_risk": 0.15,
                    "weather_risk": 0.10,
                    "geopolitical_risk": 0.10
                },
                "correlation_matrix": {"route_cargo": 0.3},
                "tail_parameters": {
                    "degrees_of_freedom": 4,
                    "tail_shock_probability": 0.05,
                    "extreme_loss_multiplier": 2.5
                },
                "interaction_multipliers": {"high_value_perishable": 1.3},
                "loss_transform_params": {
                    "base_loss_rate": 0.02,
                    "risk_score_exponent": 1.5,
                    "min_loss_pct": 0.001,
                    "max_loss_pct": 0.15
                }
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_model"
        assert data["status"] == "DRAFT"
        assert data["immutable_hash"] is not None
    
    def test_publish_model_version(self, client, auth_headers, draft_model):
        """Test publishing a draft model."""
        response = client.post(
            f"/api/v3/models/versions/{draft_model.id}/publish",
            headers=auth_headers,
            params={"approval_notes": "Approved for production"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "PUBLISHED"
    
    def test_cannot_publish_already_published(self, client, auth_headers, published_model):
        """Cannot publish an already published model."""
        response = client.post(
            f"/api/v3/models/versions/{published_model.id}/publish",
            headers=auth_headers
        )
        
        assert response.status_code == 409
    
    def test_create_activation(self, client, auth_headers, published_model):
        """Test creating a model activation."""
        response = client.post(
            "/api/v3/models/activations",
            headers=auth_headers,
            json={
                "model_version_id": published_model.id,
                "scope_type": "DEFAULT",
                "effective_from": datetime.utcnow().isoformat()
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "ACTIVE"
    
    def test_activation_supersedes_previous(self, client, auth_headers, published_model, existing_activation):
        """New activation should supersede existing one."""
        response = client.post(
            "/api/v3/models/activations",
            headers=auth_headers,
            json={
                "model_version_id": published_model.id,
                "scope_type": "DEFAULT",
                "effective_from": datetime.utcnow().isoformat()
            }
        )
        
        assert response.status_code == 201
        
        # Check old activation is superseded
        old = client.get(
            "/api/v3/models/activations?active_only=false",
            headers=auth_headers
        )
        activations = old.json()
        superseded = [a for a in activations if a["id"] == existing_activation.id]
        assert len(superseded) > 0
        assert superseded[0]["status"] == "SUPERSEDED"
    
    def test_selection_preview(self, client, auth_headers, setup_activations):
        """Test model selection preview."""
        response = client.get(
            "/api/v3/models/selection/preview",
            headers=auth_headers,
            params={"corridor_id": setup_activations['corridor_id']}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["model_version_id"] is not None
        assert "selection_reason" in data
    
    def test_deprecate_model_version(self, client, auth_headers, published_model):
        """Test deprecating a published model."""
        response = client.post(
            f"/api/v3/models/versions/{published_model.id}/deprecate",
            headers=auth_headers,
            params={"reason": "Replaced by newer version"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DEPRECATED"
    
    def test_deactivate_activation(self, client, auth_headers, published_model):
        """Test deactivating an activation."""
        # Create activation first
        create_response = client.post(
            "/api/v3/models/activations",
            headers=auth_headers,
            json={
                "model_version_id": published_model.id,
                "scope_type": "DEFAULT",
                "effective_from": datetime.utcnow().isoformat()
            }
        )
        activation_id = create_response.json()["id"]
        
        # Deactivate it
        response = client.post(
            f"/api/v3/models/activations/{activation_id}/deactivate",
            headers=auth_headers,
            params={"reason": "No longer needed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DISABLED"
    
    def test_list_model_versions(self, client, auth_headers, draft_model, published_model):
        """Test listing model versions."""
        response = client.get(
            "/api/v3/models/versions",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least our test models
    
    def test_list_activations(self, client, auth_headers, published_model):
        """Test listing activations."""
        # Create an activation
        client.post(
            "/api/v3/models/activations",
            headers=auth_headers,
            json={
                "model_version_id": published_model.id,
                "scope_type": "DEFAULT",
                "effective_from": datetime.utcnow().isoformat()
            }
        )
        
        response = client.get(
            "/api/v3/models/activations",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
