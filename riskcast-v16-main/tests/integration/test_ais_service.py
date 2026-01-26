"""
Tests for AIS Vessel Tracking Service
"""

import pytest
from datetime import datetime, timedelta

from app.integrations.ais import AISService, MarineTrafficAISClient
from app.integrations.ais.ais_service import VesselType, NavigationStatus


class TestAISService:
    """Test AIS Service functionality."""
    
    @pytest.fixture
    def ais_service(self):
        client = MarineTrafficAISClient()  # Will use mock data
        return AISService(marine_traffic_client=client)
    
    @pytest.mark.asyncio
    async def test_get_vessel_position(self, ais_service):
        """Test getting vessel position."""
        position = await ais_service.get_vessel_position(mmsi="123456789")
        
        assert position is not None
        assert position.mmsi == "123456789"
        assert -90 <= position.latitude <= 90
        assert -180 <= position.longitude <= 180
        assert position.speed_knots >= 0
    
    @pytest.mark.asyncio
    async def test_get_vessel_info(self, ais_service):
        """Test getting vessel info."""
        info = await ais_service.get_vessel_info(mmsi="123456789")
        
        assert info is not None
        assert info.length_meters > 0
        assert info.width_meters > 0
        assert info.vessel_type in VesselType
    
    @pytest.mark.asyncio
    async def test_vessel_risk_assessment(self, ais_service):
        """Test vessel risk assessment."""
        risk = await ais_service.assess_vessel_risk(mmsi="123456789")
        
        assert "risk_score" in risk
        assert "risk_grade" in risk
        assert 0 <= risk["risk_score"] <= 1
        assert risk["risk_grade"] in ["A", "B", "C", "D", "F"]
    
    @pytest.mark.asyncio
    async def test_high_risk_zone_detection(self, ais_service):
        """Test high-risk zone detection."""
        # Create position in Gulf of Aden
        from app.integrations.ais.models import VesselPosition
        
        position = VesselPosition(
            mmsi="123456789",
            imo="9999999",
            vessel_name="TEST VESSEL",
            latitude=12.5,  # In Gulf of Aden
            longitude=47.0,
            speed_knots=12.0,
            course=270.0,
            heading=270.0,
            navigation_status=NavigationStatus.UNDER_WAY_ENGINE,
            timestamp=datetime.utcnow(),
            received_at=datetime.utcnow()
        )
        
        alerts = await ais_service.check_vessel_in_high_risk_zone(position)
        
        # Should detect Gulf of Aden zone
        assert len(alerts) > 0
        assert any(a.zone_name == "Gulf of Aden / Somali Waters" for a in alerts)
    
    @pytest.mark.asyncio
    async def test_area_search(self, ais_service):
        """Test vessel area search."""
        vessels = await ais_service.search_vessels_in_area(
            min_lat=1.0,
            min_lon=103.0,
            max_lat=2.0,
            max_lon=105.0
        )
        
        assert isinstance(vessels, list)
        # Mock should return some vessels
        assert len(vessels) > 0
    
    @pytest.mark.asyncio
    async def test_historical_track(self, ais_service):
        """Test historical track retrieval."""
        track = await ais_service.get_historical_track(
            mmsi="123456789",
            start_time=datetime.utcnow() - timedelta(hours=24),
            end_time=datetime.utcnow()
        )
        
        assert isinstance(track, list)
        assert len(track) > 0
        
        for point in track:
            assert -90 <= point.latitude <= 90
            assert -180 <= point.longitude <= 180
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, ais_service):
        """Test that caching works correctly."""
        # First call
        position1 = await ais_service.get_vessel_position(mmsi="123456789")
        assert position1 is not None
        
        # Second call should use cache (within TTL)
        position2 = await ais_service.get_vessel_position(mmsi="123456789")
        assert position2 is not None
        assert position2.mmsi == position1.mmsi
