"""
Project44 API Integration

Real-time carrier performance, reliability, and tracking data.
Replaces static carrier ratings in the system.
"""

import httpx
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


class CarrierDataQuality(Enum):
    """Carrier data quality indicators."""
    REAL_TIME = "REAL_TIME"
    CACHED = "CACHED"
    HISTORICAL = "HISTORICAL"
    FALLBACK = "FALLBACK"


@dataclass
class CarrierPerformance:
    """Carrier performance metrics with quality tracking."""
    carrier_code: str  # SCAC code
    carrier_name: str
    
    # Reliability metrics
    on_time_delivery_pct: float
    on_time_pickup_pct: float
    schedule_reliability_pct: float
    
    # Performance metrics
    avg_transit_time_variance_hours: float
    avg_dwell_time_hours: float
    claim_frequency_pct: float
    damage_rate_pct: float
    
    # Capacity metrics
    capacity_utilization_pct: float
    booking_acceptance_rate_pct: float
    
    # Service metrics
    tracking_quality_score: float  # 0-1
    documentation_quality_score: float  # 0-1
    communication_score: float  # 0-1
    
    # Overall rating
    carrier_rating: float  # 1-5 scale
    carrier_risk_score: float  # 0-10 scale
    risk_factors: List[Dict[str, Any]]
    
    # Quality metadata
    data_quality: CarrierDataQuality
    data_source: str
    sample_size: int  # Number of shipments used
    sample_period_days: int
    fetched_at: datetime
    data_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "carrier_code": self.carrier_code,
            "carrier_name": self.carrier_name,
            "reliability": {
                "on_time_delivery_pct": self.on_time_delivery_pct,
                "on_time_pickup_pct": self.on_time_pickup_pct,
                "schedule_reliability_pct": self.schedule_reliability_pct,
            },
            "performance": {
                "avg_transit_variance_hours": self.avg_transit_time_variance_hours,
                "avg_dwell_time_hours": self.avg_dwell_time_hours,
                "claim_frequency_pct": self.claim_frequency_pct,
                "damage_rate_pct": self.damage_rate_pct,
            },
            "capacity": {
                "capacity_utilization_pct": self.capacity_utilization_pct,
                "booking_acceptance_rate_pct": self.booking_acceptance_rate_pct,
            },
            "service": {
                "tracking_quality": self.tracking_quality_score,
                "documentation_quality": self.documentation_quality_score,
                "communication_score": self.communication_score,
            },
            "rating": {
                "carrier_rating": self.carrier_rating,
                "carrier_risk_score": self.carrier_risk_score,
                "risk_factors": self.risk_factors,
            },
            "data_quality": {
                "quality": self.data_quality.value,
                "source": self.data_source,
                "sample_size": self.sample_size,
                "sample_period_days": self.sample_period_days,
                "fetched_at": self.fetched_at.isoformat(),
                "data_hash": self.data_hash,
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CarrierPerformance":
        """Create from dictionary."""
        data = data.copy()
        # Convert nested dicts back
        if "reliability" in data:
            reliability = data.pop("reliability")
            data.update({
                "on_time_delivery_pct": reliability["on_time_delivery_pct"],
                "on_time_pickup_pct": reliability["on_time_pickup_pct"],
                "schedule_reliability_pct": reliability["schedule_reliability_pct"],
            })
        if "performance" in data:
            performance = data.pop("performance")
            data.update({
                "avg_transit_time_variance_hours": performance["avg_transit_variance_hours"],
                "avg_dwell_time_hours": performance["avg_dwell_time_hours"],
                "claim_frequency_pct": performance["claim_frequency_pct"],
                "damage_rate_pct": performance["damage_rate_pct"],
            })
        if "capacity" in data:
            capacity = data.pop("capacity")
            data.update({
                "capacity_utilization_pct": capacity["capacity_utilization_pct"],
                "booking_acceptance_rate_pct": capacity["booking_acceptance_rate_pct"],
            })
        if "service" in data:
            service = data.pop("service")
            data.update({
                "tracking_quality_score": service["tracking_quality"],
                "documentation_quality_score": service["documentation_quality"],
                "communication_score": service["communication_score"],
            })
        if "rating" in data:
            rating = data.pop("rating")
            data.update({
                "carrier_rating": rating["carrier_rating"],
                "carrier_risk_score": rating["carrier_risk_score"],
                "risk_factors": rating["risk_factors"],
            })
        if "data_quality" in data:
            quality = data.pop("data_quality")
            data.update({
                "data_quality": CarrierDataQuality(quality["quality"]),
                "data_source": quality["source"],
                "sample_size": quality["sample_size"],
                "sample_period_days": quality["sample_period_days"],
                "fetched_at": datetime.fromisoformat(quality["fetched_at"].replace("Z", "+00:00")),
                "data_hash": quality["data_hash"],
            })
        return cls(**data)


@dataclass
class CarrierRoutePerformance:
    """Carrier performance on specific route."""
    carrier_code: str
    origin_port: str
    destination_port: str
    
    # Route-specific metrics
    route_on_time_pct: float
    route_avg_transit_days: float
    route_transit_variance_days: float
    route_claim_rate_pct: float
    
    # Comparison to carrier average
    vs_carrier_avg_on_time: float  # Difference in %
    vs_carrier_avg_transit: float  # Difference in days
    
    # Sample info
    shipment_count: int
    period_days: int
    
    data_quality: CarrierDataQuality
    data_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "carrier_code": self.carrier_code,
            "origin_port": self.origin_port,
            "destination_port": self.destination_port,
            "route_on_time_pct": self.route_on_time_pct,
            "route_avg_transit_days": self.route_avg_transit_days,
            "route_transit_variance_days": self.route_transit_variance_days,
            "route_claim_rate_pct": self.route_claim_rate_pct,
            "vs_carrier_avg_on_time": self.vs_carrier_avg_on_time,
            "vs_carrier_avg_transit": self.vs_carrier_avg_transit,
            "shipment_count": self.shipment_count,
            "period_days": self.period_days,
            "data_quality": self.data_quality.value,
            "data_hash": self.data_hash,
        }


class Project44Client:
    """
    Project44 API client for carrier intelligence.
    
    Replaces hardcoded carrier ratings with real performance data.
    """
    
    BASE_URL = "https://api.project44.com/api/v4"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        audit_ledger: Optional[Any] = None
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.audit = audit_ledger
        self.client = httpx.AsyncClient(timeout=30.0)
        self.access_token = None
        self.token_expires_at = None
        
        self.PERFORMANCE_CACHE_TTL = 86400  # 24 hours
        self.ROUTE_CACHE_TTL = 43200  # 12 hours
    
    async def get_carrier_performance(
        self,
        carrier_code: str
    ) -> CarrierPerformance:
        """
        Get carrier performance metrics.
        
        This REPLACES static carrier_rating values in the system.
        """
        cache_key = f"carrier:performance:{carrier_code}"
        
        cached = get_cache(cache_key)
        if cached:
            try:
                perf = CarrierPerformance.from_dict(cached)
                perf.data_quality = CarrierDataQuality.CACHED
                return perf
            except Exception as e:
                logger.warning(f"Failed to deserialize cached carrier data: {e}")
        
        try:
            await self._ensure_authenticated()
            
            # Fetch carrier performance from Project44
            perf = await self._fetch_carrier_performance(carrier_code)
            
            set_cache(
                cache_key,
                perf.to_dict(),
                ttl=self.PERFORMANCE_CACHE_TTL
            )
            
            if self.audit:
                try:
                    tenant_id = getattr(settings, 'DEFAULT_TENANT_ID', None) or "system"
                    self.audit.append_event(
                        tenant_id=tenant_id,
                        event_type="DATA_FETCH",
                        action="CARRIER_PERFORMANCE",
                        entity_type="carrier",
                        entity_id=carrier_code,
                        actor_type="SYSTEM",
                        payload={
                            "quality": perf.data_quality.value,
                            "rating": perf.carrier_rating,
                            "data_hash": perf.data_hash
                        }
                    )
                except Exception as e:
                    logger.warning(f"Failed to audit carrier fetch: {e}")
            
            return perf
            
        except Exception as e:
            logger.error(f"Error fetching carrier performance: {e}")
            return self._create_fallback_performance(carrier_code, str(e))
    
    async def get_carrier_route_performance(
        self,
        carrier_code: str,
        origin_port: str,
        destination_port: str
    ) -> CarrierRoutePerformance:
        """
        Get carrier performance on specific route.
        
        This provides ROUTE-SPECIFIC risk data, not global averages.
        """
        cache_key = f"carrier:route:{carrier_code}:{origin_port}:{destination_port}"
        
        cached = get_cache(cache_key)
        if cached:
            try:
                return CarrierRoutePerformance(**cached)
            except Exception as e:
                logger.warning(f"Failed to deserialize cached route data: {e}")
        
        try:
            await self._ensure_authenticated()
            
            # Fetch route-specific performance
            perf = await self._fetch_route_performance(
                carrier_code, origin_port, destination_port
            )
            
            set_cache(
                cache_key,
                perf.to_dict(),
                ttl=self.ROUTE_CACHE_TTL
            )
            
            return perf
            
        except Exception as e:
            logger.warning(f"Error fetching route performance: {e}")
            # Return route performance based on global carrier performance
            global_perf = await self.get_carrier_performance(carrier_code)
            return CarrierRoutePerformance(
                carrier_code=carrier_code,
                origin_port=origin_port,
                destination_port=destination_port,
                route_on_time_pct=global_perf.on_time_delivery_pct,
                route_avg_transit_days=0,  # Unknown
                route_transit_variance_days=global_perf.avg_transit_time_variance_hours / 24,
                route_claim_rate_pct=global_perf.claim_frequency_pct,
                vs_carrier_avg_on_time=0,
                vs_carrier_avg_transit=0,
                shipment_count=0,
                period_days=0,
                data_quality=CarrierDataQuality.FALLBACK,
                data_hash=""
            )
    
    async def get_historical_performance(
        self,
        carrier_code: str,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Get historical performance for calibration.
        
        Used to calibrate carrier risk weights against actual outcomes.
        """
        cache_key = f"carrier:history:{carrier_code}:{months}"
        cached = get_cache(cache_key)
        if cached:
            return cached
        
        try:
            await self._ensure_authenticated()
            
            url = f"{self.BASE_URL}/visibility/carriers/{carrier_code}/performance/history"
            params = {"months": months}
            
            response = await self.client.get(
                url,
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params
            )
            response.raise_for_status()
            
            data = response.json().get("data", [])
            
            # Cache for 24 hours (historical data doesn't change frequently)
            set_cache(cache_key, data, ttl=86400)
            return data
        except httpx.HTTPStatusError as e:
            logger.error(f"Project44 API error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Error fetching historical performance: {e}")
            return []
    
    async def _fetch_carrier_performance(
        self,
        carrier_code: str
    ) -> CarrierPerformance:
        """Fetch and parse carrier performance from Project44."""
        url = f"{self.BASE_URL}/visibility/carriers/{carrier_code}/performance"
        
        response = await self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Project44 API structure may vary - handle both formats
        if "metrics" in data:
            metrics = data.get("metrics", {})
        else:
            # If metrics not nested, use data directly
            metrics = data
        
        # Calculate carrier rating (1-5) from metrics
        rating = self._calculate_carrier_rating(metrics)
        
        # Calculate risk score (0-10)
        risk_score, risk_factors = self._calculate_carrier_risk(metrics)
        
        now = datetime.utcnow()
        
        perf_data = {
            "carrier_code": carrier_code,
            "carrier_name": data.get("carrierName", data.get("name", carrier_code)),
            "on_time_delivery_pct": metrics.get("onTimeDeliveryPercent", metrics.get("onTimeDelivery", 85.0)),
            "on_time_pickup_pct": metrics.get("onTimePickupPercent", metrics.get("onTimePickup", 90.0)),
            "schedule_reliability_pct": metrics.get("scheduleReliabilityPercent", metrics.get("scheduleReliability", 85.0)),
            "avg_transit_time_variance_hours": metrics.get("avgTransitVarianceHours", metrics.get("transitVariance", 12.0)),
            "avg_dwell_time_hours": metrics.get("avgDwellTimeHours", metrics.get("dwellTime", 24.0)),
            "claim_frequency_pct": metrics.get("claimFrequencyPercent", metrics.get("claimFrequency", 2.0)),
            "damage_rate_pct": metrics.get("damageRatePercent", metrics.get("damageRate", 0.5)),
            "capacity_utilization_pct": metrics.get("capacityUtilizationPercent", metrics.get("capacityUtilization", 80.0)),
            "booking_acceptance_rate_pct": metrics.get("bookingAcceptancePercent", metrics.get("bookingAcceptance", 95.0)),
            "tracking_quality_score": metrics.get("trackingQualityScore", metrics.get("trackingQuality", 0.8)),
            "documentation_quality_score": metrics.get("documentationQualityScore", metrics.get("documentationQuality", 0.85)),
            "communication_score": metrics.get("communicationScore", 0.8),
            "carrier_rating": rating,
            "carrier_risk_score": risk_score,
            "risk_factors": risk_factors,
            "data_quality": CarrierDataQuality.REAL_TIME,
            "data_source": "project44",
            "sample_size": data.get("sampleSize", metrics.get("sampleSize", 0)),
            "sample_period_days": data.get("samplePeriodDays", metrics.get("samplePeriodDays", 90)),
            "fetched_at": now,
        }
        
        perf_data["data_hash"] = self._compute_hash(perf_data)
        
        return CarrierPerformance(**perf_data)
    
    async def _fetch_route_performance(
        self,
        carrier_code: str,
        origin_port: str,
        destination_port: str
    ) -> CarrierRoutePerformance:
        """Fetch route-specific performance from Project44."""
        url = f"{self.BASE_URL}/visibility/carriers/{carrier_code}/routes/{origin_port}/{destination_port}/performance"
        
        response = await self.client.get(
            url,
            headers={"Authorization": f"Bearer {self.access_token}"}
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Handle different API response formats
        if "metrics" in data:
            metrics = data.get("metrics", {})
        else:
            metrics = data
        
        # Get global performance for comparison
        global_perf = await self.get_carrier_performance(carrier_code)
        
        route_on_time = metrics.get("onTimeDeliveryPercent", metrics.get("onTimeDelivery", global_perf.on_time_delivery_pct))
        route_transit = metrics.get("avgTransitDays", metrics.get("avgTransit", 0))
        route_variance = metrics.get("transitVarianceDays", metrics.get("transitVariance", global_perf.avg_transit_time_variance_hours / 24))
        route_claims = metrics.get("claimRatePercent", metrics.get("claimRate", global_perf.claim_frequency_pct))
        
        now = datetime.utcnow()
        
        route_data = {
            "carrier_code": carrier_code,
            "origin_port": origin_port,
            "destination_port": destination_port,
            "route_on_time_pct": route_on_time,
            "route_avg_transit_days": route_transit,
            "route_transit_variance_days": route_variance,
            "route_claim_rate_pct": route_claims,
            "vs_carrier_avg_on_time": route_on_time - global_perf.on_time_delivery_pct,
            "vs_carrier_avg_transit": route_transit - (global_perf.avg_transit_time_variance_hours / 24),
            "shipment_count": metrics.get("shipmentCount", metrics.get("shipments", 0)),
            "period_days": metrics.get("periodDays", metrics.get("period", 90)),
            "data_quality": CarrierDataQuality.REAL_TIME,
            "data_hash": "",
        }
        
        route_data["data_hash"] = self._compute_hash(route_data)
        
        return CarrierRoutePerformance(**route_data)
    
    def _calculate_carrier_rating(self, metrics: Dict[str, Any]) -> float:
        """
        Calculate carrier rating (1-5) from performance metrics.
        
        This REPLACES hardcoded carrier_rating values.
        """
        # Weight different factors
        on_time = metrics.get("onTimeDeliveryPercent", 85.0)
        reliability = metrics.get("scheduleReliabilityPercent", 85.0)
        claim_rate = metrics.get("claimFrequencyPercent", 2.0)
        damage_rate = metrics.get("damageRatePercent", 0.5)
        tracking = metrics.get("trackingQualityScore", 0.8)
        
        # Convert to 0-1 scale
        on_time_score = on_time / 100
        reliability_score = reliability / 100
        claims_score = max(0, 1 - claim_rate / 10)  # Lower is better
        damage_score = max(0, 1 - damage_rate / 5)  # Lower is better
        
        # Weighted average
        weighted_score = (
            on_time_score * 0.30 +
            reliability_score * 0.25 +
            claims_score * 0.20 +
            damage_score * 0.15 +
            tracking * 0.10
        )
        
        # Convert to 1-5 scale
        rating = 1 + weighted_score * 4
        return round(rating, 2)
    
    def _calculate_carrier_risk(
        self,
        metrics: Dict[str, Any]
    ) -> tuple[float, List[Dict[str, Any]]]:
        """
        Calculate carrier risk score from real performance data.
        
        This REPLACES hardcoded risk calculations.
        """
        risk_score = 0.0
        factors = []
        
        # On-time delivery risk (0-3 points)
        on_time = metrics.get("onTimeDeliveryPercent", 85.0)
        delay_risk = (100 - on_time) / 100 * 3
        risk_score += delay_risk
        factors.append({
            "factor": "delay_risk",
            "metric": "on_time_delivery_pct",
            "value": on_time,
            "contribution": delay_risk,
            "description": f"On-time delivery: {on_time}%"
        })
        
        # Claim frequency risk (0-3 points)
        claim_rate = metrics.get("claimFrequencyPercent", 2.0)
        claim_risk = min(claim_rate / 10, 1.0) * 3
        risk_score += claim_risk
        factors.append({
            "factor": "claim_risk",
            "metric": "claim_frequency_pct",
            "value": claim_rate,
            "contribution": claim_risk,
            "description": f"Claim frequency: {claim_rate}%"
        })
        
        # Damage risk (0-2 points)
        damage_rate = metrics.get("damageRatePercent", 0.5)
        damage_risk = min(damage_rate / 5, 1.0) * 2
        risk_score += damage_risk
        factors.append({
            "factor": "damage_risk",
            "metric": "damage_rate_pct",
            "value": damage_rate,
            "contribution": damage_risk,
            "description": f"Damage rate: {damage_rate}%"
        })
        
        # Transit variance risk (0-2 points)
        variance = metrics.get("avgTransitVarianceHours", 12.0)
        variance_risk = min(variance / 48, 1.0) * 2
        risk_score += variance_risk
        factors.append({
            "factor": "variance_risk",
            "metric": "transit_variance_hours",
            "value": variance,
            "contribution": variance_risk,
            "description": f"Transit variance: {variance} hours"
        })
        
        return risk_score, factors
    
    def _create_fallback_performance(
        self,
        carrier_code: str,
        error_reason: str
    ) -> CarrierPerformance:
        """Create fallback with explicit quality flag."""
        # Use industry averages
        now = datetime.utcnow()
        
        perf_data = {
            "carrier_code": carrier_code,
            "carrier_name": carrier_code,
            "on_time_delivery_pct": 85.0,  # Industry average
            "on_time_pickup_pct": 90.0,
            "schedule_reliability_pct": 85.0,
            "avg_transit_time_variance_hours": 12.0,
            "avg_dwell_time_hours": 24.0,
            "claim_frequency_pct": 2.0,
            "damage_rate_pct": 0.5,
            "capacity_utilization_pct": 80.0,
            "booking_acceptance_rate_pct": 95.0,
            "tracking_quality_score": 0.8,
            "documentation_quality_score": 0.85,
            "communication_score": 0.8,
            "carrier_rating": 4.0,  # Industry average
            "carrier_risk_score": 3.0,  # Moderate risk
            "risk_factors": [{
                "factor": "fallback_data",
                "description": f"Using fallback: {error_reason}",
                "confidence": 0.5
            }],
            "data_quality": CarrierDataQuality.FALLBACK,
            "data_source": "industry_average",
            "sample_size": 0,
            "sample_period_days": 0,
            "fetched_at": now,
            "data_hash": "",
        }
        
        perf_data["data_hash"] = self._compute_hash(perf_data)
        
        return CarrierPerformance(**perf_data)
    
    async def _ensure_authenticated(self):
        """Ensure we have valid access token."""
        if self.access_token and self.token_expires_at and datetime.utcnow() < self.token_expires_at:
            return
        
        # Get new token
        auth_url = f"{self.BASE_URL}/oauth/token"
        response = await self.client.post(
            auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
    
    @staticmethod
    def _compute_hash(data: Dict[str, Any]) -> str:
        """Compute hash for audit trail."""
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


def create_carrier_client(audit_ledger: Optional[Any] = None) -> Project44Client:
    """Create configured carrier client."""
    client_id = getattr(settings, 'PROJECT44_CLIENT_ID', None)
    client_secret = getattr(settings, 'PROJECT44_CLIENT_SECRET', None)
    
    if not client_id or not client_secret:
        raise ValueError(
            "PROJECT44_CLIENT_ID and PROJECT44_CLIENT_SECRET not configured. "
            "Set environment variables to enable carrier performance tracking."
        )
    
    return Project44Client(
        client_id=client_id,
        client_secret=client_secret,
        audit_ledger=audit_ledger
    )
