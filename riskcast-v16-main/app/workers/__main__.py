"""
Risk Run Worker Entry Point
Entry point for running the background worker process
RISKCAST V3 - Modular Monolith

Usage:
    python -m app.workers
    # or
    python app/workers/__main__.py
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.workers.risk_run_worker import RiskRunWorker
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for worker"""
    logger.info("Starting Risk Run Worker")
    logger.info(f"Database URL: {settings.DATABASE_URL[:20]}...")  # Don't log full URL
    
    worker = RiskRunWorker(db_url=settings.DATABASE_URL)
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        await worker.stop()
    except Exception as e:
        logger.exception(f"Worker crashed: {e}")
        raise
    finally:
        logger.info("Worker stopped")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
