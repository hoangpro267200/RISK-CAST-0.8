"""
Tests for Enterprise Features
==============================
Test persona adapter, scenario engine, audit trail, and privacy services.
"""

import pytest
from datetime import datetime, timedelta
from app.services.persona_adapter import PersonaAdapter, UserPersona
from app.services.scenario_engine import ScenarioEngine, compare_shipment_scenarios
from app.models.audit_trail import AuditEntry, AuditTrailStore, AuditService
from app.core.model_versioning import ModelVersionRegistry, ModelVersion, VersionStatus
from app.services.data_privacy import DataPrivacyService


class TestPersonaAdapter:
    """Tests for multi-persona risk formatting."""
    
    @pytest.fixture
    def sample_risk_data(self):
        """Sample risk data for testing."""
        return {
            'risk_score': 65,
            'risk_level': 'high',
            'expected_loss': 12500,
            'confidence': 0.85,
            'cargo_value': 100000,
            'risk_factors': [
                {'name': 'weather', 'score': 7.5, 'contribution': 25},
                {'name': 'carrier', 'score': 6.0, 'contribution': 20},
                {'name': 'route', 'score': 5.5, 'contribution': 15}
            ],
            'monte_carlo_results': {
                'var_95': 25000,
                'cvar_95': 35000,
                'max_loss': 50000
            }
        }
    
    def test_executive_format(self, sample_risk_data):
        """Test executive persona formatting."""
        result = PersonaAdapter.format_for_executive(sample_risk_data)
        
        assert result['persona'] == 'executive'
        assert 'summary' in result
        assert 'key_drivers' in result
        assert 'action_items' in result
        
        # Executive should have limited KPIs
        assert len(result['key_drivers']) <= 3
        assert len(result['action_items']) <= 3
    
    def test_analyst_format(self, sample_risk_data):
        """Test analyst persona formatting."""
        result = PersonaAdapter.format_for_analyst(sample_risk_data)
        
        assert result['persona'] == 'analyst'
        assert 'detailed_breakdown' in result
        assert 'methodology' in result
        assert 'sensitivity_analysis' in result
    
    def test_operations_format(self, sample_risk_data):
        """Test operations persona formatting."""
        result = PersonaAdapter.format_for_operations(sample_risk_data)
        
        assert result['persona'] == 'operations'
        assert 'risk_alert' in result
        assert 'mitigation_steps' in result
        assert 'timeline_impact' in result
        assert 'monitoring_plan' in result
    
    def test_insurance_format(self, sample_risk_data):
        """Test insurance persona formatting."""
        result = PersonaAdapter.format_for_insurance(sample_risk_data)
        
        assert result['persona'] == 'insurance'
        assert 'underwriting_summary' in result
        assert 'loss_metrics' in result
        assert 'actuarial_data' in result
        assert 'policy_recommendations' in result
    
    def test_premium_calculation(self, sample_risk_data):
        """Test insurance premium calculation."""
        result = PersonaAdapter.format_for_insurance(sample_risk_data)
        
        premium_data = result['underwriting_summary']['suggested_premium_adjustment']
        
        assert 'base_premium_rate' in premium_data
        assert 'risk_multiplier' in premium_data
        assert 'suggested_premium_usd' in premium_data
        assert premium_data['suggested_premium_usd'] > 0
    
    def test_risk_class_determination(self, sample_risk_data):
        """Test insurance risk class determination."""
        result = PersonaAdapter.format_for_insurance(sample_risk_data)
        
        risk_class = result['underwriting_summary']['risk_class']
        
        # Score of 65 should be Class C or D
        assert 'Class' in risk_class


class TestScenarioEngine:
    """Tests for what-if scenario analysis."""
    
    @pytest.fixture
    def baseline_shipment(self):
        """Baseline shipment for testing."""
        return {
            'transport_mode': 'sea',
            'cargo_type': 'electronics',
            'cargo_value': 100000,
            'carrier_rating': 5.0,
            'transit_time': 30,
            'route': 'vn_us'
        }
    
    def test_scenario_comparison(self, baseline_shipment):
        """Test basic scenario comparison."""
        scenarios = [
            {
                'name': 'Better Carrier',
                'description': 'Use higher-rated carrier',
                'changes': {'carrier_rating': 9.0},
                'estimated_cost': 500
            }
        ]
        
        result = compare_shipment_scenarios(
            baseline=baseline_shipment,
            scenarios=scenarios
        )
        
        assert 'baseline' in result
        assert 'scenarios' in result
        assert 'recommendation' in result
        assert len(result['scenarios']) >= 1
    
    def test_preset_scenarios(self, baseline_shipment):
        """Test including preset scenarios."""
        result = compare_shipment_scenarios(
            baseline=baseline_shipment,
            scenarios=[],
            include_presets=True
        )
        
        # Should have preset scenarios
        assert len(result['scenarios']) > 0
    
    def test_scenario_ranking(self, baseline_shipment):
        """Test scenarios are ranked by improvement."""
        scenarios = [
            {'name': 'Minor', 'changes': {'carrier_rating': 6.0}, 'estimated_cost': 100},
            {'name': 'Major', 'changes': {'carrier_rating': 10.0}, 'estimated_cost': 500}
        ]
        
        result = compare_shipment_scenarios(
            baseline=baseline_shipment,
            scenarios=scenarios
        )
        
        # Should be ordered by improvement
        if len(result['scenarios']) >= 2:
            # First should have better improvement than last
            first = result['scenarios'][0]
            last = result['scenarios'][-1]
            assert first['improvement_pct'] >= last['improvement_pct']
    
    def test_get_presets(self):
        """Test getting available presets."""
        from app.services.scenario_engine import get_available_presets
        
        presets = get_available_presets()
        
        assert 'alternative_carrier' in presets
        assert 'air_freight' in presets


class TestAuditTrail:
    """Tests for audit trail functionality."""
    
    def test_create_audit_entry(self):
        """Test creating an audit entry."""
        entry = AuditEntry(
            user_id='test_user',
            endpoint='/api/v2/risk/analyze',
            request_payload={'cargo_value': 50000},
            response_payload={'risk_score': 45},
            risk_score=45.0
        )
        
        assert entry.audit_id is not None
        assert entry.request_hash != ''
        assert entry.response_hash != ''
    
    def test_chain_hash_computation(self):
        """Test blockchain-style chain hash."""
        entry1 = AuditEntry(
            request_payload={'test': 1},
            response_payload={'result': 1}
        )
        entry1.compute_chain_hash()
        
        entry2 = AuditEntry(
            request_payload={'test': 2},
            response_payload={'result': 2}
        )
        entry2.compute_chain_hash(entry1.chain_hash)
        
        # Chain should be linked
        assert entry2.previous_hash == entry1.chain_hash
        assert entry2.chain_hash != entry1.chain_hash
    
    def test_audit_store_append(self):
        """Test appending to audit store."""
        store = AuditTrailStore()
        
        entry = AuditEntry(
            user_id='test_user',
            request_payload={'test': True},
            response_payload={'result': True}
        )
        
        chain_hash = store.append(entry)
        
        assert chain_hash == entry.chain_hash
        assert store.get_by_id(entry.audit_id) is not None
    
    def test_audit_chain_verification(self):
        """Test chain integrity verification."""
        store = AuditTrailStore()
        
        # Add some entries
        for i in range(5):
            entry = AuditEntry(
                request_payload={'test': i},
                response_payload={'result': i}
            )
            store.append(entry)
        
        # Verify integrity
        is_valid, broken_links = store.verify_chain_integrity()
        
        assert is_valid == True
        assert len(broken_links) == 0
    
    def test_audit_query_by_user(self):
        """Test querying audit by user."""
        store = AuditTrailStore()
        
        # Add entries for different users
        for i in range(3):
            entry = AuditEntry(
                user_id='user_a',
                request_payload={'test': i},
                response_payload={'result': i}
            )
            store.append(entry)
        
        entry_b = AuditEntry(
            user_id='user_b',
            request_payload={'test': 99},
            response_payload={'result': 99}
        )
        store.append(entry_b)
        
        # Query for user_a
        results = store.get_by_user('user_a')
        
        assert len(results) == 3
        for r in results:
            assert r.user_id == 'user_a'


class TestModelVersioning:
    """Tests for model version registry."""
    
    def test_get_current_version(self):
        """Test getting current version."""
        from app.core.model_versioning import get_current_model_version
        
        version = get_current_model_version()
        
        assert 'version' in version
        assert 'release_date' in version
        assert 'status' in version
    
    def test_list_versions(self):
        """Test listing versions."""
        from app.core.model_versioning import list_model_versions
        
        versions = list_model_versions(include_deprecated=True)
        
        assert len(versions) >= 2  # At least v1.0.0 and v2.0.0
    
    def test_version_comparison(self):
        """Test comparing versions."""
        registry = ModelVersionRegistry()
        
        comparison = registry.compare_versions('1.0.0', '2.0.0')
        
        assert 'versions' in comparison
        assert 'component_changes' in comparison


class TestDataPrivacy:
    """Tests for GDPR/CCPA compliance."""
    
    def test_export_user_data(self):
        """Test data export."""
        from app.services.data_privacy import export_user_data
        
        result = export_user_data('test_user')
        
        assert 'data_subject' in result
        assert 'data_categories' in result
        assert 'processing_activities' in result
        assert 'your_rights' in result
    
    def test_processing_register(self):
        """Test GDPR Article 30 register."""
        from app.services.data_privacy import get_processing_register
        
        register = get_processing_register()
        
        assert len(register) > 0
        assert 'activity_name' in register[0]
        assert 'legal_basis' in register[0]
    
    def test_record_consent(self):
        """Test consent recording."""
        from app.services.data_privacy import record_consent
        
        result = record_consent('test_user', 'marketing', True)
        
        assert 'consent_id' in result
        assert result['granted'] == True
    
    def test_delete_user_data(self):
        """Test data deletion/anonymization."""
        from app.services.data_privacy import delete_user_data
        
        result = delete_user_data('test_user', 'User request')
        
        assert 'actions_taken' in result
        assert 'retention_note' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
