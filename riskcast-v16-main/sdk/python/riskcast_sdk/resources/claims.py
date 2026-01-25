"""
Claims Resource
"""

from typing import Optional, List
from ..models import Claim


class ClaimsResource:
    """Claims API resource."""
    
    def __init__(self, client):
        self.client = client
    
    def file(
        self,
        policy_id: str,
        loss_date: str,
        loss_type: str,
        loss_description: str,
        claimed_amount_usd: float
    ) -> Claim:
        """File a new claim."""
        data = {
            "policy_id": policy_id,
            "loss_date": loss_date,
            "loss_type": loss_type,
            "loss_description": loss_description,
            "claimed_amount_usd": claimed_amount_usd
        }
        response = self.client.post("/api/v3/claims", data=data)
        return Claim.from_dict(response)
    
    def get(self, claim_id: str) -> Claim:
        """Get claim details."""
        response = self.client.get(f"/api/v3/claims/{claim_id}")
        return Claim.from_dict(response)
    
    def list(self, status: Optional[str] = None, limit: int = 50) -> List[Claim]:
        """List claims."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = self.client.get("/api/v3/claims", params=params)
        claims_data = response if isinstance(response, list) else response.get("claims", [])
        return [Claim.from_dict(c) for c in claims_data]
