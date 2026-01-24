"""
MarineTraffic Oracle Provider

Implements OracleProvider interface for port congestion data.
Replaces stub port congestion provider with real API integration.
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
from app.integrations.ports.marine_traffic import (
    MarineTrafficClient,
    create_port_client,
    PortDataQuality
)
from app.config import settings

logger = logging.getLogger(__name__)


class MarineTrafficProvider(OracleProvider):
    """
    MarineTraffic port congestion oracle provider.
    
    Fetches real-time port congestion data from MarineTraffic API
    and normalizes it for parametric trigger evaluation.
    """
    
    def __init__(self, audit_ledger: Optional[Any] = None):
        """Initialize MarineTraffic provider."""
        self.audit = audit_ledger
        self._client: Optional[MarineTrafficClient] = None
    
    @property
    def source_name(self) -> str:
        """Return provider source name."""
        return "marinetraffic"
    
    def is_configured(self) -> bool:
        """Check if MarineTraffic API key is configured."""
        return bool(settings.MARINE_TRAFFIC_API_KEY or settings.MARINETRAFFIC_API_KEY)
    
    def _get_client(self) -> MarineTrafficClient:
        """Get or create port client."""
        if self._client is None:
            if not self.is_configured():
                raise OracleNotConfiguredError(
                    "MarineTraffic API key not configured. "
                    "Set MARINE_TRAFFIC_API_KEY or MARINETRAFFIC_API_KEY environment variable."
                )
            self._client = create_port_client(self.audit)
        return self._client
    
    async def fetch_event(self, query: OracleQuery) -> OraclePayload:
        """
        Fetch port congestion data from MarineTraffic.
        
        Args:
            query: OracleQuery with location (port_code)
            
        Returns:
            OraclePayload with port congestion data
            
        Raises:
            OracleNotConfiguredError: If API key not configured
            OracleFetchError: If fetch fails
        """
        if not self.is_configured():
            raise OracleNotConfiguredError(
                "MarineTraffic API key not configured. "
                "Set MARINE_TRAFFIC_API_KEY or MARINETRAFFIC_API_KEY environment variable."
            )
        
        client = self._get_client()
        
        # Extract port code from query
        port_code = query.location
        if not port_code:
            raise OracleFetchError("Port code not specified in query")
        
        try:
            # Fetch real-time port conditions
            conditions = await client.get_port_conditions(port_code)
            
            # Convert to oracle payload format
            payload = {
                "port_code": port_code,
                "port_name": conditions.port_name,
                "location": {
                    "latitude": conditions.latitude,
                    "longitude": conditions.longitude
                },
                "congestion": {
                    "level": conditions.congestion_level.value,
                    "score": conditions.congestion_score,
                    "avg_waiting_hours": conditions.avg_waiting_time_hours,
                    "vessels_at_anchor": conditions.vessels_at_anchor,
                    "berth_utilization_pct": conditions.berth_utilization_pct,
                },
                "port_risk_score": conditions.port_risk_score,
                "risk_factors": conditions.risk_factors,
                "data_quality": conditions.data_quality.value,
                "data_source": conditions.data_source,
                "data_hash": conditions.data_hash,
                "fetched_at": conditions.fetched_at.isoformat(),
                "data_timestamp": conditions.data_timestamp.isoformat(),
            }
            
            # Check data quality - reject fallback data if configured
            if (conditions.data_quality == PortDataQuality.FALLBACK and 
                not settings.ALLOW_FALLBACK_DATA_IN_RISK):
                logger.warning(
                    f"Received fallback port data for {port_code}. "
                    "Rejecting due to ALLOW_FALLBACK_DATA_IN_RISK=False"
                )
                raise OracleFetchError(
                    f"Only fallback port data available for {port_code}. "
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
            logger.error(f"Error fetching port data from MarineTraffic: {e}", exc_info=True)
            raise OracleFetchError(f"Failed to fetch port data: {str(e)}") from e
    
    def validate(self, payload: OraclePayload) -> ValidationResult:
        """
        Validate port congestion payload structure.
        
        Required fields:
        - port_code
        - congestion.score
        - port_risk_score
        - data_quality
        - data_source
        """
        result = ValidationResult(valid=True)
        data = payload.payload
        
        required_fields = [
            "port_code",
            "congestion",
            "port_risk_score",
            "data_quality",
            "data_source"
        ]
        
        for field in required_fields:
            if field not in data:
                result.add_error(f"Missing required field: {field}")
        
        # Validate congestion structure
        if "congestion" in data:
            congestion = data["congestion"]
            if "score" not in congestion:
                result.add_error("Missing congestion.score")
            elif not isinstance(congestion["score"], (int, float)):
                result.add_error("congestion.score must be numeric")
            elif not (0 <= congestion["score"] <= 1):
                result.add_error("congestion.score must be between 0 and 1")
        
        # Validate data quality
        if "data_quality" in data:
            quality = data["data_quality"]
            if quality == PortDataQuality.FALLBACK.value:
                result.add_warning(
                    "Port data is fallback/historical average. "
                    "Not suitable for parametric trigger evaluation."
                )
            elif quality == PortDataQuality.STALE.value:
                result.add_warning(
                    "Port data is stale. May not reflect current conditions."
                )
        
        # Validate risk score
        if "port_risk_score" in data:
            risk = data["port_risk_score"]
            if not isinstance(risk, (int, float)) or not (0 <= risk <= 10):
                result.add_error("port_risk_score must be between 0 and 10")
        
        return result
    
    def normalize(self, payload: OraclePayload) -> dict:
        """
        Normalize port congestion payload to standard format for trigger evaluation.
        
        Standard format:
        {
            "port_code": str,
            "congestion_score": float (0-1),
            "avg_waiting_hours": float,
            "port_risk_score": float (0-10),
            "data_quality": str,
            "data_source": str,
            "timestamp": str (ISO)
        }
        """
        data = payload.payload
        
        congestion = data.get("congestion", {})
        
        normalized = {
            "port_code": data.get("port_code"),
            "congestion_score": congestion.get("score", 0.5),
            "avg_waiting_hours": congestion.get("avg_waiting_hours", 0.0),
            "vessels_at_anchor": congestion.get("vessels_at_anchor", 0),
            "berth_utilization_pct": congestion.get("berth_utilization_pct", 70.0),
            "port_risk_score": data.get("port_risk_score", 5.0),
            "data_quality": data.get("data_quality", "UNKNOWN"),
            "data_source": data.get("data_source", payload.source),
            "timestamp": data.get("data_timestamp", payload.captured_at.isoformat()),
        }
        
        # Add optional fields if available
        if "risk_factors" in data:
            normalized["risk_factors"] = data["risk_factors"]
        if "data_hash" in data:
            normalized["data_hash"] = data["data_hash"]
        if "location" in data:
            normalized["location"] = data["location"]
        
        return normalized
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.close()
