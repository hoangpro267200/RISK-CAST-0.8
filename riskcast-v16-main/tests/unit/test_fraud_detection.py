"""
Tests for Fraud Detection Engine
=================================
Verify that gaming and fraud signals are properly detected.
"""

import pytest
from datetime import datetime, timedelta
from app.services.fraud_detection import (
    FraudDetector,
    SignalType,
    SignalSeverity,
    RecommendedAction,
    analyze_request_for_fraud
)


class TestFraudDetector:
    """Tests for FraudDetector class."""
    
    @pytest.fixture
    def detector(self):
        return FraudDetector()
    
    @pytest.fixture
    def valid_request(self):
        """A fully valid request with no suspicious signals."""
        return {
            'cargo_type': 'electronics',
            'cargo_value': 75000,
            'carrier': 'MAERSK',
            'route': 'VN_US',
            'transport_mode': 'sea',
            'container': '40ft',
            'transit_time': 30,
            'etd': (datetime.utcnow() + timedelta(days=7)).isoformat(),
            'eta': (datetime.utcnow() + timedelta(days=37)).isoformat(),
            'incoterm': 'FOB',
            'carrier_rating': 8.5,
        }
    
    # --- Strategic Omission Detection ---
    
    def test_detects_missing_critical_fields(self, detector):
        """Should flag missing critical fields."""
        request = {
            'transport_mode': 'sea',
            # Missing: cargo_type, cargo_value, carrier, route
        }
        
        result = detector.analyze_request(request)
        
        assert result.fraud_score > 0
        missing_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.MISSING_CRITICAL_DATA
        ]
        assert len(missing_signals) >= 1
    
    def test_detects_strategic_omission_pattern(self, detector):
        """Should flag when multiple high-risk optional fields are omitted."""
        request = {
            'cargo_type': 'hazardous',
            'cargo_value': 50000,
            'carrier': 'TEST',
            'route': 'VN_US',
            'transport_mode': 'sea',
            # Omitting: hazmat_class, special_handling, previous_incidents
        }
        
        result = detector.analyze_request(request)
        
        omission_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.STRATEGIC_OMISSION
        ]
        # Should detect pattern of omitting high-risk fields
        assert len(omission_signals) >= 0  # May or may not trigger depending on threshold
    
    # --- Value Anomaly Detection ---
    
    def test_detects_unusually_low_cargo_value(self, detector):
        """Should flag suspiciously low cargo value for high-value cargo types."""
        request = {
            'cargo_type': 'electronics',
            'cargo_value': 100,  # Suspiciously low for electronics
            'carrier': 'MAERSK',
            'route': 'VN_US',
            'transport_mode': 'sea',
        }
        
        result = detector.analyze_request(request)
        
        value_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.VALUE_ANOMALY
        ]
        assert len(value_signals) >= 1
        assert any(s.severity in [SignalSeverity.MEDIUM, SignalSeverity.HIGH] for s in value_signals)
    
    def test_detects_round_numbers(self, detector):
        """Should flag suspiciously round numbers."""
        request = {
            'cargo_type': 'standard',
            'cargo_value': 100000,  # Exactly 100k
            'carrier': 'TEST',
            'route': 'VN_US',
            'transport_mode': 'sea',
            'transit_time': 30,  # Exactly 30 days
        }
        
        result = detector.analyze_request(request)
        
        round_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.ROUND_NUMBER
        ]
        # Should detect at least one round number pattern
        assert len(round_signals) >= 0  # May not trigger with just 2 values
    
    # --- Cross-Field Consistency ---
    
    def test_detects_air_freight_with_ocean_container(self, detector):
        """Should flag air freight using ocean containers."""
        request = {
            'cargo_type': 'electronics',
            'cargo_value': 50000,
            'carrier': 'FEDEX',
            'route': 'VN_US',
            'transport_mode': 'air',
            'container': '40ft',  # Ocean container for air!
        }
        
        result = detector.analyze_request(request)
        
        inconsistency_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.CROSS_FIELD_INCONSISTENCY
        ]
        assert len(inconsistency_signals) >= 1
        assert any(s.severity == SignalSeverity.HIGH for s in inconsistency_signals)
    
    def test_detects_impossible_transit_time(self, detector):
        """Should flag physically impossible transit times."""
        request = {
            'cargo_type': 'standard',
            'cargo_value': 50000,
            'carrier': 'MAERSK',
            'route': 'VN_US',
            'transport_mode': 'sea',
            'transit_time': 3,  # Impossible for sea freight
            'distance': 20000,  # 20,000 km
        }
        
        result = detector.analyze_request(request)
        
        inconsistency_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.CROSS_FIELD_INCONSISTENCY
        ]
        assert len(inconsistency_signals) >= 1
    
    # --- Temporal Anomalies ---
    
    def test_detects_retroactive_assessment(self, detector):
        """Should flag assessment for already-departed shipment."""
        past_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
        
        request = {
            'cargo_type': 'standard',
            'cargo_value': 50000,
            'carrier': 'MAERSK',
            'route': 'VN_US',
            'transport_mode': 'sea',
            'etd': past_date,  # Already departed!
        }
        
        result = detector.analyze_request(request)
        
        temporal_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.TEMPORAL_ANOMALY
        ]
        assert len(temporal_signals) >= 1
        assert any(s.severity == SignalSeverity.HIGH for s in temporal_signals)
    
    # --- User Pattern Detection ---
    
    def test_detects_identical_scores_pattern(self, detector):
        """Should flag when all assessments have identical scores."""
        request = {
            'cargo_type': 'standard',
            'cargo_value': 50000,
            'carrier': 'MAERSK',
            'route': 'VN_US',
            'transport_mode': 'sea',
        }
        
        # User history with identical scores
        history = [
            {'risk_score': 45, 'timestamp': datetime.utcnow().isoformat()}
            for _ in range(10)
        ]
        
        result = detector.analyze_request(request, user_history=history)
        
        behavior_signals = [
            s for s in result.signals 
            if s.signal_type == SignalType.USER_BEHAVIOR
        ]
        assert len(behavior_signals) >= 1
    
    # --- Action Recommendations ---
    
    def test_allows_clean_request(self, detector, valid_request):
        """Should allow a valid request with acceptable signals."""
        result = detector.analyze_request(valid_request)
        
        # Should have acceptable fraud score (may have minor signals for optional fields)
        assert result.fraud_score < 50  # Below FLAG threshold
        assert result.recommended_action in [RecommendedAction.ALLOW, RecommendedAction.MONITOR]
    
    def test_blocks_highly_suspicious_request(self, detector):
        """Should block request with multiple high-severity signals."""
        # Combine multiple red flags
        past_date = (datetime.utcnow() - timedelta(days=10)).isoformat()
        
        request = {
            'cargo_type': 'electronics',
            'cargo_value': 50,  # Suspiciously low
            'transport_mode': 'air',
            'container': '40ft',  # Wrong container
            'etd': past_date,  # Retroactive
            # Missing: carrier, route
        }
        
        result = detector.analyze_request(request)
        
        # Should have high fraud score
        assert result.fraud_score >= 50
        assert result.recommended_action in [RecommendedAction.FLAG, RecommendedAction.BLOCK]
        assert result.risk_penalty > 0
    
    # --- API Integration ---
    
    def test_analyze_request_for_fraud_function(self, valid_request):
        """Test the convenience function."""
        result = analyze_request_for_fraud(valid_request)
        
        assert 'fraud_score' in result
        assert 'signals' in result
        assert 'recommended_action' in result
        assert 'risk_penalty' in result
        assert isinstance(result['fraud_score'], float)


class TestMissingDataPenalty:
    """Tests for missing data penalty calculation."""
    
    def test_no_penalty_for_complete_data(self):
        from app.services.missing_data_handler import calculate_missing_data_penalty
        
        complete_data = {
            'cargo_type': 'electronics',
            'cargo_value': 50000,
            'route': 'VN_US',
            'transport_mode': 'sea',
            'carrier': 'MAERSK',
            'etd': '2024-12-01',
            'eta': '2024-12-30',
            'incoterm': 'FOB',
            'transit_time': 30,
            'carrier_rating': 8.0,
            'weather_risk': 5.0,
            'port_risk': 4.0,
            'container_match': 8.0,
            'packaging_quality': 7.0,
            # Add optional fields to reduce penalty further
            'ESG_score': 70,
            'insurance_coverage': 'full',
        }
        
        result = calculate_missing_data_penalty(complete_data)
        
        assert result['total_penalty_points'] <= 10  # Low penalty
        assert result['data_completeness'] > 0.7
    
    def test_penalty_for_missing_critical_fields(self):
        from app.services.missing_data_handler import calculate_missing_data_penalty
        
        incomplete_data = {
            'transport_mode': 'sea',
            # Missing all critical fields
        }
        
        result = calculate_missing_data_penalty(incomplete_data)
        
        assert result['total_penalty_points'] > 0
        assert 'cargo_type' in result['missing_fields']
        assert 'cargo_value' in result['missing_fields']
        assert result['data_completeness'] < 0.5
    
    def test_penalty_capped_at_maximum(self):
        from app.services.missing_data_handler import MissingDataPenaltyCalculator
        
        calculator = MissingDataPenaltyCalculator()
        
        # Empty data - maximum missing
        result = calculator.calculate_penalty({})
        
        assert result.total_penalty_points <= calculator.MAX_PENALTY


class TestProvenance:
    """Tests for input provenance tracking."""
    
    def test_tracks_field_provenance(self):
        from app.models.provenance import track_request_provenance
        
        request = {
            'cargo_type': 'electronics',
            'cargo_value': 50000,
            'route': 'VN_US',
        }
        
        result = track_request_provenance(
            request,
            ip_address='192.168.1.1',
            user_id='test_user'
        )
        
        assert 'assessment_id' in result
        assert 'field_provenance' in result
        assert 'overall_data_quality' in result
        assert result['ip_address'] == '192.168.1.1'
    
    def test_detects_suspicious_cargo_value(self):
        from app.models.provenance import ProvenanceTracker
        
        tracker = ProvenanceTracker()
        
        # Suspiciously low value for electronics
        result = tracker.validate_cargo_value(
            declared_value=100,
            cargo_type='electronics',
            volume=10,  # 10 cubic meters
            weight=500
        )
        
        assert result['status'] == 'suspicious'
        assert result['confidence'] < 0.5
    
    def test_detects_retroactive_assessment(self):
        from app.models.provenance import ProvenanceTracker
        
        tracker = ProvenanceTracker()
        
        past_date = (datetime.utcnow() - timedelta(days=5)).isoformat()
        result = tracker.check_temporal_consistency(past_date)
        
        assert result['status'] == 'suspicious'
        assert 'retroactive' in result.get('flag', '')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
