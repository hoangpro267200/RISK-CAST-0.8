import random
from datetime import datetime

from app.models.shipment import Shipment


def build_tracking_event_from_mock_ais(shipment: Shipment) -> dict:
    """
    Create a fake tracking event for a shipment.
    """
    base_lat = 1.29  # near Singapore
    base_lon = 103.85
    jitter = lambda: random.uniform(-0.5, 0.5)
    return {
        "shipmentId": shipment.id,
        "lat": base_lat + jitter(),
        "lon": base_lon + jitter(),
        "status": "IN_TRANSIT",
        "source": "MOCK_AIS",
        "timestamp": datetime.utcnow().isoformat(),
    }









