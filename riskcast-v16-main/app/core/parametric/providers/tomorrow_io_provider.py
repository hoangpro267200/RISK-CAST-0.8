"""
Tomorrow.io Oracle Provider

Implements OracleProvider interface for weather data.
Replaces stub weather provider with real API integration.
"""
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from app.core.parametric.oracle_gateway import (
    OracleProvider,
    OracleQuery,
    OraclePayload,
    ValidationResult
)
from app.core.parametric.exceptions import (
    OracleNotConfiguredError,
    OracleFetchError
)
from app.integrations.weather.tomorrow_io import (
    TomorrowIOClient,
    create_weather_client,
    WeatherDataQuality
)
from app.config import settings

logger = logging.getLogger(__name__)


class TomorrowIOProvider(OracleProvider):
    """
    Tomorrow.io weather oracle provider.
    
    Fetches real-time weather data from Tomorrow.io API
    and normalizes it for parametric trigger evaluation.
    """
    
    def __init__(self, audit_ledger: Optional[Any] = None):
        """Initialize Tomorrow.io provider."""
        self.audit = audit_ledger
        self._client: Optional[TomorrowIOClient] = None
    
    @property
    def source_name(self) -> str:
        """Return provider source name."""
        return "tomorrow_io"
    
    def is_configured(self) -> bool:
        """Check if Tomorrow.io API key is configured."""
        return bool(settings.TOMORROW_IO_API_KEY)
    
    def _get_client(self) -> TomorrowIOClient:
        """Get or create weather client."""
        if self._client is None:
            if not self.is_configured():
                raise OracleNotConfiguredError(
                    "Tomorrow.io API key not configured. Set TOMORROW_IO_API_KEY environment variable."
                )
            self._client = create_weather_client(self.audit)
        return self._client
    
    async def fetch_event(self, query: OracleQuery) -> OraclePayload:
        """
        Fetch weather data from Tomorrow.io.
        
        Args:
            query: OracleQuery with location (port_code or coordinates)
            
        Returns:
            OraclePayload with weather data
            
        Raises:
            OracleNotConfiguredError: If API key not configured
            OracleFetchError: If fetch fails
        """
        if not self.is_configured():
            raise OracleNotConfiguredError(
                "Tomorrow.io API key not configured. Set TOMORROW_IO_API_KEY environment variable."
            )
        
        client = self._get_client()
        
        # Extract location from query
        location = query.location
        if not location:
            raise OracleFetchError("Location not specified in query")
        
        # Try to get coordinates from location (could be port code or lat,lng)
        lat, lng = self._parse_location(location)
        
        try:
            # Fetch real-time weather
            observation = await client.get_realtime_weather(
                lat=lat,
                lng=lng,
                location_name=location
            )
            
            # Convert to oracle payload format
            payload = {
                "location": location,
                "coordinates": {"lat": lat, "lng": lng},
                "timestamp": observation.timestamp.isoformat(),
                "temperature_c": observation.temperature_c,
                "humidity_pct": observation.humidity_pct,
                "wind_speed_ms": observation.wind_speed_ms,
                "wind_gust_ms": observation.wind_gust_ms,
                "precipitation_mm": observation.precipitation_mm,
                "precipitation_probability": observation.precipitation_probability,
                "visibility_km": observation.visibility_km,
                "pressure_hpa": observation.pressure_hpa,
                "cloud_cover_pct": observation.cloud_cover_pct,
                "uv_index": observation.uv_index,
                "weather_code": observation.weather_code,
                "weather_description": observation.weather_description,
                "data_quality": observation.data_quality.value,
                "data_source": observation.data_source,
                "data_hash": observation.data_hash,
                "fetched_at": observation.fetched_at.isoformat(),
            }
            
            # Check data quality - reject fallback data if configured
            if (observation.data_quality == WeatherDataQuality.FALLBACK and 
                not settings.ALLOW_FALLBACK_DATA_IN_RISK):
                logger.warning(
                    f"Received fallback weather data for {location}. "
                    "Rejecting due to ALLOW_FALLBACK_DATA_IN_RISK=False"
                )
                raise OracleFetchError(
                    f"Only fallback weather data available for {location}. "
                    "Cannot use for risk calculation."
                )
            
            return OraclePayload.from_dict(
                source=self.source_name,
                payload=payload
            )
            
        except OracleNotConfiguredError:
            raise
        except OracleFetchError:
            raise
        except Exception as e:
            logger.error(f"Error fetching weather from Tomorrow.io: {e}", exc_info=True)
            raise OracleFetchError(f"Failed to fetch weather data: {str(e)}") from e
    
    def validate(self, payload: OraclePayload) -> ValidationResult:
        """
        Validate weather payload structure.
        
        Required fields:
        - location
        - timestamp
        - temperature_c
        - precipitation_mm
        - wind_speed_ms
        - data_quality
        - data_source
        """
        result = ValidationResult(valid=True)
        data = payload.payload
        
        required_fields = [
            "location",
            "timestamp",
            "temperature_c",
            "precipitation_mm",
            "wind_speed_ms",
            "data_quality",
            "data_source"
        ]
        
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Validate data quality
        if "data_quality" in data:
            quality = data["data_quality"]
            if quality == WeatherDataQuality.FALLBACK.value:
                result.add_warning(
                    "Weather data is fallback/climatological average. "
                    "Not suitable for parametric trigger evaluation."
                )
            elif quality == WeatherDataQuality.STALE.value:
                result.add_warning(
                    "Weather data is stale (cache expired, API failed). "
                    "May not reflect current conditions."
                )
        
        # Validate numeric ranges
        if "temperature_c" in data:
            temp = data["temperature_c"]
            if not isinstance(temp, (int, float)) or temp < -100 or temp > 100:
                result.add_error(f"Invalid temperature: {temp}")
        
        if "precipitation_mm" in data:
            precip = data["precipitation_mm"]
            if not isinstance(precip, (int, float)) or precip < 0:
                result.add_error(f"Invalid precipitation: {precip}")
        
        return result
    
    def normalize(self, payload: OraclePayload) -> dict:
        """
        Normalize weather payload to standard format for trigger evaluation.
        
        Standard format:
        {
            "rainfall_mm": float,
            "temperature_c": float,
            "wind_speed_ms": float,
            "data_quality": str,
            "data_source": str,
            "timestamp": str (ISO)
        }
        """
        data = payload.payload
        
        normalized = {
            "rainfall_mm": data.get("precipitation_mm", 0.0),
            "temperature_c": data.get("temperature_c", 20.0),
            "wind_speed_ms": data.get("wind_speed_ms", 5.0),
            "data_quality": data.get("data_quality", "UNKNOWN"),
            "data_source": data.get("data_source", payload.source),
            "timestamp": data.get("timestamp", payload.captured_at.isoformat()),
            "location": data.get("location"),
            "coordinates": data.get("coordinates"),
        }
        
        # Add optional fields if available
        if "wind_gust_ms" in data:
            normalized["wind_gust_ms"] = data["wind_gust_ms"]
        if "precipitation_probability" in data:
            normalized["precipitation_probability"] = data["precipitation_probability"]
        if "visibility_km" in data:
            normalized["visibility_km"] = data["visibility_km"]
        if "weather_code" in data:
            normalized["weather_code"] = data["weather_code"]
        if "data_hash" in data:
            normalized["data_hash"] = data["data_hash"]
        
        return normalized
    
    def _parse_location(self, location: str) -> tuple[float, float]:
        """
        Parse location string to lat/lng coordinates.
        
        Supports:
        - Port codes (lookup needed - simplified for now)
        - "lat,lng" format
        - Coordinates dict lookup (future enhancement)
        """
        # Try "lat,lng" format
        if "," in location:
            try:
                parts = location.split(",")
                return float(parts[0].strip()), float(parts[1].strip())
            except (ValueError, IndexError):
                pass
        
        # TODO: Port code lookup - would need port database
        # For now, return default coordinates (should be replaced with port lookup)
        logger.warning(
            f"Location '{location}' not in lat,lng format. "
            "Using default coordinates. Port code lookup not implemented."
        )
        
        # Default to a safe location (middle of ocean)
        return 0.0, 0.0
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.close()
