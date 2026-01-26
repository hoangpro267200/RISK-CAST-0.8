"""
Market Data Integration

Provides:
1. Lloyd's market rates
2. Industry benchmarks
3. Market indices
4. Competitive rate analysis
"""

from app.integrations.market.market_service import (
    MarketDataService,
    CargoCategory,
    RouteCategory,
    MarketRate,
    MarketBenchmark,
    MarketIndex
)
from app.integrations.market.lloyds_client import LloydsListClient

__all__ = [
    "MarketDataService",
    "LloydsListClient",
    "CargoCategory",
    "RouteCategory",
    "MarketRate",
    "MarketBenchmark",
    "MarketIndex"
]
