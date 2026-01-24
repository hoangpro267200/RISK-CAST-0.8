"""
Weather Integration Module
Real-time weather data from external APIs
"""

from app.integrations.weather.tomorrow_io import (
    TomorrowIOClient,
    WeatherObservation,
    WeatherForecast,
    WeatherDataQuality,
    create_weather_client
)
from app.integrations.weather.weather_service import (
    WeatherService,
    get_weather_service
)

__all__ = [
    "TomorrowIOClient",
    "WeatherObservation",
    "WeatherForecast",
    "WeatherDataQuality",
    "create_weather_client",
    "WeatherService",
    "get_weather_service",
]
