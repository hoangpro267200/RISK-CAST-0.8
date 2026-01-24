"""
Data Quality Module

Ensures the system does NOT make production decisions with low-quality
or fallback data without explicit acknowledgment.
"""

from app.core.data_quality.gateway import (
    DataQualityGateway,
    DataQualityLevel,
    DecisionType,
    DataSource as GatewayDataSource,
    DataQualityReport,
    DataQualityError,
    data_quality_gateway,
    require_data_quality,
)

from app.core.data_quality.validation import (
    DataValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationCategory,
    OutlierDetector,
    get_data_validator,
)

__all__ = [
    "DataQualityGateway",
    "DataQualityLevel",
    "DecisionType",
    "GatewayDataSource",
    "DataQualityReport",
    "DataQualityError",
    "data_quality_gateway",
    "require_data_quality",
    "DataValidator",
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    "ValidationCategory",
    "OutlierDetector",
    "get_data_validator",
]
