"""
RISKCAST Allianz AGCS (Allianz Global Corporate & Specialty) Adapter
=====================================================================
Integration with Allianz marine cargo insurance API.
"""

from typing import Dict, Optional, Any
import httpx
import logging
from datetime import datetime, timedelta

from app.services.carriers.base_adapter import CarrierAdapter
from app.models.insurance import (
    CarrierQuoteRequest, CarrierQuoteResponse,
    CarrierBindRequest, CarrierBindResponse
)

logger = logging.getLogger(__name__)


class AllianzAdapter(CarrierAdapter):
    """
    Allianz AGCS API adapter.
    
    API Documentation: https://api.agcs.allianz.com/docs
    """
    
    def __init__(self, api_key: str, api_secret: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key, api_secret, base_url)
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
    
    def get_default_base_url(self) -> str:
        return "https://api.agcs.allianz.com/v2"
    
    def get_rate_limit(self) -> int:
        return 100  # 100 requests per minute
    
    def authenticate(self) -> Dict[str, str]:
        """
        Authenticate with Allianz using OAuth 2.0 client credentials.
        
        Returns:
            Headers with Bearer token
        """
        # Check if token is still valid
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return {"Authorization": f"Bearer {self.access_token}"}
        
        # Get new token
        try:
            # In production, use actual OAuth endpoint
            # For now, mock the authentication
            logger.warning("Allianz authentication - using mock token (implement OAuth in production)")
            
            # Mock token (replace with actual OAuth flow)
            self.access_token = "mock_allianz_token"
            self.token_expires_at = datetime.now() + timedelta(hours=1)
            
            return {"Authorization": f"Bearer {self.access_token}"}
            
        except Exception as e:
            self.handle_error(e, "authentication")
            raise
    
    async def get_quote(
        self,
        request: Any  # CarrierQuoteRequest or Dict
    ) -> CarrierQuoteResponse:
        """
        Get quote from Allianz AGCS.
        
        API Endpoint: POST /marine/quotes
        """
        headers = self.authenticate()
        headers["Content-Type"] = "application/json"
        
        # Convert to dict if needed
        if isinstance(request, dict):
            from app.models.insurance import CarrierQuoteRequest
            request = CarrierQuoteRequest(**request)
        
        # Build Allianz-specific request format
        allianz_request = self._build_allianz_quote_request(request)
        
        try:
            # In production, make actual HTTP request
            # For now, return mock response
            logger.info(f"Requesting Allianz quote for request_id: {request.request_id}")
            
            # Mock response (replace with actual API call)
            mock_response = await self._mock_quote_response(request)
            
            return self.normalize_quote_response(mock_response)
            
        except Exception as e:
            self.handle_error(e, "get_quote")
            raise
    
    async def bind_policy(
        self,
        request: Any  # CarrierBindRequest or Dict
    ) -> CarrierBindResponse:
        """
        Bind policy with Allianz AGCS.
        
        API Endpoint: POST /marine/quotes/{quote_id}/bind
        """
        headers = self.authenticate()
        headers["Content-Type"] = "application/json"
        
        try:
            quote_id = request.quote_id if hasattr(request, 'quote_id') else request.get("quote_id", "")
            logger.info(f"Binding Allianz policy for quote_id: {quote_id}")
            
            # Mock response (replace with actual API call)
            mock_response = await self._mock_bind_response(request)
            
            return CarrierBindResponse(
                policy_number=mock_response.get("policy_number", ""),
                status="bound",
                policy_document_url=mock_response.get("policy_document_url"),
                certificate_of_insurance=mock_response.get("certificate_of_insurance"),
                payment_instructions=mock_response.get("payment_instructions"),
                effective_date=mock_response.get("effective_date", datetime.now().isoformat())
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
        Submit claim to Allianz.
        
        API Endpoint: POST /marine/claims
        """
        headers = self.authenticate()
        headers["Content-Type"] = "application/json"
        
        try:
            logger.info(f"Submitting Allianz claim for policy: {policy_number}")
            
            # Mock response (replace with actual API call)
            return {
                "claim_number": f"ALZ-CLM-{datetime.now().strftime('%Y%m%d')}-{policy_number[:8]}",
                "status": "submitted",
                "adjuster_name": "John Smith",
                "adjuster_contact": "john.smith@allianz.com",
                "estimated_processing_days": 30
            }
            
        except Exception as e:
            self.handle_error(e, "submit_claim")
            raise
    
    def _build_allianz_quote_request(self, request: Any) -> Dict[str, Any]:
        """Build Allianz-specific quote request format."""
        # Handle both dict and CarrierQuoteRequest
        if isinstance(request, dict):
            shipment = request.get("shipment", {})
            coverage = request.get("coverage", {})
            risk_data = request.get("risk_data", {})
        else:
            shipment = request.shipment if hasattr(request, 'shipment') else {}
            coverage = request.coverage if hasattr(request, 'coverage') else {}
            risk_data = request.risk_data if hasattr(request, 'risk_data') else {}
        
        return {
            "request_id": request.request_id if hasattr(request, 'request_id') else request.get("request_id", ""),
            "shipment": {
                "origin": {
                    "port_code": shipment.get("origin", {}).get("port_code", ""),
                    "country": shipment.get("origin", {}).get("country", "")
                },
                "destination": {
                    "port_code": shipment.get("destination", {}).get("port_code", ""),
                    "country": shipment.get("destination", {}).get("country", "")
                },
                "cargo": {
                    "description": shipment.get("cargo", {}).get("description", ""),
                    "hs_code": shipment.get("cargo", {}).get("hs_code"),
                    "declared_value": shipment.get("cargo", {}).get("declared_value", 0),
                    "currency": shipment.get("cargo", {}).get("currency", "USD"),
                    "packaging": shipment.get("cargo", {}).get("packaging", ""),
                    "container_type": shipment.get("cargo", {}).get("container_type")
                },
                "voyage": {
                    "departure_date": shipment.get("voyage", {}).get("departure_date", ""),
                    "estimated_arrival": shipment.get("voyage", {}).get("estimated_arrival", ""),
                    "vessel_name": shipment.get("voyage", {}).get("vessel_name"),
                    "imo_number": shipment.get("voyage", {}).get("imo_number")
                }
            },
            "coverage": {
                "type": coverage.get("type", "ICC_A"),
                "deductible": coverage.get("deductible", 0),
                "extensions": coverage.get("extensions", [])
            },
            "risk_data": {
                "riskcast_score": risk_data.get("riskcast_score", 50),
                "riskcast_assessment_id": risk_data.get("riskcast_assessment_id", ""),
                "risk_factors": risk_data.get("risk_factors", {})
            }
        }
    
    async def _mock_quote_response(self, request: Any) -> Dict[str, Any]:
        """Mock Allianz quote response (replace with actual API call)."""
        # Handle both dict and CarrierQuoteRequest
        if isinstance(request, dict):
            cargo_value = request.get("shipment", {}).get("cargo", {}).get("declared_value", 0)
            risk_score = request.get("risk_data", {}).get("riskcast_score", 50)
            request_id = request.get("request_id", "")
        else:
            cargo_value = request.shipment.get("cargo", {}).get("declared_value", 0) if isinstance(request.shipment, dict) else 0
            risk_score = request.risk_data.get("riskcast_score", 50) if isinstance(request.risk_data, dict) else 50
            request_id = request.request_id if hasattr(request, 'request_id') else ""
        
        # Base rate calculation
        base_rate = 0.008  # 0.8% of cargo value
        base_premium = cargo_value * base_rate
        
        # Risk adjustment based on RISKCAST score
        if risk_score < 30:
            risk_multiplier = 0.6  # 40% discount
        elif risk_score < 50:
            risk_multiplier = 0.8  # 20% discount
        elif risk_score < 70:
            risk_multiplier = 1.0  # Base rate
        elif risk_score < 85:
            risk_multiplier = 1.5  # 50% surcharge
        else:
            risk_multiplier = 2.5  # 150% surcharge
        
        risk_adjustment = base_premium * (risk_multiplier - 1.0)
        total_premium = base_premium * risk_multiplier
        
        return {
            "quote_id": f"ALZ_Q_{datetime.now().strftime('%Y%m%d')}_{request_id[:8] if request_id else 'MOCK'}",
            "status": "quoted",
            "premium": {
                "base_premium": base_premium,
                "risk_adjustment": risk_adjustment,
                "surcharges": [],
                "total_premium": total_premium,
                "currency": "USD"
            },
            "coverage": {
                "sum_insured": cargo_value,
                "deductible": request.coverage["deductible"],
                "policy_type": request.coverage["type"],
                "territorial_scope": "worldwide_excluding_excluded_countries"
            },
            "valid_until": (datetime.now() + timedelta(days=7)).isoformat(),
            "bind_endpoint": f"/marine/quotes/ALZ_Q_{request_id[:8] if request_id else 'MOCK'}/bind"
        }
    
    async def _mock_bind_response(self, request: CarrierBindRequest) -> Dict[str, Any]:
        """Mock Allianz bind response (replace with actual API call)."""
        return {
            "policy_number": f"AGCS-MAR-{datetime.now().strftime('%Y')}-{datetime.now().strftime('%m%d%H%M%S')}",
            "status": "bound",
            "policy_document_url": f"https://docs.agcs.allianz.com/policies/{datetime.now().strftime('%Y%m%d')}",
            "certificate_of_insurance": f"https://docs.agcs.allianz.com/coi/{datetime.now().strftime('%Y%m%d')}",
            "payment_instructions": {
                "bank_name": "JPMorgan Chase Bank",
                "account_number": "1234567890",
                "swift_code": "CHASUS33"
            },
            "effective_date": datetime.now().isoformat()
        }
    
    def normalize_quote_response(self, carrier_response: Dict[str, Any]) -> CarrierQuoteResponse:
        """Normalize Allianz response to standard format."""
        return CarrierQuoteResponse(
            quote_id=carrier_response["quote_id"],
            status="quoted" if carrier_response["status"] == "quoted" else "declined",
            premium={
                "base_premium": carrier_response["premium"]["base_premium"],
                "risk_adjustment": carrier_response["premium"]["risk_adjustment"],
                "surcharges": carrier_response["premium"].get("surcharges", []),
                "total_premium": carrier_response["premium"]["total_premium"],
                "currency": carrier_response["premium"].get("currency", "USD")
            },
            coverage_details={
                "sum_insured": carrier_response["coverage"]["sum_insured"],
                "deductible": carrier_response["coverage"]["deductible"],
                "policy_type": carrier_response["coverage"]["policy_type"],
                "territorial_scope": carrier_response["coverage"]["territorial_scope"]
            },
            valid_until=carrier_response.get("valid_until", ""),
            bind_endpoint=carrier_response.get("bind_endpoint")
        )
