"""
RISKCAST API Client
"""

from typing import Optional, Dict, Any
import httpx

from .resources.quotes import QuotesResource
from .resources.policies import PoliciesResource
from .resources.claims import ClaimsResource
from .resources.risk import RiskResource
from .resources.webhooks import WebhooksResource
from .exceptions import RiskcastError, AuthenticationError, RateLimitError, ValidationError, NotFoundError


class RiskcastClient:
    """
    RISKCAST API Client.
    
    Usage:
        client = RiskcastClient(api_key="your_api_key")
        
        # Get a quote
        quote = client.quotes.request(
            origin_port="CNSHA",
            destination_port="USLAX",
            cargo_type="ELECTRONICS",
            cargo_value_usd=100000
        )
        
        # Accept and bind
        client.quotes.accept(quote.id)
        policy = client.quotes.bind(quote.id)
    """
    
    DEFAULT_BASE_URL = "https://api.riskcast.io"
    SANDBOX_BASE_URL = "https://sandbox.api.riskcast.io"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        sandbox: bool = False,
        timeout: float = 30.0
    ):
        """
        Initialize the client.
        
        Args:
            api_key: Your RISKCAST API key
            base_url: Override the base URL (optional)
            sandbox: Use sandbox environment
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif sandbox:
            self.base_url = self.SANDBOX_BASE_URL
        else:
            self.base_url = self.DEFAULT_BASE_URL
        
        self.timeout = timeout
        
        # HTTP client
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={
                "X-API-Key": api_key,
                "User-Agent": f"riskcast-python/1.0.0",
                "Content-Type": "application/json"
            }
        )
        
        # Initialize resources
        self.quotes = QuotesResource(self)
        self.policies = PoliciesResource(self)
        self.claims = ClaimsResource(self)
        self.risk = RiskResource(self)
        self.webhooks = WebhooksResource(self)
    
    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request.
        """
        try:
            response = self._client.request(
                method=method,
                url=path,
                params=params,
                json=data
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    f"Rate limit exceeded. Retry after {retry_after} seconds",
                    retry_after=retry_after
                )
            
            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            
            if response.status_code == 403:
                raise AuthenticationError("Access denied")
            
            # Handle not found
            if response.status_code == 404:
                raise NotFoundError("Resource not found")
            
            # Handle validation errors
            if response.status_code == 422:
                error_data = response.json().get("error", {})
                raise ValidationError(
                    message=error_data.get("message", "Validation error"),
                    code=error_data.get("code"),
                    details=error_data.get("details", {})
                )
            
            # Handle other errors
            if response.status_code >= 400:
                error_data = response.json().get("error", {})
                raise RiskcastError(
                    message=error_data.get("message", "Unknown error"),
                    code=error_data.get("code"),
                    status_code=response.status_code
                )
            
            return response.json()
            
        except httpx.RequestError as e:
            raise RiskcastError(f"Request failed: {str(e)}")
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request."""
        return self.request("GET", path, params=params)
    
    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a POST request."""
        return self.request("POST", path, data=data)
    
    def put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a PUT request."""
        return self.request("PUT", path, data=data)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """Make a DELETE request."""
        return self.request("DELETE", path)
    
    def close(self):
        """Close the client."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        self.close()
