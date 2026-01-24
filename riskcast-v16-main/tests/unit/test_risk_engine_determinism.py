"""
Unit Tests for Risk Engine Determinism
Tests for deterministic seed computation and result reproducibility
RISKCAST V3 - Modular Monolith
"""
import pytest
from app.modules.risk_engine_v3.service import RiskEngineV3
from app.modules.risk_engine_v3.schemas import (
    RiskEngineInputV3,
    RiskEngineRunConfig
)


class TestRiskEngineDeterminism:
    """Tests for risk engine determinism and reproducibility"""
    
    def test_same_seed_produces_same_result(self):
        """Same seed and input should produce identical results"""
        engine = RiskEngineV3()
        
        input_dto = RiskEngineInputV3(
            tenant_id="test-tenant",
            risk_assessment_id="assessment-1",
            input_schema_version="risk_input_v3.0",
            input_snapshot={"origin": "VN", "destination": "US", "value": 100000},
            input_hash="test-hash-123"
        )
        
        config = RiskEngineRunConfig(
            engine_version="v3.0.0",
            seed=12345,
            iterations=1000,
            seed_strategy="USER_PROVIDED",
            result_schema_version="risk_result_v3.0",
            model_version_id=None
        )
        
        result1, hash1 = engine.run(input_dto, config)
        result2, hash2 = engine.run(input_dto, config)
        
        # Results should be identical
        assert hash1 == hash2
        assert result1.overall_risk_score == result2.overall_risk_score
        assert result1.provenance.engine_version == result2.provenance.engine_version
        assert result1.provenance.seed == result2.provenance.seed
        
        # Layer contributions should be identical
        if result1.layer_contributions and result2.layer_contributions:
            assert len(result1.layer_contributions) == len(result2.layer_contributions)
            for l1, l2 in zip(result1.layer_contributions, result2.layer_contributions):
                assert l1.layer_name == l2.layer_name
                assert l1.contribution == l2.contribution
    
    def test_different_seed_produces_different_result(self):
        """Different seeds should produce different results"""
        engine = RiskEngineV3()
        
        input_dto = RiskEngineInputV3(
            tenant_id="test-tenant",
            risk_assessment_id="assessment-1",
            input_schema_version="risk_input_v3.0",
            input_snapshot={"origin": "VN", "destination": "US", "value": 100000},
            input_hash="test-hash-123"
        )
        
        config1 = RiskEngineRunConfig(
            engine_version="v3.0.0",
            seed=12345,
            iterations=1000,
            seed_strategy="USER_PROVIDED",
            result_schema_version="risk_result_v3.0",
            model_version_id=None
        )
        config2 = RiskEngineRunConfig(
            engine_version="v3.0.0",
            seed=67890,
            iterations=1000,
            seed_strategy="USER_PROVIDED",
            result_schema_version="risk_result_v3.0",
            model_version_id=None
        )
        
        result1, hash1 = engine.run(input_dto, config1)
        result2, hash2 = engine.run(input_dto, config2)
        
        # Results should be different
        assert hash1 != hash2
        assert result1.overall_risk_score != result2.overall_risk_score
    
    def test_deterministic_seed_computation(self):
        """Seed computation should be deterministic"""
        engine = RiskEngineV3()
        
        seed1 = engine.compute_deterministic_seed("hash1", None, 1000, "v3.0")
        seed2 = engine.compute_deterministic_seed("hash1", None, 1000, "v3.0")
        
        assert seed1 == seed2
        
        # Different inputs should produce different seeds
        seed3 = engine.compute_deterministic_seed("hash2", None, 1000, "v3.0")
        assert seed1 != seed3
        
        seed4 = engine.compute_deterministic_seed("hash1", "model-v1", 1000, "v3.0")
        assert seed1 != seed4
        
        seed5 = engine.compute_deterministic_seed("hash1", None, 2000, "v3.0")
        assert seed1 != seed5
    
    def test_seed_computation_includes_all_parameters(self):
        """Seed computation should include all parameters"""
        engine = RiskEngineV3()
        
        # Same parameters should produce same seed
        seed1 = engine.compute_deterministic_seed("hash1", "model-v1", 1000, "v3.0")
        seed2 = engine.compute_deterministic_seed("hash1", "model-v1", 1000, "v3.0")
        assert seed1 == seed2
        
        # Changing any parameter should change seed
        seed3 = engine.compute_deterministic_seed("hash2", "model-v1", 1000, "v3.0")
        assert seed1 != seed3
        
        seed4 = engine.compute_deterministic_seed("hash1", "model-v2", 1000, "v3.0")
        assert seed1 != seed4
        
        seed5 = engine.compute_deterministic_seed("hash1", "model-v1", 2000, "v3.0")
        assert seed1 != seed5
        
        seed6 = engine.compute_deterministic_seed("hash1", "model-v1", 1000, "v3.1")
        assert seed1 != seed6
    
    def test_result_hash_is_deterministic(self):
        """Result hash should be deterministic for same results"""
        engine = RiskEngineV3()
        
        input_dto = RiskEngineInputV3(
            tenant_id="test-tenant",
            risk_assessment_id="assessment-1",
            input_schema_version="risk_input_v3.0",
            input_snapshot={"origin": "VN", "destination": "US"},
            input_hash="test-hash"
        )
        
        config = RiskEngineRunConfig(seed=12345, iterations=1000, model_version_id=None)
        
        result1, hash1 = engine.run(input_dto, config)
        result2, hash2 = engine.run(input_dto, config)
        
        # Hashes should be identical
        assert hash1 == hash2
        
        # Hash should be 64 characters (SHA256 hex)
        assert len(hash1) == 64
    
    def test_canonicalize_result_stable(self):
        """Result canonicalization should produce stable output"""
        engine = RiskEngineV3()
        
        # Create a result with floating point values
        result_data = {
            "overall_risk_score": 0.123456789,
            "layer_contributions": [
                {"layer_name": "layer1", "contribution": 0.5},
                {"layer_name": "layer2", "contribution": 0.3}
            ]
        }
        
        canonical1 = engine._canonicalize_result(result_data)
        canonical2 = engine._canonicalize_result(result_data)
        
        assert canonical1 == canonical2
    
    def test_canonicalize_result_rounds_floats(self):
        """Result canonicalization should round floats for stability"""
        engine = RiskEngineV3()
        
        result_data1 = {
            "overall_risk_score": 0.123456789012345,
            "value": 100.0
        }
        
        result_data2 = {
            "overall_risk_score": 0.123456789012346,  # Slightly different
            "value": 100.0
        }
        
        canonical1 = engine._canonicalize_result(result_data1)
        canonical2 = engine._canonicalize_result(result_data2)
        
        # After rounding, they should be the same
        assert canonical1 == canonical2
    
    def test_engine_version_consistency(self):
        """Engine version should be consistent across runs"""
        engine1 = RiskEngineV3()
        engine2 = RiskEngineV3()
        
        assert engine1.engine_version == engine2.engine_version
