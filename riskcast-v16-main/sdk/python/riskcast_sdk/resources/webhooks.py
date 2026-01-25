"""
Webhooks Resource
"""

from typing import List, Optional, Dict, Any


class WebhooksResource:
    """Webhooks API resource."""
    
    def __init__(self, client):
        self.client = client
    
    def create(
        self,
        url: str,
        events: List[str],
        description: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a webhook subscription."""
        data = {
            "url": url,
            "events": events
        }
        if description:
            data["description"] = description
        if filters:
            data["filters"] = filters
        
        return self.client.post("/api/v3/webhooks", data=data)
    
    def list(self) -> List[Dict[str, Any]]:
        """List webhook subscriptions."""
        return self.client.get("/api/v3/webhooks")
    
    def get(self, webhook_id: str) -> Dict[str, Any]:
        """Get webhook details."""
        return self.client.get(f"/api/v3/webhooks/{webhook_id}")
    
    def delete(self, webhook_id: str):
        """Delete a webhook subscription."""
        return self.client.delete(f"/api/v3/webhooks/{webhook_id}")
