"""
Tests for Scientific Calibration Framework
============================================
Verify calibration quality and uncertainty quantification.
"""

import pytest
import numpy as np
from scripts.calibration.calibrator_v2 import RiskScoreCalibrator, CalibrationMetrics


class TestRiskScoreCalibrator:
    """Tests for RiskScoreCalibrator class."""
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic calibration data."""
        np.random.seed(42)
        n_samples = 500
        
        # Generate raw scores with some noise
        raw_scores = np.random.uniform(0, 100, n_samples)
        
        # Generate outcomes correlated with scores (higher score = higher probability)
        # P(outcome=1) = sigmoid(score/50 - 1)
        probs = 1 / (1 + np.exp(-(raw_scores - 50) / 15))
        outcomes = (np.random.uniform(0, 1, n_samples) < probs).astype(int)
        
        return raw_scores, outcomes
    
    def test_isotonic_calibration(self, synthetic_data):
        """Test isotonic regression calibration."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='isotonic')
        calibrator.fit(raw_scores, outcomes)
        
        assert calibrator.is_fitted
        assert calibrator.validation_metrics is not None
        assert calibrator.validation_metrics.brier_score >= 0
        assert calibrator.validation_metrics.brier_score <= 1
    
    def test_platt_calibration(self, synthetic_data):
        """Test Platt scaling calibration."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='platt')
        calibrator.fit(raw_scores, outcomes)
        
        assert calibrator.is_fitted
        assert calibrator.validation_metrics is not None
    
    def test_bayesian_calibration(self, synthetic_data):
        """Test Bayesian calibration."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='bayesian')
        calibrator.fit(raw_scores, outcomes)
        
        assert calibrator.is_fitted
    
    def test_transform_returns_probabilities(self, synthetic_data):
        """Transformed scores should be valid probabilities."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='isotonic')
        calibrator.fit(raw_scores, outcomes)
        
        # Transform new scores
        new_scores = np.array([0, 25, 50, 75, 100])
        calibrated = calibrator.transform(new_scores)
        
        # All values should be between 0 and 1
        assert np.all(calibrated >= 0)
        assert np.all(calibrated <= 1)
        
        # Should be monotonically increasing (higher risk = higher probability)
        assert np.all(np.diff(calibrated) >= -0.1)  # Allow small violations
    
    def test_calibration_improves_brier_score(self, synthetic_data):
        """Calibration should not worsen Brier score significantly."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='isotonic')
        calibrator.fit(raw_scores, outcomes)
        
        # Brier score should be reasonable
        brier = calibrator.validation_metrics.brier_score
        assert brier < 0.3  # Should be better than random
    
    def test_invalid_method_raises_error(self):
        """Should raise error for unknown calibration method."""
        with pytest.raises(ValueError):
            RiskScoreCalibrator(method='unknown')
    
    def test_transform_before_fit_raises_error(self):
        """Should raise error if transform called before fit."""
        calibrator = RiskScoreCalibrator(method='isotonic')
        
        with pytest.raises(RuntimeError):
            calibrator.transform(np.array([50]))
    
    def test_is_acceptable_method(self, synthetic_data):
        """Test acceptability check against thresholds."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='isotonic')
        calibrator.fit(raw_scores, outcomes)
        
        is_acceptable, issues = calibrator.is_acceptable()
        
        assert isinstance(is_acceptable, bool)
        assert isinstance(issues, list)
    
    def test_get_report(self, synthetic_data):
        """Test report generation."""
        raw_scores, outcomes = synthetic_data
        
        calibrator = RiskScoreCalibrator(method='isotonic')
        calibrator.fit(raw_scores, outcomes)
        
        report = calibrator.get_report()
        
        assert 'method' in report
        assert 'metrics' in report
        assert 'is_acceptable' in report
        assert report['method'] == 'isotonic'


class TestSensitivityAnalysis:
    """Tests for sensitivity analysis."""
    
    def test_tornado_analysis(self):
        """Test tornado diagram generation."""
        from app.services.sensitivity_analysis import SensitivityAnalyzer
        
        # Create analyzer with mock calculator
        def mock_calculate(shipment):
            # Simple linear model for testing
            score = (
                shipment.get('cargo_value', 50000) / 10000 +
                shipment.get('transit_time', 30) / 5 +
                shipment.get('weather_risk', 5) * 2
            )
            return {'overall_risk': min(score, 10)}
        
        analyzer = SensitivityAnalyzer(risk_calculator_func=mock_calculate)
        
        baseline = {
            'cargo_value': 50000,
            'transit_time': 30,
            'weather_risk': 5,
        }
        
        result = analyzer.run_tornado_analysis(
            baseline_shipment=baseline,
            parameters=['cargo_value', 'transit_time', 'weather_risk'],
            variation_pct=0.2
        )
        
        assert result.baseline_score >= 0
        assert len(result.sensitivities) == 3
        assert result.most_sensitive is not None
    
    def test_sensitivity_ordering(self):
        """Sensitivities should be ordered by magnitude."""
        from app.services.sensitivity_analysis import SensitivityAnalyzer
        
        def mock_calculate(shipment):
            # weather_risk has highest coefficient for sensitivity at ±20% variation
            # cargo_value: 50000 * 0.2 / 100000 = 0.1 change
            # transit_time: 30 * 0.2 / 100 = 0.06 change
            # weather_risk: 5 * 0.2 * 10 = 10 change (highest!)
            score = (
                shipment.get('cargo_value', 50000) / 100000 +
                shipment.get('transit_time', 30) / 100 +
                shipment.get('weather_risk', 5) * 10
            )
            return {'overall_risk': min(score, 10)}
        
        analyzer = SensitivityAnalyzer(risk_calculator_func=mock_calculate)
        
        baseline = {
            'cargo_value': 50000,
            'transit_time': 30,
            'weather_risk': 5,
        }
        
        result = analyzer.run_tornado_analysis(
            baseline_shipment=baseline,
            parameters=['cargo_value', 'transit_time', 'weather_risk']
        )
        
        # Results should be ordered by sensitivity (highest first)
        assert len(result.sensitivities) == 3
        # Most sensitive should have highest sensitivity value
        assert result.sensitivities[0].sensitivity >= result.sensitivities[1].sensitivity
        assert result.sensitivities[1].sensitivity >= result.sensitivities[2].sensitivity


class TestUncertaintyQuantification:
    """Tests for uncertainty quantification."""
    
    def test_bootstrap_confidence_interval(self):
        """Test bootstrap CI calculation."""
        from app.models.uncertainty import UncertaintyQuantifier
        
        np.random.seed(42)
        
        # Simulate MC results
        mc_results = np.random.normal(50, 10, 1000)
        
        interval = UncertaintyQuantifier.bootstrap_confidence_interval(
            risk_score=50,
            monte_carlo_results=mc_results,
            confidence_level=0.95
        )
        
        assert interval.point_estimate == 50
        assert interval.lower_bound < 50
        assert interval.upper_bound > 50
        assert interval.confidence_level == 0.95
        assert interval.interval_width > 0
    
    def test_bayesian_credible_interval(self):
        """Test Bayesian credible interval."""
        from app.models.uncertainty import UncertaintyQuantifier
        
        interval = UncertaintyQuantifier.bayesian_credible_interval(
            risk_score=60,
            prior_mean=50,
            prior_std=20,
            confidence_level=0.95
        )
        
        assert interval.lower_bound < interval.upper_bound
        assert interval.confidence_level == 0.95  # Uses confidence_level attribute
        # Posterior should be pulled toward prior
        assert 50 < interval.point_estimate < 60
    
    def test_reliability_grading(self):
        """Test reliability grade assignment."""
        from app.models.uncertainty import UncertaintyQuantifier
        
        assert UncertaintyQuantifier.grade_reliability(5) == 'A'
        assert UncertaintyQuantifier.grade_reliability(15) == 'B'
        assert UncertaintyQuantifier.grade_reliability(25) == 'C'
        assert UncertaintyQuantifier.grade_reliability(40) == 'D'
        assert UncertaintyQuantifier.grade_reliability(60) == 'F'
    
    def test_full_uncertainty_analysis(self):
        """Test complete uncertainty analysis."""
        from app.models.uncertainty import UncertaintyQuantifier
        
        np.random.seed(42)
        mc_results = np.random.normal(65, 8, 1000)
        
        report = UncertaintyQuantifier.full_uncertainty_analysis(
            risk_score=65,
            monte_carlo_results=mc_results,
            layer_contributions={'delay': 0.5, 'damage': 0.3, 'cost': 0.2},
            layer_variances={'delay': 16, 'damage': 9, 'cost': 4}
        )
        
        assert report.risk_score == 65
        assert report.interval is not None
        assert report.reliability_grade in ['A', 'B', 'C', 'D', 'F']
        assert report.interpretation != ''
    
    def test_insufficient_mc_samples_warning(self):
        """Should handle insufficient MC samples gracefully."""
        from app.models.uncertainty import UncertaintyQuantifier
        
        # Only 5 samples - too few
        mc_results = np.array([50, 52, 48, 51, 49])
        
        interval = UncertaintyQuantifier.bootstrap_confidence_interval(
            risk_score=50,
            monte_carlo_results=mc_results
        )
        
        # Should return wide interval indicating high uncertainty
        assert interval.interval_width > 30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
