"""
MarineTraffic API Integration

Real-time port congestion, vessel tracking, and port conditions.
Replaces ALL hardcoded PORT_RISK_DATABASE values.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import logging

from app.config import settings
from app.core.utils.cache import get_cache, set_cache

logger = logging.getLogger(__name__)


class PortDataQuality(Enum):
    """Port data quality indicators."""
    REAL_TIME = "REAL_TIME"      # Fresh from API (< 1 hour)
    RECENT = "RECENT"            # 1-6 hours old
    STALE = "STALE"              # 6-24 hours old
    HISTORICAL = "HISTORICAL"    # > 24 hours old (from historical DB)
    FALLBACK = "FALLBACK"        # Using defaults


class CongestionLevel(Enum):
    """Port congestion levels."""
    VERY_LOW = "VERY_LOW"        # < 20% utilization
    LOW = "LOW"                  # 20-40%
    MODERATE = "MODERATE"        # 40-60%
    HIGH = "HIGH"                # 60-80%
    VERY_HIGH = "VERY_HIGH"      # 80-90%
    CRITICAL = "CRITICAL"        # > 90%


@dataclass
class PortConditions:
    """Real-time port conditions with quality metadata."""
    port_code: str  # UN/LOCODE
    port_name: str
    country: str
    
    # Location
    latitude: float
    longitude: float
    
    # Current conditions
    congestion_level: CongestionLevel
    congestion_score: float  # 0-1
    avg_waiting_time_hours: float
    avg_berth_time_hours: float
    vessels_at_berth: int
    vessels_at_anchor: int
    vessels_expected_24h: int
    
    # Port efficiency
    berth_utilization_pct: float
    crane_availability_pct: float
    
    # Weather impact
    weather_delays: bool
    weather_delay_hours: float
    
    # Labor/strikes
    labor_disruption: bool
    labor_disruption_severity: Optional[str]
    
    # Risk score (computed from conditions)
    port_risk_score: float  # 0-10 scale
    risk_factors: List[Dict[str, Any]]
    
    # Quality metadata - CRITICAL
    data_quality: PortDataQuality
    data_source: str
    fetched_at: datetime
    data_timestamp: datetime  # When MarineTraffic captured this
    data_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "port_code": self.port_code,
            "port_name": self.port_name,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "congestion": {
                "level": self.congestion_level.value,
                "score": self.congestion_score,
                "avg_waiting_hours": self.avg_waiting_time_hours,
                "avg_berth_hours": self.avg_berth_time_hours,
                "vessels_at_berth": self.vessels_at_berth,
                "vessels_at_anchor": self.vessels_at_anchor,
                "vessels_expected_24h": self.vessels_expected_24h,
            },
            "efficiency": {
                "berth_utilization_pct": self.berth_utilization_pct,
                "crane_availability_pct": self.crane_availability_pct,
            },
            "disruptions": {
                "weather_delays": self.weather_delays,
                "weather_delay_hours": self.weather_delay_hours,
                "labor_disruption": self.labor_disruption,
                "labor_disruption_severity": self.labor_disruption_severity,
            },
            "risk": {
                "port_risk_score": self.port_risk_score,
                "risk_factors": self.risk_factors,
            },
            "data_quality": {
                "quality": self.data_quality.value,
                "source": self.data_source,
                "fetched_at": self.fetched_at.isoformat(),
                "data_timestamp": self.data_timestamp.isoformat(),
                "data_hash": self.data_hash,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PortConditions":
        """Create from dictionary."""
        data = data.copy()
        # Convert nested dicts back
        if "congestion" in data:
            congestion = data.pop("congestion")
            data.update({
                "congestion_level": CongestionLevel(congestion["level"]),
                "congestion_score": congestion["score"],
                "avg_waiting_time_hours": congestion["avg_waiting_hours"],
                "avg_berth_time_hours": congestion.get("avg_berth_hours", 0),
                "vessels_at_berth": congestion["vessels_at_berth"],
                "vessels_at_anchor": congestion["vessels_at_anchor"],
                "vessels_expected_24h": congestion.get("vessels_expected_24h", 0),
            })
        if "efficiency" in data:
            efficiency = data.pop("efficiency")
            data.update({
                "berth_utilization_pct": efficiency["berth_utilization_pct"],
                "crane_availability_pct": efficiency.get("crane_availability_pct", 100.0),
            })
        if "disruptions" in data:
            disruptions = data.pop("disruptions")
            data.update({
                "weather_delays": disruptions.get("weather_delays", False),
                "weather_delay_hours": disruptions.get("weather_delay_hours", 0.0),
                "labor_disruption": disruptions.get("labor_disruption", False),
                "labor_disruption_severity": disruptions.get("labor_disruption_severity"),
            })
        if "risk" in data:
            risk = data.pop("risk")
            data.update({
                "port_risk_score": risk["port_risk_score"],
                "risk_factors": risk["risk_factors"],
            })
        if "data_quality" in data:
            quality = data.pop("data_quality")
            data.update({
                "data_quality": PortDataQuality(quality["quality"]),
                "data_source": quality["source"],
                "fetched_at": datetime.fromisoformat(quality["fetched_at"].replace("Z", "+00:00")),
                "data_timestamp": datetime.fromisoformat(quality["data_timestamp"].replace("Z", "+00:00")),
                "data_hash": quality["data_hash"],
            })
        return cls(**data)


# Port database with ONLY static info (no risk scores!)
# Risk scores now come from real-time data
PORT_INFO_DATABASE = {
    "CNSHA": {"name": "Shanghai", "country": "China", "lat": 31.23, "lng": 121.47, "infrastructure_rating": 9},
    "SGSIN": {"name": "Singapore", "country": "Singapore", "lat": 1.29, "lng": 103.85, "infrastructure_rating": 10},
    "NLRTM": {"name": "Rotterdam", "country": "Netherlands", "lat": 51.92, "lng": 4.48, "infrastructure_rating": 9},
    "DEHAM": {"name": "Hamburg", "country": "Germany", "lat": 53.55, "lng": 9.99, "infrastructure_rating": 9},
    "USLAX": {"name": "Los Angeles", "country": "USA", "lat": 33.74, "lng": -118.27, "infrastructure_rating": 8},
    "USNYC": {"name": "New York", "country": "USA", "lat": 40.69, "lng": -74.04, "infrastructure_rating": 8},
    "HKHKG": {"name": "Hong Kong", "country": "China", "lat": 22.29, "lng": 114.19, "infrastructure_rating": 9},
    "JPYOK": {"name": "Yokohama", "country": "Japan", "lat": 35.44, "lng": 139.64, "infrastructure_rating": 9},
    "KRPUS": {"name": "Busan", "country": "South Korea", "lat": 35.10, "lng": 129.04, "infrastructure_rating": 9},
    "AEJEA": {"name": "Jebel Ali", "country": "UAE", "lat": 25.01, "lng": 55.06, "infrastructure_rating": 9},
    "VNSGN": {"name": "Ho Chi Minh", "country": "Vietnam", "lat": 10.76, "lng": 106.66, "infrastructure_rating": 7},
    "VNHPH": {"name": "Hai Phong", "country": "Vietnam", "lat": 20.85, "lng": 106.68, "infrastructure_rating": 7},
    "USLGB": {"name": "Long Beach", "country": "USA", "lat": 33.77, "lng": -118.19, "infrastructure_rating": 8},
    "USOAK": {"name": "Oakland", "country": "USA", "lat": 37.80, "lng": -122.28, "infrastructure_rating": 8},
    "CNSHE": {"name": "Shenzhen", "country": "China", "lat": 22.53, "lng": 114.13, "infrastructure_rating": 9},
    "CNNBO": {"name": "Ningbo", "country": "China", "lat": 29.87, "lng": 121.55, "infrastructure_rating": 9},
}


class MarineTrafficClient:
    """
    MarineTraffic API client for port intelligence.
    
    Provides real-time port conditions to replace hardcoded PORT_RISK_DATABASE.
    """
    
    BASE_URL = "https://services.marinetraffic.com/api"
    
    def __init__(
        self,
        api_key: str,
        audit_ledger: Optional[Any] = None
    ):
        self.api_key = api_key
        self.audit = audit_ledger
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Cache TTLs
        self.PORT_CONDITIONS_TTL = 3600  # 1 hour
        self.VESSEL_POSITION_TTL = 300   # 5 minutes
    
    async def get_port_conditions(
        self,
        port_code: str
    ) -> PortConditions:
        """
        Get real-time port conditions.
        
        This is the PRIMARY replacement for hardcoded port risk data.
        """
        cache_key = f"port:conditions:{port_code}"
        
        # Try cache
        cached = get_cache(cache_key)
        if cached:
            try:
                conditions = PortConditions.from_dict(cached)
                # Update quality based on age
                age = datetime.utcnow() - conditions.data_timestamp
                if age < timedelta(hours=1):
                    conditions.data_quality = PortDataQuality.REAL_TIME
                elif age < timedelta(hours=6):
                    conditions.data_quality = PortDataQuality.RECENT
                else:
                    conditions.data_quality = PortDataQuality.STALE
                return conditions
            except Exception as e:
                logger.warning(f"Failed to deserialize cached port data: {e}")
        
        try:
            # Fetch from MarineTraffic
            conditions = await self._fetch_port_conditions(port_code)
            
            # Cache
            set_cache(
                cache_key,
                conditions.to_dict(),
                ttl=self.PORT_CONDITIONS_TTL
            )
            
            # Audit
            if self.audit:
                try:
                    tenant_id = getattr(settings, 'DEFAULT_TENANT_ID', None) or "system"
                    self.audit.append_event(
                        tenant_id=tenant_id,
                        event_type="DATA_FETCH",
                        action="PORT_CONDITIONS",
                        entity_type="port",
                        entity_id=port_code,
                        actor_type="SYSTEM",
                        payload={
                            "quality": conditions.data_quality.value,
                            "congestion_score": conditions.congestion_score,
                            "data_hash": conditions.data_hash
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to audit port fetch: {e}")
            
            return conditions
            
        except Exception as e:
            logger.error(f"Error fetching port conditions: {e}")
            # Return fallback with explicit quality flag
            return self._create_fallback_conditions(port_code, str(e))
    
    async def get_port_congestion_history(
        self,
        port_code: str,
        days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Get historical port congestion for calibration.
        
        Used to calibrate port risk weights against actual delays.
        """
        cache_key = f"port:history:{port_code}:{days}"
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        # MarineTraffic historical congestion endpoint
        url = f"{self.BASE_URL}/portcongestion/{port_code}/historicalstats/v:3"
        params = {
            "protocol": "jsono",
            "apikey": self.api_key,
            "days": days
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache for 24 hours (historical data doesn't change)
            set_cache(cache_key, data, ttl=86400)
            return data
        except Exception as e:
            logger.error(f"Error fetching port history: {e}")
            return []
    
    async def get_vessels_in_port(
        self,
        port_code: str
    ) -> Dict[str, Any]:
        """
        Get current vessels in port area.
        
        Used for congestion calculation and risk assessment.
        """
        cache_key = f"port:vessels:{port_code}"
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        url = f"{self.BASE_URL}/exportvessels/v:8"
        params = {
            "protocol": "jsono",
            "apikey": self.api_key,
            "portcode": port_code,
            "msgtype": "full"
        }
        
        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            vessels = response.json()
            
            # Categorize vessels
            at_berth = [v for v in vessels if v.get("NAVSTAT") == "5"]
            at_anchor = [v for v in vessels if v.get("NAVSTAT") == "1"]
            
            result = {
                "port_code": port_code,
                "total_vessels": len(vessels),
                "vessels_at_berth": len(at_berth),
                "vessels_at_anchor": len(at_anchor),
                "vessel_details": vessels[:50],  # Limit for response size
                "fetched_at": datetime.utcnow().isoformat()
            }
            
            set_cache(cache_key, result, ttl=self.VESSEL_POSITION_TTL)
            return result
        except Exception as e:
            logger.error(f"Error fetching vessels: {e}")
            return {
                "port_code": port_code,
                "total_vessels": 0,
                "vessels_at_berth": 0,
                "vessels_at_anchor": 0,
                "vessel_details": [],
                "fetched_at": datetime.utcnow().isoformat()
            }
    
    async def _fetch_port_conditions(
        self,
        port_code: str
    ) -> PortConditions:
        """Fetch and parse port conditions from MarineTraffic."""
        # Get port info first
        port_info = self._get_port_info(port_code)
        
        # Port congestion endpoint
        congestion_url = f"{self.BASE_URL}/portcongestion/{port_code}/v:3"
        params = {
            "protocol": "jsono",
            "apikey": self.api_key
        }
        
        response = await self.client.get(congestion_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Get vessel counts
        vessels = await self.get_vessels_in_port(port_code)
        
        # Parse congestion data
        avg_waiting = float(data.get("AVG_WAITING_TIME", 0))
        avg_berth = float(data.get("AVG_BERTH_TIME", 0))
        berth_util = float(data.get("BERTH_UTILIZATION", 70.0))
        
        # Calculate congestion score (0-1)
        # Based on waiting time: 0h = 0, 48h+ = 1
        congestion_score = min(avg_waiting / 48, 1.0)
        # Also factor in berth utilization
        congestion_score = max(congestion_score, berth_util / 100)
        
        # Determine congestion level
        if congestion_score < 0.2:
            congestion_level = CongestionLevel.VERY_LOW
        elif congestion_score < 0.4:
            congestion_level = CongestionLevel.LOW
        elif congestion_score < 0.6:
            congestion_level = CongestionLevel.MODERATE
        elif congestion_score < 0.8:
            congestion_level = CongestionLevel.HIGH
        elif congestion_score < 0.9:
            congestion_level = CongestionLevel.VERY_HIGH
        else:
            congestion_level = CongestionLevel.CRITICAL
        
        # Calculate risk score (0-10)
        risk_score, risk_factors = self._compute_port_risk(
            congestion_score=congestion_score,
            avg_waiting=avg_waiting,
            vessels_at_anchor=vessels["vessels_at_anchor"],
            port_info=port_info
        )
        
        now = datetime.utcnow()
        data_timestamp = datetime.fromisoformat(
            data.get("TIMESTAMP", now.isoformat()).replace("Z", "+00:00")
        ) if data.get("TIMESTAMP") else now
        
        conditions_data = {
            "port_code": port_code,
            "port_name": port_info.get("name", port_code),
            "country": port_info.get("country", "Unknown"),
            "latitude": port_info.get("lat", 0.0),
            "longitude": port_info.get("lng", 0.0),
            "congestion_level": congestion_level,
            "congestion_score": congestion_score,
            "avg_waiting_time_hours": avg_waiting,
            "avg_berth_time_hours": avg_berth,
            "vessels_at_berth": vessels["vessels_at_berth"],
            "vessels_at_anchor": vessels["vessels_at_anchor"],
            "vessels_expected_24h": int(data.get("EXPECTED_ARRIVALS", 0)),
            "berth_utilization_pct": berth_util,
            "crane_availability_pct": 100.0,  # Would need separate API
            "weather_delays": False,  # Combine with weather service
            "weather_delay_hours": 0.0,
            "labor_disruption": False,  # Would need news API
            "labor_disruption_severity": None,
            "port_risk_score": risk_score,
            "risk_factors": risk_factors,
            "data_quality": PortDataQuality.REAL_TIME,
            "data_source": "marinetraffic",
            "fetched_at": now,
            "data_timestamp": data_timestamp,
        }
        
        conditions_data["data_hash"] = self._compute_hash(conditions_data)
        
        return PortConditions(**conditions_data)
    
    def _compute_port_risk(
        self,
        congestion_score: float,
        avg_waiting: float,
        vessels_at_anchor: int,
        port_info: Dict[str, Any]
    ) -> tuple[float, List[Dict[str, Any]]]:
        """
        Compute port risk score from real data.
        
        THIS REPLACES HARDCODED PORT_RISK_DATABASE VALUES.
        """
        risk_score = 0.0
        factors = []
        
        # Congestion risk (0-4 points)
        congestion_risk = congestion_score * 4
        risk_score += congestion_risk
        factors.append({
            "factor": "congestion",
            "value": congestion_score,
            "contribution": congestion_risk,
            "description": f"Congestion score {congestion_score:.2f}"
        })
        
        # Waiting time risk (0-3 points)
        waiting_risk = min(avg_waiting / 72, 1.0) * 3
        risk_score += waiting_risk
        factors.append({
            "factor": "waiting_time",
            "value": avg_waiting,
            "unit": "hours",
            "contribution": waiting_risk,
            "description": f"Average waiting time {avg_waiting:.1f} hours"
        })
        
        # Anchor queue risk (0-2 points)
        anchor_risk = min(vessels_at_anchor / 50, 1.0) * 2
        risk_score += anchor_risk
        factors.append({
            "factor": "anchor_queue",
            "value": vessels_at_anchor,
            "contribution": anchor_risk,
            "description": f"{vessels_at_anchor} vessels at anchor"
        })
        
        # Infrastructure risk from port info (0-1 point)
        infra_rating = port_info.get("infrastructure_rating", 7)
        infra_risk = (10 - infra_rating) / 10
        risk_score += infra_risk
        factors.append({
            "factor": "infrastructure",
            "value": infra_rating,
            "contribution": infra_risk,
            "description": f"Infrastructure rating {infra_rating}/10"
        })
        
        return risk_score, factors
    
    def _get_port_info(self, port_code: str) -> Dict[str, Any]:
        """Get static port information from database."""
        return PORT_INFO_DATABASE.get(port_code.upper(), {
            "name": port_code,
            "country": "Unknown",
            "lat": 0.0,
            "lng": 0.0,
            "infrastructure_rating": 7.0
        })
    
    def _get_historical_average(self, port_code: str) -> Dict[str, Any]:
        """Get historical average for fallback."""
        port_info = self._get_port_info(port_code)
        return {
            **port_info,
            "avg_waiting_hours": 24.0,
            "avg_berth_hours": 48.0,
        }
    
    def _create_fallback_conditions(
        self,
        port_code: str,
        error_reason: str
    ) -> PortConditions:
        """
        Create fallback with EXPLICIT quality flag.
        
        Uses historical averages from port database.
        """
        # Try to get from historical database
        historical = self._get_historical_average(port_code)
        
        now = datetime.utcnow()
        
        return PortConditions(
            port_code=port_code,
            port_name=historical.get("name", port_code),
            country=historical.get("country", "Unknown"),
            latitude=historical.get("lat", 0.0),
            longitude=historical.get("lng", 0.0),
            congestion_level=CongestionLevel.MODERATE,
            congestion_score=0.5,  # Assume moderate
            avg_waiting_time_hours=historical.get("avg_waiting_hours", 24.0),
            avg_berth_time_hours=historical.get("avg_berth_hours", 48.0),
            vessels_at_berth=0,
            vessels_at_anchor=0,
            vessels_expected_24h=0,
            berth_utilization_pct=70.0,
            crane_availability_pct=100.0,
            weather_delays=False,
            weather_delay_hours=0.0,
            labor_disruption=False,
            labor_disruption_severity=None,
            port_risk_score=5.0,  # Middle of scale
            risk_factors=[{
                "factor": "fallback_data",
                "description": f"Using fallback data: {error_reason}",
                "confidence": 0.5
            }],
            data_quality=PortDataQuality.FALLBACK,
            data_source="historical_average",
            fetched_at=now,
            data_timestamp=now,
            data_hash=self._compute_hash({"port_code": port_code, "fallback": True})
        )
    
    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        """Compute hash for audit trail."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def create_port_client(audit_ledger: Optional[Any] = None) -> MarineTrafficClient:
    """Create configured port client."""
    api_key = settings.MARINE_TRAFFIC_API_KEY or settings.MARINETRAFFIC_API_KEY
    if not api_key:
        raise ValueError("MARINE_TRAFFIC_API_KEY or MARINETRAFFIC_API_KEY not configured")
    
    return MarineTrafficClient(
        api_key=api_key,
        audit_ledger=audit_ledger
    )
