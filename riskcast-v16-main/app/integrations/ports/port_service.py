"""
Port Service - Unified interface for port data.

Aggregates multiple port data sources with quality tracking.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.integrations.ports.marine_traffic import (
    MarineTrafficClient,
    PortConditions,
    PortDataQuality,
    CongestionLevel,
    create_port_client
)

logger = logging.getLogger(__name__)


class PortService:
    """
    Unified port service with:
    - Multiple source fallback
    - Quality tracking at every level
    - Audit trail for all data access
    """
    
    def __init__(self, audit_ledger: Optional[Any] = None):
        self.audit = audit_ledger
        self.marine_traffic = create_port_client(audit_ledger)
        
        # Could add backup sources:
        # self.port_authority = PortAuthorityClient(audit_ledger)
        # self.project44 = Project44Client(audit_ledger)
    
    async def get_port_risk_assessment(
        self,
        port_code: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive port risk assessment.
        
        This REPLACES hardcoded PORT_RISK_DATABASE lookups.
        
        Returns:
            Port risk assessment with explicit quality indicators
        """
        # Get real-time port conditions
        conditions = await self.marine_traffic.get_port_conditions(port_code)
        
        # Get historical data for context
        history = await self.marine_traffic.get_port_congestion_history(port_code, days=30)
        
        # Analyze trends
        trend = self._analyze_congestion_trend(history)
        
        return {
            "port_code": port_code,
            "port_name": conditions.port_name,
            "country": conditions.country,
            "location": {
                "latitude": conditions.latitude,
                "longitude": conditions.longitude
            },
            "current_conditions": {
                "congestion_level": conditions.congestion_level.value,
                "congestion_score": conditions.congestion_score,
                "avg_waiting_hours": conditions.avg_waiting_time_hours,
                "vessels_at_anchor": conditions.vessels_at_anchor,
                "berth_utilization_pct": conditions.berth_utilization_pct,
            },
            "risk_assessment": {
                "port_risk_score": conditions.port_risk_score,
                "risk_factors": conditions.risk_factors,
                "trend": trend,
            },
            "data_quality": {
                "quality": conditions.data_quality.value,
                "source": conditions.data_source,
                "fetched_at": conditions.fetched_at.isoformat(),
                "data_timestamp": conditions.data_timestamp.isoformat(),
            },
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    async def get_multiple_ports(
        self,
        port_codes: List[str]
    ) -> Dict[str, PortConditions]:
        """
        Get conditions for multiple ports in parallel.
        
        Used for route risk assessment (POL + POD).
        """
        import asyncio
        
        # Fetch all ports in parallel
        tasks = [
            self.marine_traffic.get_port_conditions(code)
            for code in port_codes
        ]
        
        conditions_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Build result dict, handling errors
        result = {}
        for code, conditions in zip(port_codes, conditions_list):
            if isinstance(conditions, Exception):
                logger.error(f"Error fetching {code}: {conditions}")
                # Use fallback
                result[code] = self.marine_traffic._create_fallback_conditions(
                    code, str(conditions)
                )
            else:
                result[code] = conditions
        
        return result
    
    def _analyze_congestion_trend(
        self,
        history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze congestion trend from historical data."""
        if not history or len(history) < 2:
            return {
                "direction": "unknown",
                "change_pct": 0.0,
                "confidence": 0.0
            }
        
        # Extract congestion scores from history
        scores = []
        for entry in history[-30:]:  # Last 30 days
            if "congestion_score" in entry:
                scores.append(entry["congestion_score"])
            elif "avg_waiting" in entry:
                # Convert waiting time to congestion score
                scores.append(min(entry["avg_waiting"] / 48, 1.0))
        
        if len(scores) < 2:
            return {
                "direction": "unknown",
                "change_pct": 0.0,
                "confidence": 0.0
            }
        
        # Calculate trend
        recent_avg = sum(scores[-7:]) / len(scores[-7:]) if len(scores) >= 7 else scores[-1]
        older_avg = sum(scores[:-7]) / len(scores[:-7]) if len(scores) > 7 else scores[0]
        
        change_pct = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0.0
        
        if change_pct > 10:
            direction = "increasing"
        elif change_pct < -10:
            direction = "decreasing"
        else:
            direction = "stable"
        
        return {
            "direction": direction,
            "change_pct": change_pct,
            "confidence": min(len(scores) / 30, 1.0),
            "recent_avg": recent_avg,
            "older_avg": older_avg
        }
    
    async def close(self):
        """Close all port clients."""
        await self.marine_traffic.close()


# Export singleton
port_service: Optional[PortService] = None


def get_port_service(audit_ledger: Optional[Any] = None) -> PortService:
    """Get or create port service singleton."""
    global port_service
    if port_service is None:
        port_service = PortService(audit_ledger)
    return port_service
