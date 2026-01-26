"""
Billing Service - Core billing functionality

Provides:
1. Subscription management
2. Usage-based billing
3. Invoice generation
4. Payment processing
5. Revenue analytics
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class PlanTier(str, Enum):
    """Subscription plan tiers."""
    FREE = "FREE"
    STARTER = "STARTER"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"


class BillingCycle(str, Enum):
    """Billing cycle options."""
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"


class PaymentStatus(str, Enum):
    """Payment status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    CANCELED = "CANCELED"
    UNPAID = "UNPAID"


@dataclass
class PlanConfig:
    """Plan configuration."""
    tier: PlanTier
    name: str
    
    # Pricing
    monthly_price_usd: Decimal
    annual_price_usd: Decimal  # With discount
    
    # Quotas
    quotes_per_month: int
    policies_per_month: int
    api_calls_per_day: int
    users: int
    
    # Features
    features: List[str]
    
    # Stripe IDs
    stripe_monthly_price_id: str = ""
    stripe_annual_price_id: str = ""


# Plan Configurations
PLANS: Dict[PlanTier, PlanConfig] = {
    PlanTier.FREE: PlanConfig(
        tier=PlanTier.FREE,
        name="Free",
        monthly_price_usd=Decimal("0"),
        annual_price_usd=Decimal("0"),
        quotes_per_month=10,
        policies_per_month=5,
        api_calls_per_day=100,
        users=1,
        features=["Basic risk assessment", "Email support"],
        stripe_monthly_price_id=""
    ),
    PlanTier.STARTER: PlanConfig(
        tier=PlanTier.STARTER,
        name="Starter",
        monthly_price_usd=Decimal("99"),
        annual_price_usd=Decimal("990"),
        quotes_per_month=100,
        policies_per_month=50,
        api_calls_per_day=1000,
        users=5,
        features=[
            "Advanced risk assessment",
            "Weather integration",
            "Email & chat support",
            "Basic analytics"
        ],
        stripe_monthly_price_id="price_starter_monthly",
        stripe_annual_price_id="price_starter_annual"
    ),
    PlanTier.PROFESSIONAL: PlanConfig(
        tier=PlanTier.PROFESSIONAL,
        name="Professional",
        monthly_price_usd=Decimal("299"),
        annual_price_usd=Decimal("2990"),
        quotes_per_month=500,
        policies_per_month=250,
        api_calls_per_day=10000,
        users=20,
        features=[
            "Full risk engine",
            "All data integrations",
            "Priority support",
            "Advanced analytics",
            "Custom reports",
            "API access",
            "Webhook notifications"
        ],
        stripe_monthly_price_id="price_professional_monthly",
        stripe_annual_price_id="price_professional_annual"
    ),
    PlanTier.ENTERPRISE: PlanConfig(
        tier=PlanTier.ENTERPRISE,
        name="Enterprise",
        monthly_price_usd=Decimal("999"),
        annual_price_usd=Decimal("9990"),
        quotes_per_month=-1,  # Unlimited
        policies_per_month=-1,
        api_calls_per_day=-1,
        users=-1,
        features=[
            "Everything in Professional",
            "Dedicated account manager",
            "Custom integrations",
            "SLA guarantee",
            "On-premise option",
            "White-labeling",
            "Custom ML models"
        ],
        stripe_monthly_price_id="price_enterprise_monthly",
        stripe_annual_price_id="price_enterprise_annual"
    )
}


@dataclass
class Subscription:
    """Subscription data."""
    id: str
    tenant_id: str
    plan_tier: PlanTier
    billing_cycle: BillingCycle
    status: SubscriptionStatus
    price_usd: float
    
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Invoice:
    """Invoice data."""
    id: str
    tenant_id: str
    subscription_id: str
    invoice_number: str
    status: str
    
    subtotal_usd: float
    tax_usd: float
    total_usd: float
    line_items: List[Dict]
    
    invoice_date: datetime
    due_date: datetime
    paid_at: Optional[datetime] = None
    
    stripe_invoice_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class Payment:
    """Payment data."""
    id: str
    tenant_id: str
    invoice_id: str
    amount_usd: float
    currency: str
    status: PaymentStatus
    
    payment_method_type: Optional[str] = None
    payment_method_last4: Optional[str] = None
    
    stripe_payment_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    
    failure_reason: Optional[str] = None
    
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class BillingService:
    """
    Main billing service.
    """
    
    def __init__(
        self,
        stripe_client = None,
        usage_tracker = None
    ):
        from app.services.billing.stripe_client import StripeClient
        from app.services.billing.usage_tracker import UsageTracker
        
        self.stripe = stripe_client or StripeClient()
        self.usage = usage_tracker or UsageTracker()
        
        # In-memory storage (replace with database in production)
        self._subscriptions: Dict[str, Subscription] = {}
        self._invoices: Dict[str, Invoice] = {}
        self._payments: Dict[str, Payment] = {}
        self._invoice_counter: Dict[str, int] = {}
    
    # =========================================================================
    # Subscription Management
    # =========================================================================
    
    async def create_subscription(
        self,
        tenant_id: str,
        plan_tier: PlanTier,
        billing_cycle: BillingCycle = BillingCycle.MONTHLY,
        payment_method_id: Optional[str] = None,
        trial_days: int = 14
    ) -> Subscription:
        """
        Create a new subscription for a tenant.
        """
        # Get plan config
        plan = PLANS[plan_tier]
        
        # Determine price
        price = (
            plan.monthly_price_usd 
            if billing_cycle == BillingCycle.MONTHLY 
            else plan.annual_price_usd
        )
        
        # Create Stripe customer if needed
        stripe_customer_id = await self._get_or_create_stripe_customer(
            tenant_id, payment_method_id
        )
        
        # Create Stripe subscription
        stripe_price_id = (
            plan.stripe_monthly_price_id 
            if billing_cycle == BillingCycle.MONTHLY 
            else plan.stripe_annual_price_id
        )
        
        stripe_subscription = None
        if stripe_price_id and price > 0:
            stripe_subscription = await self.stripe.create_subscription(
                customer_id=stripe_customer_id,
                price_id=stripe_price_id,
                trial_days=trial_days
            )
        
        # Calculate dates
        now = datetime.utcnow()
        trial_end = now + timedelta(days=trial_days) if trial_days > 0 else None
        
        period_end = (
            now + timedelta(days=30 if billing_cycle == BillingCycle.MONTHLY else 365)
        )
        
        # Create subscription record
        subscription = Subscription(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            plan_tier=plan_tier,
            billing_cycle=billing_cycle,
            status=SubscriptionStatus.TRIALING if trial_days > 0 else SubscriptionStatus.ACTIVE,
            price_usd=float(price),
            trial_start=now if trial_days > 0 else None,
            trial_end=trial_end,
            current_period_start=now,
            current_period_end=period_end,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription.id if stripe_subscription else None
        )
        
        self._subscriptions[subscription.id] = subscription
        
        logger.info(
            f"Subscription created",
            extra={
                "tenant_id": tenant_id,
                "plan": plan_tier.value,
                "subscription_id": subscription.id
            }
        )
        
        return subscription
    
    async def upgrade_subscription(
        self,
        tenant_id: str,
        new_plan_tier: PlanTier
    ) -> Subscription:
        """Upgrade subscription to a higher tier."""
        subscription = await self.get_subscription(tenant_id)
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        old_tier = subscription.plan_tier
        new_plan = PLANS[new_plan_tier]
        
        # Update Stripe subscription
        if subscription.stripe_subscription_id:
            new_price_id = (
                new_plan.stripe_monthly_price_id 
                if subscription.billing_cycle == BillingCycle.MONTHLY 
                else new_plan.stripe_annual_price_id
            )
            await self.stripe.update_subscription(
                subscription.stripe_subscription_id,
                new_price_id
            )
        
        # Update local record
        subscription.plan_tier = new_plan_tier
        subscription.price_usd = float(
            new_plan.monthly_price_usd 
            if subscription.billing_cycle == BillingCycle.MONTHLY 
            else new_plan.annual_price_usd
        )
        subscription.updated_at = datetime.utcnow()
        
        logger.info(
            f"Subscription upgraded",
            extra={
                "tenant_id": tenant_id,
                "old_tier": old_tier.value,
                "new_tier": new_plan_tier.value
            }
        )
        
        return subscription
    
    async def cancel_subscription(
        self,
        tenant_id: str,
        cancel_immediately: bool = False,
        reason: Optional[str] = None
    ) -> Subscription:
        """Cancel subscription."""
        subscription = await self.get_subscription(tenant_id)
        
        if not subscription:
            raise ValueError("No active subscription found")
        
        # Cancel in Stripe
        if subscription.stripe_subscription_id:
            await self.stripe.cancel_subscription(
                subscription.stripe_subscription_id,
                cancel_immediately
            )
        
        # Update local record
        subscription.canceled_at = datetime.utcnow()
        
        if cancel_immediately:
            subscription.status = SubscriptionStatus.CANCELED
        
        logger.info(
            f"Subscription cancelled",
            extra={
                "tenant_id": tenant_id,
                "immediate": cancel_immediately
            }
        )
        
        return subscription
    
    async def get_subscription(self, tenant_id: str) -> Optional[Subscription]:
        """Get active subscription for tenant."""
        for sub in self._subscriptions.values():
            if sub.tenant_id == tenant_id and sub.status in [
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING,
                SubscriptionStatus.PAST_DUE
            ]:
                return sub
        return None
    
    async def get_plan_details(self, plan_tier: PlanTier) -> PlanConfig:
        """Get plan configuration details."""
        return PLANS[plan_tier]
    
    async def get_all_plans(self) -> List[PlanConfig]:
        """Get all available plans."""
        return list(PLANS.values())
    
    # =========================================================================
    # Invoicing
    # =========================================================================
    
    async def generate_invoice(
        self,
        tenant_id: str,
        subscription: Subscription,
        line_items: List[Dict]
    ) -> Invoice:
        """Generate invoice for subscription."""
        # Calculate totals
        subtotal = sum(item.get("amount", 0) for item in line_items)
        tax = subtotal * 0.1  # 10% tax example
        total = subtotal + tax
        
        # Generate invoice number
        if tenant_id not in self._invoice_counter:
            self._invoice_counter[tenant_id] = 0
        self._invoice_counter[tenant_id] += 1
        invoice_number = f"INV-{tenant_id[:8]}-{self._invoice_counter[tenant_id]:05d}"
        
        invoice = Invoice(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subscription_id=subscription.id,
            invoice_number=invoice_number,
            status="PENDING",
            subtotal_usd=subtotal,
            tax_usd=tax,
            total_usd=total,
            line_items=line_items,
            invoice_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=30)
        )
        
        self._invoices[invoice.id] = invoice
        
        return invoice
    
    async def get_invoices(
        self,
        tenant_id: str,
        limit: int = 10
    ) -> List[Invoice]:
        """Get invoices for tenant."""
        invoices = [
            inv for inv in self._invoices.values()
            if inv.tenant_id == tenant_id
        ]
        invoices.sort(key=lambda x: x.created_at, reverse=True)
        return invoices[:limit]
    
    # =========================================================================
    # Payments
    # =========================================================================
    
    async def process_payment(
        self,
        invoice_id: str,
        payment_method_id: str
    ) -> Payment:
        """Process payment for invoice."""
        invoice = self._invoices.get(invoice_id)
        
        if not invoice:
            raise ValueError("Invoice not found")
        
        # Create payment record
        payment = Payment(
            id=str(uuid.uuid4()),
            tenant_id=invoice.tenant_id,
            invoice_id=invoice.id,
            amount_usd=invoice.total_usd,
            currency="USD",
            status=PaymentStatus.PROCESSING
        )
        self._payments[payment.id] = payment
        
        try:
            # Process with Stripe
            stripe_payment = await self.stripe.create_payment(
                amount=int(invoice.total_usd * 100),  # Convert to cents
                currency="usd",
                payment_method_id=payment_method_id
            )
            
            payment.stripe_payment_id = stripe_payment.id
            payment.status = PaymentStatus.SUCCEEDED
            payment.completed_at = datetime.utcnow()
            
            # Update invoice
            invoice.status = "PAID"
            invoice.paid_at = datetime.utcnow()
            invoice.stripe_payment_intent_id = stripe_payment.id
            
        except Exception as e:
            payment.status = PaymentStatus.FAILED
            payment.failure_reason = str(e)
            
            logger.error(
                f"Payment failed",
                extra={
                    "invoice_id": invoice_id,
                    "error": str(e)
                }
            )
        
        return payment
    
    # =========================================================================
    # Usage & Quotas
    # =========================================================================
    
    async def check_quota(
        self,
        tenant_id: str,
        resource: str  # "quotes", "policies", "api_calls"
    ) -> Dict[str, Any]:
        """Check if tenant has quota remaining."""
        subscription = await self.get_subscription(tenant_id)
        
        if not subscription:
            # Default to free tier
            plan = PLANS[PlanTier.FREE]
        else:
            plan = PLANS[subscription.plan_tier]
        
        # Get current usage
        usage = await self.usage.get_usage(tenant_id, resource)
        
        # Get limit
        if resource == "quotes":
            limit = plan.quotes_per_month
        elif resource == "policies":
            limit = plan.policies_per_month
        elif resource == "api_calls":
            limit = plan.api_calls_per_day
        else:
            limit = 0
        
        # -1 means unlimited
        has_quota = limit == -1 or usage < limit
        
        return {
            "resource": resource,
            "used": usage,
            "limit": limit if limit != -1 else "unlimited",
            "remaining": limit - usage if limit != -1 else "unlimited",
            "has_quota": has_quota,
            "plan_tier": subscription.plan_tier.value if subscription else "FREE"
        }
    
    async def increment_usage(
        self,
        tenant_id: str,
        resource: str,
        amount: int = 1
    ):
        """Increment usage counter."""
        await self.usage.increment(tenant_id, resource, amount)
    
    # =========================================================================
    # Helpers
    # =========================================================================
    
    async def _get_or_create_stripe_customer(
        self,
        tenant_id: str,
        payment_method_id: Optional[str] = None
    ) -> str:
        """Get or create Stripe customer."""
        # Check if customer exists
        subscription = await self.get_subscription(tenant_id)
        if subscription and subscription.stripe_customer_id:
            return subscription.stripe_customer_id
        
        # Create new customer
        customer = await self.stripe.create_customer(
            tenant_id=tenant_id,
            payment_method_id=payment_method_id
        )
        
        return customer.id
