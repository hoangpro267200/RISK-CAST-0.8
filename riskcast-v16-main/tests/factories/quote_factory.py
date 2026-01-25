"""
Quote Factory
"""

import factory
from factory import fuzzy
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

try:
    from app.models.quote import Quote
except ImportError:
    # Fallback for when models aren't available
    Quote = None

from tests.factories.base import BaseFactory, Generators


class QuoteFactory(BaseFactory):
    """Factory for generating Quote test data."""
    
    class Meta:
        model = Quote
        skip_postgeneration_if_model_is_none = True
    
    # Identifiers
    quote_number = factory.LazyFunction(
        lambda: f"QT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
    )
    
    # Status
    status = "PENDING"
    
    # Shipment details
    origin_port = factory.LazyFunction(Generators.random_port)
    destination_port = factory.LazyFunction(
        lambda: random.choice([p for p in Generators.PORTS if p != "CNSHA"])
    )
    cargo_type = factory.LazyFunction(Generators.random_cargo_type)
    cargo_value_usd = factory.LazyFunction(lambda: Generators.random_cargo_value())
    container_count = fuzzy.FuzzyInteger(1, 10)
    transit_days = fuzzy.FuzzyInteger(14, 45)
    
    # Coverage
    coverage_type = "ALL_RISKS"
    coverage_limit_usd = factory.LazyAttribute(lambda o: o.cargo_value_usd)
    deductible_type = "PERCENTAGE"
    deductible_amount = factory.LazyAttribute(
        lambda o: (o.cargo_value_usd * Decimal("0.01")).quantize(Decimal("0.01"))
    )
    
    # Pricing
    total_premium_usd = factory.LazyAttribute(
        lambda o: Generators.random_premium(o.cargo_value_usd)
    )
    rate_per_mille = factory.LazyAttribute(
        lambda o: (o.total_premium_usd / o.cargo_value_usd * 1000).quantize(Decimal("0.001"))
    )
    
    # Risk
    risk_score = factory.LazyFunction(Generators.random_risk_score)
    risk_grade = factory.LazyAttribute(
        lambda o: Generators.risk_grade_from_score(o.risk_score)
    )
    
    # Validity
    valid_from = factory.LazyFunction(datetime.utcnow)
    valid_until = factory.LazyFunction(
        lambda: datetime.utcnow() + timedelta(days=7)
    )
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    version = 1
    
    # Relationships
    customer_id = factory.LazyFunction(
        lambda: f"cust-{random.randint(1000, 9999)}"
    )
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    # Departure/arrival dates
    departure_date = factory.LazyFunction(
        lambda: Generators.future_date(7, 30)
    )
    arrival_date = factory.LazyAttribute(
        lambda o: o.departure_date + timedelta(days=random.randint(14, 45))
    )
    
    # Optional fields
    carrier_code = factory.LazyFunction(Generators.random_carrier)
    voyage_number = factory.LazyFunction(
        lambda: f"V{random.randint(100, 999)}"
    )
    
    class Params:
        """Traits for different quote states."""
        
        # Accepted quote
        accepted = factory.Trait(
            status="ACCEPTED",
            accepted_at=factory.LazyFunction(datetime.utcnow),
            accepted_by=factory.LazyFunction(
                lambda: f"user-{random.randint(100, 999)}"
            )
        )
        
        # Declined quote
        declined = factory.Trait(
            status="DECLINED",
            declined_at=factory.LazyFunction(datetime.utcnow),
            decline_reason="PRICE_TOO_HIGH",
            declined_by=factory.LazyFunction(
                lambda: f"user-{random.randint(100, 999)}"
            )
        )
        
        # Expired quote
        expired = factory.Trait(
            status="EXPIRED",
            valid_until=factory.LazyFunction(
                lambda: datetime.utcnow() - timedelta(days=1)
            )
        )
        
        # Bound quote
        bound = factory.Trait(
            status="BOUND",
            accepted_at=factory.LazyFunction(datetime.utcnow),
            bound_at=factory.LazyFunction(datetime.utcnow),
            policy_id=factory.LazyFunction(
                lambda: f"pol-{random.randint(1000, 9999)}"
            )
        )
        
        # High value shipment
        high_value = factory.Trait(
            cargo_value_usd=factory.LazyFunction(
                lambda: Generators.random_cargo_value(1000000, 5000000)
            ),
            coverage_limit_usd=factory.LazyAttribute(lambda o: o.cargo_value_usd),
            total_premium_usd=factory.LazyAttribute(
                lambda o: (o.cargo_value_usd * Decimal("0.003")).quantize(Decimal("0.01"))
            )
        )
        
        # Low value shipment
        low_value = factory.Trait(
            cargo_value_usd=factory.LazyFunction(
                lambda: Generators.random_cargo_value(10000, 50000)
            )
        )
        
        # High risk
        high_risk = factory.Trait(
            risk_score=factory.LazyFunction(lambda: round(random.uniform(0.7, 0.95), 2)),
            risk_grade="D",
            total_premium_usd=factory.LazyAttribute(
                lambda o: (o.cargo_value_usd * Decimal("0.008")).quantize(Decimal("0.01"))
            )
        )
        
        # Low risk
        low_risk = factory.Trait(
            risk_score=factory.LazyFunction(lambda: round(random.uniform(0.05, 0.20), 2)),
            risk_grade="A",
            total_premium_usd=factory.LazyAttribute(
                lambda o: (o.cargo_value_usd * Decimal("0.001")).quantize(Decimal("0.01"))
            )
        )
        
        # Electronics shipment
        electronics = factory.Trait(
            cargo_type="ELECTRONICS",
            risk_score=factory.LazyFunction(lambda: round(random.uniform(0.3, 0.6), 2))
        )
        
        # Perishable cargo
        perishable = factory.Trait(
            cargo_type="FOOD_PERISHABLE",
            transit_days=fuzzy.FuzzyInteger(7, 21),
            risk_score=factory.LazyFunction(lambda: round(random.uniform(0.4, 0.7), 2))
        )
        
        # Trans-Pacific route
        trans_pacific = factory.Trait(
            origin_port=fuzzy.FuzzyChoice(["CNSHA", "CNNBO", "HKHKG", "SGSIN"]),
            destination_port=fuzzy.FuzzyChoice(["USLAX", "USOAK", "USSEA"]),
            transit_days=fuzzy.FuzzyInteger(14, 25)
        )
        
        # Trans-Atlantic route
        trans_atlantic = factory.Trait(
            origin_port=fuzzy.FuzzyChoice(["USNYC", "GBFXT", "NLRTM"]),
            destination_port=fuzzy.FuzzyChoice(["DEHAM", "FRLEH", "NLRTM"]),
            transit_days=fuzzy.FuzzyInteger(10, 18)
        )
