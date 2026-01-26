"""
Lloyd's List Intelligence API Client

API Documentation: https://lloydslistintelligence.com/api

Provides:
1. Market rate data from Lloyd's
2. Vessel valuations
3. Industry statistics
4. Market intelligence
"""

import aiohttp
import os
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

from app.integrations.market.market_service import (
    MarketRate, CargoCategory, RouteCategory
)


logger = logging.getLogger(__name__)


class LloydsListClient:
    """
    Lloyd's List Intelligence API client.
    """
    
    BASE_URL = "https://api.lloydslistintelligence.com/v1"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.api_key = api_key or os.getenv("LLOYDS_API_KEY")
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("Lloyd's API key not configured - using calculated rates")
    
    async def get_rate(
        self,
        cargo_category: CargoCategory,
        route_category: RouteCategory
    ) -> Optional[MarketRate]:
        """Get market rate from Lloyd's."""
        if not self.api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {
                    "cargo_type": cargo_category.value,
                    "route": route_category.value
                }
                
                async with session.get(
                    f"{self.BASE_URL}/insurance-rates",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Lloyd's API error: {response.status}")
                        return None
                    
                    data = await response.json()
                    
                    return MarketRate(
                        rate_id=data.get("rate_id", ""),
                        cargo_category=cargo_category,
                        route_category=route_category,
                        min_rate=Decimal(str(data.get("min_rate", 0))),
                        max_rate=Decimal(str(data.get("max_rate", 0))),
                        avg_rate=Decimal(str(data.get("avg_rate", 0))),
                        median_rate=Decimal(str(data.get("median_rate", 0))),
                        market_hardness=data.get("market_hardness", "NEUTRAL"),
                        trend=data.get("trend", "STABLE"),
                        effective_from=date.fromisoformat(data.get("effective_from", str(date.today()))),
                        effective_to=date.fromisoformat(data.get("effective_to", str(date.today()))),
                        source="LLOYDS",
                        last_updated=datetime.utcnow(),
                        sample_size=data.get("sample_size", 0),
                        confidence=data.get("confidence", 0.9)
                    )
                    
        except Exception as e:
            logger.error(f"Lloyd's API request failed: {e}")
            return None
    
    async def get_vessel_valuation(self, imo: str) -> Optional[Dict[str, Any]]:
        """Get vessel valuation data."""
        if not self.api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                async with session.get(
                    f"{self.BASE_URL}/vessels/{imo}/valuation",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Vessel valuation failed: {e}")
            return None
    
    async def get_market_statistics(
        self,
        category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get market statistics."""
        if not self.api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {}
                if category:
                    params["category"] = category
                
                async with session.get(
                    f"{self.BASE_URL}/market/statistics",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Market statistics failed: {e}")
            return None
    
    async def search_casualties(
        self,
        vessel_type: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """Search casualty database."""
        if not self.api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {}
                if vessel_type:
                    params["vessel_type"] = vessel_type
                if from_date:
                    params["from_date"] = from_date.isoformat()
                if to_date:
                    params["to_date"] = to_date.isoformat()
                
                async with session.get(
                    f"{self.BASE_URL}/casualties/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Casualty search failed: {e}")
            return None
    
    async def get_fleet_data(self, owner: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get fleet data for an owner."""
        if not self.api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                params = {}
                if owner:
                    params["owner"] = owner
                
                async with session.get(
                    f"{self.BASE_URL}/fleet",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            logger.error(f"Fleet data failed: {e}")
            return None
    
    def is_configured(self) -> bool:
        """Check if API is configured."""
        return bool(self.api_key)
