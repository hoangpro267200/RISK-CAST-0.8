"""
VesselFinder AIS API Client (Fallback Provider)

Alternative AIS data provider for redundancy.
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

from app.core.logging import get_logger
from app.integrations.ais.models import (
    VesselPosition, VesselInfo, VoyageInfo,
    VesselType, NavigationStatus
)


logger = get_logger(__name__)


class VesselFinderClient:
    """
    VesselFinder AIS API client (fallback provider).
    
    Used when MarineTraffic is unavailable.
    """
    
    BASE_URL = "https://www.vesselfinder.com/api"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("VESSEL_FINDER_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("VesselFinder API key not configured")
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict
    ) -> Optional[Dict]:
        """Make API request with retry logic."""
        if not self.api_key:
            return None
        
        params["key"] = self.api_key
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        params=params,
                        timeout=aiohttp.ClientTimeout(total=self.timeout)
                    ) as response:
                        if response.status == 200:
                            return await response.json()
                        elif response.status == 429:
                            wait_time = 2 ** attempt
                            logger.warning(f"Rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"VesselFinder API error: {response.status}")
                            return None
                            
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Request failed: {e}")
        
        return None
    
    async def get_vessel_position(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None,
        vessel_name: Optional[str] = None
    ) -> Optional[VesselPosition]:
        """
        Get vessel position (fallback implementation).
        """
        # If no API key, return mock data
        if not self.api_key:
            return self._mock_vessel_position(mmsi, imo, vessel_name)
        
        # VesselFinder API implementation would go here
        # For now, return mock data
        logger.info("VesselFinder API not fully implemented, using mock data")
        return self._mock_vessel_position(mmsi, imo, vessel_name)
    
    async def get_vessel_info(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None
    ) -> Optional[VesselInfo]:
        """Get vessel info (fallback)."""
        if not self.api_key:
            return self._mock_vessel_info(mmsi, imo)
        
        # API implementation would go here
        return self._mock_vessel_info(mmsi, imo)
    
    def _mock_vessel_position(
        self,
        mmsi: Optional[str],
        imo: Optional[str],
        vessel_name: Optional[str]
    ) -> VesselPosition:
        """Generate mock vessel position."""
        import random
        
        return VesselPosition(
            mmsi=mmsi or "123456789",
            imo=imo or "9999999",
            vessel_name=vessel_name or "MOCK VESSEL (VF)",
            latitude=1.2644 + random.uniform(-0.1, 0.1),
            longitude=103.8217 + random.uniform(-0.1, 0.1),
            speed_knots=12.5 + random.uniform(-2, 2),
            course=45.0 + random.uniform(-10, 10),
            heading=47.0 + random.uniform(-10, 10),
            navigation_status=NavigationStatus.UNDER_WAY_ENGINE,
            destination="ROTTERDAM",
            eta=datetime.utcnow() + timedelta(days=21),
            draught=10.5,
            timestamp=datetime.utcnow() - timedelta(minutes=5),
            received_at=datetime.utcnow(),
            data_source="VesselFinder (MOCK)"
        )
    
    def _mock_vessel_info(
        self,
        mmsi: Optional[str],
        imo: Optional[str]
    ) -> VesselInfo:
        """Generate mock vessel info."""
        return VesselInfo(
            mmsi=mmsi or "123456789",
            imo=imo or "9999999",
            vessel_name="MOCK VESSEL (VF)",
            vessel_type=VesselType.CONTAINER,
            vessel_type_code=71,
            length_meters=350.0,
            width_meters=45.0,
            gross_tonnage=150000,
            deadweight_tonnage=165000,
            flag_country="Singapore",
            flag_code="SG",
            call_sign="9V1234",
            year_built=2018,
            owner="Mock Shipping Co",
            operator="Mock Lines"
        )
