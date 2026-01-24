"""
Climate Integration Module
Real-time climate data from NOAA and JTWC
"""

try:
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
    from app.integrations.climate.climate_service import (
        ClimateService,
        get_climate_service
    )
    
    __all__ = [
        "NOAAClient",
        "ClimateIndices",
        "ENSOPhase",
        "ClimateDataQuality",
        "create_climate_client",
        "JTWCClient",
        "create_jtwc_client",
        "ClimateService",
        "get_climate_service",
    ]
except ImportError as e:
    # Graceful degradation if dependencies missing
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Climate integration not available: {e}")
    __all__ = []
