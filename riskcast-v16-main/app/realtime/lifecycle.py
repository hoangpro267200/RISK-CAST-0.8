"""
Real-time System Lifecycle Management

Handles startup and shutdown of WebSocket manager and risk monitor.
"""

from app.realtime.websocket_manager import ws_manager
from app.realtime.risk_monitor import risk_monitor
from app.core.logging import get_logger


logger = get_logger(__name__)


async def startup_realtime_systems():
    """
    Start real-time monitoring systems.
    
    Called during application startup.
    """
    try:
        # Start WebSocket manager
        await ws_manager.start()
        logger.info("WebSocket manager started successfully")
        
        # Start risk monitor
        await risk_monitor.start()
        logger.info("Risk monitor started successfully")
        
        logger.info("Real-time systems startup complete")
        
    except Exception as e:
        logger.error(f"Real-time systems startup failed: {e}")
        raise


async def shutdown_realtime_systems():
    """
    Stop real-time monitoring systems.
    
    Called during application shutdown.
    """
    try:
        # Stop risk monitor
        await risk_monitor.stop()
        logger.info("Risk monitor stopped")
        
        # Stop WebSocket manager (will close all connections)
        await ws_manager.stop()
        logger.info("WebSocket manager stopped")
        
        logger.info("Real-time systems shutdown complete")
        
    except Exception as e:
        logger.error(f"Real-time systems shutdown failed: {e}")
        # Don't raise during shutdown
