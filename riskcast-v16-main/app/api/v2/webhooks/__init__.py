"""
RISKCAST Webhook Handlers
==========================
Webhook endpoints for external integrations.
"""

from app.api.v2.webhooks.insurance_webhooks import router as insurance_webhooks_router

__all__ = ['insurance_webhooks_router']
