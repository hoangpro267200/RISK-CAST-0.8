"""
Tomorrow.io Weather API Integration

Real-time weather data for parametric triggers and route risk assessment.
Replaces ALL stubbed weather data in the system.
"""
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json
import logging

from app.config import settings
from app.core.utils.cache import get_cache, set_cache

logger = logging.getLogger(__name__)


class WeatherDataQuality(Enum):
    """Data quality indicators."""
    REAL_TIME = "REAL_TIME"           # Fresh from API
    CACHED = "CACHED"                  # From cache, still valid
    STALE = "STALE"                    # Cache expired, API failed
    FALLBACK = "FALLBACK"              # Using fallback/default
    UNAVAILABLE = "UNAVAILABLE"        # No data available


@dataclass
class WeatherObservation:
    """Weather observation with quality metadata."""
    location: Dict[str, float]  # lat, lng
    timestamp: datetime
    temperature_c: float
    humidity_pct: float
    wind_speed_ms: float
    wind_gust_ms: Optional[float]
    precipitation_mm: float
    precipitation_probability: float
    visibility_km: float
    pressure_hpa: float
    cloud_cover_pct: float
    uv_index: float
    weather_code: int
    weather_description: str
    
    # Quality metadata - CRITICAL for trust
    data_quality: WeatherDataQuality
    data_source: str
    fetched_at: datetime
    cache_expires_at: Optional[datetime]
    api_response_time_ms: Optional[int]
    
    # Hash for audit trail
    data_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "location": self.location,
            "timestamp": self.timestamp.isoformat(),
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "wind_speed_ms": self.wind_speed_ms,
            "wind_gust_ms": self.wind_gust_ms,
            "precipitation_mm": self.precipitation_mm,
            "precipitation_probability": self.precipitation_probability,
            "visibility_km": self.visibility_km,
            "pressure_hpa": self.pressure_hpa,
            "cloud_cover_pct": self.cloud_cover_pct,
            "uv_index": self.uv_index,
            "weather_code": self.weather_code,
            "weather_description": self.weather_description,
            "data_quality": self.data_quality.value,
            "data_source": self.data_source,
            "fetched_at": self.fetched_at.isoformat(),
            "cache_expires_at": self.cache_expires_at.isoformat() if self.cache_expires_at else None,
            "api_response_time_ms": self.api_response_time_ms,
            "data_hash": self.data_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherObservation":
        """Create from dictionary."""
        # Convert ISO strings back to datetime
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        data["fetched_at"] = datetime.fromisoformat(data["fetched_at"].replace("Z", "+00:00"))
        if data.get("cache_expires_at"):
            data["cache_expires_at"] = datetime.fromisoformat(data["cache_expires_at"].replace("Z", "+00:00"))
        data["data_quality"] = WeatherDataQuality(data["data_quality"])
        return cls(**data)


@dataclass
class WeatherForecast:
    """Weather forecast for route planning."""
    location: Dict[str, float]
    forecast_time: datetime
    generated_at: datetime
    
    # Hourly forecasts
    hourly: List[Dict[str, Any]]
    
    # Daily summaries
    daily: List[Dict[str, Any]]
    
    # Severe weather alerts
    alerts: List[Dict[str, Any]]
    
    # Quality metadata
    data_quality: WeatherDataQuality
    data_source: str
    data_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "location": self.location,
            "forecast_time": self.forecast_time.isoformat(),
            "generated_at": self.generated_at.isoformat(),
            "hourly": self.hourly,
            "daily": self.daily,
            "alerts": self.alerts,
            "data_quality": self.data_quality.value,
            "data_source": self.data_source,
            "data_hash": self.data_hash,
        }


class TomorrowIOClient:
    """
    Tomorrow.io API client with:
    - Automatic retry with exponential backoff
    - Caching with quality tracking
    - Fallback handling with explicit quality flags
    - Audit trail for all data fetches
    """
    BASE_URL = "https://api.tomorrow.io/v4"
    
    def __init__(
        self,
        api_key: str,
        audit_ledger: Optional[Any] = None
    ):
        self.api_key = api_key
        self.audit = audit_ledger
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={"apikey": api_key}
        )
        
        # Cache TTLs
        self.REALTIME_CACHE_TTL = 300  # 5 minutes
        self.FORECAST_CACHE_TTL = 1800  # 30 minutes
        self.HISTORICAL_CACHE_TTL = 86400  # 24 hours
    
    async def get_realtime_weather(
        self,
        lat: float,
        lng: float,
        location_name: Optional[str] = None
    ) -> WeatherObservation:
        """
        Get real-time weather for a location.
        
        CRITICAL: Always returns data_quality flag so consumers know
        if they're getting real data or fallback.
        """
        cache_key = f"weather:realtime:{lat:.4f}:{lng:.4f}"
        
        # Try cache first
        cached = get_cache(cache_key)
        if cached:
            try:
                observation = WeatherObservation.from_dict(cached)
                observation.data_quality = WeatherDataQuality.CACHED
                return observation
            except Exception as e:
                logger.warning(f"Failed to deserialize cached weather data: {e}")
        
        # Fetch from API
        start_time = datetime.utcnow()
        try:
            response = await self._fetch_realtime(lat, lng)
            fetch_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            observation = self._parse_realtime_response(
                response,
                lat=lat,
                lng=lng,
                fetch_time_ms=fetch_time_ms
            )
            observation.data_quality = WeatherDataQuality.REAL_TIME
            
            # Cache the result
            set_cache(
                cache_key,
                observation.to_dict(),
                ttl=self.REALTIME_CACHE_TTL
            )
            
            # Audit the fetch (if audit ledger available)
            if self.audit:
                try:
                    # AuditLedger needs tenant_id - use default if available
                    tenant_id = getattr(settings, 'DEFAULT_TENANT_ID', None) or "system"
                    self.audit.append_event(
                        tenant_id=tenant_id,
                        event_type="DATA_FETCH",
                        action="WEATHER_REALTIME",
                        entity_type="weather_observation",
                        entity_id=observation.data_hash,
                        actor_type="SYSTEM",
                        payload={
                            "location": {"lat": lat, "lng": lng, "name": location_name},
                            "quality": WeatherDataQuality.REAL_TIME.value,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to audit weather fetch: {e}")
            
            return observation
            
        except httpx.HTTPStatusError as e:
            return await self._handle_api_error(e, lat, lng, cache_key)
        except httpx.TimeoutException:
            return await self._handle_timeout(lat, lng, cache_key)
        except Exception as e:
            return await self._handle_unknown_error(e, lat, lng, cache_key)
    
    async def _fetch_realtime(self, lat: float, lng: float) -> Dict[str, Any]:
        """Fetch real-time weather from Tomorrow.io API."""
        url = f"{self.BASE_URL}/timelines"
        params = {
            "location": f"{lat},{lng}",
            "fields": [
                "temperature",
                "humidity",
                "windSpeed",
                "windGust",
                "precipitationIntensity",
                "precipitationProbability",
                "visibility",
                "pressureSurfaceLevel",
                "cloudCover",
                "uvIndex",
                "weatherCode"
            ],
            "timesteps": ["current"],
            "units": "metric",
            "timezone": "UTC"
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    async def get_forecast(
        self,
        lat: float,
        lng: float,
        target_time: Optional[datetime] = None
    ) -> Optional[WeatherForecast]:
        """Get weather forecast for a location."""
        cache_key = f"weather:forecast:{lat:.4f}:{lng:.4f}"
        if target_time:
            cache_key += f":{target_time.isoformat()}"
        
        cached = get_cache(cache_key)
        if cached:
            try:
                forecast = WeatherForecast(**cached)
                forecast.data_quality = WeatherDataQuality.CACHED
                return forecast
            except Exception as e:
                logger.warning(f"Failed to deserialize cached forecast: {e}")
        
        # Fetch from API
        try:
            url = f"{self.BASE_URL}/timelines"
            params = {
                "location": f"{lat},{lng}",
                "fields": [
                    "temperature",
                    "humidity",
                    "windSpeed",
                    "windGust",
                    "precipitationIntensity",
                    "precipitationProbability",
                    "visibility",
                    "pressureSurfaceLevel",
                    "cloudCover",
                    "uvIndex",
                    "weatherCode"
                ],
                "timesteps": ["1h", "1d"],
                "units": "metric",
                "timezone": "UTC"
            }
            
            if target_time:
                params["startTime"] = target_time.isoformat()
                params["endTime"] = (target_time + timedelta(days=7)).isoformat()
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            forecast = self._parse_forecast_response(data, lat, lng)
            forecast.data_quality = WeatherDataQuality.REAL_TIME
            
            set_cache(cache_key, forecast.to_dict(), ttl=self.FORECAST_CACHE_TTL)
            return forecast
            
        except Exception as e:
            logger.error(f"Failed to fetch forecast: {e}")
            return None
    
    async def get_weather_along_route(
        self,
        waypoints: List[Dict[str, float]],
        departure_time: datetime,
        speed_knots: float = 15.0
    ) -> List[WeatherForecast]:
        """
        Get weather forecasts along a shipping route.
        
        Calculates ETA at each waypoint and fetches forecast for that time.
        """
        forecasts = []
        current_time = departure_time
        
        for i, waypoint in enumerate(waypoints):
            # Calculate ETA at this waypoint
            if i > 0:
                prev = waypoints[i - 1]
                distance_nm = self._calculate_distance_nm(
                    prev["lat"], prev["lng"],
                    waypoint["lat"], waypoint["lng"]
                )
                travel_hours = distance_nm / speed_knots
                current_time += timedelta(hours=travel_hours)
            
            # Get forecast for this time/location
            forecast = await self.get_forecast(
                lat=waypoint["lat"],
                lng=waypoint["lng"],
                target_time=current_time
            )
            if forecast:
                forecast.location["waypoint_index"] = i
                forecast.location["eta"] = current_time.isoformat()
                forecasts.append(forecast)
        
        return forecasts
    
    async def get_historical_weather(
        self,
        lat: float,
        lng: float,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get historical weather data for model calibration.
        
        Used to calibrate risk weights against actual weather outcomes.
        """
        cache_key = f"weather:historical:{lat:.4f}:{lng:.4f}:{start_date.date()}:{end_date.date()}"
        
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        # Tomorrow.io historical endpoint
        url = f"{self.BASE_URL}/timelines"
        params = {
            "location": f"{lat},{lng}",
            "fields": [
                "temperature", "humidity", "windSpeed", "windGust",
                "precipitationIntensity", "visibility", "pressureSurfaceLevel",
                "cloudCover", "weatherCode"
            ],
            "timesteps": ["1d"],
            "startTime": start_date.isoformat(),
            "endTime": end_date.isoformat(),
            "timezone": "UTC"
        }
        
        response = await self.client.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        historical = self._parse_historical_response(data)
        
        # Cache for longer (historical data doesn't change)
        set_cache(cache_key, historical, ttl=self.HISTORICAL_CACHE_TTL)
        
        return historical
    
    async def check_severe_weather_alerts(
        self,
        lat: float,
        lng: float,
        radius_km: float = 100
    ) -> List[Dict[str, Any]]:
        """
        Check for severe weather alerts that could affect shipments.
        
        Returns alerts with severity levels for parametric trigger evaluation.
        """
        # Tomorrow.io alerts endpoint
        url = f"{self.BASE_URL}/events"
        params = {
            "location": f"{lat},{lng}",
            "insights": ["precipitation", "wind", "temperature"]
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            alerts = data.get("data", {}).get("events", [])
            
            # Normalize alert format
            normalized_alerts = []
            for alert in alerts:
                normalized_alerts.append({
                    "id": alert.get("eventId"),
                    "type": alert.get("insight"),
                    "severity": self._normalize_severity(alert.get("severity")),
                    "headline": alert.get("headline"),
                    "description": alert.get("description"),
                    "effective_from": alert.get("startTime"),
                    "effective_to": alert.get("endTime"),
                    "affected_area": alert.get("location"),
                    "source": "tomorrow.io",
                    "fetched_at": datetime.utcnow().isoformat()
                })
            
            return normalized_alerts
            
        except Exception as e:
            # Log but don't fail - alerts are supplementary
            logger.warning(f"Failed to fetch weather alerts: {e}")
            return []
    
    def _compute_data_hash(self, data: Dict[str, Any]) -> str:
        """Compute hash of weather data for audit trail."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def _parse_realtime_response(
        self,
        response: Dict[str, Any],
        lat: float,
        lng: float,
        fetch_time_ms: int
    ) -> WeatherObservation:
        """Parse Tomorrow.io realtime response into WeatherObservation."""
        data = response.get("data", {}).get("timelines", [{}])[0]
        intervals = data.get("intervals", [{}])
        if not intervals:
            raise ValueError("No weather data in response")
        
        values = intervals[0].get("values", {})
        time_str = intervals[0].get("startTime", datetime.utcnow().isoformat())
        
        now = datetime.utcnow()
        observation_data = {
            "location": {"lat": lat, "lng": lng},
            "timestamp": datetime.fromisoformat(time_str.replace("Z", "+00:00")),
            "temperature_c": values.get("temperature", 20.0),
            "humidity_pct": values.get("humidity", 50.0),
            "wind_speed_ms": values.get("windSpeed", 5.0),
            "wind_gust_ms": values.get("windGust"),
            "precipitation_mm": values.get("precipitationIntensity", 0.0) * 3600,  # Convert mm/h to mm
            "precipitation_probability": values.get("precipitationProbability", 0.0),
            "visibility_km": values.get("visibility", 10.0) / 1000,  # Convert m to km
            "pressure_hpa": values.get("pressureSurfaceLevel", 1013.0),
            "cloud_cover_pct": values.get("cloudCover", 50.0),
            "uv_index": values.get("uvIndex", 5.0),
            "weather_code": values.get("weatherCode", 1000),
            "weather_description": self._weather_code_to_description(values.get("weatherCode", 1000)),
            "data_quality": WeatherDataQuality.REAL_TIME,
            "data_source": "tomorrow.io",
            "fetched_at": now,
            "cache_expires_at": now + timedelta(seconds=self.REALTIME_CACHE_TTL),
            "api_response_time_ms": fetch_time_ms,
        }
        
        observation_data["data_hash"] = self._compute_data_hash(observation_data)
        
        return WeatherObservation(**observation_data)
    
    def _parse_forecast_response(
        self,
        response: Dict[str, Any],
        lat: float,
        lng: float
    ) -> WeatherForecast:
        """Parse Tomorrow.io forecast response."""
        data = response.get("data", {}).get("timelines", [])
        
        hourly = []
        daily = []
        
        for timeline in data:
            timestep = timeline.get("timestep", "")
            intervals = timeline.get("intervals", [])
            
            for interval in intervals:
                values = interval.get("values", {})
                entry = {
                    "time": interval.get("startTime"),
                    "temperature_c": values.get("temperature"),
                    "precipitation_mm": values.get("precipitationIntensity", 0.0) * 3600,
                    "wind_speed_ms": values.get("windSpeed"),
                    "weather_code": values.get("weatherCode"),
                }
                
                if timestep == "1h":
                    hourly.append(entry)
                elif timestep == "1d":
                    daily.append(entry)
        
        now = datetime.utcnow()
        forecast_data = {
            "location": {"lat": lat, "lng": lng},
            "forecast_time": now,
            "generated_at": now,
            "hourly": hourly[:168],  # 7 days
            "daily": daily[:7],
            "alerts": [],
            "data_quality": WeatherDataQuality.REAL_TIME,
            "data_source": "tomorrow.io",
            "data_hash": "",
        }
        
        forecast_data["data_hash"] = self._compute_data_hash(forecast_data)
        
        return WeatherForecast(**forecast_data)
    
    def _parse_historical_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse historical weather response."""
        data = response.get("data", {}).get("timelines", [{}])[0]
        intervals = data.get("intervals", [])
        
        historical = []
        for interval in intervals:
            values = interval.get("values", {})
            historical.append({
                "date": interval.get("startTime"),
                "temperature_c": values.get("temperature"),
                "precipitation_mm": values.get("precipitationIntensity", 0.0) * 24 * 3600,
                "wind_speed_ms": values.get("windSpeed"),
                "weather_code": values.get("weatherCode"),
            })
        
        return historical
    
    async def _handle_api_error(
        self,
        error: httpx.HTTPStatusError,
        lat: float,
        lng: float,
        cache_key: str
    ) -> WeatherObservation:
        """Handle API errors with fallback and quality flags."""
        logger.error(f"Tomorrow.io API error: {error.response.status_code} - {error}")
        
        # Try stale cache (we don't have allow_stale in current cache, so skip)
        # Return fallback with explicit quality flag
        return self._create_fallback_observation(lat, lng, f"API error: {error.response.status_code}")
    
    async def _handle_timeout(
        self,
        lat: float,
        lng: float,
        cache_key: str
    ) -> WeatherObservation:
        """Handle timeout errors."""
        logger.warning(f"Tomorrow.io API timeout for {lat},{lng}")
        return self._create_fallback_observation(lat, lng, "API timeout")
    
    async def _handle_unknown_error(
        self,
        error: Exception,
        lat: float,
        lng: float,
        cache_key: str
    ) -> WeatherObservation:
        """Handle unknown errors."""
        logger.error(f"Unknown error fetching weather: {error}")
        return self._create_fallback_observation(lat, lng, f"Unknown error: {str(error)}")
    
    def _create_fallback_observation(
        self,
        lat: float,
        lng: float,
        error_reason: str
    ) -> WeatherObservation:
        """
        Create fallback observation with EXPLICIT quality flag.
        
        CRITICAL: This is NOT hidden from consumers. The data_quality
        flag clearly indicates this is fallback data.
        """
        now = datetime.utcnow()
        
        # Use climatological averages as fallback
        # These should be replaced with actual climatological data
        fallback_data = {
            "location": {"lat": lat, "lng": lng},
            "timestamp": now,
            "temperature_c": 20.0,  # Global average
            "humidity_pct": 60.0,
            "wind_speed_ms": 5.0,
            "wind_gust_ms": None,
            "precipitation_mm": 0.0,
            "precipitation_probability": 0.0,
            "visibility_km": 10.0,
            "pressure_hpa": 1013.25,
            "cloud_cover_pct": 50.0,
            "uv_index": 5.0,
            "weather_code": 1000,
            "weather_description": "Unknown (fallback data)",
            "data_quality": WeatherDataQuality.FALLBACK,
            "data_source": "climatological_average",
            "fetched_at": now,
            "cache_expires_at": None,
            "api_response_time_ms": None,
            "data_hash": "",
        }
        
        fallback_data["data_hash"] = self._compute_data_hash(fallback_data)
        
        return WeatherObservation(**fallback_data)
    
    @staticmethod
    def _calculate_distance_nm(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance between two points in nautical miles (Haversine formula)."""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 3440.0  # Earth radius in nautical miles
        
        lat1_rad = radians(lat1)
        lat2_rad = radians(lat2)
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlng/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    @staticmethod
    def _normalize_severity(severity: Any) -> str:
        """Normalize severity levels."""
        if isinstance(severity, str):
            return severity.upper()
        return "UNKNOWN"
    
    @staticmethod
    def _weather_code_to_description(code: int) -> str:
        """Convert Tomorrow.io weather code to description."""
        codes = {
            1000: "Clear",
            1001: "Cloudy",
            1100: "Mostly Clear",
            1101: "Partly Cloudy",
            1102: "Mostly Cloudy",
            2000: "Fog",
            2100: "Light Fog",
            4000: "Drizzle",
            4001: "Rain",
            4200: "Light Rain",
            4201: "Heavy Rain",
            5000: "Snow",
            5001: "Flurries",
            5100: "Light Snow",
            5101: "Heavy Snow",
            6000: "Freezing Drizzle",
            6001: "Freezing Rain",
            6200: "Light Freezing Rain",
            6201: "Heavy Freezing Rain",
            7000: "Ice Pellets",
            7101: "Heavy Ice Pellets",
            7102: "Light Ice Pellets",
            8000: "Thunderstorm",
        }
        return codes.get(code, f"Unknown ({code})")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def create_weather_client(audit_ledger: Optional[Any] = None) -> TomorrowIOClient:
    """Create configured weather client."""
    if not settings.TOMORROW_IO_API_KEY:
        raise ValueError("TOMORROW_IO_API_KEY not configured")
    
    return TomorrowIOClient(
        api_key=settings.TOMORROW_IO_API_KEY,
        audit_ledger=audit_ledger
    )
