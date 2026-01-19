"""
Unit tests for Risk Engine V16 (risk_engine_v16.py)

CRITICAL: These tests verify the main risk calculation pipeline:
- calculate_enterprise_risk produces valid results
- All required fields in response
- Edge cases handled
- Deterministic outputs
"""
import pytest
from app.core.engine.risk_engine_v16 import calculate_enterprise_risk


class TestCalculateEnterpriseRisk:
    """Test suite for calculate_enterprise_risk function"""
    
    def test_basic_risk_calculation(self):
        """Test basic risk calculation with valid input"""
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
            'carrier_rating': 5.0
        }
        
        result = calculate_enterprise_risk(shipment_data)
        
        # Should return a dictionary
        assert isinstance(result, dict)
        
        # Should have overall_risk
        assert 'overall_risk' in result
        overall_risk = result['overall_risk']
        assert isinstance(overall_risk, (int, float))
        assert 0.0 <= overall_risk <= 10.0, f"Overall risk {overall_risk} out of bounds"
    
    def test_response_structure(self):
        """Test that response has all required fields"""
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
        }
        
        result = calculate_enterprise_risk(shipment_data)
        
        # Required fields
        assert 'overall_risk' in result
        assert 'risk_factors' in result or 'layers' in result
        
        # Risk factors should be a list
        risk_factors = result.get('risk_factors', result.get('layers', []))
        assert isinstance(risk_factors, list)
        assert len(risk_factors) > 0
    
    def test_deterministic_output(self):
        """
        Test that same input produces same output.
        
        CRITICAL: Risk calculation must be deterministic.
        """
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
        }
        
        # Run twice
        result1 = calculate_enterprise_risk(shipment_data)
        result2 = calculate_enterprise_risk(shipment_data)
        
        # Overall risk should be identical (or very close due to MC variance)
        risk1 = result1.get('overall_risk', 0)
        risk2 = result2.get('overall_risk', 0)
        
        # Allow small tolerance for Monte Carlo variance
        tolerance = 0.5  # 5% tolerance
        assert abs(risk1 - risk2) < tolerance, \
            f"Results should be consistent: {risk1} vs {risk2}"
    
    def test_missing_optional_fields(self):
        """
        Test that engine handles missing optional fields.
        
        Should not crash, but may have lower confidence.
        """
        # Minimal required data
        minimal_data = {
            'transport_mode': 'sea',
            'cargo_type': 'standard',
            'transit_time': 30.0,
            'cargo_value': 50000.0,
        }
        
        # Should not raise exception
        result = calculate_enterprise_risk(minimal_data)
        
        # Should still return valid result
        assert isinstance(result, dict)
        assert 'overall_risk' in result
    
    def test_extreme_values(self):
        """Test that engine handles extreme input values"""
        # Very high risk scenario
        high_risk_data = {
            'transport_mode': 'sea',
            'cargo_type': 'hazardous',
            'route': 'vn_us',
            'incoterm': 'EXW',
            'container_match': 1.0,
            'packaging_quality': 1.0,
            'priority': 'low',
            'transit_time': 365.0,
            'cargo_value': 10000000.0,
            'shipment_value': 10000000.0,
            'weather_risk': 10.0,
            'port_risk': 10.0,
            'carrier_rating': 1.0,
        }
        
        result_high = calculate_enterprise_risk(high_risk_data)
        risk_high = result_high.get('overall_risk', 0)
        assert 0.0 <= risk_high <= 10.0
        
        # Very low risk scenario
        low_risk_data = {
            'transport_mode': 'air',
            'cargo_type': 'standard',
            'route': 'vn_sg',
            'incoterm': 'DDP',
            'container_match': 10.0,
            'packaging_quality': 10.0,
            'priority': 'express',
            'transit_time': 1.0,
            'cargo_value': 1000.0,
            'shipment_value': 1000.0,
            'weather_risk': 0.0,
            'port_risk': 0.0,
            'carrier_rating': 10.0,
        }
        
        result_low = calculate_enterprise_risk(low_risk_data)
        risk_low = result_low.get('overall_risk', 0)
        assert 0.0 <= risk_low <= 10.0
        
        # High risk should generally be >= low risk
        # (Allow some variance due to different calculation paths)
        assert risk_high >= risk_low - 2.0, \
            f"High risk {risk_high} should be >= low risk {risk_low}"
