"""
Carrier Service - Unified interface for carrier data.

Aggregates multiple carrier data sources with quality tracking.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.integrations.carriers.project44 import (
    Project44Client,
    CarrierPerformance,
    CarrierRoutePerformance,
    CarrierDataQuality,
    create_carrier_client
)

logger = logging.getLogger(__name__)


class CarrierService:
    """
    Unified carrier service with:
    - Multiple source fallback
    - Quality tracking at every level
    - Audit trail for all data access
    """
    
    def __init__(self, audit_ledger: Optional[Any] = None):
        self.audit = audit_ledger
        try:
            self.project44 = create_carrier_client(audit_ledger)
        except ValueError as e:
            logger.warning(f"Project44 not configured: {e}")
            self.project44 = None
        
        # Could add backup sources:
        # self.fourkites = FourKitesClient(audit_ledger)
        # self.carrier_direct = CarrierDirectAPI(audit_ledger)
    
    async def get_carrier_risk_assessment(
        self,
        carrier_code: str,
        origin_port: Optional[str] = None,
        destination_port: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive carrier risk assessment.
        
        This REPLACES hardcoded carrier_rating lookups.
        
        Args:
            carrier_code: Carrier SCAC code
            origin_port: Optional origin port for route-specific data
            destination_port: Optional destination port for route-specific data
            
        Returns:
            Carrier risk assessment with explicit quality indicators
        """
        if not self.project44:
            # Return fallback if Project44 not configured
            return self._create_fallback_assessment(carrier_code)
        
        # Get global carrier performance
        performance = await self.project44.get_carrier_performance(carrier_code)
        
        # Get route-specific performance if ports provided
        route_perf = None
        if origin_port and destination_port:
            try:
                route_perf = await self.project44.get_carrier_route_performance(
                    carrier_code, origin_port, destination_port
                )
            except Exception as e:
                logger.warning(f"Failed to fetch route performance: {e}")
        
        # Analyze performance
        analysis = self._analyze_carrier_performance(performance, route_perf)
        
        return {
            "carrier_code": carrier_code,
            "carrier_name": performance.carrier_name,
            "performance": {
                "on_time_delivery_pct": performance.on_time_delivery_pct,
                "schedule_reliability_pct": performance.schedule_reliability_pct,
                "claim_frequency_pct": performance.claim_frequency_pct,
                "damage_rate_pct": performance.damage_rate_pct,
            },
            "rating": {
                "carrier_rating": performance.carrier_rating,
                "carrier_risk_score": performance.carrier_risk_score,
                "risk_factors": performance.risk_factors,
            },
            "route_specific": route_perf.to_dict() if route_perf else None,
            "analysis": analysis,
            "data_quality": {
                "quality": performance.data_quality.value,
                "source": performance.data_source,
                "sample_size": performance.sample_size,
                "sample_period_days": performance.sample_period_days,
                "fetched_at": performance.fetched_at.isoformat(),
            },
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    async def get_multiple_carriers(
        self,
        carrier_codes: List[str]
    ) -> Dict[str, CarrierPerformance]:
        """
        Get performance for multiple carriers in parallel.
        
        Used for carrier comparison in risk assessment.
        """
        if not self.project44:
            # Return fallbacks
            return {
                code: self.project44._create_fallback_performance(code, "Project44 not configured")
                for code in carrier_codes
            }
        
        import asyncio
        
        # Fetch all carriers in parallel
        tasks = [
            self.project44.get_carrier_performance(code)
            for code in carrier_codes
        ]
        
        performances = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dict, handling errors
        result = {}
        for code, perf in zip(carrier_codes, performances):
            if isinstance(perf, Exception):
                logger.error(f"Error fetching {code}: {perf}")
                result[code] = self.project44._create_fallback_performance(
                    code, str(perf)
                )
            else:
                result[code] = perf
        
        return result
    
    def _analyze_carrier_performance(
        self,
        performance: CarrierPerformance,
        route_perf: Optional[CarrierRoutePerformance]
    ) -> Dict[str, Any]:
        """Analyze carrier performance to provide insights."""
        insights = []
        warnings = []
        
        # On-time delivery analysis
        if performance.on_time_delivery_pct < 80:
            warnings.append({
                "type": "low_on_time",
                "severity": "high" if performance.on_time_delivery_pct < 70 else "medium",
                "message": f"On-time delivery {performance.on_time_delivery_pct}% is below industry average (85%)"
            })
        elif performance.on_time_delivery_pct > 95:
            insights.append({
                "type": "excellent_on_time",
                "message": f"Excellent on-time delivery: {performance.on_time_delivery_pct}%"
            })
        
        # Claim frequency analysis
        if performance.claim_frequency_pct > 5:
            warnings.append({
                "type": "high_claims",
                "severity": "high",
                "message": f"High claim frequency: {performance.claim_frequency_pct}% (industry avg: 2%)"
            })
        
        # Route-specific insights
        if route_perf:
            if route_perf.vs_carrier_avg_on_time < -10:
                warnings.append({
                    "type": "route_performance_degradation",
                    "severity": "medium",
                    "message": f"Route performance {route_perf.vs_carrier_avg_on_time:.1f}% below carrier average"
                })
            elif route_perf.vs_carrier_avg_on_time > 10:
                insights.append({
                    "type": "route_performance_improvement",
                    "message": f"Route performance {route_perf.vs_carrier_avg_on_time:.1f}% above carrier average"
                })
        
        return {
            "insights": insights,
            "warnings": warnings,
            "overall_assessment": self._get_overall_assessment(performance)
        }
    
    def _get_overall_assessment(self, performance: CarrierPerformance) -> str:
        """Get overall assessment of carrier."""
        if performance.carrier_rating >= 4.5:
            return "EXCELLENT"
        elif performance.carrier_rating >= 4.0:
            return "GOOD"
        elif performance.carrier_rating >= 3.5:
            return "ACCEPTABLE"
        elif performance.carrier_rating >= 3.0:
            return "BELOW_AVERAGE"
        else:
            return "POOR"
    
    def _create_fallback_assessment(self, carrier_code: str) -> Dict[str, Any]:
        """Create fallback assessment when API not configured."""
        if self.project44:
            perf = self.project44._create_fallback_performance(carrier_code, "API not configured")
        else:
            # Create minimal fallback
            from app.integrations.carriers.project44 import CarrierPerformance, CarrierDataQuality
            perf = CarrierPerformance(
                carrier_code=carrier_code,
                carrier_name=carrier_code,
                on_time_delivery_pct=85.0,
                on_time_pickup_pct=90.0,
                schedule_reliability_pct=85.0,
                avg_transit_time_variance_hours=12.0,
                avg_dwell_time_hours=24.0,
                claim_frequency_pct=2.0,
                damage_rate_pct=0.5,
                capacity_utilization_pct=80.0,
                booking_acceptance_rate_pct=95.0,
                tracking_quality_score=0.8,
                documentation_quality_score=0.85,
                communication_score=0.8,
                carrier_rating=4.0,
                carrier_risk_score=3.0,
                risk_factors=[],
                data_quality=CarrierDataQuality.FALLBACK,
                data_source="industry_average",
                sample_size=0,
                sample_period_days=0,
                fetched_at=datetime.utcnow(),
                data_hash=""
            )
        
        return {
            "carrier_code": carrier_code,
            "carrier_name": perf.carrier_name,
            "performance": {
                "on_time_delivery_pct": perf.on_time_delivery_pct,
                "schedule_reliability_pct": perf.schedule_reliability_pct,
                "claim_frequency_pct": perf.claim_frequency_pct,
                "damage_rate_pct": perf.damage_rate_pct,
            },
            "rating": {
                "carrier_rating": perf.carrier_rating,
                "carrier_risk_score": perf.carrier_risk_score,
                "risk_factors": perf.risk_factors,
            },
            "route_specific": None,
            "analysis": {
                "insights": [],
                "warnings": [{
                    "type": "fallback_data",
                    "severity": "low",
                    "message": "Using fallback carrier data - real-time data unavailable"
                }],
                "overall_assessment": "UNKNOWN"
            },
            "data_quality": {
                "quality": perf.data_quality.value,
                "source": perf.data_source,
                "sample_size": perf.sample_size,
                "sample_period_days": perf.sample_period_days,
                "fetched_at": perf.fetched_at.isoformat(),
            },
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    async def close(self):
        """Close all carrier clients."""
        if self.project44:
            await self.project44.close()


# Export singleton
carrier_service: Optional[CarrierService] = None


def get_carrier_service(audit_ledger: Optional[Any] = None) -> CarrierService:
    """Get or create carrier service singleton."""
    global carrier_service
    if carrier_service is None:
        carrier_service = CarrierService(audit_ledger)
    return carrier_service
