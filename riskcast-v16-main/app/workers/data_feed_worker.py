"""
Scheduled data feed ingestion worker.

Runs data feed ingestion on a schedule.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.data_feed_service import (
    DataFeedService,
    MarineTrafficProvider,
    Project44Provider
)
from app.services.corridor_intelligence_service import CorridorIntelligenceService
from app.services.oracle_event_service import OracleEventService
from app.core.audit_ledger.ledger import AuditLedger
from app.config import settings

logger = logging.getLogger(__name__)


# Schedule configuration (cron format)
INGESTION_SCHEDULE = {
    "port_congestion": "0 */4 * * *",    # Every 4 hours
    "carrier_reliability": "0 0 * * *",   # Daily at midnight
    "corridor_delays": "0 */6 * * *"      # Every 6 hours
}


async def run_data_feed_ingestion():
    """
    Run scheduled data feed ingestion.
    
    This function can be called by:
    - Cron job
    - Task scheduler (Celery, APScheduler, etc.)
    - Manual trigger via API
    """
    logger.info("Starting scheduled data feed ingestion")
    
    db: Optional[Session] = None
    
    try:
        db = SessionLocal()
        
        audit = AuditLedger(db)
        corridor_service = CorridorIntelligenceService(db, audit)
        oracle_service = OracleEventService(db, audit)
        
        feed_service = DataFeedService(
            db, corridor_service, oracle_service, audit
        )
        
        # Register providers based on available API keys
        # Try both MARINE_TRAFFIC_API_KEY and MARINETRAFFIC_API_KEY for compatibility
        marine_traffic_key = (
            getattr(settings, 'MARINE_TRAFFIC_API_KEY', None) or
            getattr(settings, 'MARINETRAFFIC_API_KEY', None)
        )
        
        if marine_traffic_key:
            feed_service.register_provider(
                MarineTrafficProvider(marine_traffic_key)
            )
            logger.info("Registered MarineTraffic provider")
        else:
            logger.warning("MarineTraffic API key not configured, skipping MarineTraffic provider")
        
        if hasattr(settings, 'PROJECT44_API_KEY') and settings.PROJECT44_API_KEY:
            feed_service.register_provider(
                Project44Provider(settings.PROJECT44_API_KEY)
            )
            logger.info("Registered Project44 provider")
        else:
            logger.warning("PROJECT44_API_KEY not configured, skipping Project44 provider")
        
        if not feed_service.providers:
            logger.warning("No data feed providers registered, skipping ingestion")
            return {
                "error": "No providers configured",
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": datetime.utcnow().isoformat()
            }
        
        # Run ingestion
        results = feed_service.run_scheduled_ingestion()
        
        logger.info(f"Data feed ingestion completed successfully: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"Data feed ingestion failed: {e}", exc_info=True)
        raise
    finally:
        if db:
            db.close()


def run_sync():
    """
    Synchronous wrapper for running data feed ingestion.
    
    Useful for cron jobs or direct execution.
    """
    return asyncio.run(run_data_feed_ingestion())


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run ingestion
    try:
        results = run_sync()
        logger.info(f"Ingestion completed: {results}")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        exit(1)
