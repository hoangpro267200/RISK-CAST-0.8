"""
MarineTraffic AIS API Client

API Documentation: https://www.marinetraffic.com/en/ais-api-services
"""

import aiohttp
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

from app.core.logging import get_logger
from app.integrations.ais.models import (
    VesselPosition, VesselInfo, VoyageInfo, TrackPoint,
    VesselType, NavigationStatus
)


logger = get_logger(__name__)


class MarineTrafficAISClient:
    """
    MarineTraffic AIS API client.
    
    Services used:
    - PS01: Vessel Positions
    - PS02: Vessel Particulars
    - PS07: Voyage Information
    - EV01: Track Data
    """
    
    BASE_URL = "https://services.marinetraffic.com/api"
    
    # Vessel type code mapping
    VESSEL_TYPE_MAP = {
        (70, 79): VesselType.GENERAL_CARGO,
        (80, 89): VesselType.TANKER,
        (60, 69): VesselType.PASSENGER,
        (30, 39): VesselType.FISHING,
        (40, 49): VesselType.TUG,
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("MARINE_TRAFFIC_API_KEY")
        self.timeout = timeout
        self.max_retries = max_retries
        
        if not self.api_key:
            logger.warning("MarineTraffic API key not configured")
    
    async def _make_request(
        self,
        endpoint: str,
        params: Dict
    ) -> Optional[Dict]:
        """Make API request with retry logic."""
        params["apikey"] = self.api_key
        params["protocol"] = "jsono"  # JSON output
        
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
                            data = await response.json()
                            
                            # Check for API errors
                            if isinstance(data, dict) and data.get("errors"):
                                logger.error(f"MarineTraffic API error: {data['errors']}")
                                return None
                            
                            return data
                        elif response.status == 429:
                            # Rate limited
                            wait_time = 2 ** attempt
                            logger.warning(f"Rate limited, waiting {wait_time}s")
                            await asyncio.sleep(wait_time)
                        else:
                            logger.error(f"MarineTraffic API error: {response.status}")
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
        Get vessel position using PS01 service.
        """
        if not self.api_key:
            return self._mock_vessel_position(mmsi, imo, vessel_name)
        
        params = {"msgtype": "simple"}
        
        if mmsi:
            params["mmsi"] = mmsi
        elif imo:
            params["imo"] = imo
        elif vessel_name:
            params["shipname"] = vessel_name
        
        data = await self._make_request("exportvessel/v:5", params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return None
        
        vessel = data[0]
        
        return VesselPosition(
            mmsi=vessel.get("MMSI", ""),
            imo=vessel.get("IMO"),
            vessel_name=vessel.get("SHIPNAME", ""),
            latitude=float(vessel.get("LAT", 0)),
            longitude=float(vessel.get("LON", 0)),
            speed_knots=float(vessel.get("SPEED", 0)) / 10,  # Stored as 10x
            course=float(vessel.get("COURSE", 0)),
            heading=float(vessel.get("HEADING", 0)),
            navigation_status=NavigationStatus(str(vessel.get("STATUS", 15))),
            destination=vessel.get("DESTINATION"),
            eta=self._parse_eta(vessel.get("ETA")),
            draught=float(vessel.get("DRAUGHT", 0)) / 10 if vessel.get("DRAUGHT") else None,
            timestamp=self._parse_timestamp(vessel.get("TIMESTAMP")),
            received_at=datetime.utcnow(),
            data_source="MarineTraffic"
        )
    
    async def get_vessel_info(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None
    ) -> Optional[VesselInfo]:
        """
        Get vessel particulars using PS02 service.
        """
        if not self.api_key:
            return self._mock_vessel_info(mmsi, imo)
        
        params = {}
        if mmsi:
            params["mmsi"] = mmsi
        elif imo:
            params["imo"] = imo
        
        data = await self._make_request("vesselmasterdata/v:4", params)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return None
        
        vessel = data[0]
        
        return VesselInfo(
            mmsi=vessel.get("MMSI", ""),
            imo=vessel.get("IMO"),
            vessel_name=vessel.get("SHIPNAME", ""),
            vessel_type=self._map_vessel_type(vessel.get("TYPE_CODE")),
            vessel_type_code=vessel.get("TYPE_CODE", 0),
            length_meters=float(vessel.get("LENGTH", 0)),
            width_meters=float(vessel.get("WIDTH", 0)),
            gross_tonnage=vessel.get("GRT"),
            deadweight_tonnage=vessel.get("DWT"),
            flag_country=vessel.get("FLAG", ""),
            flag_code=vessel.get("FLAG_CODE", ""),
            call_sign=vessel.get("CALLSIGN"),
            year_built=vessel.get("YEAR_BUILT"),
            owner=vessel.get("OWNER"),
            operator=vessel.get("MANAGER")
        )
    
    async def get_voyage_info(
        self,
        mmsi: Optional[str] = None,
        imo: Optional[str] = None
    ) -> Optional[VoyageInfo]:
        """
        Get voyage information using PS07 service.
        """
        if not self.api_key:
            return self._mock_voyage_info(mmsi, imo)
        
        params = {}
        if mmsi:
            params["mmsi"] = mmsi
        elif imo:
            params["imo"] = imo
        
        data = await self._make_request("voyageforecast/v:2", params)
        
        if not data:
            return None
        
        return VoyageInfo(
            mmsi=data.get("MMSI", mmsi or ""),
            imo=data.get("IMO", imo),
            vessel_name=data.get("SHIPNAME", ""),
            origin_port=data.get("LAST_PORT"),
            origin_port_name=data.get("LAST_PORT_NAME"),
            destination_port=data.get("NEXT_PORT_ID"),
            destination_port_name=data.get("NEXT_PORT_NAME"),
            eta=self._parse_eta(data.get("ETA")),
            distance_remaining_nm=data.get("DISTANCE_TO_GO")
        )
    
    async def get_historical_track(
        self,
        mmsi: str,
        start_time: datetime,
        end_time: datetime,
        interval_minutes: int = 30
    ) -> List[TrackPoint]:
        """
        Get historical track using EV01 service.
        """
        if not self.api_key:
            return self._mock_historical_track(mmsi, start_time, end_time)
        
        params = {
            "mmsi": mmsi,
            "fromdate": start_time.strftime("%Y-%m-%d %H:%M"),
            "todate": end_time.strftime("%Y-%m-%d %H:%M"),
            "interval": interval_minutes
        }
        
        data = await self._make_request("exportvesseltrack/v:2", params)
        
        if not data or not isinstance(data, list):
            return []
        
        return [
            TrackPoint(
                latitude=float(point.get("LAT", 0)),
                longitude=float(point.get("LON", 0)),
                timestamp=self._parse_timestamp(point.get("TIMESTAMP")),
                speed_knots=float(point.get("SPEED", 0)) / 10,
                course=float(point.get("COURSE", 0))
            )
            for point in data
        ]
    
    async def search_vessels_in_area(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float,
        vessel_types: Optional[List[VesselType]] = None
    ) -> List[VesselPosition]:
        """
        Search vessels in geographic area using PS01.
        """
        if not self.api_key:
            return self._mock_area_search(min_lat, min_lon, max_lat, max_lon)
        
        params = {
            "MINLAT": min_lat,
            "MAXLAT": max_lat,
            "MINLON": min_lon,
            "MAXLON": max_lon,
            "msgtype": "simple"
        }
        
        data = await self._make_request("exportvessels/v:8", params)
        
        if not data or not isinstance(data, list):
            return []
        
        positions = []
        for vessel in data:
            position = VesselPosition(
                mmsi=vessel.get("MMSI", ""),
                imo=vessel.get("IMO"),
                vessel_name=vessel.get("SHIPNAME", ""),
                latitude=float(vessel.get("LAT", 0)),
                longitude=float(vessel.get("LON", 0)),
                speed_knots=float(vessel.get("SPEED", 0)) / 10,
                course=float(vessel.get("COURSE", 0)),
                heading=float(vessel.get("HEADING", 0)),
                navigation_status=NavigationStatus(str(vessel.get("STATUS", 15))),
                timestamp=self._parse_timestamp(vessel.get("TIMESTAMP")),
                received_at=datetime.utcnow(),
                data_source="MarineTraffic"
            )
            
            # Filter by vessel type if specified
            if vessel_types:
                vessel_type = self._map_vessel_type(vessel.get("TYPE_CODE"))
                if vessel_type not in vessel_types:
                    continue
            
            positions.append(position)
        
        return positions
    
    def _map_vessel_type(self, type_code: Optional[int]) -> VesselType:
        """Map AIS type code to VesselType."""
        if not type_code:
            return VesselType.OTHER
        
        # Container ships (specific codes)
        if type_code in [71, 72, 73, 74, 75, 76, 77, 78, 79]:
            # Cargo ships - need to check name for container
            return VesselType.GENERAL_CARGO
        
        # Tankers
        if 80 <= type_code <= 89:
            return VesselType.TANKER
        
        # Bulk carriers typically 70-79 with specific subtypes
        if type_code == 70:
            return VesselType.BULK_CARRIER
        
        return VesselType.OTHER
    
    def _parse_timestamp(self, ts: Optional[str]) -> datetime:
        """Parse MarineTraffic timestamp."""
        if not ts:
            return datetime.utcnow()
        
        try:
            return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return datetime.utcnow()
    
    def _parse_eta(self, eta: Optional[str]) -> Optional[datetime]:
        """Parse ETA string."""
        if not eta:
            return None
        
        try:
            return datetime.strptime(eta, "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return None
    
    # =========================================================================
    # Mock methods for development/testing
    # =========================================================================
    
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
            vessel_name=vessel_name or "MOCK VESSEL",
            latitude=1.2644 + random.uniform(-0.1, 0.1),  # Near Singapore
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
            data_source="MOCK"
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
            vessel_name="MOCK VESSEL",
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
    
    def _mock_voyage_info(
        self,
        mmsi: Optional[str],
        imo: Optional[str]
    ) -> VoyageInfo:
        """Generate mock voyage info."""
        return VoyageInfo(
            mmsi=mmsi or "123456789",
            imo=imo,
            vessel_name="MOCK VESSEL",
            origin_port="SGSIN",
            origin_port_name="Singapore",
            destination_port="NLRTM",
            destination_port_name="Rotterdam",
            departure_time=datetime.utcnow() - timedelta(days=7),
            eta=datetime.utcnow() + timedelta(days=21),
            distance_remaining_nm=8500.0,
            distance_traveled_nm=2100.0,
            progress_percentage=19.8
        )
    
    def _mock_historical_track(
        self,
        mmsi: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[TrackPoint]:
        """Generate mock historical track."""
        import random
        
        points = []
        current = start_time
        lat, lon = 1.2644, 103.8217  # Start near Singapore
        
        while current < end_time:
            points.append(TrackPoint(
                latitude=lat,
                longitude=lon,
                timestamp=current,
                speed_knots=12.0 + random.uniform(-1, 1),
                course=315.0 + random.uniform(-5, 5)  # NW towards Europe
            ))
            
            # Move vessel (simplified)
            lat += 0.1 + random.uniform(-0.02, 0.02)
            lon -= 0.05 + random.uniform(-0.02, 0.02)
            current += timedelta(hours=1)
        
        return points
    
    def _mock_area_search(
        self,
        min_lat: float,
        min_lon: float,
        max_lat: float,
        max_lon: float
    ) -> List[VesselPosition]:
        """Generate mock area search results."""
        import random
        
        vessel_names = [
            "EVER GIVEN", "MSC OSCAR", "MAERSK EINDHOVEN",
            "CMA CGM MARCO POLO", "COSCO SHIPPING TAURUS"
        ]
        
        positions = []
        for i, name in enumerate(vessel_names):
            positions.append(VesselPosition(
                mmsi=f"12345678{i}",
                imo=f"999999{i}",
                vessel_name=name,
                latitude=min_lat + random.uniform(0, max_lat - min_lat),
                longitude=min_lon + random.uniform(0, max_lon - min_lon),
                speed_knots=random.uniform(10, 18),
                course=random.uniform(0, 360),
                heading=random.uniform(0, 360),
                navigation_status=NavigationStatus.UNDER_WAY_ENGINE,
                timestamp=datetime.utcnow() - timedelta(minutes=random.randint(1, 30)),
                received_at=datetime.utcnow(),
                data_source="MOCK"
            ))
        
        return positions
