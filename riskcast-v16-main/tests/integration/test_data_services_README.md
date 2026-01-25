# External Data Services Integration Tests - README

## Overview

Comprehensive integration tests for external data services including weather, ports, carriers, climate data, and the unified data service.

## Test Coverage

### 1. Weather Data Tests (`TestWeatherDataService`) - 5 tests
- ✅ Fetch weather success
- ✅ API error handling (fallback)
- ✅ Route weather fetching
- ✅ Data caching
- ✅ Storm detection

### 2. Port Data Tests (`TestPortDataService`) - 5 tests
- ✅ Fetch port data success
- ✅ Unknown port handling (fallback)
- ✅ Congestion calculation
- ✅ Multiple ports fetching
- ✅ Efficiency metrics

### 3. Carrier Data Tests (`TestCarrierDataService`) - 4 tests
- ✅ Fetch carrier data success
- ✅ Unknown carrier handling (defaults)
- ✅ Route-specific performance
- ✅ Claims history inclusion

### 4. Climate Data Tests (`TestClimateDataService`) - 3 tests
- ✅ Seasonal patterns
- ✅ ENSO phase detection
- ✅ Route climate assessment

### 5. Data Quality Gateway Tests (`TestDataQualityGateway`) - 5 tests
- ✅ Complete data validation
- ✅ Partial data validation
- ✅ Stale data detection
- ✅ Quality threshold enforcement
- ✅ Multiple source aggregation

### 6. Unified Data Service Tests (`TestUnifiedDataService`) - 3 tests
- ✅ Complete data collection
- ✅ Partial failure handling
- ✅ Audit trail creation

### 7. Fallback Behavior Tests (`TestFallbackBehavior`) - 4 tests
- ✅ Weather fallback to historical
- ✅ Carrier fallback to industry average
- ✅ Port fallback to defaults
- ✅ Graceful degradation (all services fail)

### 8. Caching Behavior Tests (`TestCachingBehavior`) - 3 tests
- ✅ Weather data caching
- ✅ Port data caching
- ✅ Cache invalidation on date change

### 9. Error Handling Tests (`TestErrorHandling`) - 3 tests
- ✅ Timeout handling
- ✅ Invalid response handling
- ✅ Rate limit handling

## Running Tests

### Run all data service tests:
```bash
pytest tests/integration/test_data_services.py -v
```

### Run specific test class:
```bash
pytest tests/integration/test_data_services.py::TestWeatherDataService -v
```

### Run specific test:
```bash
pytest tests/integration/test_data_services.py::TestWeatherDataService::test_fetch_weather_success -v
```

### Run with coverage:
```bash
pytest tests/integration/test_data_services.py \
  --cov=app.integrations \
  --cov=app.services.unified_data_service \
  --cov-report=html \
  --cov-report=term-missing
```

## Test Structure

### Fixtures

1. **`mock_audit`**: Mock audit logger

2. **`weather_service`**: Weather service instance
   - Tomorrow.io integration
   - Forecast fetching
   - Route weather analysis

3. **`port_service`**: Port service instance
   - MarineTraffic integration
   - Port conditions
   - Congestion data

4. **`carrier_service`**: Carrier service instance
   - Project44 integration
   - Carrier performance
   - Route-specific data

5. **`climate_service`**: Climate service instance
   - NOAA integration
   - Seasonal patterns
   - ENSO indices

6. **`unified_service`**: Unified data service
   - Orchestrates all services
   - Quality tracking
   - Fallback handling

7. **`quality_gateway`**: Data quality gateway
   - Quality validation
   - Threshold enforcement
   - Source aggregation

## Test Patterns

### Testing External API Call
```python
@pytest.mark.asyncio
async def test_fetch_weather_success(self, weather_service):
    with patch.object(weather_service.client, 'get_forecast') as mock_forecast:
        mock_forecast.return_value = {
            "temperature": 25.5,
            "wind_speed": 15.2,
            "storm_probability": 0.20
        }
        
        result = await weather_service.get_weather_forecast(
            lat=31.23, lon=121.47, date=date.today()
        )
        
        assert result is not None
        assert result["temperature"] == 25.5
```

### Testing Fallback Behavior
```python
@pytest.mark.asyncio
async def test_fetch_weather_api_error(self, weather_service):
    with patch.object(weather_service.client, 'get_forecast') as mock_forecast:
        mock_forecast.side_effect = Exception("API Error")
        
        result = await weather_service.get_weather_forecast(...)
        
        # Should return fallback data
        assert result is not None
        assert result["data_quality"] == "FALLBACK"
```

### Testing Unified Service
```python
@pytest.mark.asyncio
async def test_collect_shipment_data_success(self, unified_service):
    with patch.multiple(unified_service,
        weather_service=AsyncMock(),
        port_service=AsyncMock(),
        carrier_service=AsyncMock()
    ):
        # Setup mocks...
        
        result = await unified_service.collect_shipment_data(...)
        
        assert isinstance(result, UnifiedShipmentData)
        assert result.overall_confidence > 0.7
```

## Data Sources Tested

### Weather Service (Tomorrow.io)
- Point weather forecasts
- Route weather analysis
- Storm probability
- Wind/wave conditions
- Historical fallback

### Port Service (MarineTraffic)
- Port congestion levels
- Vessel counts
- Delay times
- Efficiency metrics
- Default fallback

### Carrier Service (Project44)
- Carrier reliability
- On-time performance
- Claims ratio
- Route-specific data
- Industry average fallback

### Climate Service (NOAA)
- Seasonal patterns
- ENSO indices
- Storm frequency
- Historical data

## Data Quality Levels

```python
HIGH     # All data available, fresh, complete
MEDIUM   # Most data available, some gaps
LOW      # Significant gaps, stale data
FALLBACK # Using defaults/historical
```

## Quality Metrics

### Completeness Score
- 1.0: All data sources available
- 0.7-0.9: Most sources available
- 0.4-0.6: Some sources missing
- <0.4: Major gaps

### Freshness Score
- 1.0: Data <1 hour old
- 0.8-0.9: Data 1-6 hours old
- 0.5-0.7: Data 6-24 hours old
- <0.5: Data >24 hours old

### Confidence Score
- Weighted combination of:
  - Completeness (40%)
  - Freshness (30%)
  - Source quality (30%)

## Expected Coverage

Target: **85%+ code coverage** for:
- `app/integrations/weather/`
- `app/integrations/ports/`
- `app/integrations/carriers/`
- `app/integrations/climate/`
- `app/services/unified_data_service.py`
- `app/core/data_quality/gateway.py`

## Dependencies

Required packages:
- `pytest` (testing framework)
- `pytest-asyncio` (async test support)
- `httpx` (async HTTP client)
- `unittest.mock` (mocking)

## Mocking Strategy

### Why Mock External APIs?
1. **Reliability**: Tests don't depend on external services
2. **Speed**: No network latency
3. **Cost**: No API charges during testing
4. **Control**: Test edge cases and failures

### What Gets Mocked?
```python
# External API clients
weather_service.client.get_forecast
port_service.client.get_port_info
carrier_service.client.get_carrier_info
climate_service.client.get_climate_data

# Not mocked (tested for real):
- Data aggregation logic
- Quality calculation
- Fallback selection
- Cache logic
```

## Test Scenarios

### Happy Path
```python
All services succeed
→ HIGH quality data
→ Confidence > 0.9
→ No warnings
```

### Partial Failure
```python
Weather succeeds
Port fails → fallback
Carrier succeeds
→ MEDIUM quality data
→ Confidence 0.5-0.7
→ Warnings present
```

### Complete Failure
```python
All services fail
→ FALLBACK quality
→ Confidence < 0.5
→ Multiple warnings
→ Uses defaults
```

### Stale Data
```python
Data >24 hours old
→ Freshness < 0.5
→ Quality degraded
→ Warning issued
```

## Key Assertions

### Weather Data
```python
assert result["temperature"] is not None
assert 0 <= result["storm_probability"] <= 1
assert result["wind_speed"] >= 0
assert result["data_quality"] in ["HIGH", "MEDIUM", "LOW", "FALLBACK"]
```

### Port Data
```python
assert result["port_code"] == "CNSHA"
assert 0 <= result["congestion_level"] <= 1
assert result["avg_delay_hours"] >= 0
```

### Carrier Data
```python
assert 0 <= result["reliability_score"] <= 1
assert 0 <= result["on_time_percentage"] <= 1
assert result["claims_ratio"] >= 0
```

### Unified Data
```python
assert isinstance(result, UnifiedShipmentData)
assert result.overall_confidence >= 0
assert result.overall_confidence <= 1
assert len(result.data_warnings) >= 0
```

## Fallback Values

### Weather Fallback
```python
temperature: Regional average
storm_probability: Historical average
wind_speed: Historical average
data_quality: FALLBACK
```

### Port Fallback
```python
congestion_level: 0.5 (medium)
avg_delay_hours: 12 (typical)
data_quality: FALLBACK
```

### Carrier Fallback
```python
reliability_score: 0.75 (industry avg)
on_time_percentage: 0.75
claims_ratio: 0.03
data_quality: FALLBACK
```

## Troubleshooting

### Import Errors
If you encounter module errors:
1. Ensure all integration modules exist
2. Check `app/integrations/` structure
3. Verify service factory functions

### Mock Issues
If mocks don't work:
1. Check patch target paths
2. Verify async/sync consistency
3. Use `AsyncMock` for async methods

### Data Quality
If quality validation fails:
1. Check DataQualityLevel enum
2. Verify quality calculation logic
3. Review threshold settings

## Related Files

- `app/integrations/weather/weather_service.py` - Weather integration
- `app/integrations/ports/port_service.py` - Port integration
- `app/integrations/carriers/carrier_service.py` - Carrier integration
- `app/integrations/climate/climate_service.py` - Climate integration
- `app/services/unified_data_service.py` - Unified orchestration
- `app/core/data_quality/gateway.py` - Quality validation

## Future Enhancements

Potential additional tests:
- [ ] Rate limiting behavior
- [ ] Retry logic
- [ ] Circuit breaker patterns
- [ ] Real API integration tests (with test credentials)
- [ ] Performance benchmarks
- [ ] Concurrent request handling
- [ ] Cache eviction policies

## Statistics

- **Total Test Methods:** 32
- **Total Test Classes:** 9
- **Total Lines:** ~700
- **Expected Coverage:** 85%+

---

**Status:** ✅ Complete and ready for execution
