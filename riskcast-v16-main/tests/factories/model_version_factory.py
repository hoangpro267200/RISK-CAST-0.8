"""
Model Version Factory
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
from decimal import Decimal
import random
import hashlib
import json

try:
    from app.models.model_version import ModelVersion
except ImportError:
    ModelVersion = None

from tests.factories.base import BaseFactory


class ModelVersionFactory(BaseFactory):
    """Factory for generating ModelVersion test data."""
    
    class Meta:
        model = ModelVersion
        skip_postgeneration_if_model_is_none = True
    
    # Identifiers
    version_number = factory.Sequence(lambda n: f"v{n+1}.0.0")
    name = factory.LazyAttribute(lambda o: f"Risk Model {o.version_number}")
    description = factory.Faker('sentence', nb_words=10)
    
    # Status
    status = "DRAFT"
    
    # Model configuration
    config_json = factory.LazyFunction(lambda: {
        "layers": [
            "weather", "port_congestion", "carrier_reliability",
            "seasonality", "geopolitical", "cargo_specific",
            "route_difficulty", "insurance_history", "compliance",
            "market_volatility", "climate", "infrastructure", "piracy"
        ],
        "weights": {
            "weather": 0.15,
            "port_congestion": 0.10,
            "carrier_reliability": 0.12,
            "seasonality": 0.08,
            "geopolitical": 0.10,
            "cargo_specific": 0.08,
            "route_difficulty": 0.08,
            "insurance_history": 0.07,
            "compliance": 0.06,
            "market_volatility": 0.06,
            "climate": 0.04,
            "infrastructure": 0.03,
            "piracy": 0.03
        },
        "monte_carlo": {
            "enabled": True,
            "runs": 10000,
            "confidence_level": 0.95
        }
    })
    
    # Performance metrics
    accuracy = fuzzy.FuzzyFloat(0.75, 0.95)
    mae = fuzzy.FuzzyFloat(0.02, 0.08)
    rmse = fuzzy.FuzzyFloat(0.03, 0.10)
    r2_score = fuzzy.FuzzyFloat(0.70, 0.92)
    
    # Training info
    training_data_size = fuzzy.FuzzyInteger(10000, 100000)
    validation_split = Decimal("0.2")
    training_started_at = factory.LazyFunction(
        lambda: datetime.utcnow() - timedelta(hours=random.randint(24, 168))
    )
    training_completed_at = factory.LazyAttribute(
        lambda o: o.training_started_at + timedelta(hours=random.randint(1, 12))
    )
    
    # Hash (immutability)
    immutable_hash = factory.LazyFunction(
        lambda: hashlib.sha256(f"model-{random.randint(1, 100000)}".encode()).hexdigest()
    )
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)
    created_by = factory.LazyFunction(
        lambda: f"user-{random.randint(100, 999)}"
    )
    
    # Relationships
    base_version_id = None  # Can be set to create derived versions
    
    class Params:
        """Traits for different model states."""
        
        # Published model
        published = factory.Trait(
            status="PUBLISHED",
            published_at=factory.LazyFunction(datetime.utcnow),
            published_by=factory.LazyFunction(
                lambda: f"user-{random.randint(100, 999)}"
            ),
            immutable_hash=factory.LazyFunction(
                lambda: hashlib.sha256(f"model-pub-{random.randint(1, 100000)}".encode()).hexdigest()
            )
        )
        
        # Active model (in production)
        active = factory.Trait(
            status="ACTIVE",
            published_at=factory.LazyFunction(datetime.utcnow),
            activated_at=factory.LazyFunction(datetime.utcnow),
            is_active=True
        )
        
        # Archived model
        archived = factory.Trait(
            status="ARCHIVED",
            archived_at=factory.LazyFunction(datetime.utcnow),
            archived_by=factory.LazyFunction(
                lambda: f"user-{random.randint(100, 999)}"
            ),
            archive_reason="Superseded by newer version"
        )
        
        # High performance model
        high_performance = factory.Trait(
            accuracy=fuzzy.FuzzyFloat(0.90, 0.98),
            mae=fuzzy.FuzzyFloat(0.01, 0.03),
            rmse=fuzzy.FuzzyFloat(0.015, 0.04),
            r2_score=fuzzy.FuzzyFloat(0.88, 0.96)
        )
        
        # Beta model
        beta = factory.Trait(
            status="BETA",
            beta_started_at=factory.LazyFunction(datetime.utcnow),
            beta_testers=factory.LazyFunction(
                lambda: [f"user-{i}" for i in range(random.randint(3, 10))]
            )
        )
        
        # Failed training
        failed = factory.Trait(
            status="FAILED",
            training_error="Insufficient training data quality",
            training_started_at=factory.LazyFunction(datetime.utcnow),
            training_failed_at=factory.LazyFunction(datetime.utcnow)
        )
