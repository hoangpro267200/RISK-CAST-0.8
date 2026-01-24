"""
Data Source Collectors

Helpers to collect data sources and their quality levels from various integrations.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

from app.core.data_quality.gateway import DataSource, DataQualityLevel

logger = logging.getLogger(__name__)


def map_quality_string_to_level(quality_str: str) -> DataQualityLevel:
    """Map quality string from integrations to DataQualityLevel enum."""
    quality_map = {
        # Weather quality
        "REAL_TIME": DataQualityLevel.EXCELLENT,
        "CACHED": DataQualityLevel.GOOD,
        "STALE": DataQualityLevel.ACCEPTABLE,
        "FALLBACK": DataQualityLevel.FALLBACK,
        "UNAVAILABLE": DataQualityLevel.UNAVAILABLE,
        # Port quality
        "RECENT": DataQualityLevel.GOOD,
        "HISTORICAL": DataQualityLevel.POOR,
        "HARDCODED": DataQualityLevel.FALLBACK,
        # Carrier quality
        "HISTORICAL": DataQualityLevel.POOR,
        # Climate quality
        "PROVISIONAL": DataQualityLevel.GOOD,
        "FORECAST": DataQualityLevel.ACCEPTABLE,
    }
    return quality_map.get(quality_str, DataQualityLevel.FALLBACK)


def collect_weather_data_source(weather_data: Optional[Dict[str, Any]]) -> Optional[DataSource]:
    """Collect weather data source information."""
    if not weather_data:
        return None
    
    quality_str = weather_data.get("data_quality", "FALLBACK")
    quality_level = map_quality_string_to_level(quality_str)
    
    # Parse timestamps
    fetched_at_str = weather_data.get("fetched_at")
    fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00")) if fetched_at_str else datetime.utcnow()
    
    data_timestamp_str = weather_data.get("data_timestamp")
    data_timestamp = None
    if data_timestamp_str:
        try:
            data_timestamp = datetime.fromisoformat(data_timestamp_str.replace("Z", "+00:00"))
        except:
            pass
    
    is_fallback = quality_str in ["FALLBACK", "UNAVAILABLE"] or weather_data.get("from_api") is False
    
    return DataSource(
        source_name="weather",
        source_type="weather",
        quality_level=quality_level,
        data_timestamp=data_timestamp,
        fetched_at=fetched_at,
        data_hash=weather_data.get("data_hash"),
        is_fallback=is_fallback,
        fallback_reason=weather_data.get("fallback_reason"),
        confidence=weather_data.get("confidence", 0.8 if not is_fallback else 0.5)
    )


def collect_port_data_source(port_data: Optional[Dict[str, Any]]) -> Optional[DataSource]:
    """Collect port data source information."""
    if not port_data:
        return None
    
    quality_str = port_data.get("data_quality", "FALLBACK")
    quality_level = map_quality_string_to_level(quality_str)
    
    fetched_at_str = port_data.get("fetched_at")
    fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00")) if fetched_at_str else datetime.utcnow()
    
    data_timestamp_str = port_data.get("data_timestamp")
    data_timestamp = None
    if data_timestamp_str:
        try:
            data_timestamp = datetime.fromisoformat(data_timestamp_str.replace("Z", "+00:00"))
        except:
            pass
    
    is_fallback = quality_str in ["FALLBACK", "HARDCODED", "HISTORICAL"] or port_data.get("from_api") is False
    
    return DataSource(
        source_name="port",
        source_type="port",
        quality_level=quality_level,
        data_timestamp=data_timestamp,
        fetched_at=fetched_at,
        data_hash=port_data.get("data_hash"),
        is_fallback=is_fallback,
        fallback_reason=port_data.get("fallback_reason"),
        confidence=port_data.get("confidence", 0.8 if not is_fallback else 0.5)
    )


def collect_carrier_data_source(carrier_data: Optional[Dict[str, Any]]) -> Optional[DataSource]:
    """Collect carrier data source information."""
    if not carrier_data:
        return None
    
    quality_str = carrier_data.get("data_quality", {}).get("quality", "FALLBACK")
    if isinstance(quality_str, dict):
        quality_str = quality_str.get("quality", "FALLBACK")
    
    quality_level = map_quality_string_to_level(quality_str)
    
    fetched_at_str = carrier_data.get("fetched_at") or carrier_data.get("data_quality", {}).get("fetched_at")
    fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00")) if fetched_at_str else datetime.utcnow()
    
    data_timestamp_str = carrier_data.get("data_timestamp")
    data_timestamp = None
    if data_timestamp_str:
        try:
            data_timestamp = datetime.fromisoformat(data_timestamp_str.replace("Z", "+00:00"))
        except:
            pass
    
    is_fallback = quality_str in ["FALLBACK", "HISTORICAL"] or carrier_data.get("from_api") is False
    
    return DataSource(
        source_name="carrier",
        source_type="carrier",
        quality_level=quality_level,
        data_timestamp=data_timestamp,
        fetched_at=fetched_at,
        data_hash=carrier_data.get("data_hash") or carrier_data.get("data_quality", {}).get("data_hash"),
        is_fallback=is_fallback,
        fallback_reason=carrier_data.get("fallback_reason"),
        confidence=carrier_data.get("confidence", 0.8 if not is_fallback else 0.5)
    )


def collect_climate_data_source(climate_data: Optional[Dict[str, Any]]) -> Optional[DataSource]:
    """Collect climate data source information."""
    if not climate_data:
        return None
    
    quality_str = climate_data.get("data_quality", {}).get("quality", "FALLBACK")
    if isinstance(quality_str, dict):
        quality_str = quality_str.get("quality", "FALLBACK")
    
    quality_level = map_quality_string_to_level(quality_str)
    
    fetched_at_str = climate_data.get("fetched_at") or climate_data.get("data_quality", {}).get("fetched_at")
    fetched_at = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00")) if fetched_at_str else datetime.utcnow()
    
    data_timestamp_str = climate_data.get("data_date") or climate_data.get("data_timestamp")
    data_timestamp = None
    if data_timestamp_str:
        try:
            if isinstance(data_timestamp_str, str):
                data_timestamp = datetime.fromisoformat(data_timestamp_str.replace("Z", "+00:00"))
        except:
            pass
    
    is_fallback = quality_str in ["FALLBACK", "HISTORICAL"] or climate_data.get("from_api") is False
    
    return DataSource(
        source_name="climate",
        source_type="climate",
        quality_level=quality_level,
        data_timestamp=data_timestamp,
        fetched_at=fetched_at,
        data_hash=climate_data.get("data_hash") or climate_data.get("data_quality", {}).get("data_hash"),
        is_fallback=is_fallback,
        fallback_reason=climate_data.get("fallback_reason"),
        confidence=climate_data.get("confidence", 0.8 if not is_fallback else 0.5)
    )


def collect_all_data_sources(
    weather_data: Optional[Dict[str, Any]] = None,
    port_data: Optional[Dict[str, Any]] = None,
    carrier_data: Optional[Dict[str, Any]] = None,
    climate_data: Optional[Dict[str, Any]] = None,
) -> List[DataSource]:
    """
    Collect all data sources from risk calculation inputs.
    
    This is used by the data quality gateway to assess data quality.
    """
    sources = []
    
    if weather_data:
        source = collect_weather_data_source(weather_data)
        if source:
            sources.append(source)
    
    if port_data:
        source = collect_port_data_source(port_data)
        if source:
            sources.append(source)
    
    if carrier_data:
        source = collect_carrier_data_source(carrier_data)
        if source:
            sources.append(source)
    
    if climate_data:
        source = collect_climate_data_source(climate_data)
        if source:
            sources.append(source)
    
    return sources
