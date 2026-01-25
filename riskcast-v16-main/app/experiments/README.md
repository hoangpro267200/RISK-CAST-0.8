# A/B Testing Framework & Feature Flags

Framework for pricing experiments, A/B tests, and feature flags.

## Features

### Experiments
- **Experiment definition**: Variants, metrics, targeting, traffic allocation
- **Deterministic assignment**: Hash-based sticky assignment per user
- **Targeting rules**: Customer tier, region, min/max rules
- **Metrics**: Conversion, continuous, count, revenue
- **Statistical analysis**: Frequentist (chi-squared, t-test), Bayesian, power calculations

### Feature Flags
- **Boolean flags**: On/off per flag
- **Percentage rollouts**: Deterministic % of users
- **Targeted flags**: Rules by user context
- **Dependencies**: Flag-on-flag (e.g. `B` requires `A`)

## Usage

### Define and run an experiment

```python
import uuid
from app.experiments import (
    Experiment, Variant, Metric, ExperimentStatus, MetricType,
    ExperimentService, AssignmentService, MetricsCollector, ExperimentTracker,
    StatisticalAnalyzer,
)
from app.database import get_db

db = next(get_db())
svc = ExperimentService(db)
assign = AssignmentService(db)
metrics = MetricsCollector(db)
tracker = ExperimentTracker(db, assign, svc)
analyzer = StatisticalAnalyzer(db)

# Create experiment
exp = Experiment(
    id=str(uuid.uuid4()),
    name="Pricing Test Q1",
    description="Test new pricing algorithm",
    hypothesis="New algorithm increases conversion",
    variants=[
        Variant(id="control", name="Control", weight=0.5, config={}),
        Variant(id="treatment", name="New Pricing", weight=0.5, config={"algorithm": "v2"}),
    ],
    metrics=[
        Metric("conversion", MetricType.CONVERSION, primary=True),
        Metric("revenue_per_user", MetricType.REVENUE),
    ],
    status=ExperimentStatus.DRAFT,
    traffic_percentage=1.0,
    min_sample_size=1000,
)
await svc.create_experiment(exp)
await svc.start_experiment(exp.id)

# Assign user and get variant
variant = await assign.get_assignment(
    exp, user_id="user-123",
    user_context={"customer_tier": "PREMIER", "region": "US"}
)
# variant.config for pricing config, etc.

# Track metrics
await tracker.track("user-123", "conversion", 1.0)
await metrics.track_revenue(exp.id, "user-123", variant.id, "revenue_per_user", Decimal("99.99"))

# Analyze
results = await analyzer.analyze_experiment(exp)
print(results.recommendation, results.winner)
```

### Feature flags

```python
from app.experiments import FeatureFlag, FeatureFlagService, FlagType, feature_flag

ff = FeatureFlagService(db)

# Create
await ff.create_flag(FeatureFlag(
    key="new_pricing_algorithm",
    name="New pricing",
    description="Use v2 pricing",
    flag_type=FlagType.PERCENTAGE,
    percentage=0.2,  # 20% rollout
))
# Update
await ff.update_flag("new_pricing_algorithm", percentage=0.5)

# Check
enabled = await ff.is_enabled("new_pricing_algorithm", user_id="user-123")
```

### Decorator

```python
@feature_flag("new_pricing_algorithm", default=old_premium, fallback=old_premium)
async def calculate_premium(data, _flag_service=None, _user_id=None, _user_context=None):
    ...
```

## DB models

- `experiments`: experiment definition (variants, metrics, targeting)
- `experiment_assignments`: user → variant (unique per experiment)
- `experiment_events`: metric events (value, timestamp)
- `feature_flags`: flag key, type, enabled, percentage, targeting, depends_on

Create tables via Alembic or `Base.metadata.create_all(bind=engine)`.

## Dependencies

- `numpy`, `scipy`: for analysis (optional; falls back to no-op if missing)
- SQLAlchemy, `app.database`, `app.core.logging`

## Acceptance criteria

- [x] Experiment definition
- [x] Variant definition with weights
- [x] Deterministic assignment
- [x] Sticky assignments
- [x] Targeting rules
- [x] Metrics collection
- [x] Conversion tracking
- [x] Frequentist analysis (chi-squared, t-test)
- [x] Bayesian analysis
- [x] Power calculations
- [x] Feature flags
- [x] Percentage rollouts
