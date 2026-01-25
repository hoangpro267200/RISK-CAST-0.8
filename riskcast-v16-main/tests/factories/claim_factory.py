"""
Claim Factory
"""

import factory
from factory import fuzzy
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

try:
    from app.models.claim import Claim
except ImportError:
    Claim = None

from tests.factories.base import BaseFactory, Generators


class ClaimFactory(BaseFactory):
    """Factory for generating Claim test data."""
    
    class Meta:
        model = Claim
        skip_postgeneration_if_model_is_none = True
    
    # Identifiers
    claim_number = factory.LazyFunction(
        lambda: f"CLM-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    )
    
    # Status
    status = "FILED"
    
    # Loss details
    loss_date = factory.LazyFunction(
        lambda: date.today() - timedelta(days=random.randint(1, 30))
    )
    loss_type = fuzzy.FuzzyChoice(Generators.LOSS_TYPES)
    loss_description = factory.Faker('paragraph', nb_sentences=3)
    loss_location = factory.Faker('city')
    
    # Amounts
    claimed_amount_usd = factory.LazyFunction(
        lambda: Decimal(random.randint(5000, 100000))
    )
    approved_amount_usd = None
    paid_amount_usd = None
    
    # Contact information
    contact_name = factory.Faker('name')
    contact_email = factory.Faker('email')
    contact_phone = factory.LazyFunction(Generators.random_phone)
    
    # Timestamps
    filed_at = factory.LazyFunction(datetime.utcnow)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    
    # Relationships
    policy_id = factory.LazyFunction(
        lambda: f"pol-{random.randint(1000, 9999)}"
    )
    customer_id = factory.LazyFunction(
        lambda: f"cust-{random.randint(1000, 9999)}"
    )
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    # Documents
    document_count = 0
    has_supporting_documents = False
    
    class Params:
        """Traits for different claim states."""
        
        # In review
        in_review = factory.Trait(
            status="IN_REVIEW",
            assigned_adjuster_id=factory.LazyFunction(
                lambda: f"adj-{random.randint(100, 999)}"
            ),
            review_started_at=factory.LazyFunction(datetime.utcnow)
        )
        
        # Approved
        approved = factory.Trait(
            status="APPROVED",
            approved_amount_usd=factory.LazyAttribute(
                lambda o: (o.claimed_amount_usd * Decimal("0.9")).quantize(Decimal("0.01"))
            ),
            approved_at=factory.LazyFunction(datetime.utcnow),
            approved_by=factory.LazyFunction(
                lambda: f"adj-{random.randint(100, 999)}"
            ),
            adjuster_notes="Claim approved with 10% depreciation deduction."
        )
        
        # Paid
        paid = factory.Trait(
            status="PAID",
            approved_amount_usd=factory.LazyAttribute(
                lambda o: (o.claimed_amount_usd * Decimal("0.9")).quantize(Decimal("0.01"))
            ),
            paid_amount_usd=factory.LazyAttribute(lambda o: o.approved_amount_usd),
            paid_at=factory.LazyFunction(datetime.utcnow),
            payment_reference=factory.LazyFunction(
                lambda: f"PAY-{random.randint(100000, 999999)}"
            ),
            payment_method="WIRE_TRANSFER"
        )
        
        # Denied
        denied = factory.Trait(
            status="DENIED",
            denial_reason="EXCLUDED_PERIL",
            denied_at=factory.LazyFunction(datetime.utcnow),
            denied_by=factory.LazyFunction(
                lambda: f"adj-{random.randint(100, 999)}"
            ),
            adjuster_notes="Loss type is excluded under policy terms."
        )
        
        # Large claim
        large_claim = factory.Trait(
            claimed_amount_usd=factory.LazyFunction(
                lambda: Decimal(random.randint(100000, 500000))
            ),
            loss_type=fuzzy.FuzzyChoice(["CARGO_LOSS", "FIRE", "COLLISION"])
        )
        
        # Small claim
        small_claim = factory.Trait(
            claimed_amount_usd=factory.LazyFunction(
                lambda: Decimal(random.randint(1000, 10000))
            ),
            loss_type=fuzzy.FuzzyChoice(["CARGO_DAMAGE", "PACKAGING_FAILURE"])
        )
        
        # Theft claim
        theft = factory.Trait(
            loss_type="THEFT",
            loss_description="Cargo was stolen during transit. Police report filed.",
            claimed_amount_usd=factory.LazyFunction(
                lambda: Decimal(random.randint(50000, 200000))
            )
        )
        
        # Water damage claim
        water_damage = factory.Trait(
            loss_type="WATER_DAMAGE",
            loss_description="Water ingress during heavy storm damaged cargo.",
            claimed_amount_usd=factory.LazyFunction(
                lambda: Decimal(random.randint(20000, 100000))
            )
        )
        
        # With documents
        with_documents = factory.Trait(
            document_count=fuzzy.FuzzyInteger(3, 8),
            has_supporting_documents=True
        )
        
        # Partial approval
        partial_approval = factory.Trait(
            status="APPROVED",
            approved_amount_usd=factory.LazyAttribute(
                lambda o: (o.claimed_amount_usd * Decimal("0.6")).quantize(Decimal("0.01"))
            ),
            approved_at=factory.LazyFunction(datetime.utcnow),
            adjuster_notes="Partial approval: 40% contributory negligence."
        )
        
        # Delay claim (often excluded)
        delay = factory.Trait(
            loss_type="DELAY",
            loss_description="Shipment delayed by 15 days due to port congestion.",
            claimed_amount_usd=factory.LazyFunction(
                lambda: Decimal(random.randint(10000, 50000))
            )
        )
