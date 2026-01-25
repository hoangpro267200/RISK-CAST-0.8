"""
Webhook Management API Endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl

from app.database import get_db
from app.api.deps import get_audit
from app.shared.dependencies import get_current_user, resolve_tenant_context, TenantContext
from app.integrations.webhooks.webhook_manager import WebhookManager, WebhookEvent


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


class CreateWebhookRequest(BaseModel):
    url: HttpUrl = Field(..., description="HTTPS URL to receive webhooks")
    events: List[str] = Field(..., description="Events to subscribe to")
    description: Optional[str] = Field(None, description="Description of this webhook")
    filters: Optional[dict] = Field(None, description="Event filters")
    headers: Optional[dict] = Field(None, description="Custom headers to include")


class UpdateWebhookRequest(BaseModel):
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    is_active: Optional[bool] = None
    filters: Optional[dict] = None
    headers: Optional[dict] = None


class WebhookResponse(BaseModel):
    id: str
    url: str
    events: List[str]
    is_active: bool
    created_at: datetime
    description: Optional[str]
    secret: Optional[str] = None  # Only returned on creation


class DeliveryResponse(BaseModel):
    id: str
    event_type: str
    status: str
    attempts: int
    last_attempt_at: Optional[datetime]
    response_status: Optional[int]
    error_message: Optional[str]
    created_at: datetime


@router.post("/", response_model=WebhookResponse)
async def create_webhook(
    request: CreateWebhookRequest,
    db=Depends(get_db),
    audit=Depends(get_audit),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Create a new webhook subscription.
    
    The secret returned should be stored securely - it won't be shown again.
    """
    # Use tenant_id as customer_id for now
    customer_id = tenant_context.tenant_id
    
    manager = WebhookManager(db, audit, tenant_id=tenant_context.tenant_id)
    
    try:
        subscription = await manager.create_subscription(
            customer_id=customer_id,
            url=str(request.url),
            events=request.events,
            description=request.description,
            filters=request.filters,
            headers=request.headers
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    return WebhookResponse(
        id=subscription.id,
        url=subscription.url,
        events=[e.value for e in subscription.events],
        is_active=subscription.is_active,
        created_at=subscription.created_at,
        description=subscription.description,
        secret=subscription.secret  # Only returned on creation
    )


@router.get("/", response_model=List[WebhookResponse])
async def list_webhooks(
    db=Depends(get_db),
    audit=Depends(get_audit),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    List all webhook subscriptions.
    """
    customer_id = tenant_context.tenant_id
    
    manager = WebhookManager(db, audit, tenant_id=tenant_context.tenant_id)
    subscriptions = await manager.list_subscriptions(customer_id)
    
    return [
        WebhookResponse(
            id=s.id,
            url=s.url,
            events=[e.value for e in s.events],
            is_active=s.is_active,
            created_at=s.created_at,
            description=s.description
        )
        for s in subscriptions
    ]


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get webhook details.
    """
    from app.models.webhook import WebhookSubscriptionModel
    
    customer_id = tenant_context.tenant_id
    
    subscription = db.query(WebhookSubscriptionModel).filter(
        WebhookSubscriptionModel.id == webhook_id,
        WebhookSubscriptionModel.customer_id == customer_id,
        WebhookSubscriptionModel.deleted_at.is_(None)
    ).first()
    
    if not subscription:
        raise HTTPException(404, "Webhook not found")
    
    return WebhookResponse(
        id=str(subscription.id),
        url=subscription.url,
        events=subscription.events,
        is_active=subscription.is_active,
        created_at=subscription.created_at,
        description=subscription.description
    )


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    request: UpdateWebhookRequest,
    db=Depends(get_db),
    audit=Depends(get_audit),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Update a webhook subscription.
    """
    customer_id = tenant_context.tenant_id
    
    manager = WebhookManager(db, audit, tenant_id=tenant_context.tenant_id)
    
    updates = {k: v for k, v in request.dict().items() if v is not None}
    if "url" in updates:
        updates["url"] = str(updates["url"])
    
    try:
        subscription = await manager.update_subscription(webhook_id, customer_id, updates)
    except ValueError as e:
        raise HTTPException(400, str(e))
    
    return WebhookResponse(
        id=subscription.id,
        url=subscription.url,
        events=[e.value for e in subscription.events],
        is_active=subscription.is_active,
        created_at=subscription.created_at,
        description=subscription.description
    )


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    db=Depends(get_db),
    audit=Depends(get_audit),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Delete a webhook subscription.
    """
    customer_id = tenant_context.tenant_id
    
    manager = WebhookManager(db, audit, tenant_id=tenant_context.tenant_id)
    
    try:
        await manager.delete_subscription(webhook_id, customer_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    
    return {"status": "deleted"}


@router.get("/{webhook_id}/deliveries", response_model=List[DeliveryResponse])
async def get_webhook_deliveries(
    webhook_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Get delivery history for a webhook.
    """
    from app.models.webhook import WebhookSubscriptionModel, WebhookDeliveryModel
    
    customer_id = tenant_context.tenant_id
    
    # Verify ownership
    subscription = db.query(WebhookSubscriptionModel).filter(
        WebhookSubscriptionModel.id == webhook_id,
        WebhookSubscriptionModel.customer_id == customer_id,
        WebhookSubscriptionModel.deleted_at.is_(None)
    ).first()
    
    if not subscription:
        raise HTTPException(404, "Webhook not found")
    
    query = db.query(WebhookDeliveryModel).filter(
        WebhookDeliveryModel.subscription_id == webhook_id
    )
    
    if status:
        query = query.filter(WebhookDeliveryModel.status == status)
    
    deliveries = query.order_by(
        WebhookDeliveryModel.created_at.desc()
    ).limit(limit).all()
    
    return [
        DeliveryResponse(
            id=str(d.id),
            event_type=d.event_type,
            status=d.status,
            attempts=d.attempts,
            last_attempt_at=d.last_attempt_at,
            response_status=d.response_status,
            error_message=d.error_message,
            created_at=d.created_at
        )
        for d in deliveries
    ]


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    db=Depends(get_db),
    audit=Depends(get_audit),
    current_user=Depends(get_current_user),
    tenant_context: TenantContext = Depends(resolve_tenant_context)
):
    """
    Send a test event to the webhook.
    """
    from app.models.webhook import WebhookSubscriptionModel
    
    customer_id = tenant_context.tenant_id
    
    subscription = db.query(WebhookSubscriptionModel).filter(
        WebhookSubscriptionModel.id == webhook_id,
        WebhookSubscriptionModel.customer_id == customer_id,
        WebhookSubscriptionModel.deleted_at.is_(None)
    ).first()
    
    if not subscription:
        raise HTTPException(404, "Webhook not found")
    
    manager = WebhookManager(db, audit, tenant_id=tenant_context.tenant_id)
    
    # Send test event
    test_payload = {
        "message": "This is a test webhook delivery",
        "timestamp": datetime.utcnow().isoformat(),
        "webhook_id": webhook_id
    }
    
    await manager.publish_event(
        WebhookEvent.QUOTE_CREATED,  # Use any event for test
        customer_id,
        test_payload
    )
    
    return {
        "status": "sent",
        "message": "Test webhook queued for delivery"
    }


@router.get("/events")
async def list_available_events():
    """
    List all available webhook events.
    """
    events = []
    for event in WebhookEvent:
        category = event.value.split(".")[0]
        events.append({
            "event": event.value,
            "category": category,
            "description": _get_event_description(event)
        })
    
    return {"events": events}


def _get_event_description(event: WebhookEvent) -> str:
    """Get description for webhook event."""
    descriptions = {
        WebhookEvent.QUOTE_CREATED: "Fired when a new quote is created",
        WebhookEvent.QUOTE_ACCEPTED: "Fired when a quote is accepted by customer",
        WebhookEvent.QUOTE_DECLINED: "Fired when a quote is declined by customer",
        WebhookEvent.QUOTE_EXPIRED: "Fired when a quote expires",
        WebhookEvent.POLICY_BOUND: "Fired when a policy is bound from a quote",
        WebhookEvent.POLICY_ACTIVATED: "Fired when a policy becomes active",
        WebhookEvent.POLICY_RENEWED: "Fired when a policy is renewed",
        WebhookEvent.POLICY_CANCELLED: "Fired when a policy is cancelled",
        WebhookEvent.POLICY_EXPIRED: "Fired when a policy expires",
        WebhookEvent.CLAIM_FILED: "Fired when a new claim is filed",
        WebhookEvent.CLAIM_UPDATED: "Fired when claim status changes",
        WebhookEvent.CLAIM_APPROVED: "Fired when a claim is approved",
        WebhookEvent.CLAIM_DENIED: "Fired when a claim is denied",
        WebhookEvent.CLAIM_PAID: "Fired when claim payment is issued",
        WebhookEvent.PAYMENT_RECEIVED: "Fired when premium payment is received",
        WebhookEvent.PAYMENT_FAILED: "Fired when payment fails",
        WebhookEvent.PAYMENT_REFUNDED: "Fired when payment is refunded",
        WebhookEvent.RISK_ASSESSMENT_COMPLETED: "Fired when risk assessment completes",
        WebhookEvent.RISK_ALERT: "Fired when risk alert is triggered"
    }
    return descriptions.get(event, "")
