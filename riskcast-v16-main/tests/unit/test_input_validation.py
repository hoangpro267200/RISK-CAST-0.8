"""
Unit tests for Input Validation (RC-C002, RC-E001)

CRITICAL: These tests verify that invalid input is rejected with
clear error messages, preventing invalid data from reaching the engine.
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from app.api.v1.risk_routes import ShipmentModel


class TestInputValidation:
    """Test suite for input validation"""
    
    def test_positive_cargo_value_required(self):
        """
        Test that cargo_value must be positive.
        
        Reproduces: RC-C002
        """
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='ocean_fcl',
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=20.0,
                cargo_value=-1000  # Invalid: negative
            )
        
        errors = exc_info.value.errors()
        assert any('cargo_value' in str(e) and 'greater than' in str(e).lower() 
                  for e in errors)
    
    def test_positive_transit_time_required(self):
        """
        Test that transit_time must be positive.
        
        Reproduces: RC-C002
        """
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='ocean_fcl',
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=-5.0,  # Invalid: negative
                cargo_value=50000
            )
        
        errors = exc_info.value.errors()
        assert any('transit_time' in str(e) and 'greater than' in str(e).lower() 
                  for e in errors)
    
    def test_invalid_transport_mode_rejected(self):
        """
        Test that invalid transport_mode is rejected.
        
        Reproduces: RC-C002
        """
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='invalid_mode',  # Invalid
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=20.0,
                cargo_value=50000
            )
        
        errors = exc_info.value.errors()
        assert any('transport_mode' in str(e) for e in errors)
    
    def test_air_freight_cannot_use_ocean_containers(self):
        """
        Test cross-field validation: air_freight + ocean container = invalid.
        
        Reproduces: RC-E001
        """
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='air_freight',
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',  # Invalid: ocean container with air freight
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=20.0,
                cargo_value=50000
            )
        
        errors = exc_info.value.errors()
        # Should have cross-field validation error
        assert any('air_freight' in str(e).lower() and 'container' in str(e).lower() 
                  for e in errors)
    
    def test_cargo_value_too_small_rejected(self):
        """
        Test that cargo_value below minimum is rejected.
        
        Reproduces: RC-C002
        """
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='ocean_fcl',
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=20.0,
                cargo_value=50  # Too small (< 100)
            )
        
        errors = exc_info.value.errors()
        assert any('cargo_value' in str(e) and 'too small' in str(e).lower() 
                  for e in errors)
    
    def test_transit_time_too_large_rejected(self):
        """
        Test that transit_time above maximum is rejected.
        
        Reproduces: RC-C002
        """
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='ocean_fcl',
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=400.0,  # Too large (> 365)
                cargo_value=50000
            )
        
        errors = exc_info.value.errors()
        assert any('transit_time' in str(e) and 'too large' in str(e).lower() 
                  for e in errors)
    
    def test_shipment_value_must_match_cargo_value(self):
        """
        Test that shipment_value must be within reasonable range of cargo_value.
        
        Reproduces: RC-E001
        """
        # shipment_value too small (< 50% of cargo_value)
        with pytest.raises(ValidationError) as exc_info:
            ShipmentModel(
                transport_mode='ocean_fcl',
                cargo_type='electronics',
                route='vn_us',
                incoterm='FOB',
                container='40ft',
                packaging='good',
                priority='standard',
                packages=100,
                etd='2024-01-01',
                eta='2024-01-20',
                transit_time=20.0,
                cargo_value=100000,
                shipment_value=40000  # Too small (< 50% of 100000)
            )
        
        errors = exc_info.value.errors()
        assert any('shipment_value' in str(e) and 'cannot be less' in str(e).lower() 
                  for e in errors)
    
    def test_valid_input_passes_validation(self):
        """
        Test that valid input passes all validations.
        
        This is a positive test case.
        """
        shipment = ShipmentModel(
            transport_mode='ocean_fcl',
            cargo_type='electronics',
            route='vn_us',
            incoterm='FOB',
            container='40ft',
            packaging='good',
            priority='standard',
            packages=100,
            etd='2024-01-01',
            eta='2024-01-20',
            transit_time=20.0,
            cargo_value=50000
        )
        
        # Should not raise any errors
        assert shipment.cargo_value == 50000
        assert shipment.transit_time == 20.0
        assert shipment.transport_mode == 'ocean_fcl'
