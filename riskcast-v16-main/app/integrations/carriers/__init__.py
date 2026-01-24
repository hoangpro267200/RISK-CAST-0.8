"""
Carrier Integration Module
Real-time carrier performance data from external APIs
"""

try:
    from app.integrations.carriers.project44 import (
        Project44Client,
        CarrierPerformance,
        CarrierRoutePerformance,
        CarrierDataQuality,
        create_carrier_client
    )
    from app.integrations.carriers.carrier_service import (
        CarrierService,
        get_carrier_service
    )
    
    __all__ = [
        "Project44Client",
        "CarrierPerformance",
        "CarrierRoutePerformance",
        "CarrierDataQuality",
        "create_carrier_client",
        "CarrierService",
        "get_carrier_service",
    ]
except ImportError as e:
    # Graceful degradation if dependencies missing
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Carrier integration not available: {e}")
    __all__ = []
