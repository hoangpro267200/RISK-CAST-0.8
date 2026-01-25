"""
Webhook Management System

Handles:
1. Webhook registration
2. Event publishing
3. Delivery with retries
4. Signature verification
5. Delivery tracking
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
from uuid import uuid4
import hashlib
import hmac
import json
import asyncio
import logging

from sqlalchemy.orm import Session
import httpx


class WebhookEvent(Enum):
    """Supported webhook events."""
    # Quotes
    QUOTE_CREATED = "quote.created"
    QUOTE_ACCEPTED = "quote.accepted"
    QUOTE_DECLINED = "quote.declined"
    QUOTE_EXPIRED = "quote.expired"
    
    # Policies
    POLICY_BOUND = "policy.bound"
    POLICY_ACTIVATED = "policy.activated"
    POLICY_RENEWED = "policy.renewed"
    POLICY_CANCELLED = "policy.cancelled"
    POLICY_EXPIRED = "policy.expired"
    
    # Claims
    CLAIM_FILED = "claim.filed"
    CLAIM_UPDATED = "claim.updated"
    CLAIM_APPROVED = "claim.approved"
    CLAIM_DENIED = "claim.denied"
    CLAIM_PAID = "claim.paid"
    
    # Payments
    PAYMENT_RECEIVED = "payment.received"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # Risk
    RISK_ASSESSMENT_COMPLETED = "risk.assessment_completed"
    RISK_ALERT = "risk.alert"


class DeliveryStatus(Enum):
    """Webhook delivery status."""
    PENDING = "PENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"


@dataclass
class WebhookSubscription:
    """Webhook subscription details."""
    id: str
    customer_id: str
    url: str
    events: List[WebhookEvent]
    secret: str
    is_active: bool
    created_at: datetime
    
    # Optional filters
    filters: Optional[Dict[str, Any]] = None
    
    # Metadata
    description: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class WebhookDelivery:
    """Record of a webhook delivery attempt."""
    id: str
    subscription_id: str
    event_type: str
    payload: Dict[str, Any]
    
    # Delivery info
    status: DeliveryStatus
    attempts: int
    last_attempt_at: Optional[datetime]
    next_retry_at: Optional[datetime]
    
    # Response
    response_status: Optional[int]
    response_body: Optional[str]
    response_time_ms: Optional[int]
    
    # Error
    error_message: Optional[str]
    
    created_at: datetime


class WebhookManager:
    """
    Manages webhook subscriptions and deliveries.
    
    Features:
    - Subscribe/unsubscribe to events
    - Event filtering
    - Signature verification (HMAC-SHA256)
    - Automatic retries with exponential backoff
    - Delivery tracking and logging
    """
    
    # Retry configuration
    MAX_RETRIES = 5
    RETRY_DELAYS = [60, 300, 900, 3600, 14400]  # 1m, 5m, 15m, 1h, 4h
    
    # Delivery timeout
    DELIVERY_TIMEOUT_SECONDS = 30
    
    def __init__(
        self,
        db: Session,
        audit,
        tenant_id: Optional[str] = None
    ):
        self.db = db
        self.audit = audit
        self.tenant_id = tenant_id
        self.logger = logging.getLogger(__name__)
    
    async def create_subscription(
        self,
        customer_id: str,
        url: str,
        events: List[str],
        description: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> WebhookSubscription:
        """
        Create a new webhook subscription.
        """
        from app.models.webhook import WebhookSubscriptionModel
        import secrets
        
        # Validate events
        valid_events = []
        for event in events:
            try:
                valid_events.append(WebhookEvent(event))
            except ValueError:
                raise ValueError(f"Invalid event type: {event}")
        
        # Validate URL
        if not url.startswith("https://"):
            raise ValueError("Webhook URL must use HTTPS")
        
        # Generate secret
        secret = secrets.token_hex(32)
        
        # Create subscription
        subscription = WebhookSubscriptionModel(
            tenant_id=self.tenant_id or customer_id,  # Use tenant_id if available
            customer_id=customer_id,
            url=url,
            events=[e.value for e in valid_events],
            secret=secret,
            is_active=True,
            description=description,
            filters_json=filters,
            headers_json=headers
        )
        
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        
        # Audit (synchronous)
        if self.audit:
            self.audit.append_event(
                event_type="WEBHOOK",
                action="SUBSCRIPTION_CREATED",
                entity_type="webhook_subscription",
                entity_id=str(subscription.id),
                actor_type="CUSTOMER",
                actor_id=customer_id,
                tenant_id=self.tenant_id,
                payload={
                    "url": url,
                    "events": [e.value for e in valid_events]
                }
            )
        
        self.logger.info(f"Created webhook subscription {subscription.id} for customer {customer_id}")
        
        return WebhookSubscription(
            id=str(subscription.id),
            customer_id=customer_id,
            url=url,
            events=valid_events,
            secret=secret,
            is_active=True,
            created_at=subscription.created_at,
            filters=filters,
            description=description,
            headers=headers
        )
    
    async def update_subscription(
        self,
        subscription_id: str,
        customer_id: str,
        updates: Dict[str, Any]
    ) -> WebhookSubscription:
        """
        Update a webhook subscription.
        """
        from app.models.webhook import WebhookSubscriptionModel
        
        subscription = self.db.query(WebhookSubscriptionModel).filter(
            WebhookSubscriptionModel.id == subscription_id,
            WebhookSubscriptionModel.customer_id == customer_id,
            WebhookSubscriptionModel.deleted_at.is_(None)  # Not soft-deleted
        ).first()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Update allowed fields
        if "url" in updates:
            if not updates["url"].startswith("https://"):
                raise ValueError("Webhook URL must use HTTPS")
            subscription.url = updates["url"]
        
        if "events" in updates:
            valid_events = []
            for event in updates["events"]:
                try:
                    valid_events.append(WebhookEvent(event).value)
                except ValueError:
                    raise ValueError(f"Invalid event type: {event}")
            subscription.events = valid_events
        
        if "is_active" in updates:
            subscription.is_active = updates["is_active"]
        
        if "filters" in updates:
            subscription.filters_json = updates["filters"]
        
        if "headers" in updates:
            subscription.headers_json = updates["headers"]
        
        subscription.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(subscription)
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="WEBHOOK",
                action="SUBSCRIPTION_UPDATED",
                entity_type="webhook_subscription",
                entity_id=subscription_id,
                actor_type="CUSTOMER",
                actor_id=customer_id,
                tenant_id=self.tenant_id,
                payload={"updates": list(updates.keys())}
            )
        
        return self._to_subscription(subscription)
    
    async def delete_subscription(
        self,
        subscription_id: str,
        customer_id: str
    ):
        """
        Delete a webhook subscription (soft delete).
        """
        from app.models.webhook import WebhookSubscriptionModel
        
        subscription = self.db.query(WebhookSubscriptionModel).filter(
            WebhookSubscriptionModel.id == subscription_id,
            WebhookSubscriptionModel.customer_id == customer_id
        ).first()
        
        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Soft delete
        subscription.is_active = False
        subscription.deleted_at = datetime.utcnow()
        self.db.commit()
        
        # Audit
        if self.audit:
            self.audit.append_event(
                event_type="WEBHOOK",
                action="SUBSCRIPTION_DELETED",
                entity_type="webhook_subscription",
                entity_id=subscription_id,
                actor_type="CUSTOMER",
                actor_id=customer_id,
                tenant_id=self.tenant_id
            )
    
    async def list_subscriptions(
        self,
        customer_id: str
    ) -> List[WebhookSubscription]:
        """
        List all active subscriptions for a customer.
        """
        from app.models.webhook import WebhookSubscriptionModel
        
        subscriptions = self.db.query(WebhookSubscriptionModel).filter(
            WebhookSubscriptionModel.customer_id == customer_id,
            WebhookSubscriptionModel.is_active == True,
            WebhookSubscriptionModel.deleted_at.is_(None)
        ).all()
        
        return [self._to_subscription(s) for s in subscriptions]
    
    async def publish_event(
        self,
        event_type: WebhookEvent,
        customer_id: str,
        payload: Dict[str, Any],
        entity_id: Optional[str] = None
    ):
        """
        Publish an event to all matching subscriptions.
        """
        from app.models.webhook import WebhookSubscriptionModel, WebhookDeliveryModel
        
        # Find matching subscriptions
        subscriptions = self.db.query(WebhookSubscriptionModel).filter(
            WebhookSubscriptionModel.customer_id == customer_id,
            WebhookSubscriptionModel.is_active == True,
            WebhookSubscriptionModel.deleted_at.is_(None)
        ).all()
        
        matching = [s for s in subscriptions if event_type.value in s.events]
        
        if not matching:
            self.logger.debug(f"No subscriptions for event {event_type.value}")
            return
        
        self.logger.info(f"Publishing {event_type.value} to {len(matching)} subscriptions")
        
        # Create delivery records and queue for delivery
        for subscription in matching:
            # Check filters
            if subscription.filters_json and not self._matches_filters(payload, subscription.filters_json):
                continue
            
            # Build webhook payload
            webhook_payload = {
                "id": str(uuid4()),
                "type": event_type.value,
                "created_at": datetime.utcnow().isoformat(),
                "data": payload
            }
            
            if entity_id:
                webhook_payload["entity_id"] = entity_id
            
            # Create delivery record
            delivery = WebhookDeliveryModel(
                tenant_id=subscription.tenant_id,
                subscription_id=subscription.id,
                event_type=event_type.value,
                payload_json=webhook_payload,
                status=DeliveryStatus.PENDING.value,
                attempts=0
            )
            
            self.db.add(delivery)
            self.db.commit()
            self.db.refresh(delivery)
            
            # Queue for async delivery
            asyncio.create_task(
                self._deliver_webhook(str(delivery.id), subscription, webhook_payload)
            )
    
    async def _deliver_webhook(
        self,
        delivery_id: str,
        subscription,
        payload: Dict[str, Any]
    ):
        """
        Deliver webhook with retry logic.
        """
        from app.models.webhook import WebhookDeliveryModel
        
        delivery = self.db.query(WebhookDeliveryModel).filter(
            WebhookDeliveryModel.id == delivery_id
        ).first()
        
        if not delivery:
            return
        
        # Generate signature
        signature = self._generate_signature(payload, subscription.secret)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": payload["type"],
            "X-Webhook-Delivery": str(delivery_id),
            "User-Agent": "RISKCAST-Webhooks/1.0"
        }
        
        # Add custom headers
        if subscription.headers_json:
            headers.update(subscription.headers_json)
        
        # Attempt delivery
        delivery.attempts += 1
        delivery.last_attempt_at = datetime.utcnow()
        delivery.status = DeliveryStatus.RETRYING.value
        
        try:
            start_time = datetime.utcnow()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    subscription.url,
                    json=payload,
                    headers=headers,
                    timeout=self.DELIVERY_TIMEOUT_SECONDS
                )
            
            elapsed_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000] if response.text else None  # Limit stored response
            delivery.response_time_ms = elapsed_ms
            
            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.DELIVERED.value
                self.logger.info(f"Webhook delivered: {delivery_id}")
            else:
                delivery.error_message = f"HTTP {response.status_code}"
                await self._schedule_retry(delivery)
                
        except httpx.TimeoutException:
            delivery.error_message = "Request timeout"
            await self._schedule_retry(delivery)
            
        except httpx.RequestError as e:
            delivery.error_message = str(e)
            await self._schedule_retry(delivery)
            
        except Exception as e:
            delivery.error_message = str(e)
            delivery.status = DeliveryStatus.FAILED.value
            self.logger.error(f"Webhook delivery failed: {e}")
        
        self.db.commit()
    
    async def _schedule_retry(self, delivery):
        """
        Schedule retry for failed delivery.
        """
        if delivery.attempts >= self.MAX_RETRIES:
            delivery.status = DeliveryStatus.FAILED.value
            self.logger.warning(f"Webhook delivery exhausted retries: {delivery.id}")
            return
        
        # Calculate next retry time
        delay_index = min(delivery.attempts - 1, len(self.RETRY_DELAYS) - 1)
        delay_seconds = self.RETRY_DELAYS[delay_index]
        delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        delivery.status = DeliveryStatus.RETRYING.value
        
        self.logger.info(f"Scheduling retry for {delivery.id} in {delay_seconds}s")
        
        # Schedule retry (in production, would use job queue)
        asyncio.create_task(
            self._retry_after_delay(str(delivery.id), delay_seconds)
        )
    
    async def _retry_after_delay(self, delivery_id: str, delay_seconds: int):
        """
        Wait and retry delivery.
        """
        await asyncio.sleep(delay_seconds)
        
        from app.models.webhook import WebhookDeliveryModel, WebhookSubscriptionModel
        
        delivery = self.db.query(WebhookDeliveryModel).filter(
            WebhookDeliveryModel.id == delivery_id
        ).first()
        
        if not delivery or delivery.status == DeliveryStatus.DELIVERED.value:
            return
        
        subscription = self.db.query(WebhookSubscriptionModel).filter(
            WebhookSubscriptionModel.id == delivery.subscription_id
        ).first()
        
        if subscription and subscription.is_active and subscription.deleted_at is None:
            await self._deliver_webhook(delivery_id, subscription, delivery.payload_json)
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for payload.
        """
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
        signature = hmac.new(
            secret.encode(),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def verify_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook signature.
        
        For customers to verify incoming webhooks.
        """
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        expected_sig = f"sha256={expected}"
        return hmac.compare_digest(signature, expected_sig)
    
    def _matches_filters(self, payload: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if payload matches subscription filters.
        """
        for key, value in filters.items():
            if key not in payload:
                return False
            if isinstance(value, list):
                if payload[key] not in value:
                    return False
            elif payload[key] != value:
                return False
        return True
    
    def _to_subscription(self, model) -> WebhookSubscription:
        """Convert model to dataclass."""
        return WebhookSubscription(
            id=str(model.id),
            customer_id=model.customer_id,
            url=model.url,
            events=[WebhookEvent(e) for e in model.events],
            secret=model.secret,
            is_active=model.is_active,
            created_at=model.created_at,
            filters=model.filters_json,
            description=model.description,
            headers=model.headers_json
        )


# ============================================================================
# Event Publishers
# ============================================================================

class WebhookPublisher:
    """
    Convenience class for publishing webhook events.
    
    Use this in services to publish events.
    """
    
    def __init__(self, webhook_manager: WebhookManager):
        self.manager = webhook_manager
    
    async def quote_created(self, customer_id: str, quote_data: Dict[str, Any]):
        await self.manager.publish_event(
            WebhookEvent.QUOTE_CREATED,
            customer_id,
            quote_data,
            entity_id=quote_data.get("quote_id")
        )
    
    async def quote_accepted(self, customer_id: str, quote_data: Dict[str, Any]):
        await self.manager.publish_event(
            WebhookEvent.QUOTE_ACCEPTED,
            customer_id,
            quote_data,
            entity_id=quote_data.get("quote_id")
        )
    
    async def policy_bound(self, customer_id: str, policy_data: Dict[str, Any]):
        await self.manager.publish_event(
            WebhookEvent.POLICY_BOUND,
            customer_id,
            policy_data,
            entity_id=policy_data.get("policy_id")
        )
    
    async def claim_filed(self, customer_id: str, claim_data: Dict[str, Any]):
        await self.manager.publish_event(
            WebhookEvent.CLAIM_FILED,
            customer_id,
            claim_data,
            entity_id=claim_data.get("claim_id")
        )
    
    async def claim_paid(self, customer_id: str, claim_data: Dict[str, Any]):
        await self.manager.publish_event(
            WebhookEvent.CLAIM_PAID,
            customer_id,
            claim_data,
            entity_id=claim_data.get("claim_id")
        )
    
    async def payment_received(self, customer_id: str, payment_data: Dict[str, Any]):
        await self.manager.publish_event(
            WebhookEvent.PAYMENT_RECEIVED,
            customer_id,
            payment_data,
            entity_id=payment_data.get("payment_id")
        )
