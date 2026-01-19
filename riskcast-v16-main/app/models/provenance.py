"""
RISKCAST Input Provenance Tracking
===================================
Track the source, validation status, and audit trail of every input field.

Required for:
1. Insurance underwriting compliance
2. Fraud detection and prevention
3. Regulatory audits
4. Data quality assessment

Author: RISKCAST Team
Version: 2.0
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class VerificationStatus(Enum):
    """Status of input verification."""
    UNVERIFIED = "unverified"       # Raw user input, not checked
    VERIFIED = "verified"           # Confirmed via external source
    SUSPICIOUS = "suspicious"       # Failed validation checks
    INFERRED = "inferred"           # Computed/derived value
    STALE = "stale"                 # Verified but outdated


class DataSource(Enum):
    """Source of input data."""
    USER_INPUT = "user_input"           # Manual user entry
    API_INTEGRATION = "api"             # External API
    DATABASE = "verified_database"       # Verified internal DB
    THIRD_PARTY = "third_party"         # Third-party data provider
    INFERRED = "inferred"               # Computed from other fields
    HISTORICAL = "historical"           # From past shipments
    DEFAULT = "default"                 # System default value


@dataclass
class FieldProvenance:
    """Provenance record for a single input field."""
    field_name: str
    field_value: Any
    source: DataSource
    verification_status: VerificationStatus
    confidence_score: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    verification_method: Optional[str] = None
    cross_check_results: Optional[Dict] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/API."""
        return {
            'field_name': self.field_name,
            'field_value': str(self.field_value),
            'source': self.source.value,
            'verification_status': self.verification_status.value,
            'confidence_score': self.confidence_score,
            'timestamp': self.timestamp.isoformat(),
            'verification_method': self.verification_method,
            'cross_check_results': self.cross_check_results,
            'notes': self.notes
        }


@dataclass
class AssessmentProvenance:
    """Complete provenance record for a risk assessment."""
    assessment_id: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    user_id: Optional[str]
    field_provenance: Dict[str, FieldProvenance]
    overall_data_quality: float  # 0-1
    flags: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            'assessment_id': self.assessment_id,
            'timestamp': self.timestamp.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'user_id': self.user_id,
            'field_provenance': {
                name: prov.to_dict()
                for name, prov in self.field_provenance.items()
            },
            'overall_data_quality': self.overall_data_quality,
            'flags': self.flags
        }


class ProvenanceTracker:
    """
    Track and verify input provenance.
    
    Provides:
    1. Field-level source tracking
    2. Cross-validation with external data
    3. Consistency checks
    4. Audit trail generation
    """
    
    # Industry benchmarks for cargo value density (USD per cubic meter)
    VALUE_DENSITY_BENCHMARKS = {
        'electronics': {'min': 5000, 'max': 50000},
        'machinery': {'min': 2000, 'max': 20000},
        'textiles': {'min': 500, 'max': 5000},
        'food': {'min': 200, 'max': 2000},
        'chemicals': {'min': 1000, 'max': 10000},
        'hazardous': {'min': 2000, 'max': 30000},
        'fragile': {'min': 3000, 'max': 40000},
        'standard': {'min': 100, 'max': 10000}
    }
    
    # Critical fields that must always be provided
    CRITICAL_FIELDS = [
        'cargo_type', 'cargo_value', 'carrier', 
        'departure_date', 'route', 'transport_mode'
    ]
    
    # High-risk optional fields (omitting these is suspicious)
    HIGH_RISK_OPTIONAL = [
        'hazmat_class', 'special_handling_requirements',
        'declared_value_accuracy', 'previous_incidents'
    ]
    
    def __init__(self):
        self.field_provenance: Dict[str, FieldProvenance] = {}
        self.flags: List[str] = []
    
    def track_input(
        self,
        request_data: Dict[str, Any],
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> AssessmentProvenance:
        """
        Track provenance for all input fields.
        
        Args:
            request_data: Raw input data from request
            ip_address: Client IP address
            user_agent: Client user agent
            user_id: Authenticated user ID
            
        Returns:
            AssessmentProvenance object
        """
        self.field_provenance = {}
        self.flags = []
        
        # Generate assessment ID
        assessment_id = self._generate_assessment_id(request_data)
        
        # Track each field
        for field_name, field_value in request_data.items():
            provenance = self._track_field(field_name, field_value, request_data)
            self.field_provenance[field_name] = provenance
        
        # Run cross-validations
        self._run_cross_validations(request_data)
        
        # Calculate overall data quality
        overall_quality = self._calculate_data_quality()
        
        return AssessmentProvenance(
            assessment_id=assessment_id,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            user_id=user_id,
            field_provenance=self.field_provenance,
            overall_data_quality=overall_quality,
            flags=self.flags
        )
    
    def _generate_assessment_id(self, data: Dict) -> str:
        """Generate unique assessment ID from content hash."""
        content = json.dumps(data, sort_keys=True, default=str)
        hash_hex = hashlib.sha256(content.encode()).hexdigest()[:16]
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"ASM-{timestamp}-{hash_hex}"
    
    def _track_field(
        self, 
        field_name: str, 
        field_value: Any,
        all_data: Dict
    ) -> FieldProvenance:
        """Track provenance for a single field."""
        
        # Determine source (simplified - in production would check actual source)
        source = DataSource.USER_INPUT
        
        # Initial verification status
        status = VerificationStatus.UNVERIFIED
        confidence = 0.5  # Default confidence for unverified
        
        # Field-specific validation
        if field_name == 'cargo_value':
            validation = self.validate_cargo_value(
                field_value,
                all_data.get('cargo_type', 'standard'),
                all_data.get('volume_cbm', 0),
                all_data.get('weight_kg', 0)
            )
            status = VerificationStatus[validation['status'].upper()]
            confidence = validation['confidence']
            
        elif field_name == 'departure_date' or field_name == 'etd':
            validation = self.check_temporal_consistency(field_value)
            status = VerificationStatus[validation['status'].upper()]
            confidence = validation['confidence']
            if validation.get('flag'):
                self.flags.append(validation['flag'])
        
        elif field_name == 'route':
            validation = self.detect_route_manipulation(
                all_data.get('pol', ''),
                all_data.get('pod', ''),
                field_value
            )
            status = VerificationStatus[validation['status'].upper()]
            confidence = validation['confidence']
        
        else:
            # Default validation based on presence
            if field_value is not None and field_value != '':
                status = VerificationStatus.UNVERIFIED
                confidence = 0.7
            else:
                status = VerificationStatus.UNVERIFIED
                confidence = 0.3
        
        return FieldProvenance(
            field_name=field_name,
            field_value=field_value,
            source=source,
            verification_status=status,
            confidence_score=confidence
        )
    
    def validate_cargo_value(
        self,
        declared_value: float,
        cargo_type: str,
        volume: float,
        weight: float
    ) -> Dict:
        """
        Check if declared cargo value is consistent with physical properties.
        
        Returns:
            Dict with status, confidence, and expected_range
        """
        if declared_value is None or declared_value <= 0:
            return {
                'status': 'suspicious',
                'reason': 'Missing or invalid cargo value',
                'confidence': 0.2
            }
        
        declared_value = float(declared_value)
        benchmark = self.VALUE_DENSITY_BENCHMARKS.get(
            cargo_type.lower() if cargo_type else 'standard',
            self.VALUE_DENSITY_BENCHMARKS['standard']
        )
        
        # If we have volume, check value density
        if volume and volume > 0:
            value_density = declared_value / volume
            
            if value_density < benchmark['min'] * 0.5:
                return {
                    'status': 'suspicious',
                    'reason': 'Value unusually low for cargo type',
                    'confidence': 0.3,
                    'expected_range': [benchmark['min'] * volume, benchmark['max'] * volume]
                }
            elif value_density > benchmark['max'] * 2:
                return {
                    'status': 'suspicious',
                    'reason': 'Value unusually high for cargo type',
                    'confidence': 0.4,
                    'expected_range': [benchmark['min'] * volume, benchmark['max'] * volume]
                }
        
        return {
            'status': 'unverified',  # Plausible but not verified
            'confidence': 0.8,
            'reason': 'Value appears plausible'
        }
    
    def detect_route_manipulation(
        self, 
        origin: str, 
        destination: str, 
        declared_route: str
    ) -> Dict:
        """
        Check if declared route is consistent with origin/destination.
        """
        if not declared_route:
            return {
                'status': 'unverified',
                'confidence': 0.5,
                'reason': 'No route declared'
            }
        
        # Simple consistency check
        route_upper = declared_route.upper()
        origin_upper = (origin or '').upper()
        dest_upper = (destination or '').upper()
        
        # Check if O-D appear in route
        if origin_upper and origin_upper[:2] not in route_upper:
            self.flags.append('route_origin_mismatch')
            return {
                'status': 'suspicious',
                'confidence': 0.4,
                'reason': f'Origin {origin} not found in route {declared_route}'
            }
        
        if dest_upper and dest_upper[:2] not in route_upper:
            self.flags.append('route_destination_mismatch')
            return {
                'status': 'suspicious',
                'confidence': 0.4,
                'reason': f'Destination {destination} not found in route {declared_route}'
            }
        
        return {
            'status': 'verified',
            'confidence': 0.9,
            'reason': 'Route consistent with O-D'
        }
    
    def check_temporal_consistency(self, departure_date: str) -> Dict:
        """
        Flag if shipment is being assessed retroactively.
        """
        if not departure_date:
            return {
                'status': 'unverified',
                'confidence': 0.5,
                'reason': 'No departure date provided'
            }
        
        try:
            # Handle various date formats
            from dateutil import parser
            departure = parser.parse(departure_date)
            now = datetime.utcnow()
            
            # Already departed
            if departure < now:
                days_past = (now - departure).days
                return {
                    'status': 'suspicious',
                    'reason': f'Assessing shipment {days_past} days after departure',
                    'confidence': 0.2,
                    'flag': 'retroactive_assessment'
                }
            
            # Far future (> 6 months)
            days_future = (departure - now).days
            if days_future > 180:
                return {
                    'status': 'suspicious',
                    'reason': 'Assessing shipment >6 months in future',
                    'confidence': 0.5,
                    'flag': 'far_future_assessment'
                }
            
            return {
                'status': 'verified',
                'confidence': 0.95,
                'reason': 'Normal assessment timing'
            }
            
        except Exception as e:
            return {
                'status': 'unverified',
                'confidence': 0.4,
                'reason': f'Could not parse date: {e}'
            }
    
    def _run_cross_validations(self, data: Dict):
        """Run cross-field validation checks."""
        
        # Check for strategic omissions
        missing_critical = [
            f for f in self.CRITICAL_FIELDS 
            if not data.get(f)
        ]
        if missing_critical:
            self.flags.append(f'missing_critical_fields:{",".join(missing_critical)}')
        
        # Check for round number values (potential fabrication)
        cargo_value = data.get('cargo_value', 0)
        if cargo_value and cargo_value > 1000 and cargo_value % 10000 == 0:
            self.flags.append('round_number_cargo_value')
        
        # Check transport mode + container consistency
        transport = data.get('transport_mode', '').lower()
        container = data.get('container', '').lower()
        
        if 'air' in transport and any(c in container for c in ['20ft', '40ft']):
            self.flags.append('air_freight_with_ocean_container')
    
    def _calculate_data_quality(self) -> float:
        """Calculate overall data quality score (0-1)."""
        if not self.field_provenance:
            return 0.5
        
        # Weight by field importance
        weights = {
            'cargo_value': 2.0,
            'route': 1.5,
            'carrier': 1.5,
            'departure_date': 1.2,
            'cargo_type': 1.0
        }
        
        total_weight = 0.0
        weighted_confidence = 0.0
        
        for field_name, provenance in self.field_provenance.items():
            weight = weights.get(field_name, 1.0)
            total_weight += weight
            weighted_confidence += weight * provenance.confidence_score
        
        if total_weight == 0:
            return 0.5
        
        base_quality = weighted_confidence / total_weight
        
        # Penalty for flags
        flag_penalty = min(0.3, len(self.flags) * 0.05)
        
        return max(0.0, base_quality - flag_penalty)


# Convenience function for API integration
def track_request_provenance(
    request_data: Dict[str, Any],
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict:
    """
    Track provenance for a risk assessment request.
    
    Returns provenance record as dictionary.
    """
    tracker = ProvenanceTracker()
    provenance = tracker.track_input(
        request_data,
        ip_address=ip_address,
        user_agent=user_agent,
        user_id=user_id
    )
    return provenance.to_dict()
