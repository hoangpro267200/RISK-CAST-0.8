"""
Webhook Database Models

Models for webhook subscriptions and delivery tracking.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, ForeignKey, Text

from app.database import Base
from app.shared.models import BaseMixin, TenantScopedMixin, SoftDeleteMixin


class WebhookSubscriptionModel(Base, BaseMixin, TenantScopedMixin, SoftDeleteMixin):
    """
    Webhook subscription model.
    
    Stores customer webhook subscriptions with events, filters, and secrets.
    """
    __tablename__ = "webhook_subscriptions"
    __tenant_scoped__ = True
    
    # Customer reference (can be tenant_id or separate customer_id)
    customer_id = Column(String(50), nullable=False, index=True)
    
    # Webhook configuration
    url = Column(String(500), nullable=False)
    events = Column(JSON, nullable=False)  # List of event type strings
    secret = Column(String(100), nullable=False)  # HMAC secret
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Optional configuration
    description = Column(Text, nullable=True)
    filters_json = Column(JSON, nullable=True)  # Event filters
    headers_json = Column(JSON, nullable=True)  # Custom headers
    
    def __repr__(self):
        return f"<WebhookSubscription(id={self.id}, customer_id={self.customer_id}, url={self.url[:50]}...)>"


class WebhookDeliveryModel(Base, BaseMixin, TenantScopedMixin):
    """
    Webhook delivery attempt model.
    
    Tracks each webhook delivery attempt with retry logic.
    """
    __tablename__ = "webhook_deliveries"
    __tenant_scoped__ = True
    
    # Subscription reference
    subscription_id = Column(
        String(26),
        ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    payload_json = Column(JSON, nullable=False)
    
    # Delivery status
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    attempts = Column(Integer, default=0, nullable=False)
    
    # Timing
    last_attempt_at = Column(DateTime, nullable=True)
    next_retry_at = Column(DateTime, nullable=True, index=True)
    
    # Response details
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)  # Limited to first 1000 chars
    response_time_ms = Column(Integer, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, subscription_id={self.subscription_id}, status={self.status})>"
