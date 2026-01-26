"""
Market Data Integration Service

Provides:
1. Lloyd's market rates
2. Industry benchmarks
3. Market indices
4. Competitive rate analysis
5. Historical market trends
"""

import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import random

logger = logging.getLogger(__name__)


class CargoCategory(str, Enum):
    """Cargo categories for market rates."""
    GENERAL = "GENERAL"
    BULK_DRY = "BULK_DRY"
    BULK_LIQUID = "BULK_LIQUID"
    CONTAINER = "CONTAINER"
    REEFER = "REEFER"
    PROJECT = "PROJECT"
    HAZARDOUS = "HAZARDOUS"
    VEHICLES = "VEHICLES"
    LIVESTOCK = "LIVESTOCK"
    ELECTRONICS = "ELECTRONICS"
    PHARMACEUTICALS = "PHARMACEUTICALS"
    TEXTILES = "TEXTILES"


class RouteCategory(str, Enum):
    """Route categories."""
    TRANS_PACIFIC = "TRANS_PACIFIC"
    TRANS_ATLANTIC = "TRANS_ATLANTIC"
    ASIA_EUROPE = "ASIA_EUROPE"
    INTRA_ASIA = "INTRA_ASIA"
    MIDDLE_EAST = "MIDDLE_EAST"
    AFRICA = "AFRICA"
    LATIN_AMERICA = "LATIN_AMERICA"
    COASTAL = "COASTAL"
    MEDITERRANEAN = "MEDITERRANEAN"


@dataclass
class MarketRate:
    """Market rate data."""
    rate_id: str
    cargo_category: CargoCategory
    route_category: RouteCategory
    
    # Rate information (per mille - per $1000 of cargo value)
    min_rate: Decimal
    max_rate: Decimal
    avg_rate: Decimal
    median_rate: Decimal
    
    # Market context
    market_hardness: str  # "SOFT", "NEUTRAL", "HARD"
    trend: str  # "DECREASING", "STABLE", "INCREASING"
    
    # Time period
    effective_from: date
    effective_to: date
    
    # Source
    source: str
    last_updated: datetime
    
    # Additional data
    sample_size: int = 0
    confidence: float = 0.8


@dataclass
class MarketBenchmark:
    """Market benchmark comparison."""
    cargo_category: CargoCategory
    route_category: RouteCategory
    
    your_rate: Decimal
    market_avg: Decimal
    market_min: Decimal
    market_max: Decimal
    
    percentile: float  # Where your rate falls (0-100)
    competitiveness: str  # "BELOW_MARKET", "AT_MARKET", "ABOVE_MARKET"
    
    recommendation: str


@dataclass
class MarketIndex:
    """Market index value."""
    index_name: str
    index_value: float
    change_1d: float
    change_7d: float
    change_30d: float
    as_of_date: date


class MarketDataService:
    """
    Comprehensive market data service.
    """
    
    # Base market rates by cargo category (per mille)
    BASE_RATES = {
        CargoCategory.GENERAL: {"min": 0.15, "max": 0.45, "avg": 0.28},
        CargoCategory.BULK_DRY: {"min": 0.10, "max": 0.30, "avg": 0.18},
        CargoCategory.BULK_LIQUID: {"min": 0.20, "max": 0.60, "avg": 0.35},
        CargoCategory.CONTAINER: {"min": 0.12, "max": 0.35, "avg": 0.22},
        CargoCategory.REEFER: {"min": 0.25, "max": 0.70, "avg": 0.42},
        CargoCategory.PROJECT: {"min": 0.30, "max": 1.00, "avg": 0.55},
        CargoCategory.HAZARDOUS: {"min": 0.40, "max": 1.50, "avg": 0.80},
        CargoCategory.VEHICLES: {"min": 0.20, "max": 0.50, "avg": 0.32},
        CargoCategory.LIVESTOCK: {"min": 0.50, "max": 1.20, "avg": 0.75},
        CargoCategory.ELECTRONICS: {"min": 0.18, "max": 0.55, "avg": 0.35},
        CargoCategory.PHARMACEUTICALS: {"min": 0.35, "max": 0.90, "avg": 0.55},
        CargoCategory.TEXTILES: {"min": 0.12, "max": 0.38, "avg": 0.24},
    }
    
    # Route risk multipliers
    ROUTE_MULTIPLIERS = {
        RouteCategory.TRANS_PACIFIC: 1.0,
        RouteCategory.TRANS_ATLANTIC: 0.95,
        RouteCategory.ASIA_EUROPE: 1.1,
        RouteCategory.INTRA_ASIA: 0.85,
        RouteCategory.MIDDLE_EAST: 1.3,
        RouteCategory.AFRICA: 1.4,
        RouteCategory.LATIN_AMERICA: 1.15,
        RouteCategory.COASTAL: 0.75,
        RouteCategory.MEDITERRANEAN: 0.90,
    }
    
    # Market indices
    INDICES = {
        "BALTIC_DRY_INDEX": {"name": "Baltic Dry Index", "base": 1500},
        "BALTIC_CLEAN_TANKER": {"name": "Baltic Clean Tanker Index", "base": 800},
        "BALTIC_DIRTY_TANKER": {"name": "Baltic Dirty Tanker Index", "base": 1200},
        "CONTAINER_INDEX": {"name": "Container Freight Index", "base": 2500},
        "MARINE_INSURANCE_INDEX": {"name": "Marine Insurance Premium Index", "base": 100},
        "LLOYDS_MARKET_INDEX": {"name": "Lloyd's Market Index", "base": 1000},
    }
    
    CACHE_TTL = 3600  # 1 hour
    
    def __init__(
        self,
        lloyds_client = None,
        redis_client = None
    ):
        self.lloyds = lloyds_client
        self.redis = redis_client
        
        # In-memory cache
        self._rate_cache: Dict[str, Tuple[MarketRate, datetime]] = {}
    
    async def get_market_rate(
        self,
        cargo_category: CargoCategory,
        route_category: RouteCategory,
        cargo_value_usd: Optional[Decimal] = None
    ) -> MarketRate:
        """
        Get current market rate for cargo/route combination.
        """
        cache_key = f"market_rate:{cargo_category.value}:{route_category.value}"
        
        # Check cache
        if cache_key in self._rate_cache:
            cached_rate, cached_at = self._rate_cache[cache_key]
            if (datetime.utcnow() - cached_at).total_seconds() < self.CACHE_TTL:
                return cached_rate
        
        # Try Lloyd's API
        if self.lloyds:
            try:
                rate = await self.lloyds.get_rate(cargo_category, route_category)
                if rate:
                    self._rate_cache[cache_key] = (rate, datetime.utcnow())
                    return rate
            except Exception as e:
                logger.warning(f"Lloyd's API failed: {e}")
        
        # Calculate from base rates
        rate = self._calculate_rate(cargo_category, route_category)
        self._rate_cache[cache_key] = (rate, datetime.utcnow())
        
        return rate
    
    async def get_all_market_rates(self) -> List[MarketRate]:
        """Get all market rates."""
        rates = []
        
        for cargo in CargoCategory:
            for route in RouteCategory:
                rate = await self.get_market_rate(cargo, route)
                rates.append(rate)
        
        return rates
    
    async def get_rates_by_cargo(self, cargo_category: CargoCategory) -> List[MarketRate]:
        """Get rates for a specific cargo category across all routes."""
        rates = []
        for route in RouteCategory:
            rate = await self.get_market_rate(cargo_category, route)
            rates.append(rate)
        return rates
    
    async def get_rates_by_route(self, route_category: RouteCategory) -> List[MarketRate]:
        """Get rates for a specific route across all cargo types."""
        rates = []
        for cargo in CargoCategory:
            rate = await self.get_market_rate(cargo, route_category)
            rates.append(rate)
        return rates
    
    async def compare_to_market(
        self,
        your_rate: Decimal,
        cargo_category: CargoCategory,
        route_category: RouteCategory
    ) -> MarketBenchmark:
        """
        Compare your rate to market benchmarks.
        """
        market_rate = await self.get_market_rate(cargo_category, route_category)
        
        # Calculate percentile
        range_size = market_rate.max_rate - market_rate.min_rate
        if range_size > 0:
            percentile = float(
                (your_rate - market_rate.min_rate) / range_size * 100
            )
            percentile = max(0, min(100, percentile))
        else:
            percentile = 50.0
        
        # Determine competitiveness
        if your_rate < market_rate.avg_rate * Decimal("0.9"):
            competitiveness = "BELOW_MARKET"
            recommendation = "Rate is competitive. Consider slight increase for better margins."
        elif your_rate > market_rate.avg_rate * Decimal("1.1"):
            competitiveness = "ABOVE_MARKET"
            recommendation = "Rate is above market. May lose competitiveness."
        else:
            competitiveness = "AT_MARKET"
            recommendation = "Rate is well-positioned within market range."
        
        return MarketBenchmark(
            cargo_category=cargo_category,
            route_category=route_category,
            your_rate=your_rate,
            market_avg=market_rate.avg_rate,
            market_min=market_rate.min_rate,
            market_max=market_rate.max_rate,
            percentile=percentile,
            competitiveness=competitiveness,
            recommendation=recommendation
        )
    
    async def get_market_indices(self) -> List[MarketIndex]:
        """Get current market indices."""
        indices = []
        
        for index_key, index_info in self.INDICES.items():
            base = index_info["base"]
            
            # Add some variation based on current date
            day_of_year = datetime.utcnow().timetuple().tm_yday
            variation = ((day_of_year % 30) - 15) / 100  # -15% to +15%
            
            current_value = base * (1 + variation + random.uniform(-0.05, 0.05))
            
            indices.append(MarketIndex(
                index_name=index_info["name"],
                index_value=round(current_value, 2),
                change_1d=round(random.uniform(-2, 2), 2),
                change_7d=round(random.uniform(-5, 5), 2),
                change_30d=round(random.uniform(-10, 10), 2),
                as_of_date=date.today()
            ))
        
        return indices
    
    async def get_market_trend(
        self,
        cargo_category: CargoCategory,
        days: int = 30
    ) -> Dict:
        """
        Get market trend for a cargo category.
        """
        trend_data = []
        base_rate = self.BASE_RATES.get(cargo_category, self.BASE_RATES[CargoCategory.GENERAL])["avg"]
        
        # Generate deterministic but varying trend data
        for i in range(days):
            day = date.today() - timedelta(days=days - i - 1)
            # Simulate gradual changes based on day
            day_seed = day.toordinal()
            variation = 1 + ((day_seed % 20) - 10) / 100
            rate = base_rate * variation
            
            trend_data.append({
                "date": day.isoformat(),
                "rate": round(rate, 4)
            })
        
        # Calculate trend direction
        first_week_avg = sum(d["rate"] for d in trend_data[:7]) / 7
        last_week_avg = sum(d["rate"] for d in trend_data[-7:]) / 7
        
        if last_week_avg > first_week_avg * 1.03:
            trend_direction = "INCREASING"
        elif last_week_avg < first_week_avg * 0.97:
            trend_direction = "DECREASING"
        else:
            trend_direction = "STABLE"
        
        return {
            "cargo_category": cargo_category.value,
            "trend_direction": trend_direction,
            "period_days": days,
            "start_rate": trend_data[0]["rate"],
            "end_rate": trend_data[-1]["rate"],
            "change_percent": round(
                (trend_data[-1]["rate"] - trend_data[0]["rate"]) / trend_data[0]["rate"] * 100, 2
            ),
            "data_points": trend_data
        }
    
    async def get_competitive_analysis(
        self,
        cargo_category: CargoCategory,
        route_category: RouteCategory,
        your_rate: Decimal
    ) -> Dict:
        """
        Comprehensive competitive analysis.
        """
        market_rate = await self.get_market_rate(cargo_category, route_category)
        benchmark = await self.compare_to_market(your_rate, cargo_category, route_category)
        trend = await self.get_market_trend(cargo_category)
        
        return {
            "your_rate": float(your_rate),
            "market_data": {
                "min_rate": float(market_rate.min_rate),
                "max_rate": float(market_rate.max_rate),
                "avg_rate": float(market_rate.avg_rate),
                "median_rate": float(market_rate.median_rate)
            },
            "your_position": {
                "percentile": benchmark.percentile,
                "competitiveness": benchmark.competitiveness,
                "vs_average": round(
                    (float(your_rate) - float(market_rate.avg_rate)) / float(market_rate.avg_rate) * 100, 2
                )
            },
            "market_trend": {
                "direction": trend["trend_direction"],
                "change_30d_percent": trend["change_percent"]
            },
            "recommendation": benchmark.recommendation,
            "optimal_rate_range": {
                "min": float(market_rate.avg_rate * Decimal("0.95")),
                "max": float(market_rate.avg_rate * Decimal("1.05"))
            }
        }
    
    async def get_premium_estimate(
        self,
        cargo_value_usd: Decimal,
        cargo_category: CargoCategory,
        route_category: RouteCategory
    ) -> Dict:
        """
        Estimate premium based on market rates.
        """
        market_rate = await self.get_market_rate(cargo_category, route_category)
        
        # Calculate premium range
        min_premium = cargo_value_usd * market_rate.min_rate / Decimal("1000")
        max_premium = cargo_value_usd * market_rate.max_rate / Decimal("1000")
        avg_premium = cargo_value_usd * market_rate.avg_rate / Decimal("1000")
        
        return {
            "cargo_value_usd": float(cargo_value_usd),
            "cargo_category": cargo_category.value,
            "route_category": route_category.value,
            "premium_estimate": {
                "min_usd": float(min_premium.quantize(Decimal("0.01"))),
                "max_usd": float(max_premium.quantize(Decimal("0.01"))),
                "avg_usd": float(avg_premium.quantize(Decimal("0.01")))
            },
            "rate_per_mille": {
                "min": float(market_rate.min_rate),
                "max": float(market_rate.max_rate),
                "avg": float(market_rate.avg_rate)
            },
            "market_conditions": {
                "hardness": market_rate.market_hardness,
                "trend": market_rate.trend
            }
        }
    
    def _calculate_rate(
        self,
        cargo_category: CargoCategory,
        route_category: RouteCategory
    ) -> MarketRate:
        """Calculate rate from base rates and multipliers."""
        base = self.BASE_RATES.get(cargo_category, self.BASE_RATES[CargoCategory.GENERAL])
        multiplier = self.ROUTE_MULTIPLIERS.get(route_category, 1.0)
        
        # Apply market conditions based on current date
        day_of_year = datetime.utcnow().timetuple().tm_yday
        market_adjustment = 1 + ((day_of_year % 30) - 15) / 200  # -7.5% to +7.5%
        
        min_rate = Decimal(str(base["min"])) * Decimal(str(multiplier)) * Decimal(str(market_adjustment))
        max_rate = Decimal(str(base["max"])) * Decimal(str(multiplier)) * Decimal(str(market_adjustment))
        avg_rate = Decimal(str(base["avg"])) * Decimal(str(multiplier)) * Decimal(str(market_adjustment))
        
        # Determine market hardness
        if market_adjustment > 1.03:
            hardness = "HARD"
            trend = "INCREASING"
        elif market_adjustment < 0.97:
            hardness = "SOFT"
            trend = "DECREASING"
        else:
            hardness = "NEUTRAL"
            trend = "STABLE"
        
        return MarketRate(
            rate_id=f"MR-{cargo_category.value}-{route_category.value}",
            cargo_category=cargo_category,
            route_category=route_category,
            min_rate=min_rate.quantize(Decimal("0.0001")),
            max_rate=max_rate.quantize(Decimal("0.0001")),
            avg_rate=avg_rate.quantize(Decimal("0.0001")),
            median_rate=((min_rate + max_rate) / 2).quantize(Decimal("0.0001")),
            market_hardness=hardness,
            trend=trend,
            effective_from=date.today(),
            effective_to=date.today() + timedelta(days=30),
            source="CALCULATED",
            last_updated=datetime.utcnow(),
            sample_size=100,
            confidence=0.75
        )
