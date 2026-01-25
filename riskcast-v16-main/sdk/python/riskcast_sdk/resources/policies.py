"""
Policies Resource
"""

from typing import Optional, List
from ..models import Policy


class PoliciesResource:
    """Policies API resource."""
    
    def __init__(self, client):
        self.client = client
    
    def get(self, policy_id: str) -> Policy:
        """Get policy details."""
        response = self.client.get(f"/api/v3/policies/{policy_id}")
        return Policy.from_dict(response)
    
    def list(self, status: Optional[str] = None, limit: int = 50) -> List[Policy]:
        """List policies."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = self.client.get("/api/v3/policies", params=params)
        policies_data = response if isinstance(response, list) else response.get("policies", [])
        return [Policy.from_dict(p) for p in policies_data]
