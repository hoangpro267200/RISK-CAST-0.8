"""
Contract tests for external services RiskCast depends on.

RiskCast as Consumer of external APIs.
"""

import pytest
import requests


@pytest.fixture(scope="module")
def pact_weather_provider():
    """
    Pact for Weather API (RiskCast as consumer).
    """
    try:
        from pact import Pact, Consumer, Provider
        
        pact = Pact(
            consumer=Consumer("RiskCast"),
            provider=Provider("TomorrowIO"),
            host_name="localhost",
            port=1240,
            pact_dir="./pacts",
            log_dir="./pact_logs"
        )
        
        pact.start_service()
        yield pact
        pact.stop_service()
    except ImportError:
        pytest.skip("pact-python not installed")


@pytest.fixture(scope="module")
def pact_marine_traffic_provider():
    """
    Pact for MarineTraffic API.
    """
    try:
        from pact import Pact, Consumer, Provider
        
        pact = Pact(
            consumer=Consumer("RiskCast"),
            provider=Provider("MarineTraffic"),
            host_name="localhost",
            port=1241,
            pact_dir="./pacts",
            log_dir="./pact_logs"
        )
        
        pact.start_service()
        yield pact
        pact.stop_service()
    except ImportError:
        pytest.skip("pact-python not installed")


class TestWeatherServiceContract:
    """Contract tests for Weather service dependency."""
    
    def test_get_marine_forecast(self, pact_weather_provider):
        """
        Contract: RiskCast can get marine weather forecast.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        expected_response = {
            "data": {
                "timelines": [{
                    "timestep": "1h",
                    "intervals": [{
                        "startTime": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-01-26T00:00:00"),
                        "values": {
                            "temperature": Like(25.5),
                            "windSpeed": Like(15.2),
                            "windDirection": Like(180),
                            "waveHeight": Like(2.5),
                            "visibility": Like(10.0),
                            "precipitationProbability": Like(20)
                        }
                    }]
                }]
            }
        }
        
        (pact_weather_provider
            .given("weather data is available")
            .upon_receiving("a request for marine weather forecast")
            .with_request(
                method="GET",
                path="/v4/timelines",
                query={
                    "location": "1.2,103.8",
                    "fields": "temperature,windSpeed,waveHeight",
                    "timesteps": "1h"
                },
                headers={"apikey": "test-api-key"}
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_weather_provider:
            response = requests.get(
                f"{pact_weather_provider.uri}/v4/timelines",
                params={
                    "location": "1.2,103.8",
                    "fields": "temperature,windSpeed,waveHeight",
                    "timesteps": "1h"
                },
                headers={"apikey": "test-api-key"}
            )
            
            assert response.status_code == 200


class TestMarineTrafficContract:
    """Contract tests for MarineTraffic dependency."""
    
    def test_get_vessel_position(self, pact_marine_traffic_provider):
        """
        Contract: RiskCast can get vessel position.
        """
        try:
            from pact import Like, Term
        except ImportError:
            pytest.skip("pact-python not installed")
        
        expected_response = [{
            "MMSI": Like("123456789"),
            "IMO": Like("9999999"),
            "SHIPNAME": Like("EVER GIVEN"),
            "LAT": Like(1.2644),
            "LON": Like(103.8217),
            "SPEED": Like(125),  # 12.5 knots * 10
            "COURSE": Like(270),
            "HEADING": Like(268),
            "STATUS": Like("0"),
            "TIMESTAMP": Term(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", "2026-01-26T10:00:00")
        }]
        
        (pact_marine_traffic_provider
            .given("vessel with MMSI 123456789 exists")
            .upon_receiving("a request for vessel position")
            .with_request(
                method="GET",
                path="/api/exportvessel/v:5",
                query={
                    "mmsi": "123456789",
                    "protocol": "jsono"
                }
            )
            .will_respond_with(
                status=200,
                headers={"Content-Type": "application/json"},
                body=expected_response
            ))
        
        with pact_marine_traffic_provider:
            response = requests.get(
                f"{pact_marine_traffic_provider.uri}/api/exportvessel/v:5",
                params={"mmsi": "123456789", "protocol": "jsono"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) > 0
            assert data[0]["MMSI"] == "123456789"
