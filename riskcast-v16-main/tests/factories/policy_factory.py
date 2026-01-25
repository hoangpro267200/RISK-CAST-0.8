"""
Policy Factory
"""

import factory
from factory import fuzzy
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

try:
    from app.models.policy import Policy
except ImportError:
    Policy = None

from tests.factories.base import BaseFactory, Generators


class PolicyFactory(BaseFactory):
    """Factory for generating Policy test data."""
    
    class Meta:
        model = Policy
        skip_postgeneration_if_model_is_none = True
    
    # Identifiers
    policy_number = factory.LazyFunction(
        lambda: f"POL-{datetime.now().strftime('%Y%m%d')}-{random.randint(10000, 99999)}"
    )
    
    # Status
    status = "ACTIVE"
    
    # Shipment details
    origin_port = factory.LazyFunction(Generators.random_port)
    destination_port = factory.LazyFunction(Generators.random_port)
    cargo_type = factory.LazyFunction(Generators.random_cargo_type)
    cargo_value_usd = factory.LazyFunction(lambda: Generators.random_cargo_value())
    container_count = fuzzy.FuzzyInteger(1, 10)
    carrier_code = factory.LazyFunction(Generators.random_carrier)
    voyage_number = factory.LazyFunction(
        lambda: f"V{random.randint(100, 999)}"
    )
    
    # Coverage
    coverage_type = "ALL_RISKS"
    coverage_limit_usd = factory.LazyAttribute(lambda o: o.cargo_value_usd)
    deductible_type = "PERCENTAGE"
    deductible_amount = factory.LazyAttribute(
        lambda o: (o.cargo_value_usd * Decimal("0.01")).quantize(Decimal("0.01"))
    )
    
    # Premium
    total_premium_usd = factory.LazyAttribute(
        lambda o: Generators.random_premium(o.cargo_value_usd)
    )
    premium_paid = True
    premium_paid_at = factory.LazyFunction(datetime.utcnow)
    
    # Dates
    effective_from = factory.LazyFunction(lambda: date.today() - timedelta(days=7))
    effective_to = factory.LazyFunction(lambda: date.today() + timedelta(days=30))
    departure_date = factory.LazyFunction(lambda: Generators.future_date(1, 30))
    arrival_date = factory.LazyAttribute(
        lambda o: o.departure_date + timedelta(days=random.randint(14, 45))
    )
    
    # Risk
    risk_score = factory.LazyFunction(Generators.random_risk_score)
    risk_grade = factory.LazyAttribute(
        lambda o: Generators.risk_grade_from_score(o.risk_score)
    )
    
    # Relationships
    customer_id = factory.LazyFunction(
        lambda: f"cust-{random.randint(1000, 9999)}"
    )
    quote_id = factory.LazyFunction(
        lambda: f"quote-{random.randint(1000, 9999)}"
    )
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    # Claims tracking
    has_claims = False
    claims_count = 0
    total_claimed_amount = Decimal("0.00")
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    
    # Optional documents
    policy_document_url = factory.LazyFunction(
        lambda: f"https://storage.example.com/policies/pol-{random.randint(1000, 9999)}.pdf"
    )
    
    class Params:
        """Traits for different policy states."""
        
        # Expired policy
        expired = factory.Trait(
            status="EXPIRED",
            effective_to=factory.LazyFunction(
                lambda: date.today() - timedelta(days=1)
            )
        )
        
        # Cancelled policy
        cancelled = factory.Trait(
            status="CANCELLED",
            cancelled_at=factory.LazyFunction(datetime.utcnow),
            cancellation_reason="Customer request",
            cancelled_by=factory.LazyFunction(
                lambda: f"user-{random.randint(100, 999)}"
            )
        )
        
        # Pending payment
        pending_payment = factory.Trait(
            premium_paid=False,
            premium_paid_at=None,
            status="PENDING_PAYMENT"
        )
        
        # Has claims
        with_claims = factory.Trait(
            has_claims=True,
            claims_count=fuzzy.FuzzyInteger(1, 3),
            total_claimed_amount=factory.LazyFunction(
                lambda: Decimal(random.randint(10000, 100000))
            )
        )
        
        # Large claim
        large_claim = factory.Trait(
            has_claims=True,
            claims_count=1,
            total_claimed_amount=factory.LazyAttribute(
                lambda o: o.cargo_value_usd * Decimal("0.5")
            )
        )
        
        # Multiple claims
        multiple_claims = factory.Trait(
            has_claims=True,
            claims_count=fuzzy.FuzzyInteger(3, 5),
            total_claimed_amount=factory.LazyAttribute(
                lambda o: o.cargo_value_usd * Decimal("0.3")
            )
        )
        
        # Completed voyage
        completed = factory.Trait(
            status="COMPLETED",
            departure_date=factory.LazyFunction(
                lambda: Generators.past_date(30, 60)
            ),
            arrival_date=factory.LazyFunction(
                lambda: Generators.past_date(15, 30)
            ),
            effective_to=factory.LazyFunction(
                lambda: date.today() - timedelta(days=7)
            )
        )
        
        # High value policy
        high_value = factory.Trait(
            cargo_value_usd=factory.LazyFunction(
                lambda: Generators.random_cargo_value(1000000, 5000000)
            ),
            coverage_limit_usd=factory.LazyAttribute(lambda o: o.cargo_value_usd)
        )
        
        # Named perils coverage
        named_perils = factory.Trait(
            coverage_type="NAMED_PERILS",
            total_premium_usd=factory.LazyAttribute(
                lambda o: (o.cargo_value_usd * Decimal("0.0015")).quantize(Decimal("0.01"))
            )
        )
