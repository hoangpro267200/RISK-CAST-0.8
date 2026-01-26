"""
Fixer.io API Client

API Documentation: https://fixer.io/documentation
"""

import aiohttp
import os
from datetime import date
from typing import Dict, Optional

from app.core.logging import get_logger


logger = get_logger(__name__)


class FixerClient:
    """
    Fixer.io API client for exchange rates.
    """
    
    BASE_URL = "http://data.fixer.io/api"  # Free tier uses HTTP
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("FIXER_API_KEY")
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("Fixer API key not configured")
    
    async def get_latest_rates(
        self,
        base: str = "USD"
    ) -> Dict[str, float]:
        """
        Get latest exchange rates.
        
        Note: Free tier only supports EUR as base
        """
        if not self.api_key:
            return self._mock_rates(base)
        
        params = {
            "access_key": self.api_key,
            "base": "EUR",  # Free tier limitation
            "symbols": ",".join([
                "USD", "GBP", "JPY", "CNY", "SGD", "HKD", "KRW",
                "AUD", "CHF", "INR", "VND", "THB", "MYR", "IDR",
                "PHP", "AED", "SAR"
            ])
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/latest",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    data = await response.json()
                    
                    if not data.get("success"):
                        logger.error(f"Fixer API error: {data.get('error')}")
                        return self._mock_rates(base)
                    
                    rates = data.get("rates", {})
                    
                    # Convert to requested base
                    if base != "EUR":
                        base_rate = rates.get(base, 1.0)
                        if base_rate:
                            rates = {
                                code: rate / base_rate
                                for code, rate in rates.items()
                            }
                            rates["EUR"] = 1.0 / base_rate
                    
                    return rates
                    
        except Exception as e:
            logger.error(f"Fixer API request failed: {e}")
            return self._mock_rates(base)
    
    async def get_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[float]:
        """Get single exchange rate."""
        rates = await self.get_latest_rates(from_currency)
        return rates.get(to_currency)
    
    async def get_historical_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date
    ) -> Optional[float]:
        """Get historical rate for a specific date."""
        if not self.api_key:
            return None
        
        params = {
            "access_key": self.api_key,
            "base": "EUR",
            "symbols": f"{from_currency},{to_currency}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/{rate_date.isoformat()}",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    data = await response.json()
                    
                    if not data.get("success"):
                        return None
                    
                    rates = data.get("rates", {})
                    from_rate = rates.get(from_currency, 1.0)
                    to_rate = rates.get(to_currency, 1.0)
                    
                    if from_rate and from_rate != 0:
                        return to_rate / from_rate
                    return None
                    
        except Exception as e:
            logger.error(f"Fixer historical request failed: {e}")
            return None
    
    def _mock_rates(self, base: str = "USD") -> Dict[str, float]:
        """Mock rates for development."""
        usd_rates = {
            "EUR": 0.92,
            "GBP": 0.79,
            "JPY": 149.50,
            "CNY": 7.24,
            "SGD": 1.34,
            "HKD": 7.82,
            "KRW": 1320.00,
            "AUD": 1.53,
            "CHF": 0.88,
            "INR": 83.10,
            "VND": 24500.00,
            "THB": 35.50,
            "MYR": 4.72,
            "IDR": 15650.00,
            "PHP": 56.20,
            "AED": 3.67,
            "SAR": 3.75,
        }
        
        if base == "USD":
            return usd_rates
        
        # Convert to requested base
        base_rate = usd_rates.get(base, 1.0)
        if base_rate:
            return {
                code: rate / base_rate
                for code, rate in usd_rates.items()
            }
        return usd_rates
