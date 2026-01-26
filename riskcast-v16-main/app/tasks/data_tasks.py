"""
Data Refresh Background Tasks
"""

from datetime import datetime, timedelta
from typing import Dict
import asyncio

from celery.utils.log import get_task_logger

from app.tasks.celery_app import celery_app


logger = get_task_logger(__name__)


@celery_app.task(name="app.tasks.data_tasks.refresh_exchange_rates")
def refresh_exchange_rates() -> Dict:
    """
    Refresh exchange rates from external API.
    """
    logger.info("Refreshing exchange rates")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_async_refresh_rates())
        return result
    finally:
        loop.close()


async def _async_refresh_rates() -> Dict:
    """Async rate refresh."""
    from app.integrations.currency import ExchangeRateService, FixerClient
    
    service = ExchangeRateService(fixer_client=FixerClient())
    rates = await service.get_all_rates("USD")
    
    return {
        "currencies_updated": len(rates),
        "refreshed_at": datetime.utcnow().isoformat()
    }


@celery_app.task(name="app.tasks.data_tasks.refresh_weather_data")
def refresh_weather_data() -> Dict:
    """
    Refresh weather data for monitored routes.
    """
    logger.info("Refreshing weather data")
    
    # Implementation would refresh weather for active routes
    return {
        "routes_updated": 0,
        "refreshed_at": datetime.utcnow().isoformat()
    }


@celery_app.task(name="app.tasks.data_tasks.refresh_port_data")
def refresh_port_data() -> Dict:
    """
    Refresh port congestion data.
    """
    logger.info("Refreshing port data")
    
    return {
        "ports_updated": 0,
        "refreshed_at": datetime.utcnow().isoformat()
    }


@celery_app.task(name="app.tasks.data_tasks.cleanup_old_data")
def cleanup_old_data() -> Dict:
    """
    Clean up old/expired data.
    """
    logger.info("Running data cleanup")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(_async_cleanup())
        return result
    finally:
        loop.close()


async def _async_cleanup() -> Dict:
    """Async data cleanup."""
    from app.database import SessionLocal
    from sqlalchemy import delete
    from app.models.quote import Quote
    
    cutoff = datetime.utcnow() - timedelta(days=90)
    
    db = SessionLocal()
    try:
        # Delete expired quotes older than 90 days
        result = db.execute(
            delete(Quote)
            .where(Quote.status == "EXPIRED")
            .where(Quote.valid_until < cutoff)
        )
        expired_deleted = result.rowcount
        
        db.commit()
        
        return {
            "expired_quotes_deleted": expired_deleted,
            "cleanup_date": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="app.tasks.data_tasks.sync_external_data"
)
def sync_external_data(self, data_source: str) -> Dict:
    """
    Sync data from external source.
    """
    logger.info(f"Syncing data from {data_source}")
    
    try:
        # Implementation based on data source
        return {
            "source": data_source,
            "status": "synced",
            "synced_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise self.retry(exc=e, countdown=300)
