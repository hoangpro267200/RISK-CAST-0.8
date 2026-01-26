"""
Currency Exchange Rate API Endpoints
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.dependencies.auth import get_current_user
from app.integrations.currency import ExchangeRateService, FixerClient, OpenExchangeClient
from app.integrations.currency.exchange_rate_service import Currency
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/currency", tags=["Currency Exchange"])


# Singleton
_exchange_service: Optional[ExchangeRateService] = None


def get_exchange_service() -> ExchangeRateService:
    global _exchange_service
    if _exchange_service is None:
        fixer = FixerClient()
        openexchange = OpenExchangeClient()
        _exchange_service = ExchangeRateService(
            fixer_client=fixer,
            openexchange_client=openexchange
        )
    return _exchange_service


# Response Models
class ExchangeRateResponse(BaseModel):
    base_currency: str
    target_currency: str
    rate: str
    timestamp: str
    source: str


class ConversionResponse(BaseModel):
    from_currency: str
    to_currency: str
    from_amount: str
    to_amount: str
    rate_used: str
    rate_timestamp: str


class AllRatesResponse(BaseModel):
    base_currency: str
    rates: dict
    timestamp: str


# Endpoints
@router.get("/rate", response_model=ExchangeRateResponse)
async def get_exchange_rate(
    from_currency: str = Query(..., description="Source currency code (e.g., USD)"),
    to_currency: str = Query(..., description="Target currency code (e.g., EUR)"),
    current_user = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_service)
):
    """Get exchange rate between two currencies."""
    try:
        rate = await service.get_rate(from_currency, to_currency)
        
        return ExchangeRateResponse(
            base_currency=rate.base_currency,
            target_currency=rate.target_currency,
            rate=str(rate.rate),
            timestamp=rate.timestamp.isoformat(),
            source=rate.source
        )
    except Exception as e:
        logger.error(f"Rate fetch error: {e}")
        raise HTTPException(500, f"Failed to fetch rate: {str(e)}")


@router.get("/rates", response_model=AllRatesResponse)
async def get_all_rates(
    base_currency: str = Query("USD", description="Base currency"),
    current_user = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_service)
):
    """Get all exchange rates for a base currency."""
    rates = await service.get_all_rates(base_currency)
    
    return AllRatesResponse(
        base_currency=base_currency,
        rates={
            code: str(rate.rate)
            for code, rate in rates.items()
        },
        timestamp=datetime.utcnow().isoformat()
    )


@router.post("/convert", response_model=ConversionResponse)
async def convert_currency(
    amount: Decimal = Query(..., description="Amount to convert"),
    from_currency: str = Query(..., description="Source currency"),
    to_currency: str = Query(..., description="Target currency"),
    current_user = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_service)
):
    """Convert amount between currencies."""
    result = await service.convert(amount, from_currency, to_currency)
    
    return ConversionResponse(
        from_currency=result.from_currency,
        to_currency=result.to_currency,
        from_amount=str(result.from_amount),
        to_amount=str(result.to_amount),
        rate_used=str(result.rate_used),
        rate_timestamp=result.rate_timestamp.isoformat()
    )


@router.get("/historical")
async def get_historical_rate(
    from_currency: str,
    to_currency: str,
    rate_date: date,
    current_user = Depends(get_current_user),
    service: ExchangeRateService = Depends(get_exchange_service)
):
    """Get historical exchange rate for a specific date."""
    rate = await service.get_historical_rate(from_currency, to_currency, rate_date)
    
    return ExchangeRateResponse(
        base_currency=rate.base_currency,
        target_currency=rate.target_currency,
        rate=str(rate.rate),
        timestamp=rate.timestamp.isoformat(),
        source=rate.source
    )


@router.get("/supported")
async def get_supported_currencies():
    """Get list of supported currencies."""
    return {
        "currencies": [
            {"code": c.value, "name": c.name}
            for c in Currency
        ]
    }
