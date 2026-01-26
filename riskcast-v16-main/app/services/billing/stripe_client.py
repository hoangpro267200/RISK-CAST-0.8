"""
Stripe API Client

Provides:
1. Customer management
2. Subscription management
3. Payment processing
4. Checkout sessions
5. Billing portal
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Try to import Stripe
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None


@dataclass
class StripeCustomer:
    """Stripe customer data."""
    id: str
    email: Optional[str]
    metadata: Dict


@dataclass
class StripeSubscription:
    """Stripe subscription data."""
    id: str
    status: str
    current_period_end: int


@dataclass
class StripePayment:
    """Stripe payment data."""
    id: str
    status: str
    amount: int


class StripeClient:
    """
    Stripe API client.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        self.webhook_secret = webhook_secret or os.getenv("STRIPE_WEBHOOK_SECRET")
        
        if STRIPE_AVAILABLE and self.api_key:
            stripe.api_key = self.api_key
            logger.info("Stripe client initialized")
        else:
            if not STRIPE_AVAILABLE:
                logger.warning("Stripe SDK not installed - using mock mode")
            else:
                logger.warning("Stripe API key not configured - using mock mode")
    
    def is_configured(self) -> bool:
        """Check if Stripe is properly configured."""
        return STRIPE_AVAILABLE and bool(self.api_key)
    
    async def create_customer(
        self,
        tenant_id: str,
        email: Optional[str] = None,
        payment_method_id: Optional[str] = None
    ) -> StripeCustomer:
        """Create Stripe customer."""
        if not self.is_configured():
            return StripeCustomer(
                id=f"cus_mock_{tenant_id[:8]}",
                email=email,
                metadata={"tenant_id": tenant_id}
            )
        
        params = {
            "metadata": {"tenant_id": tenant_id}
        }
        
        if email:
            params["email"] = email
        
        if payment_method_id:
            params["payment_method"] = payment_method_id
            params["invoice_settings"] = {
                "default_payment_method": payment_method_id
            }
        
        customer = stripe.Customer.create(**params)
        
        return StripeCustomer(
            id=customer.id,
            email=customer.get("email"),
            metadata=customer.get("metadata", {})
        )
    
    async def create_subscription(
        self,
        customer_id: str,
        price_id: str,
        trial_days: int = 0
    ) -> StripeSubscription:
        """Create Stripe subscription."""
        if not self.is_configured():
            return StripeSubscription(
                id=f"sub_mock_{customer_id[:8]}",
                status="trialing" if trial_days > 0 else "active",
                current_period_end=0
            )
        
        params = {
            "customer": customer_id,
            "items": [{"price": price_id}],
            "payment_behavior": "default_incomplete",
            "expand": ["latest_invoice.payment_intent"]
        }
        
        if trial_days > 0:
            params["trial_period_days"] = trial_days
        
        subscription = stripe.Subscription.create(**params)
        
        return StripeSubscription(
            id=subscription.id,
            status=subscription.status,
            current_period_end=subscription.current_period_end
        )
    
    async def update_subscription(
        self,
        subscription_id: str,
        new_price_id: str
    ) -> StripeSubscription:
        """Update subscription price."""
        if not self.is_configured():
            return StripeSubscription(
                id=subscription_id,
                status="active",
                current_period_end=0
            )
        
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        updated = stripe.Subscription.modify(
            subscription_id,
            items=[{
                "id": subscription["items"]["data"][0].id,
                "price": new_price_id
            }],
            proration_behavior="create_prorations"
        )
        
        return StripeSubscription(
            id=updated.id,
            status=updated.status,
            current_period_end=updated.current_period_end
        )
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        cancel_immediately: bool = False
    ):
        """Cancel subscription."""
        if not self.is_configured():
            return
        
        if cancel_immediately:
            stripe.Subscription.delete(subscription_id)
        else:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
    
    async def create_payment(
        self,
        amount: int,
        currency: str,
        payment_method_id: str,
        customer_id: Optional[str] = None
    ) -> StripePayment:
        """Create payment intent and confirm."""
        if not self.is_configured():
            return StripePayment(
                id="pi_mock",
                status="succeeded",
                amount=amount
            )
        
        params = {
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method_id,
            "confirm": True
        }
        
        if customer_id:
            params["customer"] = customer_id
        
        intent = stripe.PaymentIntent.create(**params)
        
        return StripePayment(
            id=intent.id,
            status=intent.status,
            amount=intent.amount
        )
    
    async def create_checkout_session(
        self,
        price_id: str,
        success_url: str,
        cancel_url: str,
        customer_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create Stripe Checkout session."""
        if not self.is_configured():
            return "https://checkout.stripe.com/mock"
        
        params = {
            "mode": "subscription",
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url
        }
        
        if customer_id:
            params["customer"] = customer_id
        
        if metadata:
            params["metadata"] = metadata
        
        session = stripe.checkout.Session.create(**params)
        
        return session.url
    
    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> str:
        """Create Stripe billing portal session."""
        if not self.is_configured():
            return "https://billing.stripe.com/mock"
        
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        
        return session.url
    
    def verify_webhook(
        self,
        payload: bytes,
        signature: str
    ) -> Dict[str, Any]:
        """Verify and parse webhook event."""
        if not self.is_configured():
            raise ValueError("Stripe not configured")
        
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")
        
        event = stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )
        
        return event
