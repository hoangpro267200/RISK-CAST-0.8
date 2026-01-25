"""
Customer Factory
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
from decimal import Decimal
import random

try:
    from app.models.customer import Customer
except ImportError:
    Customer = None

from tests.factories.base import BaseFactory, Generators


class CustomerFactory(BaseFactory):
    """Factory for generating Customer test data."""
    
    class Meta:
        model = Customer
        skip_postgeneration_if_model_is_none = True
    
    # Company details
    company_name = factory.LazyFunction(Generators.random_company_name)
    legal_name = factory.LazyAttribute(lambda o: f"{o.company_name}")
    registration_number = factory.LazyFunction(
        lambda: f"REG{random.randint(100000000, 999999999)}"
    )
    tax_id = factory.LazyFunction(
        lambda: f"{random.randint(10, 99)}-{random.randint(1000000, 9999999)}"
    )
    
    # Address
    address_line_1 = factory.Faker('street_address')
    address_line_2 = factory.Faker('secondary_address')
    city = factory.Faker('city')
    state_province = factory.Faker('state_abbr')
    postal_code = factory.Faker('postcode')
    country = "US"
    
    # Contact
    primary_contact_name = factory.Faker('name')
    primary_contact_email = factory.Faker('company_email')
    primary_contact_phone = factory.LazyFunction(Generators.random_phone)
    
    # Business info
    industry = fuzzy.FuzzyChoice(Generators.INDUSTRIES)
    annual_shipment_volume = fuzzy.FuzzyInteger(10, 1000)
    average_cargo_value_usd = fuzzy.FuzzyDecimal(50000, 500000)
    primary_cargo_types = factory.LazyFunction(
        lambda: random.sample(Generators.CARGO_TYPES, k=random.randint(1, 4))
    )
    primary_routes = factory.LazyFunction(
        lambda: [
            f"{o}-{d}" 
            for o, d in [Generators.random_port_pair() for _ in range(random.randint(1, 3))]
        ]
    )
    
    # Years in business
    years_in_business = fuzzy.FuzzyInteger(1, 20)
    years_insured = fuzzy.FuzzyInteger(0, 10)
    
    # Status
    status = "ACTIVE"
    onboarding_stage = "COMPLETE"
    
    # Pricing
    pricing_tier = fuzzy.FuzzyChoice(["STANDARD", "PREFERRED", "PREMIER"])
    credit_limit_usd = fuzzy.FuzzyDecimal(100000, 1000000)
    credit_score = fuzzy.FuzzyInteger(40, 90)
    credit_grade = factory.LazyAttribute(
        lambda o: Generators.credit_grade_from_score(o.credit_score)
    )
    
    # Risk profile
    loss_ratio = factory.LazyFunction(lambda: round(random.uniform(0.0, 0.5), 3))
    claims_history_count = fuzzy.FuzzyInteger(0, 10)
    
    # Tenant
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    activated_at = factory.LazyFunction(datetime.utcnow)
    last_policy_date = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(days=random.randint(1, 90))
    )
    
    # KYC
    kyc_verified = True
    kyc_verified_at = factory.LazyFunction(datetime.utcnow)
    
    class Params:
        """Traits for different customer types."""
        
        # New customer (pending onboarding)
        new_customer = factory.Trait(
            status="PENDING",
            onboarding_stage="REGISTRATION_COMPLETE",
            pricing_tier=None,
            credit_score=None,
            credit_grade=None,
            credit_limit_usd=None,
            activated_at=None,
            kyc_verified=False,
            kyc_verified_at=None
        )
        
        # High risk customer
        high_risk = factory.Trait(
            pricing_tier="HIGH_RISK",
            credit_score=fuzzy.FuzzyInteger(20, 40),
            credit_grade="D",
            loss_ratio=factory.LazyFunction(lambda: round(random.uniform(0.5, 0.9), 3)),
            claims_history_count=fuzzy.FuzzyInteger(5, 15),
            credit_limit_usd=fuzzy.FuzzyDecimal(50000, 200000)
        )
        
        # Enterprise customer
        enterprise = factory.Trait(
            pricing_tier="PREMIER",
            credit_score=fuzzy.FuzzyInteger(85, 100),
            credit_grade="A",
            annual_shipment_volume=fuzzy.FuzzyInteger(500, 5000),
            credit_limit_usd=fuzzy.FuzzyDecimal(1000000, 10000000),
            years_in_business=fuzzy.FuzzyInteger(10, 50),
            years_insured=fuzzy.FuzzyInteger(5, 20),
            loss_ratio=factory.LazyFunction(lambda: round(random.uniform(0.0, 0.2), 3))
        )
        
        # SMB customer
        smb = factory.Trait(
            pricing_tier="STANDARD",
            credit_score=fuzzy.FuzzyInteger(55, 75),
            credit_grade="B",
            annual_shipment_volume=fuzzy.FuzzyInteger(10, 100),
            credit_limit_usd=fuzzy.FuzzyDecimal(100000, 500000),
            years_in_business=fuzzy.FuzzyInteger(1, 10)
        )
        
        # Inactive customer
        inactive = factory.Trait(
            status="INACTIVE",
            last_policy_date=factory.LazyFunction(
                lambda: datetime.utcnow() - timedelta(days=random.randint(365, 730))
            )
        )
        
        # Suspended customer
        suspended = factory.Trait(
            status="SUSPENDED",
            suspension_reason="Payment default",
            suspended_at=factory.LazyFunction(datetime.utcnow)
        )
        
        # International customer
        international = factory.Trait(
            country=fuzzy.FuzzyChoice(["GB", "DE", "SG", "CN", "JP", "AU"]),
            primary_routes=factory.LazyFunction(
                lambda: ["CNSHA-NLRTM", "SGSIN-DEHAM", "HKHKG-GBFXT"]
            )
        )
        
        # Electronics specialist
        electronics_specialist = factory.Trait(
            primary_cargo_types=["ELECTRONICS", "MACHINERY"],
            industry="E_COMMERCE",
            annual_shipment_volume=fuzzy.FuzzyInteger(200, 1000)
        )
        
        # Pharmaceutical customer
        pharmaceutical = factory.Trait(
            primary_cargo_types=["PHARMACEUTICALS", "CHEMICALS"],
            industry="PHARMACEUTICAL",
            pricing_tier="PREMIER",
            credit_score=fuzzy.FuzzyInteger(80, 95)
        )
