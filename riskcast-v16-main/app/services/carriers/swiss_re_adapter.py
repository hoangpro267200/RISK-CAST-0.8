"""
RISKCAST Swiss RE Parametric Adapter
=====================================
Integration with Swiss RE parametric insurance API.
"""

from typing import Dict, Optional, Any
import logging
from datetime import datetime, timedelta

from app.services.carriers.base_adapter import CarrierAdapter
from app.models.insurance import (
    CarrierQuoteRequest, CarrierQuoteResponse,
    CarrierBindRequest, CarrierBindResponse
)

logger = logging.getLogger(__name__)


class SwissREAdapter(CarrierAdapter):
    """
    Swiss RE Parametric API adapter.
    
    Specializes in parametric weather and catastrophe products.
    """
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, api_secret, base_url)
    
    def get_default_base_url(self) -> str:
        return "https://api.swissre.com/parametric/v2"
    
    def get_rate_limit(self) -> int:
        return 25  # 25 requests per minute (parametric modeling is intensive)
    
    def authenticate(self) -> Dict[str, str]:
        """
        Authenticate with Swiss RE using OAuth 2.0 + IP whitelist.
        
        Returns:
            Headers with authentication
        """
        # In production, implement OAuth 2.0 flow
        logger.warning("Swiss RE authentication - using mock token (implement OAuth in production)")
        return {
            "Authorization": f"Bearer mock_swissre_token",
            "X-API-Key": self.api_key
        }
    
    async def get_quote(
        self,
        request: Any  # CarrierQuoteRequest or Dict
    ) -> CarrierQuoteResponse:
        """
        Get parametric quote from Swiss RE.
        
        API Endpoint: POST /parametric/quotes
        """
        headers = self.authenticate()
        
        try:
            logger.info(f"Requesting Swiss RE parametric quote for request_id: {request.request_id}")
            
            # Convert to dict if needed
            if not isinstance(request, dict):
                request_dict = request.to_dict() if hasattr(request, 'to_dict') else {}
            else:
                request_dict = request
            
            # Build parametric-specific request
            parametric_request = self._build_parametric_request(request_dict)
            
            # Mock response (replace with actual API call)
            mock_response = await self._mock_parametric_quote(parametric_request)
            
            return self.normalize_quote_response(mock_response)
            
        except Exception as e:
            self.handle_error(e, "get_quote")
            raise
    
    async def bind_policy(
        self,
        request: CarrierBindRequest
    ) -> CarrierBindResponse:
        """
        Bind parametric policy with Swiss RE.
        """
        headers = self.authenticate()
        
        try:
            logger.info(f"Binding Swiss RE parametric policy for quote_id: {request.quote_id}")
            
            # Mock response
            return CarrierBindResponse(
                policy_number=f"SRE-PARAM-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                status="bound",
                policy_document_url=f"https://docs.swissre.com/parametric/{datetime.now().strftime('%Y%m%d')}",
                certificate_of_insurance=None,
                payment_instructions=None,
                effective_date=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.handle_error(e, "bind_policy")
            raise
    
    async def submit_claim(
        self,
        policy_number: str,
        claim_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parametric claims are auto-processed, but this endpoint can be used for verification.
        """
        # Parametric claims are typically automatic
        return {
            "claim_number": f"SRE-CLM-{datetime.now().strftime('%Y%m%d')}",
            "status": "auto_processed",
            "message": "Parametric claims are processed automatically when triggers are met"
        }
    
    def _build_parametric_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Build Swiss RE parametric-specific request."""
        # Extract trigger information from risk_data if available
        trigger_type = "weather_index"  # Default
        
        shipment = request.get("shipment", {})
        risk_data = request.get("risk_data", {})
        
        return {
            "product_type": trigger_type,
            "location": {
                "port_code": shipment.get("destination", {}).get("port_code", ""),
                "lat": 0.0,  # Would be looked up
                "lon": 0.0
            },
            "exposure_period": {
                "start": shipment.get("voyage", {}).get("departure_date", ""),
                "end": shipment.get("voyage", {}).get("estimated_arrival", "")
            },
            "riskcast_data": {
                "risk_score": risk_data.get("riskcast_score", 50),
                "assessment_id": risk_data.get("riskcast_assessment_id", "")
            }
        }
    
    async def _mock_parametric_quote(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Swiss RE parametric quote response."""
        # Simulate parametric pricing
        risk_score = request["riskcast_data"]["risk_score"]
        
        # Base parametric premium calculation
        # Higher risk = higher premium
        base_premium = 1000.0
        risk_multiplier = 1.0 + (risk_score / 100) * 0.5  # 0.5x to 1.5x
        total_premium = base_premium * risk_multiplier
        
        # Expected payout based on historical burn rate
        burn_rate = 0.085  # 8.5% historical trigger frequency
        expected_payout = total_premium * 0.85  # 85% loss ratio
        
        return {
            "quote_id": f"SRE_PARAM_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "status": "quoted",
            "premium": {
                "base_premium": base_premium,
                "risk_adjustment": total_premium - base_premium,
                "surcharges": [],
                "total_premium": total_premium,
                "currency": "USD"
            },
            "coverage": {
                "sum_insured": 0,  # Parametric doesn't use sum_insured
                "deductible": 0,
                "policy_type": "parametric",
                "territorial_scope": "specified_location"
            },
            "parametric_details": {
                "expected_payout": expected_payout,
                "burn_rate": burn_rate,
                "loss_ratio": 0.85,
                "basis_risk_score": 0.15
            },
            "valid_until": (datetime.now() + timedelta(days=7)).isoformat()
        }
    
    def normalize_quote_response(self, carrier_response: Dict[str, Any]) -> CarrierQuoteResponse:
        """Normalize Swiss RE parametric response."""
        return CarrierQuoteResponse(
            quote_id=carrier_response["quote_id"],
            status="quoted",
            premium={
                "base_premium": carrier_response["premium"]["base_premium"],
                "risk_adjustment": carrier_response["premium"]["risk_adjustment"],
                "surcharges": carrier_response["premium"].get("surcharges", []),
                "total_premium": carrier_response["premium"]["total_premium"],
                "currency": carrier_response["premium"].get("currency", "USD")
            },
            coverage_details={
                "sum_insured": carrier_response["coverage"].get("sum_insured", 0),
                "deductible": carrier_response["coverage"].get("deductible", 0),
                "policy_type": carrier_response["coverage"]["policy_type"],
                "territorial_scope": carrier_response["coverage"]["territorial_scope"]
            },
            valid_until=carrier_response.get("valid_until", "")
        )
