"""
Unit Tests for Risk Engine

Tests:
1. Layer calculations
2. Weight application
3. Correlation matrix
4. Loss function
5. Monte Carlo simulation
6. Edge cases
7. Calibration integration
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import numpy as np
from typing import Dict, Any

from app.core.risk_engine.v16.risk_engine_calibrated import (
    CalibratedRiskEngine,
    CalibratedRiskResult
)
from app.modules.model_versioning.models import (
    RiskModelVersion,
    ModelVersionStatus,
    ModelScope
)
from app.services.unified_data_service import UnifiedShipmentData
from app.core.data_quality.gateway import DataQualityLevel, DataQualityReport


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_model_version():
    """Create mock model version with calibrated parameters."""
    version = Mock(spec=RiskModelVersion)
    version.id = "test-version-001"
    version.name = "Test Calibrated Model"
    version.version = "1.0.0"
    version.status = ModelVersionStatus.PUBLISHED
    version.scope = ModelScope.GLOBAL
    
    # Layer weights for 13 layers used by the engine
    base_weights = {
        "route_risk": 0.10,
        "cargo_risk": 0.12,
        "transport_risk": 0.10,
        "commercial_risk": 0.08,
        "infrastructure_risk": 0.08,
        "weather_risk": 0.12,
        "geopolitical_risk": 0.10,
        "seasonal_risk": 0.08,
        "documentation_risk": 0.06,
        "handling_risk": 0.06,
        "security_risk": 0.04,
        "regulatory_risk": 0.03,
        "financial_risk": 0.03,
    }
    
    # Mock get_layer_weight method
    def get_layer_weight(layer_name: str) -> float:
        return base_weights.get(layer_name, 0.0)
    
    version.get_layer_weight = Mock(side_effect=get_layer_weight)
    version.base_weights_json = base_weights
    
    # Mock correlations
    correlations = {
        "weather_risk:seasonal_risk": 0.6,
        "route_risk:infrastructure_risk": 0.5,
        "cargo_risk:handling_risk": 0.7,
        "transport_risk:carrier_reliability": 0.5,
        "geopolitical_risk:security_risk": 0.6,
    }
    
    def get_correlation(layer_1: str, layer_2: str) -> float:
        key1 = f"{min(layer_1, layer_2)}:{max(layer_1, layer_2)}"
        return correlations.get(key1, 0.0)
    
    version.get_correlation = Mock(side_effect=get_correlation)
    version.correlation_matrix_json = correlations
    
    # Mock loss function parameters
    loss_params = {
        "function_type": "POWER",
        "risk_score_exponent": 1.8,
        "multiplier": 1.0,
        "base_loss_rate": 0.0,
        "inflection_point": 0.5,
    }
    
    version.get_loss_function_params = Mock(return_value=loss_params)
    version.loss_transform_params_json = loss_params
    
    # Mock is_calibrated method
    version.is_calibrated = Mock(return_value=True)
    
    version.immutable_hash = "test-hash-abc123"
    
    return version


@pytest.fixture
def mock_audit():
    """Create mock audit logger."""
    audit = MagicMock()
    audit.append_event = Mock()
    return audit


@pytest.fixture
def sample_shipment_data():
    """Create sample unified shipment data."""
    data = Mock(spec=UnifiedShipmentData)
    
    # Basic shipment info
    data.origin_port = "CNSHA"
    data.destination_port = "USLAX"
    data.cargo_type = "ELECTRONICS"
    data.cargo_value_usd = 500000.0
    data.container_count = 2
    data.departure_date = date.today() + timedelta(days=7)
    data.expected_arrival_date = date.today() + timedelta(days=28)
    data.carrier_code = "MAEU"
    
    # Weather data
    data.origin_weather = {
        "weather_risk_score": 0.3,
        "storm_probability": 0.1,
        "wind_speed_knots": 15
    }
    data.destination_weather = {
        "weather_risk_score": 0.2,
        "storm_probability": 0.05,
        "wind_speed_knots": 10
    }
    data.route_weather = {
        "severe_weather_days": 2
    }
    
    # Port data
    data.origin_port_conditions = {
        "risk": {"port_risk_score": 6.0},
        "congestion": {"congestion_level": 0.6, "avg_delay_hours": 24},
        "efficiency": {"berth_utilization_pct": 75}
    }
    data.destination_port_conditions = {
        "risk": {"port_risk_score": 4.0},
        "congestion": {"congestion_level": 0.4, "avg_delay_hours": 12},
        "efficiency": {"berth_utilization_pct": 80}
    }
    
    # Carrier data
    data.carrier_performance = {
        "rating": {"carrier_risk_score": 3.5},
        "reliability_score": 0.85,
        "on_time_percentage": 0.82,
        "claims_ratio": 0.02
    }
    data.carrier_route_performance = {
        "on_time_delivery_pct": 0.85
    }
    
    # Climate data
    data.climate_indices = {
        "enso_phase": "NEUTRAL",
        "oni_value": 0.2
    }
    
    # Data quality
    data.overall_data_quality = DataQualityLevel.HIGH
    data.overall_confidence = 0.85
    data.data_warnings = []
    data.data_sources = []
    data.data_quality_report = Mock(spec=DataQualityReport)
    
    # Audit
    data.collected_at = datetime.utcnow()
    data.collection_hash = "data-hash-xyz789"
    
    return data


@pytest.fixture
def risk_engine(mock_model_version, mock_audit):
    """Create risk engine instance."""
    return CalibratedRiskEngine(
        model_version=mock_model_version,
        audit=mock_audit,
        seed=42,
        tenant_id="test-tenant"
    )


# ============================================================================
# Basic Functionality Tests
# ============================================================================

class TestRiskEngineBasics:
    """Test basic risk engine functionality."""
    
    def test_engine_initialization(self, mock_model_version, mock_audit):
        """Test engine initializes correctly."""
        engine = CalibratedRiskEngine(
            model_version=mock_model_version,
            audit=mock_audit,
            seed=42
        )
        
        assert engine.model_version == mock_model_version
        assert engine.seed == 42
        assert len(engine.layer_weights) == 13
        assert engine.correlation_matrix.shape == (13, 13)
        assert engine.loss_function is not None
    
    def test_weight_sum_equals_one(self, risk_engine):
        """Test layer weights sum to 1.0."""
        total_weight = sum(risk_engine.layer_weights.values())
        assert abs(total_weight - 1.0) < 0.001
    
    def test_correlation_matrix_is_positive_definite(self, risk_engine):
        """Test correlation matrix is valid (positive definite)."""
        eigenvalues = np.linalg.eigvalsh(risk_engine.correlation_matrix)
        # All eigenvalues should be positive (within numerical tolerance)
        assert all(eigenvalues > -1e-6)
    
    def test_correlation_matrix_diagonal_is_ones(self, risk_engine):
        """Test correlation matrix has 1.0 on diagonal."""
        diagonal = np.diag(risk_engine.correlation_matrix)
        assert np.allclose(diagonal, 1.0)
    
    @pytest.mark.asyncio
    async def test_run_assessment_returns_result(
        self, risk_engine, sample_shipment_data
    ):
        """Test assessment returns valid result."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert isinstance(result, CalibratedRiskResult)
        assert 0 <= result.overall_risk_score <= 1
        assert result.expected_loss_pct >= 0
        assert result.expected_loss_usd >= 0
        assert result.var_95 >= 0
        assert result.var_99 >= result.var_95
        assert result.cvar_95 >= result.var_95
        assert result.cvar_99 >= result.var_99
    
    @pytest.mark.asyncio
    async def test_assessment_creates_audit_event(
        self, risk_engine, sample_shipment_data, mock_audit
    ):
        """Test assessment creates audit trail."""
        await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        mock_audit.append_event.assert_called()
        call_kwargs = mock_audit.append_event.call_args[1]
        assert call_kwargs["event_type"] == "RISK_ASSESSMENT"
        assert call_kwargs["action"] == "CALIBRATED_ASSESSMENT_COMPLETE"
        assert call_kwargs["tenant_id"] == "test-tenant"


# ============================================================================
# Layer Calculation Tests
# ============================================================================

class TestLayerCalculations:
    """Test individual layer calculations."""
    
    def test_route_risk_calculation(self, risk_engine, sample_shipment_data):
        """Test route risk layer calculation."""
        layer_scores = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        assert "route_risk" in layer_scores
        assert 0 <= layer_scores["route_risk"] <= 1
        
        # Route risk should be average of origin and destination port risk
        origin_risk = 6.0 / 10.0  # From sample data
        dest_risk = 4.0 / 10.0
        expected = (origin_risk + dest_risk) / 2.0
        assert abs(layer_scores["route_risk"] - expected) < 0.01
    
    def test_weather_risk_calculation(self, risk_engine, sample_shipment_data):
        """Test weather risk layer calculation."""
        layer_scores = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        assert "weather_risk" in layer_scores
        assert 0 <= layer_scores["weather_risk"] <= 1
        
        # Weather risk should be average of origin and destination weather risk
        origin_weather = 0.3  # From sample data
        dest_weather = 0.2
        expected = (origin_weather + dest_weather) / 2.0
        assert abs(layer_scores["weather_risk"] - expected) < 0.01
    
    def test_cargo_risk_by_type(self, risk_engine, sample_shipment_data):
        """Test cargo risk varies by cargo type."""
        # Electronics
        sample_shipment_data.cargo_type = "ELECTRONICS"
        scores_electronics = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        # Textiles (lower risk)
        sample_shipment_data.cargo_type = "TEXTILES"
        scores_textiles = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        # Food perishable (higher risk)
        sample_shipment_data.cargo_type = "FOOD_PERISHABLE"
        scores_perishable = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        # Perishable should have highest cargo risk
        assert scores_perishable["cargo_risk"] > scores_electronics["cargo_risk"]
        assert scores_electronics["cargo_risk"] > scores_textiles["cargo_risk"]
    
    def test_transport_risk_from_carrier(self, risk_engine, sample_shipment_data):
        """Test transport risk is calculated from carrier performance."""
        layer_scores = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        assert "transport_risk" in layer_scores
        assert 0 <= layer_scores["transport_risk"] <= 1
        
        # Should use carrier risk score
        expected = 3.5 / 10.0  # From sample data
        assert abs(layer_scores["transport_risk"] - expected) < 0.01
    
    def test_transport_risk_fallback_no_carrier(self, risk_engine, sample_shipment_data):
        """Test transport risk uses fallback when carrier data missing."""
        sample_shipment_data.carrier_performance = None
        
        layer_scores = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        assert layer_scores["transport_risk"] == 0.5  # Default fallback
    
    def test_seasonal_risk_enso_phase(self, risk_engine, sample_shipment_data):
        """Test seasonal risk varies with ENSO phase."""
        # Strong El Niño
        sample_shipment_data.climate_indices = {"enso_phase": "STRONG_EL_NINO"}
        scores_strong = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        # Moderate
        sample_shipment_data.climate_indices = {"enso_phase": "MODERATE_EL_NINO"}
        scores_moderate = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        # Neutral
        sample_shipment_data.climate_indices = {"enso_phase": "NEUTRAL"}
        scores_neutral = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        # Strong should have highest seasonal risk
        assert scores_strong["seasonal_risk"] > scores_moderate["seasonal_risk"]
        assert scores_moderate["seasonal_risk"] > scores_neutral["seasonal_risk"]
    
    def test_all_layer_scores_bounded(self, risk_engine, sample_shipment_data):
        """Test all layer scores are bounded between 0 and 1."""
        layer_scores = risk_engine._calculate_layer_scores(sample_shipment_data)
        
        for layer, score in layer_scores.items():
            assert 0 <= score <= 1, f"Layer {layer} score {score} out of bounds"
    
    def test_missing_data_uses_defaults(self, risk_engine):
        """Test missing data results in default scores."""
        # Create minimal data
        minimal_data = Mock(spec=UnifiedShipmentData)
        minimal_data.origin_port = "CNSHA"
        minimal_data.destination_port = "USLAX"
        minimal_data.cargo_type = "GENERAL"
        minimal_data.cargo_value_usd = 100000.0
        minimal_data.origin_weather = None
        minimal_data.destination_weather = None
        minimal_data.origin_port_conditions = None
        minimal_data.destination_port_conditions = None
        minimal_data.carrier_performance = None
        minimal_data.climate_indices = None
        
        layer_scores = risk_engine._calculate_layer_scores(minimal_data)
        
        # Should have all 13 layers with default values
        assert len(layer_scores) == 13
        for score in layer_scores.values():
            assert 0 <= score <= 1


# ============================================================================
# Weight Application Tests
# ============================================================================

class TestWeightApplication:
    """Test weight application to layer scores."""
    
    @pytest.mark.asyncio
    async def test_weighted_scores_sum_to_overall(self, risk_engine, sample_shipment_data):
        """Test weighted layer scores sum to overall risk score."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        # Sum of weighted scores should equal overall risk
        weighted_sum = sum(result.weighted_layer_scores.values())
        assert abs(weighted_sum - result.overall_risk_score) < 0.001
    
    @pytest.mark.asyncio
    async def test_weighted_scores_reflect_weights(self, risk_engine, sample_shipment_data):
        """Test weighted scores are layer scores multiplied by weights."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        for layer in result.layer_scores:
            expected_weighted = result.layer_scores[layer] * risk_engine.layer_weights[layer]
            actual_weighted = result.weighted_layer_scores[layer]
            assert abs(expected_weighted - actual_weighted) < 0.001
    
    def test_zero_weight_excludes_layer(self, mock_model_version, mock_audit):
        """Test zero weight effectively excludes a layer."""
        # Create custom weights with one zero
        custom_weights = {
            "route_risk": 0.0,  # Zero weight
            "cargo_risk": 0.20,
            "transport_risk": 0.20,
            "commercial_risk": 0.10,
            "infrastructure_risk": 0.10,
            "weather_risk": 0.15,
            "geopolitical_risk": 0.10,
            "seasonal_risk": 0.05,
            "documentation_risk": 0.04,
            "handling_risk": 0.03,
            "security_risk": 0.02,
            "regulatory_risk": 0.005,
            "financial_risk": 0.005,
        }
        
        def get_layer_weight_custom(layer_name: str) -> float:
            return custom_weights.get(layer_name, 0.0)
        
        mock_model_version.get_layer_weight = Mock(side_effect=get_layer_weight_custom)
        
        engine = CalibratedRiskEngine(mock_model_version, mock_audit)
        
        # Route risk weight should be zero
        assert engine.layer_weights["route_risk"] == 0.0


# ============================================================================
# Correlation Matrix Tests
# ============================================================================

class TestCorrelationMatrix:
    """Test correlation matrix application."""
    
    def test_correlation_matrix_symmetric(self, risk_engine):
        """Test correlation matrix is symmetric."""
        matrix = risk_engine.correlation_matrix
        assert np.allclose(matrix, matrix.T)
    
    def test_correlation_matrix_valid_range(self, risk_engine):
        """Test correlation values are in valid range [-1, 1]."""
        matrix = risk_engine.correlation_matrix
        # Off-diagonal elements should be between -1 and 1
        off_diagonal = matrix[~np.eye(matrix.shape[0], dtype=bool)]
        assert all(-1 <= val <= 1 for val in off_diagonal)
    
    def test_monte_carlo_uses_correlation(self, risk_engine):
        """Test Monte Carlo simulation uses correlation matrix."""
        layer_scores = {layer: 0.5 for layer in risk_engine.LAYER_NAMES}
        rng = np.random.default_rng(42)
        
        # Run simulation
        loss_dist = risk_engine._run_monte_carlo(layer_scores, 1000, rng)
        
        # Should produce valid distribution
        assert len(loss_dist) == 1000
        assert all(0 <= val <= 1 for val in loss_dist)


# ============================================================================
# Loss Function Tests
# ============================================================================

class TestLossFunction:
    """Test loss function calculations."""
    
    def test_loss_function_low_risk(self, risk_engine):
        """Test loss function for low risk scores."""
        # Low risk (0-1 scale, converted to 0-10 internally)
        low_risk = np.array([0.1])
        loss_pct = risk_engine._apply_loss_function(low_risk)
        
        # Low risk should have low expected loss
        assert loss_pct[0] < 0.15
    
    def test_loss_function_high_risk(self, risk_engine):
        """Test loss function for high risk scores."""
        # High risk
        high_risk = np.array([0.9])
        loss_pct = risk_engine._apply_loss_function(high_risk)
        
        # High risk should have higher expected loss
        assert loss_pct[0] > 0.4
    
    def test_loss_function_monotonic(self, risk_engine):
        """Test loss function is monotonically increasing."""
        risk_scores = np.linspace(0, 1, 100)
        losses = risk_engine._apply_loss_function(risk_scores)
        
        # Each subsequent loss should be >= previous
        for i in range(len(losses) - 1):
            assert losses[i] <= losses[i + 1] + 1e-6  # Small tolerance for numerical errors
    
    def test_loss_function_bounded(self, risk_engine):
        """Test loss function output is bounded [0, 1]."""
        risk_scores = np.linspace(0, 1, 100)
        losses = risk_engine._apply_loss_function(risk_scores)
        
        assert all(0 <= loss <= 1 for loss in losses)
    
    def test_loss_function_vectorized(self, risk_engine):
        """Test loss function works with vectorized input."""
        # Multiple risk scores
        risk_array = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        losses = risk_engine._apply_loss_function(risk_array)
        
        assert len(losses) == len(risk_array)
        assert all(0 <= loss <= 1 for loss in losses)


# ============================================================================
# Monte Carlo Simulation Tests
# ============================================================================

class TestMonteCarloSimulation:
    """Test Monte Carlo simulation."""
    
    @pytest.mark.asyncio
    async def test_simulation_produces_distribution(self, risk_engine, sample_shipment_data):
        """Test simulation produces valid loss distribution."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0,
            n_simulations=1000
        )
        
        # Should have loss distribution
        assert len(result.loss_distribution) == 1000
        assert all(0 <= val <= 1 for val in result.loss_distribution)
    
    @pytest.mark.asyncio
    async def test_var_ordering(self, risk_engine, sample_shipment_data):
        """Test VaR values are properly ordered."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        # VaR 99 should be >= VaR 95
        assert result.var_99 >= result.var_95
        
        # CVaR should be >= VaR
        assert result.cvar_95 >= result.var_95
        assert result.cvar_99 >= result.var_99
    
    @pytest.mark.asyncio
    async def test_simulation_reproducible_with_seed(
        self, mock_model_version, mock_audit, sample_shipment_data
    ):
        """Test simulation is reproducible with same seed."""
        engine1 = CalibratedRiskEngine(mock_model_version, mock_audit, seed=42)
        engine2 = CalibratedRiskEngine(mock_model_version, mock_audit, seed=42)
        
        result1 = await engine1.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        result2 = await engine2.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        # Should be identical with same seed
        assert abs(result1.overall_risk_score - result2.overall_risk_score) < 0.001
        assert abs(result1.expected_loss_pct - result2.expected_loss_pct) < 0.001
        assert abs(result1.var_95 - result2.var_95) < 0.01
        assert abs(result1.var_99 - result2.var_99) < 0.01
    
    @pytest.mark.asyncio
    async def test_higher_risk_higher_var(self, risk_engine):
        """Test higher risk scores produce higher VaR."""
        # Create low risk data
        low_risk_data = Mock(spec=UnifiedShipmentData)
        low_risk_data.origin_port = "CNSHA"
        low_risk_data.destination_port = "USLAX"
        low_risk_data.cargo_type = "TEXTILES"
        low_risk_data.cargo_value_usd = 100000.0
        low_risk_data.origin_weather = {"weather_risk_score": 0.1}
        low_risk_data.destination_weather = {"weather_risk_score": 0.1}
        low_risk_data.origin_port_conditions = {
            "risk": {"port_risk_score": 2.0},
            "efficiency": {"berth_utilization_pct": 90}
        }
        low_risk_data.destination_port_conditions = {
            "risk": {"port_risk_score": 2.0},
            "efficiency": {"berth_utilization_pct": 90}
        }
        low_risk_data.carrier_performance = {"rating": {"carrier_risk_score": 2.0}}
        low_risk_data.climate_indices = {"enso_phase": "NEUTRAL"}
        low_risk_data.overall_data_quality = DataQualityLevel.HIGH
        low_risk_data.overall_confidence = 0.9
        low_risk_data.data_warnings = []
        low_risk_data.collected_at = datetime.utcnow()
        low_risk_data.collection_hash = "low-hash"
        
        # Create high risk data
        high_risk_data = Mock(spec=UnifiedShipmentData)
        high_risk_data.origin_port = "CNSHA"
        high_risk_data.destination_port = "USLAX"
        high_risk_data.cargo_type = "FOOD_PERISHABLE"
        high_risk_data.cargo_value_usd = 100000.0
        high_risk_data.origin_weather = {"weather_risk_score": 0.9}
        high_risk_data.destination_weather = {"weather_risk_score": 0.8}
        high_risk_data.origin_port_conditions = {
            "risk": {"port_risk_score": 9.0},
            "efficiency": {"berth_utilization_pct": 50}
        }
        high_risk_data.destination_port_conditions = {
            "risk": {"port_risk_score": 8.0},
            "efficiency": {"berth_utilization_pct": 55}
        }
        high_risk_data.carrier_performance = {"rating": {"carrier_risk_score": 8.0}}
        high_risk_data.climate_indices = {"enso_phase": "STRONG_EL_NINO"}
        high_risk_data.overall_data_quality = DataQualityLevel.MEDIUM
        high_risk_data.overall_confidence = 0.6
        high_risk_data.data_warnings = ["Limited data"]
        high_risk_data.collected_at = datetime.utcnow()
        high_risk_data.collection_hash = "high-hash"
        
        low_result = await risk_engine.run_assessment(
            shipment_data=low_risk_data,
            cargo_value_usd=100000.0
        )
        
        high_result = await risk_engine.run_assessment(
            shipment_data=high_risk_data,
            cargo_value_usd=100000.0
        )
        
        # High risk should have higher VaR
        assert high_result.overall_risk_score > low_result.overall_risk_score
        assert high_result.var_95 > low_result.var_95
        assert high_result.var_99 > low_result.var_99
    
    @pytest.mark.asyncio
    async def test_percentiles_calculated(self, risk_engine, sample_shipment_data):
        """Test percentiles are calculated correctly."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        # Should have percentiles
        assert "p50" in result.percentiles
        assert "p75" in result.percentiles
        assert "p90" in result.percentiles
        assert "p95" in result.percentiles
        assert "p99" in result.percentiles
        
        # Percentiles should be ordered
        assert result.percentiles["p50"] <= result.percentiles["p75"]
        assert result.percentiles["p75"] <= result.percentiles["p90"]
        assert result.percentiles["p90"] <= result.percentiles["p95"]
        assert result.percentiles["p95"] <= result.percentiles["p99"]


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_very_high_cargo_value(self, risk_engine, sample_shipment_data):
        """Test handling of very high cargo values."""
        # $100M cargo
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=100_000_000.0
        )
        
        assert result.expected_loss_usd > 0
        assert result.var_95_usd > 0
        assert result.var_99_usd > 0
        # Financial numbers should be reasonable
        assert result.expected_loss_usd < 100_000_000.0
    
    @pytest.mark.asyncio
    async def test_minimal_cargo_value(self, risk_engine, sample_shipment_data):
        """Test handling of minimal cargo values."""
        # $1,000 cargo
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=1000.0
        )
        
        assert result.expected_loss_usd >= 0
        assert result.var_95_usd >= 0
        # Should be proportional
        assert result.expected_loss_usd < 1000.0
    
    @pytest.mark.asyncio
    async def test_all_default_scores(self, risk_engine):
        """Test handling when all layers use default scores."""
        # Create completely minimal data
        minimal_data = Mock(spec=UnifiedShipmentData)
        minimal_data.origin_port = "XXXXX"
        minimal_data.destination_port = "YYYYY"
        minimal_data.cargo_type = None
        minimal_data.cargo_value_usd = 50000.0
        minimal_data.origin_weather = None
        minimal_data.destination_weather = None
        minimal_data.origin_port_conditions = None
        minimal_data.destination_port_conditions = None
        minimal_data.carrier_performance = None
        minimal_data.climate_indices = None
        minimal_data.overall_data_quality = DataQualityLevel.LOW
        minimal_data.overall_confidence = 0.3
        minimal_data.data_warnings = ["No external data available"]
        minimal_data.collected_at = datetime.utcnow()
        minimal_data.collection_hash = "minimal-hash"
        
        result = await risk_engine.run_assessment(
            shipment_data=minimal_data,
            cargo_value_usd=50000.0
        )
        
        # Should still produce valid result
        assert 0 <= result.overall_risk_score <= 1
        assert result.expected_loss_pct >= 0
        # Data quality should reflect limitations
        assert result.data_quality == "LOW"
    
    @pytest.mark.asyncio
    async def test_extreme_weather_conditions(self, risk_engine, sample_shipment_data):
        """Test handling of extreme weather conditions."""
        # Set extreme weather
        sample_shipment_data.origin_weather = {"weather_risk_score": 1.0}
        sample_shipment_data.destination_weather = {"weather_risk_score": 1.0}
        
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        # Weather risk should be high
        assert result.layer_scores["weather_risk"] >= 0.9
        # But overall risk should still be bounded
        assert 0 <= result.overall_risk_score <= 1


# ============================================================================
# Attribution Tests
# ============================================================================

class TestRiskAttribution:
    """Test risk factor attribution."""
    
    @pytest.mark.asyncio
    async def test_attribution_sums_to_one(self, risk_engine, sample_shipment_data):
        """Test risk attribution sums to 1.0."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        # Attribution should sum to 1.0
        total_attribution = sum(result.risk_factor_attribution.values())
        assert abs(total_attribution - 1.0) < 0.001
    
    @pytest.mark.asyncio
    async def test_attribution_reflects_high_risk_factors(self, risk_engine):
        """Test attribution is higher for high-risk factors."""
        # Create data with one dominant risk factor (weather)
        data = Mock(spec=UnifiedShipmentData)
        data.origin_port = "CNSHA"
        data.destination_port = "USLAX"
        data.cargo_type = "TEXTILES"  # Low risk
        data.cargo_value_usd = 100000.0
        data.origin_weather = {"weather_risk_score": 0.95}  # Very high
        data.destination_weather = {"weather_risk_score": 0.95}
        data.origin_port_conditions = {
            "risk": {"port_risk_score": 3.0},  # Low
            "efficiency": {"berth_utilization_pct": 80}
        }
        data.destination_port_conditions = {
            "risk": {"port_risk_score": 3.0},
            "efficiency": {"berth_utilization_pct": 80}
        }
        data.carrier_performance = {"rating": {"carrier_risk_score": 3.0}}  # Low
        data.climate_indices = {"enso_phase": "NEUTRAL"}
        data.overall_data_quality = DataQualityLevel.HIGH
        data.overall_confidence = 0.85
        data.data_warnings = []
        data.collected_at = datetime.utcnow()
        data.collection_hash = "attr-hash"
        
        result = await risk_engine.run_assessment(
            shipment_data=data,
            cargo_value_usd=100000.0
        )
        
        # Weather should have significant attribution
        weather_attr = result.risk_factor_attribution.get("weather_risk", 0.0)
        assert weather_attr > 0.15  # Should be a significant contributor


# ============================================================================
# Hashing and Audit Tests
# ============================================================================

class TestHashingAndAudit:
    """Test hashing and audit functionality."""
    
    @pytest.mark.asyncio
    async def test_input_hash_created(self, risk_engine, sample_shipment_data):
        """Test input hash is created."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.input_hash is not None
        assert len(result.input_hash) == 64  # SHA256 hex
    
    @pytest.mark.asyncio
    async def test_result_hash_created(self, risk_engine, sample_shipment_data):
        """Test result hash is created."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.result_hash is not None
        assert len(result.result_hash) == 64  # SHA256 hex
    
    @pytest.mark.asyncio
    async def test_same_input_same_hash(
        self, risk_engine, sample_shipment_data
    ):
        """Test same input produces same input hash."""
        result1 = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        result2 = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result1.input_hash == result2.input_hash
    
    @pytest.mark.asyncio
    async def test_result_to_dict(self, risk_engine, sample_shipment_data):
        """Test result can be converted to dict."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "overall_risk_score" in result_dict
        assert "expected_loss_pct" in result_dict
        assert "var_95" in result_dict
        assert "var_99" in result_dict
        assert "model" in result_dict
        assert "audit" in result_dict


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_assessment_completes_quickly(self, risk_engine, sample_shipment_data):
        """Test assessment completes within time limit."""
        import time
        
        start = time.time()
        await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0,
            n_simulations=1000
        )
        elapsed = time.time() - start
        
        # Should complete within 2 seconds
        assert elapsed < 2.0
    
    @pytest.mark.asyncio
    async def test_large_simulation_count(self, risk_engine, sample_shipment_data):
        """Test engine handles large simulation counts."""
        import time
        
        start = time.time()
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0,
            n_simulations=50000
        )
        elapsed = time.time() - start
        
        # Should complete within reasonable time
        assert elapsed < 10.0
        assert len(result.loss_distribution) == 50000


# ============================================================================
# Calibration Integration Tests
# ============================================================================

class TestCalibrationIntegration:
    """Test calibration integration."""
    
    @pytest.mark.asyncio
    async def test_calibrated_model_flag(self, risk_engine, sample_shipment_data):
        """Test calibrated model flag is set correctly."""
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.model_is_calibrated == True
    
    @pytest.mark.asyncio
    async def test_uncalibrated_model_flag(self, mock_model_version, mock_audit, sample_shipment_data):
        """Test uncalibrated model flag is set correctly."""
        mock_model_version.is_calibrated = Mock(return_value=False)
        
        engine = CalibratedRiskEngine(mock_model_version, mock_audit)
        
        result = await engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.model_is_calibrated == False
    
    def test_different_loss_functions(self, mock_model_version, mock_audit):
        """Test engine supports different loss function types."""
        # Test EXPONENTIAL
        mock_model_version.get_loss_function_params = Mock(return_value={
            "function_type": "EXPONENTIAL",
            "risk_score_exponent": 2.0,
            "base_loss_rate": 0.01,
        })
        engine = CalibratedRiskEngine(mock_model_version, mock_audit)
        assert engine.loss_function is not None
        
        # Test LOGISTIC
        mock_model_version.get_loss_function_params = Mock(return_value={
            "function_type": "LOGISTIC",
            "risk_score_exponent": 5.0,
            "base_loss_rate": 0.8,
            "inflection_point": 0.5,
        })
        engine = CalibratedRiskEngine(mock_model_version, mock_audit)
        assert engine.loss_function is not None
        
        # Test POWER (default)
        mock_model_version.get_loss_function_params = Mock(return_value={
            "function_type": "POWER",
            "risk_score_exponent": 1.8,
            "multiplier": 1.0,
        })
        engine = CalibratedRiskEngine(mock_model_version, mock_audit)
        assert engine.loss_function is not None


# ============================================================================
# Data Quality Tests
# ============================================================================

class TestDataQuality:
    """Test data quality tracking."""
    
    @pytest.mark.asyncio
    async def test_high_quality_data_reflected(self, risk_engine, sample_shipment_data):
        """Test high quality data is reflected in result."""
        sample_shipment_data.overall_data_quality = DataQualityLevel.HIGH
        sample_shipment_data.overall_confidence = 0.95
        
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.data_quality == "HIGH"
        assert result.data_confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_low_quality_data_reflected(self, risk_engine, sample_shipment_data):
        """Test low quality data is reflected in result."""
        sample_shipment_data.overall_data_quality = DataQualityLevel.LOW
        sample_shipment_data.overall_confidence = 0.4
        sample_shipment_data.data_warnings = ["Missing carrier data", "Weather data unavailable"]
        
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.data_quality == "LOW"
        assert result.data_confidence < 0.5
        assert len(result.data_warnings) > 0
    
    @pytest.mark.asyncio
    async def test_data_warnings_propagated(self, risk_engine, sample_shipment_data):
        """Test data warnings are propagated to result."""
        warnings = ["Test warning 1", "Test warning 2"]
        sample_shipment_data.data_warnings = warnings
        
        result = await risk_engine.run_assessment(
            shipment_data=sample_shipment_data,
            cargo_value_usd=500000.0
        )
        
        assert result.data_warnings == warnings
