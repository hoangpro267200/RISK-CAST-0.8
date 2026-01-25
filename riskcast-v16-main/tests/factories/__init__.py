"""
Test Data Factories

Provides consistent test data generation using Factory Boy.

Usage:
    from tests.factories import QuoteFactory, PolicyFactory
    
    # Create a quote
    quote = QuoteFactory()
    
    # Create with specific attributes
    quote = QuoteFactory(cargo_value_usd=500000)
    
    # Create with trait
    quote = QuoteFactory(high_risk=True)
    
    # Build without saving
    quote = QuoteFactory.build()
"""

from .quote_factory import QuoteFactory
from .policy_factory import PolicyFactory
from .claim_factory import ClaimFactory
from .customer_factory import CustomerFactory
from .user_factory import UserFactory
from .risk_run_factory import RiskRunFactory
from .model_version_factory import ModelVersionFactory
from .audit_event_factory import AuditEventFactory


__all__ = [
    "QuoteFactory",
    "PolicyFactory",
    "ClaimFactory",
    "CustomerFactory",
    "UserFactory",
    "RiskRunFactory",
    "ModelVersionFactory",
    "AuditEventFactory"
]

__version__ = "1.0.0"
