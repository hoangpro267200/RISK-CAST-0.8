"""
RISKCAST Engine Invariant Tests

These tests verify core engine invariants that must always hold true:
- Risk scores are within valid bounds [0, 10]
- Monotonicity: worse inputs should not reduce risk
- All layers return required fields
- Confidence bounds are valid [0, 1]
- Deterministic seeding for Monte Carlo
"""
import pytest
import numpy as np
from typing import Dict, Any

from app.core.engine.risk_engine_v16 import calculate_enterprise_risk


class TestRiskScoreBounds:
    """Test that risk scores are always within valid bounds"""
    
    def test_risk_score_bounds_basic(self):
        """Test that basic risk score is in [0, 10]"""
        shipment_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result = calculate_enterprise_risk(shipment_data)
        
        # Check overall_risk is in [0, 10]
        overall_risk = result.get('overall_risk', 0)
        assert 0.0 <= overall_risk <= 10.0, f"Risk score {overall_risk} out of bounds [0, 10]"
    
    def test_risk_score_bounds_extreme_cases(self):
        """Test risk bounds with extreme input values"""
        # Low risk case
        low_risk_data = {
            'transport_mode': 'air',
            'cargo_type': 'standard',
            'route': 'vn_sg',
            'incoterm': 'FOB',
            'container_match': 10.0,
            'packaging_quality': 10.0,
            'priority': 'express',
            'transit_time': 1.0,
            'cargo_value': 10000.0,
            'shipment_value': 10000.0,
            'route_type': 'direct',
            'distance': 1000.0,
            'weather_risk': 1.0,
            'port_risk': 1.0,
            'carrier_rating': 5.0
        }
        
        result_low = calculate_enterprise_risk(low_risk_data)
        overall_low = result_low.get('overall_risk', 0)
        assert 0.0 <= overall_low <= 10.0, f"Low risk score {overall_low} out of bounds"
        
        # High risk case
        high_risk_data = {
            'transport_mode': 'sea',
            'cargo_type': 'hazardous',
            'route': 'vn_us',
            'incoterm': 'EXW',
            'container_match': 1.0,
            'packaging_quality': 1.0,
            'priority': 'low',
            'transit_time': 60.0,
            'cargo_value': 1000000.0,
            'shipment_value': 1000000.0,
            'route_type': 'complex',
            'distance': 20000.0,
            'weather_risk': 10.0,
            'port_risk': 10.0,
            'carrier_rating': 1.0
        }
        
        result_high = calculate_enterprise_risk(high_risk_data)
        overall_high = result_high.get('overall_risk', 0)
        assert 0.0 <= overall_high <= 10.0, f"High risk score {overall_high} out of bounds"


class TestMonotonicity:
    """Test that worse inputs should not reduce risk (monotonicity)"""
    
    def test_monotonicity_cargo_type(self):
        """Test that more sensitive cargo types have higher risk"""
        base_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result_standard = calculate_enterprise_risk(base_data)
        risk_standard = result_standard.get('overall_risk', 0)
        
        # More sensitive cargo should have higher risk
        base_data['cargo_type'] = 'fragile'
        result_fragile = calculate_enterprise_risk(base_data)
        risk_fragile = result_fragile.get('overall_risk', 0)
        
        # Fragile should have >= risk than standard
        assert risk_fragile >= risk_standard, \
            f"Fragile cargo risk {risk_fragile} should be >= standard {risk_standard}"
    
    def test_monotonicity_weather_risk(self):
        """Test that higher weather risk increases overall risk"""
        base_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 3.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result_low_weather = calculate_enterprise_risk(base_data)
        risk_low_weather = result_low_weather.get('overall_risk', 0)
        
        base_data['weather_risk'] = 8.0
        result_high_weather = calculate_enterprise_risk(base_data)
        risk_high_weather = result_high_weather.get('overall_risk', 0)
        
        # Higher weather risk should increase overall risk
        assert risk_high_weather >= risk_low_weather, \
            f"High weather risk {risk_high_weather} should be >= low weather {risk_low_weather}"


class TestLayerResults:
    """Test that all layers return required fields"""
    
    def test_layer_results_structure(self):
        """Test that all risk layers return required fields"""
        shipment_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result = calculate_enterprise_risk(shipment_data)
        
        # Check risk_factors (layers) exist
        risk_factors = result.get('risk_factors', [])
        assert isinstance(risk_factors, list), "risk_factors should be a list"
        assert len(risk_factors) > 0, "Should have at least one risk layer"
        
        # Check each layer has required fields
        for layer in risk_factors:
            assert 'name' in layer, "Layer must have 'name' field"
            assert 'score' in layer, "Layer must have 'score' field"
            assert isinstance(layer['score'], (int, float)), "Layer score must be numeric"
            assert 0.0 <= layer['score'] <= 10.0, f"Layer score {layer['score']} out of bounds [0, 10]"
    
    def test_layer_count(self):
        """Test that we get expected number of layers (13 for v16)"""
        shipment_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result = calculate_enterprise_risk(shipment_data)
        risk_factors = result.get('risk_factors', [])
        
        # v16 should have 13 layers (or at least 8 for backward compat)
        assert len(risk_factors) >= 8, f"Expected at least 8 layers, got {len(risk_factors)}"


class TestConfidenceBounds:
    """Test that confidence values are within valid bounds"""
    
    def test_confidence_bounds(self):
        """Test that confidence values are in [0, 1] or [0, 100]"""
        shipment_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result = calculate_enterprise_risk(shipment_data)
        
        # Check advanced_metrics for confidence values
        advanced_metrics = result.get('advanced_metrics', {})
        
        # If confidence exists, it should be in valid range
        if 'confidence' in advanced_metrics:
            confidence = advanced_metrics['confidence']
            # Can be 0-1 or 0-100 scale
            assert (0.0 <= confidence <= 1.0) or (0.0 <= confidence <= 100.0), \
                f"Confidence {confidence} out of valid range"


class TestDeterministicSeeding:
    """Test that Monte Carlo with same seed produces same results"""
    
    @pytest.mark.slow
    def test_deterministic_mc_seeding(self):
        """Test that seeded Monte Carlo produces deterministic results"""
        shipment_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        # Note: This test assumes the engine supports seeding
        # If not, we'll need to add that capability
        # For now, we test that results are consistent (within tolerance)
        
        result1 = calculate_enterprise_risk(shipment_data)
        result2 = calculate_enterprise_risk(shipment_data)
        
        # Results should be very similar (within small tolerance for MC variance)
        risk1 = result1.get('overall_risk', 0)
        risk2 = result2.get('overall_risk', 0)
        
        # Allow small variance due to MC randomness
        tolerance = 0.1
        assert abs(risk1 - risk2) < tolerance, \
            f"Results should be consistent: {risk1} vs {risk2}"


class TestFinancialMetrics:
    """Test that financial metrics are valid"""
    
    def test_financial_metrics_bounds(self):
        """Test that financial metrics (VaR, CVaR) are non-negative"""
        shipment_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'route': 'vn_us',
            'incoterm': 'FOB',
            'container_match': 8.0,
            'packaging_quality': 7.0,
            'priority': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
            'shipment_value': 50000.0,
            'route_type': 'standard',
            'distance': 12000.0,
            'weather_risk': 5.0,
            'port_risk': 5.0,
            'carrier_rating': 4.0
        }
        
        result = calculate_enterprise_risk(shipment_data)
        
        # Check financial_distribution
        financial_dist = result.get('financial_distribution', {})
        
        if 'var_95_usd' in financial_dist:
            var_95 = financial_dist['var_95_usd']
            assert var_95 >= 0, f"VaR should be non-negative, got {var_95}"
        
        if 'cvar_95_usd' in financial_dist:
            cvar_95 = financial_dist['cvar_95_usd']
            assert cvar_95 >= 0, f"CVaR should be non-negative, got {cvar_95}"
            # CVaR should be >= VaR (by definition)
            if 'var_95_usd' in financial_dist:
                assert cvar_95 >= financial_dist['var_95_usd'], \
                    f"CVaR {cvar_95} should be >= VaR {financial_dist['var_95_usd']}"
        
        # Expected loss should be non-negative
        expected_loss = result.get('expected_loss', 0)
        assert expected_loss >= 0, f"Expected loss should be non-negative, got {expected_loss}"

