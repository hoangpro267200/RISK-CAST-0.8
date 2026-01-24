"""
Data Quality Gateway

CRITICAL: Ensures the system does NOT make production decisions
with low-quality or fallback data without explicit acknowledgment.

This is the "data truth" layer that prevents the system from
appearing to work while actually using fake/default data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from enum import Enum
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DataQualityLevel(Enum):
    """Data quality levels for gateway decisions."""
    EXCELLENT = "EXCELLENT"     # Real-time, verified
    GOOD = "GOOD"              # Cached, recent
    ACCEPTABLE = "ACCEPTABLE"  # Stale but usable
    POOR = "POOR"              # Very stale or partial
    FALLBACK = "FALLBACK"      # Using defaults
    UNAVAILABLE = "UNAVAILABLE" # No data at all


class DecisionType(Enum):
    """Types of decisions requiring data quality checks."""
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    INSURANCE_QUOTE = "INSURANCE_QUOTE"
    POLICY_BINDING = "POLICY_BINDING"
    PARAMETRIC_TRIGGER = "PARAMETRIC_TRIGGER"
    CLAIM_ADJUDICATION = "CLAIM_ADJUDICATION"
    ANALYTICS = "ANALYTICS"  # Can use lower quality


@dataclass
class DataSource:
    """Represents a data source with quality info."""
    source_name: str
    source_type: str
    quality_level: DataQualityLevel
    data_timestamp: Optional[datetime]
    fetched_at: datetime
    data_hash: Optional[str]
    is_fallback: bool
    fallback_reason: Optional[str]
    confidence: float  # 0-1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "source_name": self.source_name,
            "source_type": self.source_type,
            "quality_level": self.quality_level.value,
            "data_timestamp": self.data_timestamp.isoformat() if self.data_timestamp else None,
            "fetched_at": self.fetched_at.isoformat(),
            "data_hash": self.data_hash,
            "is_fallback": self.is_fallback,
            "fallback_reason": self.fallback_reason,
            "confidence": self.confidence,
        }


@dataclass
class DataQualityReport:
    """Report on data quality for a decision."""
    decision_type: DecisionType
    overall_quality: DataQualityLevel
    overall_confidence: float
    sources: List[DataSource]
    missing_sources: List[str]
    fallback_sources: List[str]
    warnings: List[str]
    can_proceed: bool
    requires_acknowledgment: bool
    block_reason: Optional[str]
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision_type": self.decision_type.value,
            "overall_quality": self.overall_quality.value,
            "overall_confidence": self.overall_confidence,
            "sources": [s.to_dict() for s in self.sources],
            "missing_sources": self.missing_sources,
            "fallback_sources": self.fallback_sources,
            "warnings": self.warnings,
            "can_proceed": self.can_proceed,
            "requires_acknowledgment": self.requires_acknowledgment,
            "block_reason": self.block_reason,
            "generated_at": self.generated_at.isoformat(),
        }


class DataQualityGateway:
    """
    Gateway that enforces data quality requirements for different decisions.
    
    CRITICAL: This prevents the system from silently using fake data.
    """
    
    # Minimum quality requirements by decision type
    QUALITY_REQUIREMENTS = {
        DecisionType.POLICY_BINDING: {
            "min_quality": DataQualityLevel.GOOD,
            "required_sources": {"weather", "port", "carrier"},
            "allow_fallback": False,
            "min_confidence": 0.8
        },
        DecisionType.INSURANCE_QUOTE: {
            "min_quality": DataQualityLevel.ACCEPTABLE,
            "required_sources": {"weather", "port", "carrier"},
            "allow_fallback": False,
            "min_confidence": 0.7
        },
        DecisionType.RISK_ASSESSMENT: {
            "min_quality": DataQualityLevel.ACCEPTABLE,
            "required_sources": {"weather", "port"},
            "allow_fallback": True,  # With warning
            "min_confidence": 0.6
        },
        DecisionType.PARAMETRIC_TRIGGER: {
            "min_quality": DataQualityLevel.EXCELLENT,
            "required_sources": {"weather", "oracle"},
            "allow_fallback": False,  # NEVER for payouts
            "min_confidence": 0.9,
            "require_corroboration": True
        },
        DecisionType.CLAIM_ADJUDICATION: {
            "min_quality": DataQualityLevel.GOOD,
            "required_sources": {"evidence"},
            "allow_fallback": False,
            "min_confidence": 0.8
        },
        DecisionType.ANALYTICS: {
            "min_quality": DataQualityLevel.POOR,  # Can use historical
            "required_sources": set(),
            "allow_fallback": True,
            "min_confidence": 0.5
        }
    }
    
    # Quality level ordering
    QUALITY_ORDER = {
        DataQualityLevel.EXCELLENT: 5,
        DataQualityLevel.GOOD: 4,
        DataQualityLevel.ACCEPTABLE: 3,
        DataQualityLevel.POOR: 2,
        DataQualityLevel.FALLBACK: 1,
        DataQualityLevel.UNAVAILABLE: 0
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_data_quality(
        self,
        decision_type: DecisionType,
        data_sources: List[DataSource]
    ) -> DataQualityReport:
        """
        Check if data quality is sufficient for the decision type.
        
        This is the CRITICAL gate that prevents bad data from being used.
        """
        requirements = self.QUALITY_REQUIREMENTS[decision_type]
        
        now = datetime.utcnow()
        warnings = []
        
        # Check for missing required sources
        source_names = {s.source_type for s in data_sources}
        required = requirements["required_sources"]
        missing = required - source_names
        
        # Check for fallback sources
        fallback_sources = [
            s.source_name for s in data_sources 
            if s.is_fallback
        ]
        
        # Calculate overall quality
        if not data_sources:
            overall_quality = DataQualityLevel.UNAVAILABLE
            overall_confidence = 0.0
        else:
            # Lowest quality determines overall
            min_quality_order = min(
                self.QUALITY_ORDER[s.quality_level] 
                for s in data_sources
            )
            overall_quality = next(
                level for level, order in self.QUALITY_ORDER.items()
                if order == min_quality_order
            )
            
            # Average confidence
            overall_confidence = sum(s.confidence for s in data_sources) / len(data_sources)
        
        # Determine if we can proceed
        can_proceed = True
        requires_acknowledgment = False
        block_reason = None
        
        # Check 1: Missing required sources
        if missing:
            if decision_type == DecisionType.ANALYTICS:
                warnings.append(f"Missing data sources: {missing}")
            else:
                can_proceed = False
                block_reason = f"Missing required data sources: {missing}"
        
        # Check 2: Quality level
        min_required_quality = requirements["min_quality"]
        if self.QUALITY_ORDER[overall_quality] < self.QUALITY_ORDER[min_required_quality]:
            if requirements["allow_fallback"]:
                requires_acknowledgment = True
                warnings.append(
                    f"Data quality ({overall_quality.value}) below required "
                    f"({min_required_quality.value}). Proceed with caution."
                )
            else:
                can_proceed = False
                block_reason = (
                    f"Data quality ({overall_quality.value}) below minimum "
                    f"required ({min_required_quality.value}) for {decision_type.value}"
                )
        
        # Check 3: Fallback data
        if fallback_sources:
            if not requirements["allow_fallback"]:
                can_proceed = False
                block_reason = (
                    f"Fallback data not allowed for {decision_type.value}. "
                    f"Fallback sources: {fallback_sources}"
                )
            else:
                requires_acknowledgment = True
                warnings.append(f"Using fallback data for: {fallback_sources}")
        
        # Check 4: Confidence threshold
        if overall_confidence < requirements["min_confidence"]:
            if decision_type in [DecisionType.POLICY_BINDING, DecisionType.PARAMETRIC_TRIGGER]:
                can_proceed = False
                block_reason = (
                    f"Confidence ({overall_confidence:.2f}) below minimum "
                    f"({requirements['min_confidence']}) for {decision_type.value}"
                )
            else:
                requires_acknowledgment = True
                warnings.append(
                    f"Low confidence ({overall_confidence:.2f}). "
                    f"Minimum recommended: {requirements['min_confidence']}"
                )
        
        # Check 5: Corroboration for parametric triggers
        if requirements.get("require_corroboration"):
            unique_sources = len(set(s.source_name for s in data_sources if not s.is_fallback))
            if unique_sources < 2:
                can_proceed = False
                block_reason = (
                    f"Parametric trigger requires corroboration from multiple sources. "
                    f"Found: {unique_sources}"
                )
        
        return DataQualityReport(
            decision_type=decision_type,
            overall_quality=overall_quality,
            overall_confidence=overall_confidence,
            sources=data_sources,
            missing_sources=list(missing),
            fallback_sources=fallback_sources,
            warnings=warnings,
            can_proceed=can_proceed,
            requires_acknowledgment=requires_acknowledgment,
            block_reason=block_reason,
            generated_at=now
        )
    
    def enforce_quality(
        self,
        decision_type: DecisionType,
        data_sources: List[DataSource],
        user_acknowledged: bool = False
    ) -> tuple[bool, Optional[str], DataQualityReport]:
        """
        Enforce data quality requirements.
        
        Returns (can_proceed, error_message, report).
        
        CRITICAL: This method should be called before ANY production decision.
        """
        report = self.check_data_quality(decision_type, data_sources)
        
        if not report.can_proceed:
            self.logger.warning(
                f"Data quality gate BLOCKED {decision_type.value}: {report.block_reason}"
            )
            return False, report.block_reason, report
        
        if report.requires_acknowledgment and not user_acknowledged:
            self.logger.info(
                f"Data quality gate requires acknowledgment for {decision_type.value}"
            )
            return False, "User acknowledgment required for low-quality data", report
        
        if report.warnings:
            self.logger.info(
                f"Data quality warnings for {decision_type.value}: {report.warnings}"
            )
        
        return True, None, report


# Singleton instance
data_quality_gateway = DataQualityGateway()


def require_data_quality(
    decision_type: DecisionType,
    min_quality: Optional[DataQualityLevel] = None
):
    """
    Decorator to enforce data quality on service methods.
    
    Usage:
        @require_data_quality(DecisionType.POLICY_BINDING)
        async def bind_policy(self, ...):
            ...
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            # Get data sources from the service
            data_sources = await self._get_data_sources(*args, **kwargs)
            
            can_proceed, error, report = data_quality_gateway.enforce_quality(
                decision_type,
                data_sources,
                user_acknowledged=kwargs.get("acknowledge_low_quality", False)
            )
            
            if not can_proceed:
                raise DataQualityError(error, report)
            
            # Attach report to kwargs for logging
            kwargs["_data_quality_report"] = report
            
            return await func(self, *args, **kwargs)
        
        return wrapper
    return decorator


class DataQualityError(Exception):
    """Raised when data quality is insufficient for the operation."""
    
    def __init__(self, message: str, report: DataQualityReport):
        super().__init__(message)
        self.report = report
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": str(self),
            "decision_type": self.report.decision_type.value,
            "overall_quality": self.report.overall_quality.value,
            "overall_confidence": self.report.overall_confidence,
            "missing_sources": self.report.missing_sources,
            "fallback_sources": self.report.fallback_sources,
            "warnings": self.report.warnings,
            "block_reason": self.report.block_reason
        }
