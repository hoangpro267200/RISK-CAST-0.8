"""
Unified Data Service

Single entry point for all external data with:
- Automatic source selection
- Quality tracking
- Fallback handling
- Audit trail

This service ensures the risk engine ALWAYS knows data quality.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib
import json
import logging

from app.integrations.weather import get_weather_service
from app.integrations.ports import get_port_service
from app.integrations.carriers import get_carrier_service
from app.integrations.climate import get_climate_service
from app.core.data_quality.gateway import (
    DataQualityGateway,
    DataSource,
    DataQualityLevel,
    DecisionType,
    DataQualityReport
)
from app.core.data_quality.collectors import (
    collect_weather_data_source,
    collect_port_data_source,
    collect_carrier_data_source,
    collect_climate_data_source,
)

logger = logging.getLogger(__name__)


@dataclass
class UnifiedShipmentData:
    """All data needed for risk assessment, with quality tracking."""
    
    # Shipment basics (from user input)
    origin_port: str
    destination_port: str
    cargo_type: str
    cargo_value_usd: float
    container_count: int
    departure_date: date
    expected_arrival_date: date
    carrier_code: Optional[str]
    
    # Weather data (from Tomorrow.io)
    origin_weather: Dict[str, Any]
    destination_weather: Dict[str, Any]
    route_weather: Optional[Dict[str, Any]]
    
    # Port data (from MarineTraffic)
    origin_port_conditions: Dict[str, Any]
    destination_port_conditions: Dict[str, Any]
    
    # Carrier data (from Project44)
    carrier_performance: Optional[Dict[str, Any]]
    carrier_route_performance: Optional[Dict[str, Any]]
    
    # Climate data (from NOAA)
    climate_indices: Dict[str, Any]
    
    # Aggregated quality info
    data_sources: List[DataSource]
    data_quality_report: DataQualityReport
    overall_data_quality: DataQualityLevel
    overall_confidence: float
    
    # Warnings for user
    data_warnings: List[str]
    
    # Audit
    collected_at: datetime
    collection_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "shipment": {
                "origin_port": self.origin_port,
                "destination_port": self.destination_port,
                "cargo_type": self.cargo_type,
                "cargo_value_usd": self.cargo_value_usd,
                "container_count": self.container_count,
                "departure_date": self.departure_date.isoformat(),
                "expected_arrival_date": self.expected_arrival_date.isoformat(),
                "carrier_code": self.carrier_code,
            },
            "weather": {
                "origin": self.origin_weather,
                "destination": self.destination_weather,
                "route": self.route_weather,
            },
            "ports": {
                "origin": self.origin_port_conditions,
                "destination": self.destination_port_conditions,
            },
            "carrier": {
                "performance": self.carrier_performance,
                "route_performance": self.carrier_route_performance,
            },
            "climate": self.climate_indices,
            "data_quality": {
                "overall_quality": self.overall_data_quality.value,
                "overall_confidence": self.overall_confidence,
                "sources": [s.to_dict() for s in self.data_sources],
                "report": self.data_quality_report.to_dict(),
            },
            "warnings": self.data_warnings,
            "metadata": {
                "collected_at": self.collected_at.isoformat(),
                "collection_hash": self.collection_hash,
            }
        }


class UnifiedDataService:
    """
    Unified data collection service.
    
    Collects all data needed for risk assessment from various sources,
    tracks quality, and provides clear warnings about data limitations.
    """
    
    def __init__(self, audit: Optional[Any] = None):
        self.audit = audit
        self.weather_service = get_weather_service(audit)
        self.port_service = get_port_service(audit)
        self.carrier_service = get_carrier_service(audit)
        self.climate_service = get_climate_service(audit)
        self.quality_gateway = DataQualityGateway()
    
    async def collect_shipment_data(
        self,
        origin_port: str,
        destination_port: str,
        cargo_type: str,
        cargo_value_usd: float,
        container_count: int,
        departure_date: date,
        expected_arrival_date: date,
        carrier_code: Optional[str] = None,
        decision_type: DecisionType = DecisionType.RISK_ASSESSMENT,
        include_route_weather: bool = True,
    ) -> UnifiedShipmentData:
        """
        Collect all data needed for risk assessment.
        
        This is the SINGLE ENTRY POINT for all external data collection.
        
        Args:
            origin_port: Origin port UN/LOCODE
            destination_port: Destination port UN/LOCODE
            cargo_type: Type of cargo
            cargo_value_usd: Total cargo value in USD
            container_count: Number of containers
            departure_date: Expected departure date
            expected_arrival_date: Expected arrival date
            carrier_code: Optional carrier SCAC code
            decision_type: Type of decision (affects quality requirements)
            include_route_weather: Whether to fetch route weather (slower)
            
        Returns:
            UnifiedShipmentData with all collected data and quality tracking
        """
        collected_at = datetime.utcnow()
        warnings: List[str] = []
        data_sources: List[DataSource] = []
        
        # Collect weather data
        origin_weather, dest_weather, route_weather = await self._collect_weather_data(
            origin_port,
            destination_port,
            departure_date,
            include_route_weather,
            warnings
        )
        
        # Collect port data
        origin_port_conditions, dest_port_conditions = await self._collect_port_data(
            origin_port,
            destination_port,
            warnings
        )
        
        # Collect carrier data
        carrier_performance, carrier_route_performance = await self._collect_carrier_data(
            carrier_code,
            origin_port,
            destination_port,
            warnings
        )
        
        # Collect climate data
        climate_indices = await self._collect_climate_data(warnings)
        
        # Extract data sources for quality gateway
        data_sources = self._extract_data_sources(
            origin_weather,
            dest_weather,
            origin_port_conditions,
            dest_port_conditions,
            carrier_performance,
            climate_indices
        )
        
        # Generate quality report
        quality_report = self.quality_gateway.check_data_quality(
            decision_type,
            data_sources
        )
        
        # Compute overall quality and confidence
        overall_quality, overall_confidence = self._compute_overall_quality(
            data_sources,
            quality_report
        )
        
        # Add warnings from quality report
        warnings.extend(quality_report.warnings)
        
        # Compute collection hash for reproducibility
        collection_hash = self._compute_collection_hash(
            origin_port,
            destination_port,
            carrier_code,
            departure_date,
            collected_at,
            data_sources
        )
        
        # Audit collection
        await self._audit_collection(
            origin_port,
            destination_port,
            carrier_code,
            data_sources,
            quality_report,
            collection_hash
        )
        
        return UnifiedShipmentData(
            origin_port=origin_port,
            destination_port=destination_port,
            cargo_type=cargo_type,
            cargo_value_usd=cargo_value_usd,
            container_count=container_count,
            departure_date=departure_date,
            expected_arrival_date=expected_arrival_date,
            carrier_code=carrier_code,
            origin_weather=origin_weather,
            destination_weather=dest_weather,
            route_weather=route_weather,
            origin_port_conditions=origin_port_conditions,
            destination_port_conditions=dest_port_conditions,
            carrier_performance=carrier_performance,
            carrier_route_performance=carrier_route_performance,
            climate_indices=climate_indices,
            data_sources=data_sources,
            data_quality_report=quality_report,
            overall_data_quality=overall_quality,
            overall_confidence=overall_confidence,
            data_warnings=warnings,
            collected_at=collected_at,
            collection_hash=collection_hash
        )
    
    async def _collect_weather_data(
        self,
        origin_port: str,
        destination_port: str,
        departure_date: date,
        include_route_weather: bool,
        warnings: List[str]
    ) -> tuple[Dict[str, Any], Dict[str, Any], Optional[Dict[str, Any]]]:
        """Collect weather data for origin, destination, and optionally route."""
        origin_weather = {}
        dest_weather = {}
        route_weather = None
        
        try:
            # Get port coordinates (simplified - would come from port database)
            origin_coords = await self._get_port_coordinates(origin_port)
            dest_coords = await self._get_port_coordinates(destination_port)
            
            if origin_coords:
                origin_weather = await self.weather_service.get_weather_for_port(
                    port_code=origin_port,
                    port_lat=origin_coords["lat"],
                    port_lng=origin_coords["lng"]
                )
            else:
                warnings.append(f"Could not get coordinates for origin port {origin_port}")
            
            if dest_coords:
                dest_weather = await self.weather_service.get_weather_for_port(
                    port_code=destination_port,
                    port_lat=dest_coords["lat"],
                    port_lng=dest_coords["lng"]
                )
            else:
                warnings.append(f"Could not get coordinates for destination port {destination_port}")
            
            # Route weather (optional, slower)
            if include_route_weather and origin_coords and dest_coords:
                try:
                    departure_datetime = datetime.combine(departure_date, datetime.min.time())
                    route_weather = await self.weather_service.get_route_weather_assessment(
                        origin_lat=origin_coords["lat"],
                        origin_lng=origin_coords["lng"],
                        dest_lat=dest_coords["lat"],
                        dest_lng=dest_coords["lng"],
                        departure_time=departure_datetime
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch route weather: {e}")
                    warnings.append(f"Route weather unavailable: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to collect weather data: {e}", exc_info=True)
            warnings.append(f"Weather data collection failed: {str(e)}")
        
        return origin_weather, dest_weather, route_weather
    
    async def _collect_port_data(
        self,
        origin_port: str,
        destination_port: str,
        warnings: List[str]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Collect port conditions for origin and destination."""
        origin_port_conditions = {}
        dest_port_conditions = {}
        
        try:
            origin_port_conditions = await self.port_service.get_port_risk_assessment(origin_port)
        except Exception as e:
            logger.warning(f"Failed to fetch origin port conditions: {e}")
            warnings.append(f"Origin port data unavailable: {str(e)}")
        
        try:
            dest_port_conditions = await self.port_service.get_port_risk_assessment(destination_port)
        except Exception as e:
            logger.warning(f"Failed to fetch destination port conditions: {e}")
            warnings.append(f"Destination port data unavailable: {str(e)}")
        
        return origin_port_conditions, dest_port_conditions
    
    async def _collect_carrier_data(
        self,
        carrier_code: Optional[str],
        origin_port: str,
        destination_port: str,
        warnings: List[str]
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Collect carrier performance data."""
        carrier_performance = None
        carrier_route_performance = None
        
        if not carrier_code:
            warnings.append("No carrier code provided, carrier data unavailable")
            return None, None
        
        try:
            carrier_performance = await self.carrier_service.get_carrier_risk_assessment(
                carrier_code=carrier_code,
                origin_port=origin_port,
                destination_port=destination_port
            )
            
            # Route-specific performance is included in carrier_performance
            if carrier_performance and "route_specific" in carrier_performance:
                carrier_route_performance = carrier_performance["route_specific"]
        except Exception as e:
            logger.warning(f"Failed to fetch carrier data: {e}")
            warnings.append(f"Carrier data unavailable: {str(e)}")
        
        return carrier_performance, carrier_route_performance
    
    async def _collect_climate_data(
        self,
        warnings: List[str]
    ) -> Dict[str, Any]:
        """Collect climate indices."""
        climate_indices = {}
        
        try:
            climate_indices = await self.climate_service.get_climate_risk_assessment()
        except Exception as e:
            logger.warning(f"Failed to fetch climate data: {e}")
            warnings.append(f"Climate data unavailable: {str(e)}")
        
        return climate_indices
    
    def _extract_data_sources(
        self,
        origin_weather: Dict[str, Any],
        dest_weather: Dict[str, Any],
        origin_port_conditions: Dict[str, Any],
        dest_port_conditions: Dict[str, Any],
        carrier_performance: Optional[Dict[str, Any]],
        climate_indices: Dict[str, Any]
    ) -> List[DataSource]:
        """Extract DataSource objects from collected data."""
        sources: List[DataSource] = []
        
        # Weather sources
        if origin_weather:
            weather_source = collect_weather_data_source(origin_weather)
            if weather_source:
                sources.append(weather_source)
        
        if dest_weather:
            weather_source = collect_weather_data_source(dest_weather)
            if weather_source:
                sources.append(weather_source)
        
        # Port sources
        if origin_port_conditions:
            port_source = collect_port_data_source(origin_port_conditions)
            if port_source:
                sources.append(port_source)
        
        if dest_port_conditions:
            port_source = collect_port_data_source(dest_port_conditions)
            if port_source:
                sources.append(port_source)
        
        # Carrier source
        if carrier_performance:
            carrier_source = collect_carrier_data_source(carrier_performance)
            if carrier_source:
                sources.append(carrier_source)
        
        # Climate source
        if climate_indices:
            climate_source = collect_climate_data_source(climate_indices)
            if climate_source:
                sources.append(climate_source)
        
        return sources
    
    def _compute_overall_quality(
        self,
        data_sources: List[DataSource],
        quality_report: DataQualityReport
    ) -> tuple[DataQualityLevel, float]:
        """Compute overall data quality and confidence."""
        if not data_sources:
            return DataQualityLevel.UNAVAILABLE, 0.0
        
        # Use quality report's overall assessment
        overall_quality = quality_report.overall_quality
        overall_confidence = quality_report.overall_confidence
        
        return overall_quality, overall_confidence
    
    def _compute_collection_hash(
        self,
        origin_port: str,
        destination_port: str,
        carrier_code: Optional[str],
        departure_date: date,
        collected_at: datetime,
        data_sources: List[DataSource]
    ) -> str:
        """
        Compute hash of collection parameters for reproducibility.
        
        This allows tracking when the same data was collected.
        """
        hash_data = {
            "origin_port": origin_port,
            "destination_port": destination_port,
            "carrier_code": carrier_code,
            "departure_date": departure_date.isoformat(),
            "collected_at": collected_at.isoformat(),
            "data_sources": [
                {
                    "name": s.source_name,
                    "type": s.source_type,
                    "quality": s.quality_level.value,
                    "timestamp": s.data_timestamp.isoformat() if s.data_timestamp else None,
                }
                for s in data_sources
            ]
        }
        
        hash_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    async def _audit_collection(
        self,
        origin_port: str,
        destination_port: str,
        carrier_code: Optional[str],
        data_sources: List[DataSource],
        quality_report: DataQualityReport,
        collection_hash: str
    ):
        """Audit data collection."""
        if not self.audit:
            return
        
        try:
            tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
            self.audit.append_event(
                tenant_id=tenant_id,
                event_type="DATA_COLLECTION",
                action="COLLECT_SHIPMENT_DATA",
                entity_type="shipment",
                entity_id=collection_hash,
                actor_type="UNIFIED_DATA_SERVICE",
                payload={
                    "origin_port": origin_port,
                    "destination_port": destination_port,
                    "carrier_code": carrier_code,
                    "data_sources": [s.source_name for s in data_sources],
                    "quality_level": quality_report.overall_quality.value,
                    "confidence": quality_report.overall_confidence,
                    "warnings": quality_report.warnings,
                    "collection_hash": collection_hash,
                }
            )
        except Exception as e:
            logger.warning(f"Failed to audit data collection: {e}")
    
    async def _get_port_coordinates(self, port_code: str) -> Optional[Dict[str, float]]:
        """Get port coordinates from database or cache."""
        try:
            from app.integrations.ports.marine_traffic import PORT_INFO_DATABASE
            port_info = PORT_INFO_DATABASE.get(port_code)
            if port_info:
                return {
                    "lat": port_info.get("lat"),
                    "lng": port_info.get("lng")
                }
        except ImportError:
            pass
        
        # Fallback: try to get from port conditions if available
        try:
            port_data = await self.port_service.get_port_risk_assessment(port_code)
            if "location" in port_data:
                return {
                    "lat": port_data["location"]["latitude"],
                    "lng": port_data["location"]["longitude"]
                }
        except Exception:
            pass
        
        return None


def create_unified_data_service(audit: Optional[Any] = None) -> UnifiedDataService:
    """Create unified data service instance."""
    return UnifiedDataService(audit)
