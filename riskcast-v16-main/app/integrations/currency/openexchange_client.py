"""
Open Exchange Rates API Client

API Documentation: https://docs.openexchangerates.org/
"""

import aiohttp
import os
from typing import Dict, Optional

from app.core.logging import get_logger


logger = get_logger(__name__)


class OpenExchangeClient:
    """
    Open Exchange Rates API client.
    """
    
    BASE_URL = "https://openexchangerates.org/api"
    
    def __init__(
        self,
        app_id: Optional[str] = None,
        timeout: int = 30
    ):
        self.app_id = app_id or os.getenv("OPENEXCHANGE_APP_ID")
        self.timeout = timeout
        
        if not self.app_id:
            logger.warning("OpenExchange App ID not configured")
    
    async def get_latest_rates(
        self,
        base: str = "USD"
    ) -> Dict[str, float]:
        """Get latest exchange rates."""
        if not self.app_id:
            return {}
        
        params = {
            "app_id": self.app_id,
            "base": base
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/latest.json",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        logger.error(f"OpenExchange API error: {response.status}")
                        return {}
                    
                    data = await response.json()
                    return data.get("rates", {})
                    
        except Exception as e:
            logger.error(f"OpenExchange request failed: {e}")
            return {}
    
    async def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[float]:
        """Get single exchange rate."""
        rates = await self.get_latest_rates(from_currency)
        return rates.get(to_currency)
