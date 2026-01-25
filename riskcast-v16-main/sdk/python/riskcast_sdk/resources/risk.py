"""
Risk Assessment Resource
"""

from ..models import RiskAssessment


class RiskResource:
    """Risk assessment API resource."""
    
    def __init__(self, client):
        self.client = client
    
    def assess(
        self,
        origin_port: str,
        destination_port: str,
        cargo_type: str,
        cargo_value_usd: float,
        departure_date: str,
        **kwargs
    ) -> RiskAssessment:
        """
        Get a risk assessment.
        
        Args:
            origin_port: Origin port code
            destination_port: Destination port code
            cargo_type: Type of cargo
            cargo_value_usd: Cargo value in USD
            departure_date: Expected departure date (YYYY-MM-DD)
        
        Returns:
            RiskAssessment object
        """
        data = {
            "origin_port": origin_port,
            "destination_port": destination_port,
            "cargo_type": cargo_type,
            "cargo_value_usd": cargo_value_usd,
            "departure_date": departure_date,
            **kwargs
        }
        
        response = self.client.post("/api/v3/risk/assess", data=data)
        return RiskAssessment.from_dict(response)
