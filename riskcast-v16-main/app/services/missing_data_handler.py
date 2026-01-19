"""
RISKCAST Missing Data Handler
==============================
Apply risk penalties for missing or low-quality data.

Rationale:
- Incomplete data = higher uncertainty = higher risk
- Prevents gaming via strategic data omission
- Incentivizes complete, accurate submissions

Author: RISKCAST Team
Version: 2.0
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FieldCategory(Enum):
    """Category of input field by importance."""
    CRITICAL = "critical"         # Essential - major penalty if missing
    IMPORTANT = "important"       # High value - moderate penalty
    VALUABLE = "valuable"         # Adds precision - small penalty
    OPTIONAL = "optional"         # Nice to have - no penalty


@dataclass
class FieldDefinition:
    """Definition of an input field."""
    name: str
    category: FieldCategory
    penalty_points: float  # Points added to risk if missing
    description: str
    fallback_value: Optional[Any] = None


@dataclass
class MissingDataPenalty:
    """Result of missing data analysis."""
    total_penalty_points: float
    missing_fields: List[str]
    field_penalties: Dict[str, float]
    data_completeness: float  # 0-1
    confidence_adjustment: float  # Multiplier for uncertainty
    recommendation: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class MissingDataPenaltyCalculator:
    """
    Calculate risk penalties for missing or incomplete data.
    
    Implements tiered penalty system:
    - Critical fields: 15 points
    - Important fields: 8 points
    - Valuable fields: 5 points
    - Optional fields: 2 points
    
    Maximum total penalty: 30 points (capped)
    """
    
    # Field definitions with penalties
    FIELD_DEFINITIONS: List[FieldDefinition] = [
        # Critical fields - 15 points each
        FieldDefinition(
            name='cargo_type',
            category=FieldCategory.CRITICAL,
            penalty_points=15,
            description="Type of cargo (determines sensitivity/handling)"
        ),
        FieldDefinition(
            name='cargo_value',
            category=FieldCategory.CRITICAL,
            penalty_points=15,
            description="Declared cargo value (determines financial exposure)"
        ),
        FieldDefinition(
            name='route',
            category=FieldCategory.CRITICAL,
            penalty_points=12,
            description="Trade route (determines geographic risk)"
        ),
        FieldDefinition(
            name='transport_mode',
            category=FieldCategory.CRITICAL,
            penalty_points=12,
            description="Mode of transport (sea, air, rail, road)"
        ),
        
        # Important fields - 8 points each
        FieldDefinition(
            name='carrier',
            category=FieldCategory.IMPORTANT,
            penalty_points=8,
            description="Carrier name/ID (determines carrier reliability)"
        ),
        FieldDefinition(
            name='etd',
            category=FieldCategory.IMPORTANT,
            penalty_points=8,
            description="Estimated departure date (determines seasonality)"
        ),
        FieldDefinition(
            name='eta',
            category=FieldCategory.IMPORTANT,
            penalty_points=8,
            description="Estimated arrival date"
        ),
        FieldDefinition(
            name='incoterm',
            category=FieldCategory.IMPORTANT,
            penalty_points=8,
            description="Incoterm (determines responsibility split)"
        ),
        FieldDefinition(
            name='transit_time',
            category=FieldCategory.IMPORTANT,
            penalty_points=8,
            description="Expected transit time in days",
            fallback_value=30.0
        ),
        
        # Valuable fields - 5 points each
        FieldDefinition(
            name='carrier_rating',
            category=FieldCategory.VALUABLE,
            penalty_points=5,
            description="Carrier performance rating",
            fallback_value=5.0
        ),
        FieldDefinition(
            name='weather_risk',
            category=FieldCategory.VALUABLE,
            penalty_points=5,
            description="Known weather risk at departure time"
        ),
        FieldDefinition(
            name='port_risk',
            category=FieldCategory.VALUABLE,
            penalty_points=5,
            description="Port congestion/risk index"
        ),
        FieldDefinition(
            name='container_match',
            category=FieldCategory.VALUABLE,
            penalty_points=5,
            description="Container type match score",
            fallback_value=7.0
        ),
        FieldDefinition(
            name='packaging_quality',
            category=FieldCategory.VALUABLE,
            penalty_points=5,
            description="Packaging quality rating",
            fallback_value=7.0
        ),
        
        # Optional fields - 2 points each
        FieldDefinition(
            name='ESG_score',
            category=FieldCategory.OPTIONAL,
            penalty_points=2,
            description="Environmental/Social/Governance score"
        ),
        FieldDefinition(
            name='insurance_coverage',
            category=FieldCategory.OPTIONAL,
            penalty_points=2,
            description="Existing insurance coverage details"
        ),
        FieldDefinition(
            name='special_handling',
            category=FieldCategory.OPTIONAL,
            penalty_points=2,
            description="Special handling requirements"
        ),
        FieldDefinition(
            name='hazmat_class',
            category=FieldCategory.OPTIONAL,
            penalty_points=2,
            description="Hazmat classification if applicable"
        ),
        FieldDefinition(
            name='previous_incidents',
            category=FieldCategory.OPTIONAL,
            penalty_points=2,
            description="History of previous incidents"
        ),
    ]
    
    # Maximum penalty cap
    MAX_PENALTY = 30.0
    
    def __init__(self):
        self._field_map = {f.name: f for f in self.FIELD_DEFINITIONS}
    
    def calculate_penalty(self, request_data: Dict[str, Any]) -> MissingDataPenalty:
        """
        Calculate risk score penalty for missing data.
        
        Args:
            request_data: Input shipment data
            
        Returns:
            MissingDataPenalty with penalty details
        """
        total_penalty = 0.0
        missing_fields = []
        field_penalties = {}
        
        # Check each defined field
        for field_def in self.FIELD_DEFINITIONS:
            value = request_data.get(field_def.name)
            
            if self._is_missing(value):
                missing_fields.append(field_def.name)
                field_penalties[field_def.name] = field_def.penalty_points
                total_penalty += field_def.penalty_points
        
        # Cap total penalty
        total_penalty = min(total_penalty, self.MAX_PENALTY)
        
        # Calculate data completeness (only for defined fields)
        total_fields = len(self.FIELD_DEFINITIONS)
        complete_fields = total_fields - len(missing_fields)
        data_completeness = complete_fields / total_fields
        
        # Confidence adjustment (lower completeness = lower confidence)
        # This affects uncertainty quantification
        confidence_adjustment = 0.5 + 0.5 * data_completeness
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            missing_fields, 
            total_penalty,
            data_completeness
        )
        
        return MissingDataPenalty(
            total_penalty_points=total_penalty,
            missing_fields=missing_fields,
            field_penalties=field_penalties,
            data_completeness=data_completeness,
            confidence_adjustment=confidence_adjustment,
            recommendation=recommendation
        )
    
    def _is_missing(self, value: Any) -> bool:
        """Check if a value is missing or empty."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == '':
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False
    
    def _generate_recommendation(
        self,
        missing_fields: List[str],
        penalty: float,
        completeness: float
    ) -> str:
        """Generate recommendation based on missing data."""
        
        if completeness >= 0.9:
            return "Data quality is excellent. No action required."
        
        if completeness >= 0.7:
            return f"Good data quality. Consider providing: {', '.join(missing_fields[:3])}"
        
        if completeness >= 0.5:
            critical_missing = [
                f for f in missing_fields 
                if self._field_map.get(f, FieldDefinition(
                    name=f, category=FieldCategory.OPTIONAL, 
                    penalty_points=0, description=""
                )).category == FieldCategory.CRITICAL
            ]
            
            if critical_missing:
                return (
                    f"IMPORTANT: Missing critical fields: {', '.join(critical_missing)}. "
                    f"Penalty of {penalty:.1f} points applied. "
                    "Provide these fields for accurate assessment."
                )
            else:
                return (
                    f"Moderate data quality. {len(missing_fields)} fields missing. "
                    f"Penalty: {penalty:.1f} points."
                )
        
        return (
            f"LOW DATA QUALITY: {len(missing_fields)} fields missing. "
            f"Maximum penalty of {penalty:.1f} points applied. "
            "Assessment confidence is significantly reduced."
        )
    
    def apply_fallbacks(self, request_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply fallback values for missing fields where available.
        
        Args:
            request_data: Input shipment data
            
        Returns:
            Tuple of (modified data, list of fields with fallbacks applied)
        """
        modified = request_data.copy()
        fallbacks_applied = []
        
        for field_def in self.FIELD_DEFINITIONS:
            if field_def.fallback_value is not None:
                if self._is_missing(request_data.get(field_def.name)):
                    modified[field_def.name] = field_def.fallback_value
                    fallbacks_applied.append(field_def.name)
        
        return modified, fallbacks_applied
    
    def get_field_importance(self, field_name: str) -> Optional[FieldCategory]:
        """Get the importance category of a field."""
        field_def = self._field_map.get(field_name)
        return field_def.category if field_def else None
    
    def get_all_critical_fields(self) -> List[str]:
        """Get list of all critical fields."""
        return [
            f.name for f in self.FIELD_DEFINITIONS 
            if f.category == FieldCategory.CRITICAL
        ]


# Integration function for API
def calculate_missing_data_penalty(request_data: Dict[str, Any]) -> Dict:
    """
    Calculate missing data penalty for a request.
    
    Args:
        request_data: Shipment data dictionary
        
    Returns:
        Penalty result as dictionary
    """
    calculator = MissingDataPenaltyCalculator()
    penalty = calculator.calculate_penalty(request_data)
    return penalty.to_dict()


def apply_missing_data_to_risk(
    base_risk_score: float,
    request_data: Dict[str, Any]
) -> Tuple[float, Dict]:
    """
    Apply missing data penalty to a risk score.
    
    Args:
        base_risk_score: Original risk score (0-100)
        request_data: Shipment data
        
    Returns:
        Tuple of (adjusted score, penalty details)
    """
    calculator = MissingDataPenaltyCalculator()
    penalty = calculator.calculate_penalty(request_data)
    
    adjusted_score = min(
        base_risk_score + penalty.total_penalty_points,
        100.0
    )
    
    return adjusted_score, penalty.to_dict()
