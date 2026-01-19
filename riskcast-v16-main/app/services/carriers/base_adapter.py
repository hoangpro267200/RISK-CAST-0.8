"""
RISKCAST Carrier API Base Adapter
==================================
Base class for all carrier API adapters.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from app.models.insurance import (
    CarrierQuoteRequest, CarrierQuoteResponse,
    CarrierBindRequest, CarrierBindResponse,
    InsuredParty, InsuranceQuote
)

logger = logging.getLogger(__name__)


class CarrierAdapter(ABC):
    """
    Base class for carrier API adapters.
    All carrier adapters must implement this interface.
    """
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize carrier adapter.
        
        Args:
            api_key: Carrier API key
            api_secret: Carrier API secret (if required)
            base_url: Base URL for carrier API
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url or self.get_default_base_url()
        self.rate_limit = self.get_rate_limit()
    
    @abstractmethod
    def get_default_base_url(self) -> str:
        """Get default base URL for carrier API."""
        pass
    
    @abstractmethod
    def get_rate_limit(self) -> int:
        """Get rate limit (requests per minute)."""
        pass
    
    @abstractmethod
    def authenticate(self) -> Dict[str, str]:
        """
        Authenticate with carrier API.
        
        Returns:
            Headers dict with authentication tokens
        """
        pass
    
    @abstractmethod
    async def get_quote(
        self,
        request: CarrierQuoteRequest
    ) -> CarrierQuoteResponse:
        """
        Get insurance quote from carrier.
        
        Args:
            request: Quote request
            
        Returns:
            Quote response
        """
        pass
    
    @abstractmethod
    async def bind_policy(
        self,
        request: CarrierBindRequest
    ) -> CarrierBindResponse:
        """
        Bind insurance policy with carrier.
        
        Args:
            request: Bind request
            
        Returns:
            Bind response
        """
        pass
    
    @abstractmethod
    async def submit_claim(
        self,
        policy_number: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Submit claim to carrier.
        
        Args:
            policy_number: Policy number
            claim_data: Claim data
            
        Returns:
            Claim submission result
        """
        pass
    
    def normalize_quote_response(
        self,
        carrier_response: Dict[str, Any]
    ) -> CarrierQuoteResponse:
        """
        Normalize carrier-specific response to standard format.
        
        Args:
            carrier_response: Raw carrier API response
            
        Returns:
            Normalized quote response
        """
        # Default implementation - override in subclasses
        return CarrierQuoteResponse(
            quote_id=carrier_response.get("quote_id", ""),
            status="quoted",
            premium={
                "base_premium": carrier_response.get("premium", {}).get("base_premium", 0),
                "risk_adjustment": carrier_response.get("premium", {}).get("risk_adjustment", 0),
                "surcharges": carrier_response.get("premium", {}).get("surcharges", []),
                "total_premium": carrier_response.get("premium", {}).get("total_premium", 0),
                "currency": carrier_response.get("premium", {}).get("currency", "USD")
            },
            coverage_details={
                "sum_insured": carrier_response.get("coverage", {}).get("sum_insured", 0),
                "deductible": carrier_response.get("coverage", {}).get("deductible", 0),
                "policy_type": carrier_response.get("coverage", {}).get("policy_type", ""),
                "territorial_scope": carrier_response.get("coverage", {}).get("territorial_scope", "")
            },
            valid_until=carrier_response.get("valid_until", "")
        )
    
    def handle_error(self, error: Exception, context: str) -> None:
        """
        Handle API errors.
        
        Args:
            error: Exception that occurred
            context: Context where error occurred
        """
        logger.error(
            f"Carrier API error in {context}: {error}",
            exc_info=True,
            extra={
                "carrier": self.__class__.__name__,
                "context": context
            }
        )
