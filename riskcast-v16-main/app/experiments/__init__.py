"""
A/B Testing Framework & Feature Flags

Features:
1. Experiment definition and variant assignment
2. Metrics collection and statistical analysis
3. Feature flags with percentage rollouts
"""

from app.experiments.framework import (
    Experiment,
    Variant,
    Metric,
    ExperimentStatus,
    MetricType,
    ExperimentService,
    ExperimentModel,
    ExperimentAssignmentModel,
    ExperimentEventModel,
)
from app.experiments.assignment import AssignmentService
from app.experiments.metrics import MetricsCollector, ExperimentTracker
from app.experiments.analysis import (
    StatisticalAnalyzer,
    PowerCalculator,
    VariantStats,
    ComparisonResult,
    ExperimentResults,
)
from app.experiments.feature_flags import (
    FeatureFlag,
    FeatureFlagService,
    FeatureFlagModel,
    FlagType,
    feature_flag,
)

__all__ = [
    "Experiment",
    "Variant",
    "Metric",
    "ExperimentStatus",
    "MetricType",
    "ExperimentService",
    "ExperimentModel",
    "ExperimentAssignmentModel",
    "ExperimentEventModel",
    "AssignmentService",
    "MetricsCollector",
    "ExperimentTracker",
    "StatisticalAnalyzer",
    "PowerCalculator",
    "VariantStats",
    "ComparisonResult",
    "ExperimentResults",
    "FeatureFlag",
    "FeatureFlagService",
    "FeatureFlagModel",
    "FlagType",
    "feature_flag",
]
