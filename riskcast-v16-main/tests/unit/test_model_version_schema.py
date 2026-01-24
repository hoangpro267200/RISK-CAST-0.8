"""
Tests for model version schema validation.
"""
import pytest
from pydantic import ValidationError
from app.modules.model_versioning.schemas import (
    BaseWeights, TailParameters, LossTransformParams, MonteCarloDefaults,
    ModelVersionCreateRequest
)


class TestBaseWeights:
    """Tests for BaseWeights schema"""
    
    def test_valid_weights(self):
        """Test that valid weights pass validation"""
        weights = BaseWeights(
            route_risk=0.25,
            cargo_risk=0.20,
            carrier_risk=0.20,
            timing_risk=0.15,
            weather_risk=0.10,
            geopolitical_risk=0.10
        )
        weights.validate_sum()  # Should not raise
        assert weights.route_risk == 0.25
    
    def test_weights_must_sum_to_one(self):
        """Test that weights must sum to 1.0"""
        weights = BaseWeights(
            route_risk=0.5,
            cargo_risk=0.5,
            carrier_risk=0.5,
            timing_risk=0.5,
            weather_risk=0.5,
            geopolitical_risk=0.5
        )
        with pytest.raises(ValueError, match="must sum to 1.0"):
            weights.validate_sum()
    
    def test_weights_cannot_be_negative(self):
        """Test that weights cannot be negative"""
        with pytest.raises(ValidationError):
            BaseWeights(
                route_risk=-0.1,
                cargo_risk=0.20,
                carrier_risk=0.20,
                timing_risk=0.15,
                weather_risk=0.10,
                geopolitical_risk=0.10
            )
    
    def test_weights_cannot_exceed_one(self):
        """Test that individual weights cannot exceed 1.0"""
        with pytest.raises(ValidationError):
            BaseWeights(
                route_risk=1.5,
                cargo_risk=0.20,
                carrier_risk=0.20,
                timing_risk=0.15,
                weather_risk=0.10,
                geopolitical_risk=0.10
            )
    
    def test_weights_accept_float_values(self):
        """Test that weights accept float values"""
        weights = BaseWeights(
            route_risk=0.25,
            cargo_risk=0.20,
            carrier_risk=0.20,
            timing_risk=0.15,
            weather_risk=0.10,
            geopolitical_risk=0.10
        )
        assert isinstance(weights.route_risk, float)


class TestTailParameters:
    """Tests for TailParameters schema"""
    
    def test_valid_tail_params(self):
        """Test that valid tail parameters pass validation"""
        params = TailParameters(
            degrees_of_freedom=4,
            tail_shock_probability=0.05,
            extreme_loss_multiplier=2.5
        )
        assert params.degrees_of_freedom == 4
        assert params.tail_shock_probability == 0.05
        assert params.extreme_loss_multiplier == 2.5
    
    def test_dof_must_be_positive(self):
        """Test that degrees_of_freedom must be > 0"""
        with pytest.raises(ValidationError):
            TailParameters(
                degrees_of_freedom=0,
                tail_shock_probability=0.05,
                extreme_loss_multiplier=2.5
            )
    
    def test_tail_shock_probability_range(self):
        """Test that tail_shock_probability must be between 0 and 1"""
        with pytest.raises(ValidationError):
            TailParameters(
                degrees_of_freedom=4,
                tail_shock_probability=1.5,
                extreme_loss_multiplier=2.5
            )
    
    def test_extreme_loss_multiplier_minimum(self):
        """Test that extreme_loss_multiplier must be >= 1"""
        with pytest.raises(ValidationError):
            TailParameters(
                degrees_of_freedom=4,
                tail_shock_probability=0.05,
                extreme_loss_multiplier=0.5
            )


class TestLossTransformParams:
    """Tests for LossTransformParams schema"""
    
    def test_valid_loss_transform_params(self):
        """Test that valid loss transform parameters pass validation"""
        params = LossTransformParams(
            base_loss_rate=0.02,
            risk_score_exponent=1.5,
            min_loss_pct=0.001,
            max_loss_pct=0.15
        )
        assert params.base_loss_rate == 0.02
        assert params.risk_score_exponent == 1.5
    
    def test_max_loss_must_be_greater_than_min_loss(self):
        """Test that max_loss_pct must be >= min_loss_pct"""
        with pytest.raises(ValidationError):
            LossTransformParams(
                base_loss_rate=0.02,
                risk_score_exponent=1.5,
                min_loss_pct=0.15,
                max_loss_pct=0.10  # Less than min_loss_pct
            )
    
    def test_base_loss_rate_range(self):
        """Test that base_loss_rate must be between 0 and 1"""
        with pytest.raises(ValidationError):
            LossTransformParams(
                base_loss_rate=1.5,
                risk_score_exponent=1.5,
                min_loss_pct=0.001,
                max_loss_pct=0.15
            )
    
    def test_risk_score_exponent_must_be_positive(self):
        """Test that risk_score_exponent must be > 0"""
        with pytest.raises(ValidationError):
            LossTransformParams(
                base_loss_rate=0.02,
                risk_score_exponent=0,
                min_loss_pct=0.001,
                max_loss_pct=0.15
            )


class TestMonteCarloDefaults:
    """Tests for MonteCarloDefaults schema"""
    
    def test_valid_mc_defaults(self):
        """Test that valid Monte Carlo defaults pass validation"""
        defaults = MonteCarloDefaults(
            default_iterations=10000,
            confidence_levels=[0.95, 0.99]
        )
        assert defaults.default_iterations == 10000
        assert defaults.confidence_levels == [0.95, 0.99]
    
    def test_default_iterations_range(self):
        """Test that default_iterations must be between 100 and 1000000"""
        with pytest.raises(ValidationError):
            MonteCarloDefaults(
                default_iterations=50,  # Too low
                confidence_levels=[0.95, 0.99]
            )
        
        with pytest.raises(ValidationError):
            MonteCarloDefaults(
                default_iterations=2000000,  # Too high
                confidence_levels=[0.95, 0.99]
            )
    
    def test_confidence_levels_validation(self):
        """Test that confidence levels must be between 0 and 1"""
        with pytest.raises(ValueError, match="must be between 0 and 1"):
            MonteCarloDefaults(
                default_iterations=10000,
                confidence_levels=[0.95, 1.5]  # Invalid confidence level
            )
    
    def test_confidence_levels_sorted(self):
        """Test that confidence levels are sorted"""
        defaults = MonteCarloDefaults(
            default_iterations=10000,
            confidence_levels=[0.99, 0.95]  # Should be sorted
        )
        assert defaults.confidence_levels == [0.95, 0.99]


class TestModelVersionCreateRequest:
    """Tests for ModelVersionCreateRequest schema"""
    
    def test_valid_model_version_create(self):
        """Test that valid model version creation request passes validation"""
        request = ModelVersionCreateRequest(
            name="test_model",
            version="1.0.0",
            description="Test model",
            base_weights=BaseWeights(
                route_risk=0.25,
                cargo_risk=0.20,
                carrier_risk=0.20,
                timing_risk=0.15,
                weather_risk=0.10,
                geopolitical_risk=0.10
            ),
            correlation_matrix={
                "route_cargo": 0.3,
                "weather_timing": 0.5
            },
            tail_parameters=TailParameters(
                degrees_of_freedom=4,
                tail_shock_probability=0.05,
                extreme_loss_multiplier=2.5
            ),
            interaction_multipliers={
                "high_value_perishable": 1.3
            },
            loss_transform_params=LossTransformParams(
                base_loss_rate=0.02,
                risk_score_exponent=1.5,
                min_loss_pct=0.001,
                max_loss_pct=0.15
            )
        )
        assert request.name == "test_model"
        assert request.version == "1.0.0"
    
    def test_correlation_matrix_validation(self):
        """Test that correlation matrix values must be between -1 and 1"""
        with pytest.raises(ValueError, match="must be between -1 and 1"):
            ModelVersionCreateRequest(
                name="test_model",
                version="1.0.0",
                base_weights=BaseWeights(
                    route_risk=0.25,
                    cargo_risk=0.20,
                    carrier_risk=0.20,
                    timing_risk=0.15,
                    weather_risk=0.10,
                    geopolitical_risk=0.10
                ),
                correlation_matrix={
                    "route_cargo": 1.5  # Invalid correlation value
                },
                tail_parameters=TailParameters(
                    degrees_of_freedom=4,
                    tail_shock_probability=0.05,
                    extreme_loss_multiplier=2.5
                ),
                interaction_multipliers={},
                loss_transform_params=LossTransformParams(
                    base_loss_rate=0.02,
                    risk_score_exponent=1.5,
                    min_loss_pct=0.001,
                    max_loss_pct=0.15
                )
            )
    
    def test_base_weights_validation_in_request(self):
        """Test that base weights are validated in the request"""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            ModelVersionCreateRequest(
                name="test_model",
                version="1.0.0",
                base_weights=BaseWeights(
                    route_risk=0.5,
                    cargo_risk=0.5,
                    carrier_risk=0.5,
                    timing_risk=0.5,
                    weather_risk=0.5,
                    geopolitical_risk=0.5
                ),
                correlation_matrix={},
                tail_parameters=TailParameters(
                    degrees_of_freedom=4,
                    tail_shock_probability=0.05,
                    extreme_loss_multiplier=2.5
                ),
                interaction_multipliers={},
                loss_transform_params=LossTransformParams(
                    base_loss_rate=0.02,
                    risk_score_exponent=1.5,
                    min_loss_pct=0.001,
                    max_loss_pct=0.15
                )
            )
    
    def test_base_weights_from_dict(self):
        """Test that base_weights can be created from dict"""
        request = ModelVersionCreateRequest(
            name="test_model",
            version="1.0.0",
            base_weights={
                "route_risk": 0.25,
                "cargo_risk": 0.20,
                "carrier_risk": 0.20,
                "timing_risk": 0.15,
                "weather_risk": 0.10,
                "geopolitical_risk": 0.10
            },
            correlation_matrix={},
            tail_parameters=TailParameters(
                degrees_of_freedom=4,
                tail_shock_probability=0.05,
                extreme_loss_multiplier=2.5
            ),
            interaction_multipliers={},
            loss_transform_params=LossTransformParams(
                base_loss_rate=0.02,
                risk_score_exponent=1.5,
                min_loss_pct=0.001,
                max_loss_pct=0.15
            )
        )
        assert isinstance(request.base_weights, BaseWeights)
        assert request.base_weights.route_risk == 0.25
