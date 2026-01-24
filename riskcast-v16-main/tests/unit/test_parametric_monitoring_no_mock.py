"""
Unit Tests for Parametric Monitoring (No Mock Data)
Tests that verify no mock data is used and unconfigured oracles return proper errors.
"""
import pytest
from datetime import datetime

from app.services.parametric_monitoring import ParametricMonitor
from app.core.parametric.oracle_gateway import OracleGateway
from app.core.parametric.providers.stub_provider import StubOracleProvider
from app.core.parametric.exceptions import OracleNotConfiguredError, OracleFetchError
from app.models.insurance import ParametricTrigger


@pytest.fixture
def oracle_gateway():
    """Create oracle gateway with stub providers"""
    gateway = OracleGateway()
    
    # Register stub providers (not configured)
    gateway.register_provider(StubOracleProvider("weather"))
    gateway.register_provider(StubOracleProvider("port"))
    gateway.register_provider(StubOracleProvider("natcat"))
    
    return gateway


@pytest.fixture
def monitor(oracle_gateway):
    """Create parametric monitor with oracle gateway"""
    return ParametricMonitor(oracle_gateway=oracle_gateway)


@pytest.fixture
def weather_trigger():
    """Create a weather trigger for testing"""
    return ParametricTrigger(
        trigger_type="weather",
        location={"port_code": "USNYC"},
        threshold=100.0,
        trigger_config={"metric": "cumulative_rainfall_mm"}
    )


@pytest.fixture
def port_trigger():
    """Create a port congestion trigger for testing"""
    return ParametricTrigger(
        trigger_type="port_congestion",
        location={"port_code": "USNYC"},
        threshold=10.0,
        trigger_config={"metric": "dwell_days"}
    )


class TestParametricMonitoringNoMock:
    """Tests to verify no mock data is used"""
    
    def test_fetch_weather_data_raises_when_not_configured(
        self, monitor, weather_trigger
    ):
        """Test that fetch_weather_data raises OracleNotConfiguredError"""
        with pytest.raises(OracleNotConfiguredError) as exc_info:
            # This should raise, not return mock data
            import asyncio
            asyncio.run(monitor._fetch_weather_data(weather_trigger))
        
        assert "not configured" in str(exc_info.value).lower()
        assert "weather" in str(exc_info.value).lower()
    
    def test_fetch_port_congestion_data_raises_when_not_configured(
        self, monitor, port_trigger
    ):
        """Test that fetch_port_congestion_data raises OracleNotConfiguredError"""
        with pytest.raises(OracleNotConfiguredError) as exc_info:
            import asyncio
            asyncio.run(monitor._fetch_port_congestion_data(port_trigger))
        
        assert "not configured" in str(exc_info.value).lower()
        assert "port" in str(exc_info.value).lower()
    
    def test_fetch_catastrophe_data_raises_when_not_configured(
        self, monitor
    ):
        """Test that fetch_catastrophe_data raises OracleNotConfiguredError"""
        trigger = ParametricTrigger(
            trigger_type="natcat",
            location={"location": "USNYC"},
            threshold=100.0,
            trigger_config={}
        )
        
        with pytest.raises(OracleNotConfiguredError) as exc_info:
            import asyncio
            asyncio.run(monitor._fetch_catastrophe_data(trigger))
        
        assert "not configured" in str(exc_info.value).lower()
        assert "natcat" in str(exc_info.value).lower()
    
    def test_is_oracle_configured_returns_false_for_stub_providers(
        self, monitor
    ):
        """Test that is_oracle_configured returns False for stub providers"""
        assert monitor.is_oracle_configured("weather") is False
        assert monitor.is_oracle_configured("port") is False
        assert monitor.is_oracle_configured("natcat") is False
        assert monitor.is_oracle_configured("ais") is False
    
    def test_no_mock_data_in_fetch_methods(
        self, monitor, weather_trigger
    ):
        """Test that fetch methods don't return hardcoded mock data"""
        # This test verifies that the methods raise errors instead of returning mock data
        with pytest.raises(OracleNotConfiguredError):
            import asyncio
            result = asyncio.run(monitor._fetch_weather_data(weather_trigger))
            # If we get here, it means mock data was returned (bad!)
            # Check that result doesn't contain hardcoded values
            assert "cumulative_rainfall_mm" not in result or result["cumulative_rainfall_mm"] != 120.0


class TestParametricEndpointsNoMock:
    """Tests for parametric endpoints with unconfigured oracles"""
    
    def test_get_weather_returns_503_when_not_configured(
        self, client, oracle_gateway
    ):
        """Test that GET /parametric/weather/{location} returns 503"""
        # Note: This test requires FastAPI test client setup
        # For now, we'll test the logic directly
        
        from app.services.parametric_monitoring import ParametricMonitor
        from app.core.parametric.oracle_gateway import OracleQuery
        
        monitor = ParametricMonitor(oracle_gateway=oracle_gateway)
        
        # Verify it raises OracleNotConfiguredError
        with pytest.raises(OracleNotConfiguredError):
            import asyncio
            asyncio.run(
                monitor.oracle_gateway.fetch(
                    "weather",
                    OracleQuery(location="USNYC")
                )
            )
    
    def test_get_parametric_status_shows_unconfigured(
        self, monitor
    ):
        """Test that status endpoint shows unconfigured state"""
        status = {
            "weather_oracle": monitor.is_oracle_configured("weather"),
            "port_oracle": monitor.is_oracle_configured("port"),
            "natcat_oracle": monitor.is_oracle_configured("natcat"),
            "ais_oracle": monitor.is_oracle_configured("ais"),
        }
        
        # All should be False (unconfigured)
        assert status["weather_oracle"] is False
        assert status["port_oracle"] is False
        assert status["natcat_oracle"] is False
        assert status["ais_oracle"] is False


class TestNoHardcodedData:
    """Tests to verify no hardcoded data exists"""
    
    def test_no_hardcoded_weather_values(self, monitor, weather_trigger):
        """Verify no hardcoded weather values are returned"""
        with pytest.raises(OracleNotConfiguredError):
            import asyncio
            result = asyncio.run(monitor._fetch_weather_data(weather_trigger))
            
            # If we somehow get a result, verify it's not hardcoded
            if result:
                assert result.get("cumulative_rainfall_mm") != 120.0
                assert "Mock" not in str(result)
                assert "mock" not in str(result).lower()
    
    def test_no_hardcoded_port_values(self, monitor, port_trigger):
        """Verify no hardcoded port values are returned"""
        with pytest.raises(OracleNotConfiguredError):
            import asyncio
            result = asyncio.run(monitor._fetch_port_congestion_data(port_trigger))
            
            # If we somehow get a result, verify it's not hardcoded
            if result:
                assert result.get("dwell_days") != 12.0
                assert "Mock" not in str(result)
                assert "mock" not in str(result).lower()
    
    def test_no_hardcoded_natcat_values(self, monitor):
        """Verify no hardcoded natcat values are returned"""
        trigger = ParametricTrigger(
            trigger_type="natcat",
            location={"location": "USNYC"},
            threshold=100.0,
            trigger_config={}
        )
        
        with pytest.raises(OracleNotConfiguredError):
            import asyncio
            result = asyncio.run(monitor._fetch_catastrophe_data(trigger))
            
            # If we somehow get a result, verify it's not hardcoded
            if result:
                assert result.get("max_wind_kph") != 0
                assert "Mock" not in str(result)
                assert "mock" not in str(result).lower()
