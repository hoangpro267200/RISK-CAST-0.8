"""
User Factory
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import random

try:
    from app.models.user import User
except ImportError:
    User = None

from tests.factories.base import BaseFactory, Generators


class UserFactory(BaseFactory):
    """Factory for generating User test data."""
    
    class Meta:
        model = User
        skip_postgeneration_if_model_is_none = True
    
    # Email and password
    email = factory.LazyFunction(lambda: Generators.random_email())
    hashed_password = factory.LazyFunction(
        lambda: f"$2b$12$hashed_password_{random.randint(100000, 999999)}"
    )
    
    # Name
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    full_name = factory.LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    
    # Status flags
    is_active = True
    is_verified = True
    is_superuser = False
    
    # Role
    role = "user"
    
    # Relationships
    customer_id = factory.LazyFunction(
        lambda: f"cust-{random.randint(1000, 9999)}"
    )
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    # Preferences
    email_notifications = True
    sms_notifications = False
    language = "en"
    timezone = "America/New_York"
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    last_login_at = factory.LazyFunction(datetime.utcnow)
    email_verified_at = factory.LazyFunction(datetime.utcnow)
    
    # Optional phone
    phone = factory.LazyFunction(Generators.random_phone)
    
    class Params:
        """Traits for different user types."""
        
        # Admin user
        admin = factory.Trait(
            role="admin",
            is_verified=True,
            is_superuser=False,
            email=factory.LazyFunction(
                lambda: f"admin{random.randint(100, 999)}@riskcast.com"
            )
        )
        
        # Superuser
        superuser = factory.Trait(
            role="admin",
            is_superuser=True,
            is_verified=True,
            email=factory.LazyFunction(
                lambda: f"superuser{random.randint(10, 99)}@riskcast.com"
            )
        )
        
        # Customer user
        customer = factory.Trait(
            role="customer",
            is_verified=True
        )
        
        # Adjuster user
        adjuster = factory.Trait(
            role="adjuster",
            is_verified=True,
            email=factory.LazyFunction(
                lambda: f"adjuster{random.randint(100, 999)}@riskcast.com"
            )
        )
        
        # Underwriter user
        underwriter = factory.Trait(
            role="underwriter",
            is_verified=True,
            email=factory.LazyFunction(
                lambda: f"underwriter{random.randint(100, 999)}@riskcast.com"
            )
        )
        
        # Inactive user
        inactive = factory.Trait(
            is_active=False,
            last_login_at=factory.LazyFunction(
                lambda: datetime.utcnow() - timedelta(days=random.randint(180, 365))
            )
        )
        
        # Unverified user
        unverified = factory.Trait(
            is_verified=False,
            email_verified_at=None
        )
        
        # New user (just registered)
        new_user = factory.Trait(
            is_verified=False,
            email_verified_at=None,
            last_login_at=None,
            created_at=factory.LazyFunction(
                lambda: datetime.utcnow() - timedelta(hours=random.randint(1, 24))
            )
        )
        
        # API-only user
        api_only = factory.Trait(
            role="api",
            is_verified=True,
            email=factory.LazyFunction(
                lambda: f"api{random.randint(1000, 9999)}@system.riskcast.com"
            ),
            last_login_at=None
        )
