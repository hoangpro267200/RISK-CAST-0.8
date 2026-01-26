"""
Billing API Endpoints

Provides:
1. Plan listing
2. Subscription management
3. Usage tracking
4. Invoice history
5. Checkout and billing portal
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
import logging

from app.dependencies.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])


# ============================================================================
# Response Models
# ============================================================================

class PlanResponse(BaseModel):
    """Plan details response."""
    tier: str
    name: str
    monthly_price_usd: float
    annual_price_usd: float
    quotes_per_month: int
    policies_per_month: int
    api_calls_per_day: int
    users: int
    features: List[str]


class SubscriptionResponse(BaseModel):
    """Subscription response."""
    id: str
    plan_tier: str
    billing_cycle: str
    status: str
    price_usd: float
    current_period_end: Optional[str] = None


class UsageResponse(BaseModel):
    """Usage response."""
    resource: str
    used: int
    limit: str
    remaining: str
    has_quota: bool


class InvoiceResponse(BaseModel):
    """Invoice response."""
    id: str
    invoice_number: str
    status: str
    total_usd: float
    invoice_date: str
    paid_at: Optional[str] = None


# ============================================================================
# Service singleton
# ============================================================================

_billing_service = None


def get_billing_service():
    """Get or create billing service."""
    global _billing_service
    if _billing_service is None:
        from app.services.billing import BillingService
        _billing_service = BillingService()
    return _billing_service


def get_tenant_id(request: Request, current_user = Depends(get_current_user)) -> str:
    """Get tenant ID from request or user."""
    # Try request state first
    tenant_id = getattr(request.state, 'tenant_id', None)
    if tenant_id:
        return tenant_id
    
    # Try user
    if current_user and hasattr(current_user, 'tenant_id'):
        return current_user.tenant_id
    
    # Fallback to user ID
    if current_user and hasattr(current_user, 'id'):
        return str(current_user.id)
    
    raise HTTPException(status_code=400, detail="Tenant ID not found")


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/plans", response_model=List[PlanResponse])
async def get_available_plans():
    """
    Get all available subscription plans.
    
    Returns plan details including pricing, quotas, and features.
    """
    from app.services.billing.billing_service import PLANS
    
    return [
        PlanResponse(
            tier=plan.tier.value,
            name=plan.name,
            monthly_price_usd=float(plan.monthly_price_usd),
            annual_price_usd=float(plan.annual_price_usd),
            quotes_per_month=plan.quotes_per_month,
            policies_per_month=plan.policies_per_month,
            api_calls_per_day=plan.api_calls_per_day,
            users=plan.users,
            features=plan.features
        )
        for plan in PLANS.values()
    ]


@router.get("/subscription", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    request: Request,
    current_user = Depends(get_current_user)
):
    """
    Get current subscription for the authenticated tenant.
    """
    try:
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        subscription = await service.get_subscription(tenant_id)
        
        if not subscription:
            return None
        
        return SubscriptionResponse(
            id=subscription.id,
            plan_tier=subscription.plan_tier.value,
            billing_cycle=subscription.billing_cycle.value,
            status=subscription.status.value,
            price_usd=subscription.price_usd,
            current_period_end=subscription.current_period_end.isoformat() if subscription.current_period_end else None
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription")


@router.post("/subscribe")
async def create_subscription(
    plan_tier: str = Query(..., description="Plan tier (FREE, STARTER, PROFESSIONAL, ENTERPRISE)"),
    billing_cycle: str = Query("MONTHLY", description="Billing cycle (MONTHLY, ANNUAL)"),
    payment_method_id: Optional[str] = Query(None, description="Stripe payment method ID"),
    request: Request = None,
    current_user = Depends(get_current_user)
):
    """
    Subscribe to a plan.
    
    Creates a new subscription with optional trial period.
    """
    try:
        from app.services.billing.billing_service import PlanTier, BillingCycle
        
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        subscription = await service.create_subscription(
            tenant_id=tenant_id,
            plan_tier=PlanTier(plan_tier),
            billing_cycle=BillingCycle(billing_cycle),
            payment_method_id=payment_method_id
        )
        
        return {
            "subscription_id": subscription.id,
            "status": subscription.status.value,
            "plan_tier": subscription.plan_tier.value,
            "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.post("/upgrade")
async def upgrade_subscription(
    new_plan_tier: str = Query(..., description="New plan tier to upgrade to"),
    request: Request = None,
    current_user = Depends(get_current_user)
):
    """
    Upgrade to a higher plan.
    
    Prorates the remaining period and charges the difference.
    """
    try:
        from app.services.billing.billing_service import PlanTier
        
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        subscription = await service.upgrade_subscription(
            tenant_id=tenant_id,
            new_plan_tier=PlanTier(new_plan_tier)
        )
        
        return {
            "subscription_id": subscription.id,
            "new_plan": subscription.plan_tier.value,
            "new_price_usd": subscription.price_usd
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error upgrading subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to upgrade subscription")


@router.post("/cancel")
async def cancel_subscription(
    cancel_immediately: bool = Query(False, description="Cancel immediately or at period end"),
    request: Request = None,
    current_user = Depends(get_current_user)
):
    """
    Cancel subscription.
    
    By default, cancels at the end of the current billing period.
    """
    try:
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        subscription = await service.cancel_subscription(
            tenant_id=tenant_id,
            cancel_immediately=cancel_immediately
        )
        
        return {
            "status": "cancelled",
            "effective_date": "immediate" if cancel_immediately else (
                subscription.current_period_end.isoformat() if subscription.current_period_end else "end_of_period"
            )
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")


@router.get("/usage", response_model=List[UsageResponse])
async def get_usage(
    request: Request,
    current_user = Depends(get_current_user)
):
    """
    Get current usage for all resources.
    
    Returns usage vs quota for quotes, policies, and API calls.
    """
    try:
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        resources = ["quotes", "policies", "api_calls"]
        usage_list = []
        
        for resource in resources:
            quota = await service.check_quota(tenant_id, resource)
            usage_list.append(UsageResponse(
                resource=quota["resource"],
                used=quota["used"],
                limit=str(quota["limit"]),
                remaining=str(quota["remaining"]),
                has_quota=quota["has_quota"]
            ))
        
        return usage_list
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage: {e}")
        raise HTTPException(status_code=500, detail="Failed to get usage")


@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(
    limit: int = Query(10, ge=1, le=50, description="Number of invoices to return"),
    request: Request = None,
    current_user = Depends(get_current_user)
):
    """
    Get invoice history.
    """
    try:
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        invoices = await service.get_invoices(tenant_id, limit)
        
        return [
            InvoiceResponse(
                id=inv.id,
                invoice_number=inv.invoice_number,
                status=inv.status,
                total_usd=inv.total_usd,
                invoice_date=inv.invoice_date.isoformat(),
                paid_at=inv.paid_at.isoformat() if inv.paid_at else None
            )
            for inv in invoices
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting invoices: {e}")
        raise HTTPException(status_code=500, detail="Failed to get invoices")


@router.post("/checkout-session")
async def create_checkout_session(
    plan_tier: str = Query(..., description="Plan tier"),
    billing_cycle: str = Query("MONTHLY", description="Billing cycle"),
    success_url: str = Query("https://app.riskcast.ai/billing/success", description="Success redirect URL"),
    cancel_url: str = Query("https://app.riskcast.ai/billing/cancel", description="Cancel redirect URL"),
    request: Request = None,
    current_user = Depends(get_current_user)
):
    """
    Create Stripe Checkout session.
    
    Returns a URL to redirect the user to Stripe's hosted checkout page.
    """
    try:
        from app.services.billing.billing_service import PLANS, PlanTier
        
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        plan = PLANS[PlanTier(plan_tier)]
        
        price_id = (
            plan.stripe_monthly_price_id 
            if billing_cycle == "MONTHLY" 
            else plan.stripe_annual_price_id
        )
        
        checkout_url = await service.stripe.create_checkout_session(
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"tenant_id": tenant_id}
        )
        
        return {"checkout_url": checkout_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/portal-session")
async def create_portal_session(
    return_url: str = Query("https://app.riskcast.ai/billing", description="Return URL after portal"),
    request: Request = None,
    current_user = Depends(get_current_user)
):
    """
    Create Stripe billing portal session.
    
    Returns a URL to redirect the user to manage their subscription.
    """
    try:
        tenant_id = get_tenant_id(request, current_user)
        service = get_billing_service()
        
        subscription = await service.get_subscription(tenant_id)
        
        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(status_code=400, detail="No billing account found")
        
        portal_url = await service.stripe.create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url
        )
        
        return {"portal_url": portal_url}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/webhook")
async def handle_stripe_webhook(request: Request):
    """
    Handle Stripe webhooks.
    
    Processes subscription updates, payments, and other events.
    """
    try:
        service = get_billing_service()
        payload = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        
        event = service.stripe.verify_webhook(payload, signature)
        
        # Handle different event types
        event_type = event.get("type", "")
        
        if event_type == "customer.subscription.updated":
            logger.info("Subscription updated via webhook")
        elif event_type == "customer.subscription.deleted":
            logger.info("Subscription deleted via webhook")
        elif event_type == "invoice.paid":
            logger.info("Invoice paid via webhook")
        elif event_type == "invoice.payment_failed":
            logger.warning("Invoice payment failed via webhook")
        
        return {"received": True}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail="Webhook processing failed")


@router.get("/health")
async def billing_health():
    """Check billing service health."""
    try:
        service = get_billing_service()
        stripe_configured = service.stripe.is_configured()
        
        return {
            "status": "healthy",
            "stripe_configured": stripe_configured,
            "subscriptions_count": len(service._subscriptions),
            "invoices_count": len(service._invoices)
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e)
        }
