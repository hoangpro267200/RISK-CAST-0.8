"""
Climate Service - Unified interface for climate data.

Aggregates NOAA and JTWC data sources with quality tracking.
"""
from typing import Dict, Optional, Any, List
from datetime import datetime
import logging

from app.integrations.climate.noaa_client import (
    NOAAClient,
    ClimateIndices,
    ENSOPhase,
    ClimateDataQuality,
    create_climate_client
)
from app.integrations.climate.jtwc_client import (
    JTWCClient,
    create_jtwc_client
)

logger = logging.getLogger(__name__)


class ClimateService:
    """
    Unified climate service with:
    - NOAA climate indices (ENSO, PDO, AMO, NAO)
    - Tropical cyclone tracking (NHC, JTWC)
    - Quality tracking at every level
    - Audit trail for all data access
    """
    
    def __init__(self, audit_ledger: Optional[Any] = None):
        self.audit = audit_ledger
        self.noaa = create_climate_client(audit_ledger)
        self.jtwc = create_jtwc_client(audit_ledger)
    
    async def get_climate_risk_assessment(
        self,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive climate risk assessment.
        
        This REPLACES synthetic climate inputs in risk calculations.
        
        Args:
            region: Optional region (e.g., "pacific", "atlantic", "indian")
            
        Returns:
            Climate risk assessment with explicit quality indicators
        """
        # Get current climate indices
        indices = await self.noaa.get_current_climate_indices()
        
        # Get risk adjustments based on real climate data
        risk_adjustments = indices.get_risk_adjustment()
        
        # Get active tropical cyclones
        active_cyclones = indices.active_tropical_systems
        
        return {
            "climate_indices": {
                "oni": indices.oni_value,
                "enso_phase": indices.enso_phase.value,
                "enso_forecast": indices.enso_forecast_3m,
                "pdo": indices.pdo_value,
                "amo": indices.amo_value,
                "nao": indices.nao_value,
            },
            "tropical_cyclones": {
                "atlantic_ace": indices.atlantic_ace,
                "pacific_ace": indices.pacific_ace,
                "active_systems": active_cyclones,
            },
            "risk_adjustments": risk_adjustments,
            "data_quality": {
                "quality": indices.data_quality.value,
                "source": indices.data_source,
                "data_date": indices.data_date.isoformat(),
                "fetched_at": indices.fetched_at.isoformat(),
            },
            "fetched_at": datetime.utcnow().isoformat()
        }
    
    async def get_historical_climate(
        self,
        start_year: int,
        end_year: int
    ) -> List[Dict[str, Any]]:
        """
        Get historical climate data for model calibration.
        
        Used to calibrate climate risk weights against actual outcomes.
        """
        return await self.noaa.get_historical_climate(start_year, end_year)
    
    async def close(self):
        """Close all climate clients."""
        await self.noaa.close()
        await self.jtwc.close()


# Export singleton
climate_service: Optional[ClimateService] = None


def get_climate_service(audit_ledger: Optional[Any] = None) -> ClimateService:
    """Get or create climate service singleton."""
    global climate_service
    if climate_service is None:
        climate_service = ClimateService(audit_ledger)
    return climate_service
