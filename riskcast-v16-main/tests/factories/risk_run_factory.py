"""
Risk Run Factory
"""

import factory
from factory import fuzzy
from datetime import datetime
from decimal import Decimal
import random
import hashlib
import json

try:
    from app.models.risk_run import RiskRun
except ImportError:
    RiskRun = None

from tests.factories.base import BaseFactory, Generators


class RiskRunFactory(BaseFactory):
    """Factory for generating RiskRun test data."""
    
    class Meta:
        model = RiskRun
        skip_postgeneration_if_model_is_none = True
    
    # Risk scores
    overall_risk_score = factory.LazyFunction(Generators.random_risk_score)
    risk_grade = factory.LazyAttribute(
        lambda o: Generators.risk_grade_from_score(o.overall_risk_score)
    )
    
    # Layer scores (13 layers)
    layer_scores_json = factory.LazyFunction(lambda: {
        "weather": round(random.uniform(0.1, 0.9), 2),
        "port_congestion": round(random.uniform(0.1, 0.9), 2),
        "carrier_reliability": round(random.uniform(0.1, 0.9), 2),
        "seasonality": round(random.uniform(0.1, 0.9), 2),
        "geopolitical": round(random.uniform(0.1, 0.9), 2),
        "cargo_specific": round(random.uniform(0.1, 0.9), 2),
        "route_difficulty": round(random.uniform(0.1, 0.9), 2),
        "insurance_history": round(random.uniform(0.1, 0.9), 2),
        "compliance": round(random.uniform(0.1, 0.9), 2),
        "market_volatility": round(random.uniform(0.1, 0.9), 2),
        "climate": round(random.uniform(0.1, 0.9), 2),
        "infrastructure": round(random.uniform(0.1, 0.9), 2),
        "piracy": round(random.uniform(0.1, 0.9), 2)
    })
    
    # Loss metrics
    expected_loss_pct = factory.LazyAttribute(
        lambda o: round(o.overall_risk_score * 0.05, 4)
    )
    var_95 = factory.LazyAttribute(
        lambda o: round(o.expected_loss_pct * 2, 4)
    )
    var_99 = factory.LazyAttribute(
        lambda o: round(o.expected_loss_pct * 3, 4)
    )
    cvar_95 = factory.LazyAttribute(
        lambda o: round(o.var_95 * 1.5, 4)
    )
    cvar_99 = factory.LazyAttribute(
        lambda o: round(o.var_99 * 1.5, 4)
    )
    
    # Inputs
    cargo_value_usd = factory.LazyFunction(lambda: Generators.random_cargo_value())
    origin_port = factory.LazyFunction(Generators.random_port)
    destination_port = factory.LazyFunction(Generators.random_port)
    cargo_type = factory.LazyFunction(Generators.random_cargo_type)
    departure_date = factory.LazyFunction(lambda: Generators.future_date(7, 30))
    
    # Input hash (for caching)
    input_hash = factory.LazyAttribute(
        lambda o: hashlib.sha256(
            json.dumps({
                "origin": o.origin_port,
                "destination": o.destination_port,
                "cargo_type": o.cargo_type,
                "value": str(o.cargo_value_usd),
                "date": str(o.departure_date)
            }, sort_keys=True).encode()
        ).hexdigest()
    )
    
    # Model version
    model_version_id = factory.LazyFunction(
        lambda: f"model-v{random.randint(1, 10)}"
    )
    model_version_hash = factory.LazyFunction(
        lambda: hashlib.sha256(f"model-{random.randint(1, 1000)}".encode()).hexdigest()[:16]
    )
    
    # Data quality
    data_quality_score = fuzzy.FuzzyFloat(0.7, 1.0)
    data_quality_level = factory.LazyAttribute(
        lambda o: "HIGH" if o.data_quality_score > 0.9 else "MEDIUM" if o.data_quality_score > 0.7 else "LOW"
    )
    
    # Confidence metrics
    confidence_score = fuzzy.FuzzyFloat(0.6, 0.95)
    
    # Recommendations
    recommendations_json = factory.LazyFunction(lambda: {
        "deductible": "Consider 1% deductible",
        "coverage": "All-risks coverage recommended",
        "mitigation": ["Use approved carrier", "Track shipment real-time"]
    })
    
    # Timestamps
    created_at = factory.LazyFunction(datetime.utcnow)
    computation_time_ms = fuzzy.FuzzyInteger(50, 500)
    
    # Relationships
    quote_id = factory.LazyFunction(
        lambda: f"quote-{random.randint(1000, 9999)}"
    )
    tenant_id = factory.LazyFunction(
        lambda: f"tenant-{random.randint(100, 999)}"
    )
    
    class Params:
        """Traits for different risk scenarios."""
        
        # High risk run
        high_risk = factory.Trait(
            overall_risk_score=factory.LazyFunction(lambda: round(random.uniform(0.7, 0.95), 2)),
            risk_grade="D",
            expected_loss_pct=factory.LazyFunction(lambda: round(random.uniform(0.03, 0.06), 4)),
            layer_scores_json=factory.LazyFunction(lambda: {
                "weather": round(random.uniform(0.7, 0.95), 2),
                "port_congestion": round(random.uniform(0.7, 0.95), 2),
                "carrier_reliability": round(random.uniform(0.7, 0.95), 2),
                "seasonality": round(random.uniform(0.7, 0.95), 2),
                "geopolitical": round(random.uniform(0.7, 0.95), 2),
                "cargo_specific": round(random.uniform(0.7, 0.95), 2),
                "route_difficulty": round(random.uniform(0.7, 0.95), 2),
                "insurance_history": round(random.uniform(0.7, 0.95), 2),
                "compliance": round(random.uniform(0.7, 0.95), 2),
                "market_volatility": round(random.uniform(0.7, 0.95), 2),
                "climate": round(random.uniform(0.7, 0.95), 2),
                "infrastructure": round(random.uniform(0.7, 0.95), 2),
                "piracy": round(random.uniform(0.7, 0.95), 2)
            })
        )
        
        # Low risk run
        low_risk = factory.Trait(
            overall_risk_score=factory.LazyFunction(lambda: round(random.uniform(0.05, 0.20), 2)),
            risk_grade="A",
            expected_loss_pct=factory.LazyFunction(lambda: round(random.uniform(0.0005, 0.001), 4)),
            layer_scores_json=factory.LazyFunction(lambda: {
                "weather": round(random.uniform(0.05, 0.25), 2),
                "port_congestion": round(random.uniform(0.05, 0.25), 2),
                "carrier_reliability": round(random.uniform(0.05, 0.25), 2),
                "seasonality": round(random.uniform(0.05, 0.25), 2),
                "geopolitical": round(random.uniform(0.05, 0.25), 2),
                "cargo_specific": round(random.uniform(0.05, 0.25), 2),
                "route_difficulty": round(random.uniform(0.05, 0.25), 2),
                "insurance_history": round(random.uniform(0.05, 0.25), 2),
                "compliance": round(random.uniform(0.05, 0.25), 2),
                "market_volatility": round(random.uniform(0.05, 0.25), 2),
                "climate": round(random.uniform(0.05, 0.25), 2),
                "infrastructure": round(random.uniform(0.05, 0.25), 2),
                "piracy": round(random.uniform(0.05, 0.25), 2)
            })
        )
        
        # Weather risk dominant
        weather_risk = factory.Trait(
            layer_scores_json=factory.LazyFunction(lambda: {
                **{layer: round(random.uniform(0.1, 0.4), 2) for layer in [
                    "port_congestion", "carrier_reliability", "seasonality",
                    "geopolitical", "cargo_specific", "route_difficulty",
                    "insurance_history", "compliance", "market_volatility",
                    "climate", "infrastructure", "piracy"
                ]},
                "weather": round(random.uniform(0.7, 0.95), 2)
            })
        )
        
        # Poor data quality
        poor_data_quality = factory.Trait(
            data_quality_score=fuzzy.FuzzyFloat(0.4, 0.7),
            data_quality_level="LOW",
            confidence_score=fuzzy.FuzzyFloat(0.3, 0.6)
        )
        
        # Monte Carlo simulation included
        with_monte_carlo = factory.Trait(
            monte_carlo_runs=10000,
            monte_carlo_results_json=factory.LazyFunction(lambda: {
                "mean_loss": round(random.uniform(0.01, 0.05), 4),
                "std_dev": round(random.uniform(0.005, 0.02), 4),
                "percentiles": {
                    "p50": round(random.uniform(0.005, 0.02), 4),
                    "p75": round(random.uniform(0.015, 0.03), 4),
                    "p90": round(random.uniform(0.025, 0.04), 4),
                    "p95": round(random.uniform(0.03, 0.05), 4),
                    "p99": round(random.uniform(0.04, 0.06), 4)
                }
            })
        )
