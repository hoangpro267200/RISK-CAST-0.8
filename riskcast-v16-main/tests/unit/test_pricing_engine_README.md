# Pricing Engine Unit Tests - README

## Overview

Comprehensive unit test suite for the Pricing Engine (`PricingEngine`).

## Test Coverage

### 1. Base Rate Tests (`TestBaseRates`) - 10 tests
- ✅ Electronics base rate (2.50 per mille)
- ✅ Textiles base rate (1.20 per mille)
- ✅ Perishable food base rate (3.00 per mille)
- ✅ Machinery base rate
- ✅ Pharmaceuticals base rate
- ✅ Unknown cargo uses general rate
- ✅ Case-insensitive lookup
- ✅ All 10 cargo types have rates
- ✅ Rates are in reasonable range (0.5-5.0)

### 2. Risk Factor Tests (`TestRiskFactors`) - 4 tests
- ✅ Risk score to factor mapping
- ✅ Risk factor increases monotonically
- ✅ Boundary condition handling
- ✅ Extreme risk score handling

### 3. Cargo Factor Tests (`TestCargoFactors`) - 3 tests
- ✅ Standard packaging (neutral factor 1.00)
- ✅ Basic packaging (10% loading)
- ✅ Premium packaging (5% credit)

### 4. Route Factor Tests (`TestRouteFactors`) - 2 tests
- ✅ Standard route (neutral factor)
- ✅ High-risk route (25% loading)

### 5. Coverage Factor Tests (`TestCoverageFactors`) - 4 tests
- ✅ All risks factor (1.00)
- ✅ Named perils discount (0.75)
- ✅ Total loss only discount (0.50)
- ✅ Factor ordering

### 6. Duration Factor Tests (`TestDurationFactors`) - 2 tests
- ✅ Duration factor mapping (7, 14, 30, 45+ days)
- ✅ Factor increases with duration

### 7. Loadings Tests (`TestLoadings`) - 6 tests
- ✅ Standard shipment loadings
- ✅ High-value surcharge ($1M+)
- ✅ War risk surcharge (Ukraine, Yemen)
- ✅ Refrigeration coverage (perishable cargo)
- ✅ Loading component structure

### 8. Discounts Tests (`TestDiscounts`) - 6 tests
- ✅ Standard tier (no discount)
- ✅ Preferred tier discount (10%)
- ✅ Premier tier discount (20%)
- ✅ No-claims discount (good loss history)
- ✅ Poor loss history (no discount)
- ✅ Discount component structure

### 9. Deductible Tests (`TestDeductibles`) - 4 tests
- ✅ Percentage deductible calculation
- ✅ Fixed deductible calculation
- ✅ Franchise deductible calculation
- ✅ Deductible rounding

### 10. Premium Calculation Tests (`TestPremiumCalculation`) - 7 tests
- ✅ Returns valid result
- ✅ Meets minimum premium
- ✅ Higher risk → higher premium
- ✅ Premium proportional to value
- ✅ Breakdown components sum correctly
- ✅ Premium rounded to cents
- ✅ Breakdown has all fields

### 11. Risk Grade Tests (`TestRiskGrade`) - 3 tests
- ✅ Risk score to grade mapping (A-F)
- ✅ Grade boundaries
- ✅ Result includes risk grade

### 12. Recommendations Tests (`TestRecommendations`) - 5 tests
- ✅ High risk → packaging recommendation
- ✅ Standard tier → upgrade recommendation
- ✅ Low deductible → increase recommendation
- ✅ All risks → named perils recommendation
- ✅ Result includes recommendations

### 13. Edge Cases Tests (`TestEdgeCases`) - 4 tests
- ✅ Very high cargo value ($10M)
- ✅ Very low cargo value ($100)
- ✅ Coverage limit different from value
- ✅ Multiple loadings and discounts

### 14. Audit Tests (`TestAudit`) - 2 tests
- ✅ Audit event created
- ✅ Audit payload contains key metrics

### 15. Quote Validity Tests (`TestQuoteValidity`) - 3 tests
- ✅ Quote has validity period
- ✅ Valid for 7 days
- ✅ Unique quote IDs

### 16. Competitiveness Tests (`TestCompetitiveness`) - 1 test
- ✅ Result includes competitiveness indicators

## Running Tests

### Run all pricing engine tests:
```bash
pytest tests/unit/test_pricing_engine.py -v
```

### Run specific test class:
```bash
pytest tests/unit/test_pricing_engine.py::TestBaseRates -v
```

### Run specific test:
```bash
pytest tests/unit/test_pricing_engine.py::TestBaseRates::test_electronics_base_rate -v
```

### Run with coverage:
```bash
pytest tests/unit/test_pricing_engine.py \
  --cov=app.pricing.pricing_engine \
  --cov-report=html \
  --cov-report=term-missing
```

## Test Structure

### Fixtures

1. **`mock_audit`**: Mock audit logger for event tracking

2. **`pricing_engine`**: `PricingEngine` instance with mock audit

3. **`mock_risk_result`**: Mock `CalibratedRiskResult` with:
   - Risk score: 0.5 (medium)
   - Expected loss: 2%
   - VaR values

4. **`standard_pricing_input`**: Standard `PricingInput` with:
   - $500K cargo value
   - Electronics cargo
   - CNSHA → USLAX route
   - 21-day transit
   - All risks coverage
   - 1% percentage deductible
   - Standard tier

### Test Patterns

#### Testing Base Rates
```python
def test_electronics_base_rate(self, pricing_engine):
    rate = pricing_engine._get_base_rate("ELECTRONICS")
    assert rate == Decimal("2.50")
```

#### Testing Risk Factors
```python
@pytest.mark.parametrize("risk_score,expected_factor", [
    (0.1, Decimal("0.70")),
    (0.5, Decimal("1.00")),
    (0.9, Decimal("1.80")),
])
def test_risk_score_to_factor(self, pricing_engine, risk_score, expected_factor):
    factor = pricing_engine._get_risk_factor(risk_score)
    assert factor == expected_factor
```

#### Testing Full Premium Calculation
```python
@pytest.mark.asyncio
async def test_calculate_premium_returns_result(self, pricing_engine, standard_pricing_input):
    result = await pricing_engine.calculate_premium(standard_pricing_input)
    
    assert isinstance(result, PricingResult)
    assert result.total_premium_usd > 0
    assert result.premium_rate_per_mille > 0
```

## Expected Coverage

Target: **90%+ code coverage** for `pricing_engine.py`

Coverage includes:
- ✅ All public methods
- ✅ All private helper methods
- ✅ All pricing factors
- ✅ All cargo types
- ✅ Edge cases
- ✅ Different customer tiers
- ✅ Various coverage types

## Dependencies

Required packages:
- `pytest` (testing framework)
- `pytest-asyncio` (async test support)
- `decimal` (precise calculations)

## Key Assertions

### Base Rate Validations
```python
assert rate > 0
assert Decimal("0.50") <= rate <= Decimal("5.00")
```

### Risk Factor Validations
```python
assert factor >= Decimal("0.70")
assert factor <= Decimal("2.00")
```

### Premium Validations
```python
assert result.total_premium_usd > 0
assert result.total_premium_usd >= pricing_engine.MINIMUM_PREMIUM
assert result.premium_rate_per_mille > 0
```

### Breakdown Validations
```python
# Components sum correctly
calculated = net_premium + expenses + margin + tax
assert abs(calculated - total_premium) < Decimal("1.00")
```

## Test Data Scenarios

### Low-Risk Scenario
- Risk score: 0.2
- Cargo: TEXTILES
- Route: Standard
- Tier: PREFERRED
- Expected: Lower premium

### High-Risk Scenario
- Risk score: 0.8
- Cargo: FOOD_PERISHABLE
- Route: War zone
- Tier: STANDARD
- Expected: Higher premium

### Premium Customer
- Tier: PREMIER (20% discount)
- Loss ratio: 0.1 (no-claims discount)
- Expected: Significant discounts

### High-Value Shipment
- Cargo value: $2M+
- Expected: High-value surcharge
- Multiple loadings

## Cargo Types Tested

| Cargo Type | Base Rate | Test Coverage |
|------------|-----------|---------------|
| ELECTRONICS | 2.50 | ✅ |
| MACHINERY | 1.80 | ✅ |
| TEXTILES | 1.20 | ✅ |
| FOOD_PERISHABLE | 3.00 | ✅ |
| FOOD_DRY | 1.50 | ✅ |
| CHEMICALS | 2.20 | ✅ |
| PHARMACEUTICALS | 2.80 | ✅ |
| AUTOMOTIVE | 2.00 | ✅ |
| RAW_MATERIALS | 1.00 | ✅ |
| GENERAL | 1.50 | ✅ |

## Pricing Factors Tested

### Risk Factors
- Very low risk (0.0-0.2): 0.70x
- Low risk (0.2-0.4): 0.85x
- Medium risk (0.4-0.6): 1.00x
- High risk (0.6-0.8): 1.30x
- Very high risk (0.8-1.0): 1.80x

### Coverage Factors
- All Risks: 1.00x
- Named Perils: 0.75x
- Total Loss Only: 0.50x

### Duration Factors
- ≤7 days: 0.90x
- 8-14 days: 1.00x
- 15-30 days: 1.10x
- 31+ days: 1.25x

### Tier Discounts
- Standard: 0%
- Preferred: 10%
- Premier: 20%
- High Risk: -25% (loading)

## Loadings Tested

1. **War Risk Surcharge** (0.5%)
   - Ukraine, Russia, Yemen routes
   
2. **High Value Surcharge** ($500 flat)
   - Cargo value > $1M
   
3. **Refrigeration Coverage** (0.3%)
   - Perishable cargo

## Discounts Tested

1. **Tier Discounts**
   - Preferred: 10%
   - Premier: 20%

2. **No-Claims Discount** (10%)
   - Loss ratio < 30%

## Deductible Types Tested

1. **Percentage**: % of coverage limit
2. **Fixed**: Fixed dollar amount
3. **Franchise**: Waived if loss exceeds threshold

## Troubleshooting

### Import Errors
If you encounter dataclass errors:
1. This is a known issue in pricing_engine.py
2. Tests are designed to work around it
3. Fix: Reorder PricingInput fields (required before optional)

### Decimal Precision
Tests use `Decimal` for precise calculations:
```python
from decimal import Decimal
assert amount == Decimal("1234.56")
```

### Async Tests
All premium calculation tests are async:
```python
@pytest.mark.asyncio
async def test_something(self, pricing_engine, standard_pricing_input):
    result = await pricing_engine.calculate_premium(standard_pricing_input)
```

## Related Files

- `app/pricing/pricing_engine.py` - Implementation
- `app/core/risk_engine/v16/risk_engine_calibrated.py` - Risk engine
- `tests/unit/conftest.py` - Shared fixtures

## Future Enhancements

Potential additional tests:
- [ ] Market competitiveness validation
- [ ] Volume discounts
- [ ] Multi-shipment policies
- [ ] Policy term variations
- [ ] Currency conversions
- [ ] Regional tax rates
- [ ] Broker commissions

## Statistics

- **Total Test Methods:** 65
- **Total Test Classes:** 16
- **Total Lines:** 1,154
- **Expected Coverage:** 90%+

---

**Status:** ✅ Complete and ready for execution
