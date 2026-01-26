"""
AIS Vessel Tracking Service

Provides:
1. Real-time vessel positions (lat/lon, speed, heading)
2. Vessel database lookup (IMO, MMSI, flag, type)
3. Voyage tracking (origin, destination, ETA)
4. Historical track playback
5. Geofencing alerts
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

from app.core.logging import get_logger
from app.integrations.ais.models import (
    VesselPosition, VesselInfo, VoyageInfo, TrackPoint, GeofenceAlert,
    VesselType, NavigationStatus
)
from app.integrations.ais.marine_traffic_ais import MarineTrafficAISClient
from app.integrations.ais.vessel_finder import VesselFinderClient
from app.core.data_quality.gateway import DataQualityGateway, DataQualityLevel


logger = get_logger(__name__)


class AISService:
    """
    Unified AIS service for vessel tracking.
    
    Supports multiple providers:
    - MarineTraffic (primary)
    - VesselFinder (fallback)
    """
    
    # High-risk zones for geofencing
    HIGH_RISK_ZONES = {
        "GULF_OF_ADEN": {
            "name": "Gulf of Aden / Somali Waters",
            "polygon": [(11.5, 43.0), (15.0, 51.0), (12.0, 51.0), (11.5, 43.0)],
            "risk_level": "CRITICAL"
        },
        "STRAIT_OF_MALACCA": {
            "name": "Strait of Malacca",
            "polygon": [(1.0, 100.0), (6.0, 100.0), (6.0, 105.0), (1.0, 105.0)],
            "risk_level": "HIGH"
        },
        "GULF_OF_GUINEA": {
            "name": "Gulf of Guinea",
            "polygon": [(0.0, -5.0), (6.0, -5.0), (6.0, 10.0), (0.0, 10.0)],
            "risk_level": "CRITICAL"
        },
        "SOUTH_CHINA_SEA": {
            "name": "South China Sea (Disputed)",
            "polygon": [(5.0, 109.0), (20.0, 109.0), (20.0, 121.0), (5.0, 121.0)],
            "risk_level": "MEDIUM"
        },
        "SINGAPORE_STRAIT": {
            "name": "Singapore Strait",
            "polygon": [(1.0, 103.5), (1.5, 103.5), (1.5, 104.5), (1.0, 104.5)],
            "risk_level": "MEDIUM"
        },
        "RED_SEA": {
            "name": "Red Sea / Bab el-Mandeb",
            "polygon": [(12.0, 42.0), (15.0, 42.0), (15.0, 45.0), (12.0, 45.0)],
            "risk_level": "HIGH"
        }
    }
    
    def __init__(
        self,
        marine_traffic_client: MarineTrafficAISClient,
        vessel_finder_client: Optional[VesselFinderClient] = None,
        data_quality_gateway: Optional[DataQualityGateway] = None,
        cache_ttl_seconds: int = 60
    ):
        self.marine_traffic = marine_traffic_client
        self.vessel_finder = vessel_finder_client
        self.data_quality = data_quality_gateway
        self.cache_ttl = cache_ttl_seconds
        
        # In-memory cache
        self._position_cache: Dict[str, Tuple[VesselPosition, datetime]] = {}
        self._vessel_cache: Dict[str, Tuple[VesselInfo, datetime]] = {}
    
    async def get_vessel_position(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None,
        vessel_name: Optional[str] = None
    ) -> Optional[VesselPosition]:
        """
        Get real-time vessel position.
        
        Args:
            mmsi: Maritime Mobile Service Identity (9 digits)
            imo: International Maritime Organization number (7 digits)
            vessel_name: Vessel name (fuzzy match)
        
        Returns:
            VesselPosition or None if not found
        """
        if not any([mmsi, imo, vessel_name]):
            raise ValueError("Must provide mmsi, imo, or vessel_name")
        
        cache_key = mmsi or imo or vessel_name
        
        # Check cache
        if cache_key in self._position_cache:
            cached, cached_at = self._position_cache[cache_key]
            if (datetime.utcnow() - cached_at).total_seconds() < self.cache_ttl:
                logger.debug(f"Position cache hit for {cache_key}")
                return cached
        
        # Try primary provider
        position = None
        try:
            position = await self.marine_traffic.get_vessel_position(
                mmsi=mmsi, imo=imo, vessel_name=vessel_name
            )
        except Exception as e:
            logger.warning(f"MarineTraffic failed: {e}")
            
            # Try fallback
            if self.vessel_finder:
                try:
                    position = await self.vessel_finder.get_vessel_position(
                        mmsi=mmsi, imo=imo, vessel_name=vessel_name
                    )
                except Exception as e2:
                    logger.error(f"VesselFinder also failed: {e2}")
        
        if position:
            # Cache result
            self._position_cache[cache_key] = (position, datetime.utcnow())
            
            # Also cache by other identifiers
            if position.mmsi:
                self._position_cache[position.mmsi] = (position, datetime.utcnow())
            if position.imo:
                self._position_cache[position.imo] = (position, datetime.utcnow())
            
            # Log data access (if data quality gateway is available)
            if self.data_quality:
                logger.info(
                    f"AIS data accessed: mmsi={position.mmsi}, "
                    f"source={position.data_source}, quality=REAL_TIME"
                )
        
        return position
    
    async def get_vessel_info(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None
    ) -> Optional[VesselInfo]:
        """
        Get static vessel information.
        """
        if not mmsi and not imo:
            raise ValueError("Must provide mmsi or imo")
        
        cache_key = f"info:{mmsi or imo}"
        
        # Check cache (longer TTL for static data)
        if cache_key in self._vessel_cache:
            cached, cached_at = self._vessel_cache[cache_key]
            if (datetime.utcnow() - cached_at).total_seconds() < 3600:  # 1 hour
                return cached
        
        try:
            vessel_info = await self.marine_traffic.get_vessel_info(
                mmsi=mmsi, imo=imo
            )
            
            if vessel_info:
                self._vessel_cache[cache_key] = (vessel_info, datetime.utcnow())
            
            return vessel_info
            
        except Exception as e:
            logger.error(f"Failed to get vessel info: {e}")
            return None
    
    async def get_voyage_info(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None
    ) -> Optional[VoyageInfo]:
        """
        Get current voyage information.
        """
        try:
            return await self.marine_traffic.get_voyage_info(mmsi=mmsi, imo=imo)
        except Exception as e:
            logger.error(f"Failed to get voyage info: {e}")
            return None
    
    async def get_historical_track(
        self,
        mmsi: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        interval_minutes: int = 30
    ) -> List[TrackPoint]:
        """
        Get historical vessel track.
        
        Args:
            mmsi: Vessel MMSI
            start_time: Track start time
            end_time: Track end time (default: now)
            interval_minutes: Point interval
        
        Returns:
            List of track points
        """
        end_time = end_time or datetime.utcnow()
        
        try:
            return await self.marine_traffic.get_historical_track(
                mmsi=mmsi,
                start_time=start_time,
                end_time=end_time,
                interval_minutes=interval_minutes
            )
        except Exception as e:
            logger.error(f"Failed to get historical track: {e}")
            return []
    
    async def search_vessels_in_area(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        vessel_types: Optional[List[VesselType]] = None
    ) -> List[VesselPosition]:
        """
        Search for vessels in a geographic area.
        """
        try:
            return await self.marine_traffic.search_vessels_in_area(
                min_lat=min_lat,
                min_lon=min_lon,
                max_lat=max_lat,
                max_lon=max_lon,
                vessel_types=vessel_types
            )
        except Exception as e:
            logger.error(f"Failed to search vessels in area: {e}")
            return []
    
    async def check_vessel_in_high_risk_zone(
        self,
        position: VesselPosition
    ) -> List[GeofenceAlert]:
        """
        Check if vessel is in or approaching high-risk zones.
        """
        alerts = []
        
        for zone_id, zone_info in self.HIGH_RISK_ZONES.items():
            # Check if position is inside zone
            is_inside = self._point_in_polygon(
                position.latitude,
                position.longitude,
                zone_info["polygon"]
            )
            
            if is_inside:
                alerts.append(GeofenceAlert(
                    alert_id=f"{position.mmsi}-{zone_id}-{datetime.utcnow().timestamp()}",
                    mmsi=position.mmsi,
                    vessel_name=position.vessel_name,
                    alert_type="INSIDE",
                    zone_name=zone_info["name"],
                    zone_type="HIGH_RISK",
                    position=position,
                    timestamp=datetime.utcnow(),
                    severity="CRITICAL" if zone_info["risk_level"] == "CRITICAL" else "WARNING"
                ))
            else:
                # Check if approaching (within 50nm)
                distance = self._distance_to_polygon(
                    position.latitude,
                    position.longitude,
                    zone_info["polygon"]
                )
                
                if distance < 50:  # 50 nautical miles
                    # Estimate time to zone based on current speed and heading
                    time_to_zone = int((distance / max(position.speed_knots, 0.1)) * 60)
                    
                    alerts.append(GeofenceAlert(
                        alert_id=f"{position.mmsi}-{zone_id}-approaching",
                        mmsi=position.mmsi,
                        vessel_name=position.vessel_name,
                        alert_type="APPROACHING",
                        zone_name=zone_info["name"],
                        zone_type="HIGH_RISK",
                        position=position,
                        distance_to_zone_nm=distance,
                        time_to_zone_minutes=time_to_zone,
                        timestamp=datetime.utcnow(),
                        severity="WARNING"
                    ))
        
        return alerts
    
    async def assess_vessel_risk(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None
    ) -> Dict:
        """
        Comprehensive vessel risk assessment.
        
        Returns risk score and factors.
        """
        # Get vessel data
        position = await self.get_vessel_position(mmsi=mmsi, imo=imo)
        vessel_info = await self.get_vessel_info(mmsi=mmsi, imo=imo)
        voyage_info = await self.get_voyage_info(mmsi=mmsi, imo=imo)
        
        if not position:
            return {"error": "Vessel not found", "risk_score": None}
        
        risk_factors = {}
        total_risk = 0.0
        
        # 1. Zone risk
        zone_alerts = await self.check_vessel_in_high_risk_zone(position)
        if zone_alerts:
            critical_zones = [a for a in zone_alerts if a.severity == "CRITICAL"]
            warning_zones = [a for a in zone_alerts if a.severity == "WARNING"]
            
            zone_risk = len(critical_zones) * 0.3 + len(warning_zones) * 0.1
            risk_factors["zone_risk"] = min(zone_risk, 0.4)
            total_risk += risk_factors["zone_risk"]
        
        # 2. Vessel age risk
        if vessel_info and vessel_info.year_built:
            age = datetime.utcnow().year - vessel_info.year_built
            age_risk = min(age / 30, 1.0) * 0.15  # Max 15% for 30+ year old
            risk_factors["age_risk"] = age_risk
            total_risk += age_risk
        
        # 3. Flag risk (FOC - Flag of Convenience)
        foc_flags = {"PA", "LR", "MH", "BS", "MT", "CY", "HK", "SG"}
        if vessel_info and vessel_info.flag_code in foc_flags:
            risk_factors["flag_risk"] = 0.05
            total_risk += 0.05
        
        # 4. Sanctions risk
        if vessel_info and vessel_info.is_sanctioned:
            risk_factors["sanctions_risk"] = 0.5
            total_risk += 0.5
        
        # 5. Navigation status risk
        risky_statuses = {NavigationStatus.NOT_UNDER_COMMAND, NavigationStatus.AGROUND}
        if position.navigation_status in risky_statuses:
            risk_factors["navigation_risk"] = 0.2
            total_risk += 0.2
        
        # 6. Speed anomaly (too slow or too fast)
        if vessel_info and vessel_info.max_speed_knots:
            if position.speed_knots > vessel_info.max_speed_knots * 1.1:
                risk_factors["speed_anomaly"] = 0.1
                total_risk += 0.1
        
        return {
            "mmsi": position.mmsi,
            "imo": position.imo,
            "vessel_name": position.vessel_name,
            "risk_score": min(total_risk, 1.0),
            "risk_grade": self._score_to_grade(total_risk),
            "risk_factors": risk_factors,
            "position": {
                "latitude": position.latitude,
                "longitude": position.longitude,
                "speed_knots": position.speed_knots,
                "heading": position.heading
            },
            "zone_alerts": [
                {
                    "zone": a.zone_name,
                    "type": a.alert_type,
                    "severity": a.severity
                }
                for a in zone_alerts
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _point_in_polygon(
        self,
        lat: float,
        lon: float,
        polygon: List[Tuple[float, float]]
    ) -> bool:
        """Check if point is inside polygon using ray casting."""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if lat > min(p1y, p2y):
                if lat <= max(p1y, p2y):
                    if lon <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (lat - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or lon <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _distance_to_polygon(
        self,
        lat: float,
        lon: float,
        polygon: List[Tuple[float, float]]
    ) -> float:
        """Calculate minimum distance to polygon in nautical miles."""
        min_distance = float('inf')
        
        for point in polygon:
            distance = self._haversine_distance(lat, lon, point[0], point[1])
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate distance between two points in nautical miles."""
        R = 3440.065  # Earth radius in nautical miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def _score_to_grade(self, score: float) -> str:
        """Convert risk score to grade."""
        if score < 0.2:
            return "A"
        elif score < 0.4:
            return "B"
        elif score < 0.6:
            return "C"
        elif score < 0.8:
            return "D"
        else:
            return "F"
