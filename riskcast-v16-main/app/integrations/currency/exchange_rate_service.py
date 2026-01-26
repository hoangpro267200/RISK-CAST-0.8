"""
Exchange Rate Service

Provides:
1. Real-time exchange rates
2. Historical rates
3. Currency conversion
4. Rate caching with TTL
5. Multiple provider fallback
"""

import asyncio
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import json

from app.core.logging import get_logger
from app.integrations.currency.fixer_client import FixerClient
from app.integrations.currency.openexchange_client import OpenExchangeClient

if TYPE_CHECKING:
    try:
        import redis.asyncio as redis
    except ImportError:
        redis = None
else:
    try:
        import redis.asyncio as redis
    except ImportError:
        redis = None


logger = get_logger(__name__)


class Currency(str, Enum):
    """Supported currencies."""
    USD = "USD"  # US Dollar (base)
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    JPY = "JPY"  # Japanese Yen
    CNY = "CNY"  # Chinese Yuan
    SGD = "SGD"  # Singapore Dollar
    HKD = "HKD"  # Hong Kong Dollar
    KRW = "KRW"  # Korean Won
    AUD = "AUD"  # Australian Dollar
    CHF = "CHF"  # Swiss Franc
    INR = "INR"  # Indian Rupee
    VND = "VND"  # Vietnamese Dong
    THB = "THB"  # Thai Baht
    MYR = "MYR"  # Malaysian Ringgit
    IDR = "IDR"  # Indonesian Rupiah
    PHP = "PHP"  # Philippine Peso
    AED = "AED"  # UAE Dirham
    SAR = "SAR"  # Saudi Riyal


@dataclass
class ExchangeRate:
    """Exchange rate data."""
    base_currency: str
    target_currency: str
    rate: Decimal
    timestamp: datetime
    source: str
    
    @property
    def inverse_rate(self) -> Decimal:
        """Get inverse rate (target -> base)."""
        if self.rate == 0:
            return Decimal(0)
        return Decimal(1) / self.rate


@dataclass
class ConversionResult:
    """Currency conversion result."""
    from_currency: str
    to_currency: str
    from_amount: Decimal
    to_amount: Decimal
    rate_used: Decimal
    rate_timestamp: datetime
    source: str


@dataclass
class RateHistory:
    """Historical rate data."""
    base_currency: str
    target_currency: str
    rates: List[Tuple[date, Decimal]]  # (date, rate)
    start_date: date
    end_date: date


class ExchangeRateService:
    """
    Unified exchange rate service with caching and fallback.
    """
    
    # Cache keys
    RATE_CACHE_PREFIX = "exchange_rate:"
    RATES_CACHE_KEY = "exchange_rates:latest"
    
    # Cache TTL
    RATE_TTL_SECONDS = 300  # 5 minutes for real-time rates
    HISTORICAL_TTL_SECONDS = 86400  # 24 hours for historical
    
    # Fallback rates (used when all providers fail)
    FALLBACK_RATES = {
        "EUR": Decimal("0.92"),
        "GBP": Decimal("0.79"),
        "JPY": Decimal("149.50"),
        "CNY": Decimal("7.24"),
        "SGD": Decimal("1.34"),
        "HKD": Decimal("7.82"),
        "KRW": Decimal("1320.00"),
        "AUD": Decimal("1.53"),
        "CHF": Decimal("0.88"),
        "INR": Decimal("83.10"),
        "VND": Decimal("24500.00"),
        "THB": Decimal("35.50"),
        "MYR": Decimal("4.72"),
        "IDR": Decimal("15650.00"),
        "PHP": Decimal("56.20"),
        "AED": Decimal("3.67"),
        "SAR": Decimal("3.75"),
    }
    
    def __init__(
        self,
        fixer_client: Optional[FixerClient] = None,
        openexchange_client: Optional[OpenExchangeClient] = None,
        redis_client: Optional[object] = None,
        base_currency: str = "USD"
    ):
        self.fixer = fixer_client
        self.openexchange = openexchange_client
        self.redis = redis_client
        self.base_currency = base_currency
        
        # In-memory cache fallback
        self._memory_cache: Dict[str, Tuple[Decimal, datetime]] = {}
    
    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        use_cache: bool = True
    ) -> ExchangeRate:
        """
        Get exchange rate between two currencies.
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            use_cache: Whether to use cached rate
        
        Returns:
            ExchangeRate object
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # Same currency
        if from_currency == to_currency:
            return ExchangeRate(
                base_currency=from_currency,
                target_currency=to_currency,
                rate=Decimal("1.0"),
                timestamp=datetime.utcnow(),
                source="identity"
            )
        
        # Check cache
        if use_cache:
            cached = await self._get_cached_rate(from_currency, to_currency)
            if cached:
                return cached
        
        # Fetch from providers
        rate = await self._fetch_rate(from_currency, to_currency)
        
        # Cache the rate
        await self._cache_rate(rate)
        
        return rate
    
    async def get_all_rates(
        self,
        base_currency: Optional[str] = None
    ) -> Dict[str, ExchangeRate]:
        """
        Get all rates for a base currency.
        """
        base = base_currency or self.base_currency
        
        # Check cache
        if self.redis:
            try:
                cached = await self.redis.get(f"{self.RATES_CACHE_KEY}:{base}")
                if cached:
                    data = json.loads(cached)
                    return {
                        code: ExchangeRate(
                            base_currency=base,
                            target_currency=code,
                            rate=Decimal(str(rate_data["rate"])),
                            timestamp=datetime.fromisoformat(rate_data["timestamp"]),
                            source=rate_data["source"]
                        )
                        for code, rate_data in data.items()
                    }
            except Exception as e:
                logger.warning(f"Redis cache read failed: {e}")
        
        # Fetch from provider
        rates = {}
        
        try:
            if self.fixer:
                provider_rates = await self.fixer.get_latest_rates(base)
                for code, rate in provider_rates.items():
                    rates[code] = ExchangeRate(
                        base_currency=base,
                        target_currency=code,
                        rate=Decimal(str(rate)),
                        timestamp=datetime.utcnow(),
                        source="fixer"
                    )
        except Exception as e:
            logger.warning(f"Fixer failed: {e}")
            
            try:
                if self.openexchange:
                    provider_rates = await self.openexchange.get_latest_rates(base)
                    for code, rate in provider_rates.items():
                        rates[code] = ExchangeRate(
                            base_currency=base,
                            target_currency=code,
                            rate=Decimal(str(rate)),
                            timestamp=datetime.utcnow(),
                            source="openexchange"
                        )
            except Exception as e2:
                logger.error(f"OpenExchange also failed: {e2}")
                # Use fallback rates
                rates = self._get_fallback_rates(base)
        
        # Cache all rates
        if rates and self.redis:
            try:
                cache_data = {
                    code: {
                        "rate": str(rate.rate),
                        "timestamp": rate.timestamp.isoformat(),
                        "source": rate.source
                    }
                    for code, rate in rates.items()
                }
                await self.redis.setex(
                    f"{self.RATES_CACHE_KEY}:{base}",
                    self.RATE_TTL_SECONDS,
                    json.dumps(cache_data)
                )
            except Exception as e:
                logger.warning(f"Redis cache write failed: {e}")
        
        return rates
    
    async def convert(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        round_decimals: int = 2
    ) -> ConversionResult:
        """
        Convert amount between currencies.
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            round_decimals: Decimal places for result
        
        Returns:
            ConversionResult with converted amount
        """
        rate = await self.get_rate(from_currency, to_currency)
        
        converted = amount * rate.rate
        
        # Round appropriately
        if round_decimals >= 0:
            quantize_str = "0." + "0" * round_decimals
            converted = converted.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
        
        return ConversionResult(
            from_currency=from_currency,
            to_currency=to_currency,
            from_amount=amount,
            to_amount=converted,
            rate_used=rate.rate,
            rate_timestamp=rate.timestamp,
            source=rate.source
        )
    
    async def convert_to_usd(
        self,
        amount: Decimal,
        currency: str
    ) -> ConversionResult:
        """Convert any currency to USD."""
        return await self.convert(amount, currency, "USD")
    
    async def convert_from_usd(
        self,
        amount: Decimal,
        currency: str
    ) -> ConversionResult:
        """Convert USD to any currency."""
        return await self.convert(amount, "USD", currency)
    
    async def get_historical_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: date
    ) -> ExchangeRate:
        """
        Get historical exchange rate for a specific date.
        """
        cache_key = f"{self.RATE_CACHE_PREFIX}historical:{from_currency}:{to_currency}:{rate_date.isoformat()}"
        
        # Check cache
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return ExchangeRate(
                        base_currency=from_currency,
                        target_currency=to_currency,
                        rate=Decimal(str(data["rate"])),
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        source=data["source"]
                    )
            except Exception as e:
                logger.warning(f"Redis historical cache read failed: {e}")
        
        # Fetch from provider
        rate = None
        
        try:
            if self.fixer:
                rate_value = await self.fixer.get_historical_rate(
                    from_currency, to_currency, rate_date
                )
                if rate_value:
                    rate = ExchangeRate(
                        base_currency=from_currency,
                        target_currency=to_currency,
                        rate=Decimal(str(rate_value)),
                        timestamp=datetime.combine(rate_date, datetime.min.time()),
                        source="fixer_historical"
                    )
        except Exception as e:
            logger.warning(f"Fixer historical failed: {e}")
        
        if not rate:
            # Use fallback (approximate with current rate)
            current = await self.get_rate(from_currency, to_currency)
            rate = ExchangeRate(
                base_currency=from_currency,
                target_currency=to_currency,
                rate=current.rate,
                timestamp=datetime.combine(rate_date, datetime.min.time()),
                source="fallback_current"
            )
        
        # Cache
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    self.HISTORICAL_TTL_SECONDS,
                    json.dumps({
                        "rate": str(rate.rate),
                        "timestamp": rate.timestamp.isoformat(),
                        "source": rate.source
                    })
                )
            except Exception as e:
                logger.warning(f"Redis historical cache write failed: {e}")
        
        return rate
    
    async def get_rate_history(
        self,
        from_currency: str,
        to_currency: str,
        start_date: date,
        end_date: date
    ) -> RateHistory:
        """
        Get historical rates for a date range.
        """
        rates = []
        current = start_date
        
        while current <= end_date:
            rate = await self.get_historical_rate(from_currency, to_currency, current)
            rates.append((current, rate.rate))
            current += timedelta(days=1)
        
        return RateHistory(
            base_currency=from_currency,
            target_currency=to_currency,
            rates=rates,
            start_date=start_date,
            end_date=end_date
        )
    
    async def _get_cached_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Get rate from cache."""
        cache_key = f"{self.RATE_CACHE_PREFIX}{from_currency}:{to_currency}"
        
        # Try Redis
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return ExchangeRate(
                        base_currency=from_currency,
                        target_currency=to_currency,
                        rate=Decimal(str(data["rate"])),
                        timestamp=datetime.fromisoformat(data["timestamp"]),
                        source=data["source"]
                    )
            except Exception as e:
                logger.debug(f"Redis cache read failed: {e}")
        
        # Try memory cache
        if cache_key in self._memory_cache:
            rate, cached_at = self._memory_cache[cache_key]
            if (datetime.utcnow() - cached_at).total_seconds() < self.RATE_TTL_SECONDS:
                return ExchangeRate(
                    base_currency=from_currency,
                    target_currency=to_currency,
                    rate=rate,
                    timestamp=cached_at,
                    source="memory_cache"
                )
        
        return None
    
    async def _cache_rate(self, rate: ExchangeRate):
        """Cache exchange rate."""
        cache_key = f"{self.RATE_CACHE_PREFIX}{rate.base_currency}:{rate.target_currency}"
        
        # Redis
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    self.RATE_TTL_SECONDS,
                    json.dumps({
                        "rate": str(rate.rate),
                        "timestamp": rate.timestamp.isoformat(),
                        "source": rate.source
                    })
                )
            except Exception as e:
                logger.debug(f"Redis cache write failed: {e}")
        
        # Memory cache
        self._memory_cache[cache_key] = (rate.rate, rate.timestamp)
        
        # Also cache inverse
        inverse_key = f"{self.RATE_CACHE_PREFIX}{rate.target_currency}:{rate.base_currency}"
        self._memory_cache[inverse_key] = (rate.inverse_rate, rate.timestamp)
    
    async def _fetch_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> ExchangeRate:
        """Fetch rate from providers with fallback."""
        # Try Fixer first
        if self.fixer:
            try:
                rate = await self.fixer.get_rate(from_currency, to_currency)
                if rate:
                    return ExchangeRate(
                        base_currency=from_currency,
                        target_currency=to_currency,
                        rate=Decimal(str(rate)),
                        timestamp=datetime.utcnow(),
                        source="fixer"
                    )
            except Exception as e:
                logger.warning(f"Fixer rate fetch failed: {e}")
        
        # Try OpenExchange
        if self.openexchange:
            try:
                rate = await self.openexchange.get_rate(from_currency, to_currency)
                if rate:
                    return ExchangeRate(
                        base_currency=from_currency,
                        target_currency=to_currency,
                        rate=Decimal(str(rate)),
                        timestamp=datetime.utcnow(),
                        source="openexchange"
                    )
            except Exception as e:
                logger.warning(f"OpenExchange rate fetch failed: {e}")
        
        # Use fallback
        return self._get_fallback_rate(from_currency, to_currency)
    
    def _get_fallback_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> ExchangeRate:
        """Get fallback rate when providers fail."""
        if from_currency == "USD":
            rate = self.FALLBACK_RATES.get(to_currency, Decimal("1.0"))
        elif to_currency == "USD":
            from_rate = self.FALLBACK_RATES.get(from_currency, Decimal("1.0"))
            rate = Decimal("1.0") / from_rate if from_rate else Decimal("1.0")
        else:
            # Cross rate via USD
            from_usd = self.FALLBACK_RATES.get(from_currency, Decimal("1.0"))
            to_usd = self.FALLBACK_RATES.get(to_currency, Decimal("1.0"))
            rate = to_usd / from_usd if from_usd else Decimal("1.0")
        
        logger.warning(
            f"Using fallback rate for {from_currency}/{to_currency}: {rate}"
        )
        
        return ExchangeRate(
            base_currency=from_currency,
            target_currency=to_currency,
            rate=rate,
            timestamp=datetime.utcnow(),
            source="fallback"
        )
    
    def _get_fallback_rates(self, base: str) -> Dict[str, ExchangeRate]:
        """Get all fallback rates for a base currency."""
        rates = {}
        
        for currency in Currency:
            if currency.value != base:
                rate = self._get_fallback_rate(base, currency.value)
                rates[currency.value] = rate
        
        return rates
