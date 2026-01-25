"""
Quotes Resource
"""

from typing import Optional, List
from datetime import date

from ..models import Quote, Policy


class QuotesResource:
    """
    Quotes API resource.
    
    Usage:
        # Request a quote
        quote = client.quotes.request(
            origin_port="CNSHA",
            destination_port="USLAX",
            cargo_type="ELECTRONICS",
            cargo_value_usd=100000,
            departure_date="2024-03-15"
        )
        
        # Get quote details
        quote = client.quotes.get("quote_id")
        
        # List quotes
        quotes = client.quotes.list(status="PENDING")
        
        # Accept a quote
        client.quotes.accept("quote_id")
        
        # Bind to policy
        policy = client.quotes.bind("quote_id")
    """
    
    def __init__(self, client):
        self.client = client
    
    def request(
        self,
        origin_port: str,
        destination_port: str,
        cargo_type: str,
        cargo_value_usd: float,
        departure_date: str,
        arrival_date: Optional[str] = None,
        container_count: int = 1,
        coverage_type: str = "ALL_RISKS",
        deductible_type: str = "PERCENTAGE",
        deductible_value: float = 0.01,
        **kwargs
    ) -> Quote:
        """
        Request a new insurance quote.
        
        Args:
            origin_port: Origin port code (e.g., "CNSHA")
            destination_port: Destination port code (e.g., "USLAX")
            cargo_type: Type of cargo (e.g., "ELECTRONICS")
            cargo_value_usd: Cargo value in USD
            departure_date: Expected departure date (YYYY-MM-DD)
            arrival_date: Expected arrival date (optional)
            container_count: Number of containers
            coverage_type: Coverage type (ALL_RISKS, NAMED_PERILS, TOTAL_LOSS_ONLY)
            deductible_type: Deductible type (PERCENTAGE, FIXED, FRANCHISE)
            deductible_value: Deductible value
        
        Returns:
            Quote object with pricing details
        """
        data = {
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_type": cargo_type,
            "cargo_value_usd": cargo_value_usd,
            "departure_date": departure_date,
            "container_count": container_count,
            "coverage_type": coverage_type,
            "deductible_type": deductible_type,
            "deductible_value": deductible_value,
            **kwargs
        }
        
        if arrival_date:
            data["arrival_date"] = arrival_date
        
        response = self.client.post("/api/v3/quotes/request", data=data)
        return Quote.from_dict(response)
    
    def get(self, quote_id: str) -> Quote:
        """
        Get quote details.
        
        Args:
            quote_id: Quote ID
        
        Returns:
            Quote object
        """
        response = self.client.get(f"/api/v3/quotes/{quote_id}")
        return Quote.from_dict(response)
    
    def list(
        self,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Quote]:
        """
        List quotes.
        
        Args:
            status: Filter by status (PENDING, ACCEPTED, DECLINED, EXPIRED)
            limit: Maximum number of quotes to return
        
        Returns:
            List of Quote objects
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = self.client.get("/api/v3/quotes", params=params)
        quotes_data = response if isinstance(response, list) else response.get("quotes", [])
        return [Quote.from_dict(q) for q in quotes_data]
    
    def accept(self, quote_id: str, notes: Optional[str] = None) -> Quote:
        """
        Accept a quote.
        
        Args:
            quote_id: Quote ID
            notes: Optional acceptance notes
        
        Returns:
            Updated Quote object
        """
        data = {}
        if notes:
            data["acceptance_notes"] = notes
        
        response = self.client.post(f"/api/v3/quotes/{quote_id}/accept", data=data)
        return Quote.from_dict(response)
    
    def decline(
        self,
        quote_id: str,
        reason: str,
        details: Optional[str] = None
    ) -> Quote:
        """
        Decline a quote.
        
        Args:
            quote_id: Quote ID
            reason: Decline reason code
            details: Optional details
        
        Returns:
            Updated Quote object
        """
        data = {"reason": reason}
        if details:
            data["reason_details"] = details
        
        response = self.client.post(f"/api/v3/quotes/{quote_id}/decline", data=data)
        return Quote.from_dict(response)
    
    def bind(self, quote_id: str) -> Policy:
        """
        Bind an accepted quote to create a policy.
        
        Args:
            quote_id: Quote ID
        
        Returns:
            Policy object
        """
        response = self.client.post(f"/api/v3/quotes/{quote_id}/bind")
        return Policy.from_dict(response)
    
    def compare_options(self, quote_id: str) -> dict:
        """
        Get comparison of coverage options.
        
        Args:
            quote_id: Quote ID
        
        Returns:
            Dictionary with coverage alternatives
        """
        return self.client.get(f"/api/v3/quotes/{quote_id}/comparison")
