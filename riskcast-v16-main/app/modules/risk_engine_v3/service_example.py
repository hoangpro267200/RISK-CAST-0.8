"""
Risk Engine V3 Service Usage Examples

This file demonstrates how to use RiskEngineV3.
"""
from app.modules.risk_engine_v3.service import RiskEngineV3
from app.modules.risk_engine_v3.schemas import (
    RiskEngineInputV3,
    RiskEngineRunConfig
)
from app.modules.risk_runs.models import SeedStrategy


# Example 1: Create engine and compute deterministic seed
async def compute_seed_example():
    """Compute deterministic seed from input parameters"""
    engine = RiskEngineV3()
    
    input_hash = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
    model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
    iterations = 10000
    result_schema_version = "risk_result_v3.0"
    
    seed = engine.compute_deterministic_seed(
        input_hash=input_hash,
        model_version_id=model_version_id,
        iterations=iterations,
        result_schema_version=result_schema_version
    )
    
    print(f"Deterministic seed: {seed}")
    return seed


# Example 2: Execute risk engine
async def execute_engine_example():
    """Execute risk engine with deterministic settings"""
    engine = RiskEngineV3()
    
    # Create input DTO
    input_dto = RiskEngineInputV3(
        tenant_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        risk_assessment_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
        input_schema_version="risk_input_v3.0",
        input_snapshot={
            "origin": {"port_code": "VNHPH", "country": "VN"},
            "destination": {"port_code": "USLAX", "country": "US"},
            "cargo": {"type": "electronics", "value_usd": 100000}
        },
        input_hash="a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
        corridor_id="VN-US-WEST",
        product_type="standard"
    )
    
    # Compute deterministic seed
    seed = engine.compute_deterministic_seed(
        input_hash=input_dto.input_hash,
        model_version_id=None,
        iterations=10000,
        result_schema_version=engine.RESULT_SCHEMA_VERSION
    )
    
    # Create run config
    config = RiskEngineRunConfig(
        engine_version=engine.engine_version,
        model_version_id=None,
        model_payload=None,
        result_schema_version=engine.RESULT_SCHEMA_VERSION,
        seed=seed,
        seed_strategy=SeedStrategy.DETERMINISTIC_INPUT_HASH.value,
        iterations=10000,
        options={"scenario_set_id": "scenario-001"}
    )
    
    # Execute engine
    result, result_hash = await engine.run(input_dto, config)
    
    print(f"Overall risk score: {result.overall_risk_score}")
    print(f"Result hash: {result_hash}")
    print(f"Provenance: {result.provenance}")
    
    return result, result_hash


# Example 3: Verify reproducibility
async def verify_reproducibility_example():
    """Verify that same inputs produce same results"""
    engine = RiskEngineV3()
    
    input_dto = RiskEngineInputV3(
        tenant_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        risk_assessment_id="01ARZ3NDEKTSV4RRFFQ69G5FAW",
        input_schema_version="risk_input_v3.0",
        input_snapshot={"test": "data"},
        input_hash="fixed_hash_for_testing"
    )
    
    seed = engine.compute_deterministic_seed(
        input_hash=input_dto.input_hash,
        model_version_id=None,
        iterations=10000,
        result_schema_version=engine.RESULT_SCHEMA_VERSION
    )
    
    config = RiskEngineRunConfig(
        engine_version=engine.engine_version,
        model_version_id=None,
        model_payload=None,
        result_schema_version=engine.RESULT_SCHEMA_VERSION,
        seed=seed,
        seed_strategy=SeedStrategy.DETERMINISTIC_INPUT_HASH.value,
        iterations=10000
    )
    
    # Run twice with same inputs
    result1, hash1 = await engine.run(input_dto, config)
    result2, hash2 = await engine.run(input_dto, config)
    
    # Verify results are identical
    assert hash1 == hash2, "Results should be identical for same inputs"
    assert result1.overall_risk_score == result2.overall_risk_score
    
    print("✅ Reproducibility verified!")
    return result1, result2
