"""
AIS Vessel Tracking Integration

Provides real-time vessel tracking, position data, and risk assessment.
"""

from app.integrations.ais.ais_service import AISService
from app.integrations.ais.marine_traffic_ais import MarineTrafficAISClient
from app.integrations.ais.vessel_finder import VesselFinderClient

__all__ = ["AISService", "MarineTrafficAISClient", "VesselFinderClient"]
