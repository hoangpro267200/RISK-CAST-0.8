"""
Recommendation Engine Module

Provides intelligent recommendations for:
- Coverage selection and extensions
- Pricing optimization
- Route optimization
"""

from app.ml.recommendations.coverage_recommender import (
    CoverageRecommender,
    CoverageRecommendation,
    DeductibleRecommendation,
    CoverageType,
    CoverageExtension,
)

from app.ml.recommendations.pricing_recommender import (
    PricingRecommender,
    PricingRecommendation,
    DiscountRecommendation,
)

from app.ml.recommendations.route_recommender import (
    RouteRecommender,
    RouteRecommendation,
    RouteOption,
)

__all__ = [
    "CoverageRecommender",
    "CoverageRecommendation",
    "DeductibleRecommendation",
    "CoverageType",
    "CoverageExtension",
    "PricingRecommender",
    "PricingRecommendation",
    "DiscountRecommendation",
    "RouteRecommender",
    "RouteRecommendation",
    "RouteOption",
]
