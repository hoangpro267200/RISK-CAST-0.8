# Risk Engine Unit Tests

## Overview

Comprehensive unit test suite for the Calibrated Risk Engine (`CalibratedRiskEngine`).

## Test Coverage

### 1. Basic Functionality Tests (`TestRiskEngineBasics`)
- ✅ Engine initialization
- ✅ Layer weights sum to 1.0
- ✅ Correlation matrix validation (positive definite, diagonal = 1.0)
- ✅ Assessment returns valid results
- ✅ Audit trail creation

### 2. Layer Calculation Tests (`TestLayerCalculations`)
- ✅ Route risk calculation (from port data)
- ✅ Weather risk calculation (from weather data)
- ✅ Cargo risk by type (ELECTRONICS, TEXTILES, FOOD_PERISHABLE, etc.)
- ✅ Transport risk from carrier performance
- ✅ Transport risk fallback (no carrier data)
- ✅ Seasonal risk varies with ENSO phase
- ✅ All layer scores bounded [0, 1]
- ✅ Missing data uses defaults

### 3. Weight Application Tests (`TestWeightApplication`)
- ✅ Weighted scores sum to overall risk
- ✅ Weighted scores = layer scores × weights
- ✅ Zero weight effectively excludes layer

### 4. Correlation Matrix Tests (`TestCorrelationMatrix`)
- ✅ Matrix is symmetric
- ✅ Correlation values in valid range [-1, 1]
- ✅ Monte Carlo uses correlation matrix

### 5. Loss Function Tests (`TestLossFunction`)
- ✅ Low risk → low loss
- ✅ High risk → high loss
- ✅ Monotonically increasing
- ✅ Output bounded [0, 1]
- ✅ Vectorized operation

### 6. Monte Carlo Simulation Tests (`TestMonteCarloSimulation`)
- ✅ Produces valid loss distribution
- ✅ VaR ordering (VaR99 ≥ VaR95)
- ✅ CVaR ordering (CVaR ≥ VaR)
- ✅ Reproducible with same seed
- ✅ Higher risk → higher VaR
- ✅ Percentiles calculated correctly

### 7. Edge Cases Tests (`TestEdgeCases`)
- ✅ Very high cargo values ($100M)
- ✅ Minimal cargo values ($1,000)
- ✅ All default scores (no external data)
- ✅ Extreme weather conditions

### 8. Attribution Tests (`TestRiskAttribution`)
- ✅ Attribution sums to 1.0
- ✅ Attribution reflects high-risk factors

### 9. Hashing and Audit Tests (`TestHashingAndAudit`)
- ✅ Input hash created (SHA256)
- ✅ Result hash created (SHA256)
- ✅ Same input → same hash
- ✅ Result serialization to dict

### 10. Performance Tests (`TestPerformance`)
- ✅ Assessment completes quickly (<2s for 1K simulations)
- ✅ Large simulation counts (50K simulations <10s)

### 11. Calibration Integration Tests (`TestCalibrationIntegration`)
- ✅ Calibrated model flag
- ✅ Uncalibrated model flag
- ✅ Different loss function types (POWER, EXPONENTIAL, LOGISTIC)

### 12. Data Quality Tests (`TestDataQuality`)
- ✅ High quality data reflected in results
- ✅ Low quality data reflected in results
- ✅ Data warnings propagated

## Running Tests

### Run all risk engine tests:
```bash
pytest tests/unit/test_risk_engine.py -v
```

### Run specific test class:
```bash
pytest tests/unit/test_risk_engine.py::TestRiskEngineBasics -v
```

### Run specific test:
```bash
pytest tests/unit/test_risk_engine.py::TestRiskEngineBasics::test_engine_initialization -v
```

### Run with coverage:
```bash
pytest tests/unit/test_risk_engine.py --cov=app.core.risk_engine.v16.risk_engine_calibrated --cov-report=html
```

### Run performance tests only:
```bash
pytest tests/unit/test_risk_engine.py::TestPerformance -v
```

## Test Structure

### Fixtures

1. **`mock_model_version`**: Mock `RiskModelVersion` with calibrated parameters
   - 13 layer weights (sum to 1.0)
   - Correlation matrix
   - Loss function parameters (POWER type)
   - Calibration status

2. **`mock_audit`**: Mock audit logger

3. **`sample_shipment_data`**: Mock `UnifiedShipmentData` with realistic values
   - Port data (CNSHA → USLAX)
   - Weather data
   - Carrier data (MAEU)
   - Climate data
   - Data quality tracking

4. **`risk_engine`**: `CalibratedRiskEngine` instance with mocks

### Test Patterns

#### Testing Layer Calculations
```python
def test_route_risk_calculation(self, risk_engine, sample_shipment_data):
    layer_scores = risk_engine._calculate_layer_scores(sample_shipment_data)
    assert "route_risk" in layer_scores
    assert 0 <= layer_scores["route_risk"] <= 1
```

#### Testing Monte Carlo
```python
@pytest.mark.asyncio
async def test_simulation_reproducible_with_seed(self, ...):
    engine1 = CalibratedRiskEngine(mock_model_version, mock_audit, seed=42)
    engine2 = CalibratedRiskEngine(mock_model_version, mock_audit, seed=42)
    result1 = await engine1.run_assessment(...)
    result2 = await engine2.run_assessment(...)
    assert abs(result1.overall_risk_score - result2.overall_risk_score) < 0.001
```

#### Testing Edge Cases
```python
@pytest.mark.asyncio
async def test_very_high_cargo_value(self, risk_engine, sample_shipment_data):
    result = await risk_engine.run_assessment(
        shipment_data=sample_shipment_data,
        cargo_value_usd=100_000_000.0  # $100M
    )
    assert result.expected_loss_usd < 100_000_000.0
```

## Expected Coverage

Target: **90%+ code coverage** for `risk_engine_calibrated.py`

Coverage includes:
- ✅ All public methods
- ✅ All private helper methods
- ✅ All loss function types
- ✅ Edge cases and error conditions
- ✅ Different data quality scenarios
- ✅ Various cargo types and risk profiles

## Dependencies

Required packages:
- `pytest` (testing framework)
- `pytest-asyncio` (async test support)
- `numpy` (numerical operations)
- `scipy` (statistical functions)

## Key Assertions

### Risk Score Validations
```python
assert 0 <= result.overall_risk_score <= 1
assert result.expected_loss_pct >= 0
assert result.var_99 >= result.var_95
assert result.cvar_95 >= result.var_95
```

### Weight Validations
```python
assert abs(sum(weights.values()) - 1.0) < 0.001
```

### Correlation Matrix Validations
```python
assert np.allclose(matrix, matrix.T)  # Symmetric
assert np.allclose(np.diag(matrix), 1.0)  # Diagonal = 1
```

### Monotonicity
```python
for i in range(len(losses) - 1):
    assert losses[i] <= losses[i + 1]
```

## Test Data Scenarios

### Low Risk Scenario
- Cargo: TEXTILES
- Weather: Low risk (0.1)
- Ports: Low congestion, high efficiency
- Carrier: High reliability (score 2.0/10)
- Climate: NEUTRAL

### High Risk Scenario
- Cargo: FOOD_PERISHABLE
- Weather: High risk (0.9)
- Ports: High congestion, low efficiency
- Carrier: Low reliability (score 8.0/10)
- Climate: STRONG_EL_NINO

### Minimal Data Scenario
- All external data sources unavailable
- Uses default scores
- Low data quality
- Limited confidence

## Troubleshooting

### Import Errors
If you encounter import errors, ensure:
1. You're in the project root directory
2. Python path includes the project root
3. All dependencies are installed

### Async Test Issues
If async tests fail:
1. Ensure `pytest-asyncio` is installed
2. Use `@pytest.mark.asyncio` decorator
3. Use `await` for async calls

### Numerical Precision
Some tests use tolerance for floating-point comparisons:
```python
assert abs(value1 - value2) < 0.001  # Tolerance for FP errors
```

## Future Enhancements

Potential additional tests:
- [ ] Stress testing with 1M+ simulations
- [ ] Boundary value analysis for all inputs
- [ ] Fuzzing with random data
- [ ] Integration with actual database models
- [ ] Performance regression tests
- [ ] Memory profiling tests

## Related Files

- `app/core/risk_engine/v16/risk_engine_calibrated.py` - Implementation
- `app/modules/model_versioning/models.py` - Model definitions
- `app/services/unified_data_service.py` - Data service
- `tests/unit/conftest.py` - Shared fixtures

## Contact

For questions or issues with these tests, refer to the main project documentation.
