"""
Data Validation & Outlier Detection

Validates incoming data and detects anomalies that could indicate
data quality issues or fraud.
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from enum import Enum
import re
import statistics
import logging

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity of validation issues."""
    ERROR = "ERROR"        # Blocks processing
    WARNING = "WARNING"    # Flags for review
    INFO = "INFO"          # Informational only


class ValidationCategory(Enum):
    """Categories of validation."""
    COMPLETENESS = "COMPLETENESS"
    RANGE = "RANGE"
    FORMAT = "FORMAT"
    CONSISTENCY = "CONSISTENCY"
    OUTLIER = "OUTLIER"
    BUSINESS_RULE = "BUSINESS_RULE"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    field: str
    category: ValidationCategory
    severity: ValidationSeverity
    message: str
    value: Any
    expected: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "field": self.field,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "value": str(self.value) if self.value is not None else None,
            "expected": self.expected,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationResult:
    """Result of data validation."""
    is_valid: bool
    issues: List[ValidationIssue]
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]
    completeness_score: float
    quality_score: float
    validated_at: datetime
    
    @property
    def error_count(self) -> int:
        return len(self.errors)
    
    @property
    def warning_count(self) -> int:
        return len(self.warnings)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "completeness_score": self.completeness_score,
            "quality_score": self.quality_score,
            "validated_at": self.validated_at.isoformat(),
            "issues": [i.to_dict() for i in self.issues],
            "errors": [i.to_dict() for i in self.errors],
            "warnings": [i.to_dict() for i in self.warnings],
        }


class OutlierDetector:
    """Simple statistical outlier detection."""
    
    def __init__(
        self,
        mean: float,
        std: float,
        min_val: float,
        max_val: float,
        z_threshold: float = 3.0
    ):
        self.mean = mean
        self.std = std
        self.min_val = min_val
        self.max_val = max_val
        self.z_threshold = z_threshold
    
    @classmethod
    def from_data(cls, values: List[float], z_threshold: float = 3.0) -> "OutlierDetector":
        """Create detector from data."""
        if len(values) < 2:
            return cls(0, 1, 0, 1, z_threshold)
        
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 1
        min_val = min(values)
        max_val = max(values)
        
        return cls(mean, std, min_val, max_val, z_threshold)
    
    def is_outlier(self, value: float) -> bool:
        """Check if value is an outlier."""
        if self.std == 0:
            return False
        
        z_score = abs(value - self.mean) / self.std
        return z_score > self.z_threshold
    
    def get_typical_range(self) -> str:
        """Get human-readable typical range."""
        lower = max(self.min_val, self.mean - 2 * self.std)
        upper = min(self.max_val, self.mean + 2 * self.std)
        return f"{lower:,.0f} - {upper:,.0f}"


class DataValidator:
    """
    Validates shipment and risk data for quality and consistency.
    
    Catches data issues BEFORE they pollute the system.
    """
    
    # Valid port codes (UN/LOCODE format)
    VALID_PORT_PATTERN = r'^[A-Z]{2}[A-Z0-9]{3}$'
    
    # Valid cargo types
    VALID_CARGO_TYPES = {
        "ELECTRONICS", "MACHINERY", "TEXTILES", "FOOD_PERISHABLE",
        "FOOD_DRY", "CHEMICALS", "PHARMACEUTICALS", "AUTOMOTIVE",
        "GENERAL", "BULK", "LIQUID_BULK", "REEFER", "HAZMAT",
        "STANDARD", "FRAGILE", "PERISHABLE", "HIGH_VALUE"
    }
    
    # Valid carrier codes (SCAC format)
    VALID_CARRIER_PATTERN = r'^[A-Z]{4}$'
    
    # Reasonable ranges
    CARGO_VALUE_MIN = 100  # $100 minimum
    CARGO_VALUE_MAX = 100_000_000  # $100M maximum
    CONTAINER_COUNT_MAX = 10000
    TRANSIT_DAYS_MAX = 365
    LOSS_PERCENTAGE_MAX = 1.0
    
    def __init__(self, audit: Optional[Any] = None):
        self.audit = audit
        self._outlier_detectors: Dict[str, OutlierDetector] = {}
    
    def validate_shipment_data(
        self,
        data: Dict[str, Any],
        context: str = "IMPORT"
    ) -> ValidationResult:
        """
        Validate shipment data comprehensively.
        
        Returns validation result with all issues found.
        """
        issues = []
        
        # 1. Completeness checks
        issues.extend(self._check_completeness(data))
        
        # 2. Format checks
        issues.extend(self._check_formats(data))
        
        # 3. Range checks
        issues.extend(self._check_ranges(data))
        
        # 4. Consistency checks
        issues.extend(self._check_consistency(data))
        
        # 5. Business rule checks
        issues.extend(self._check_business_rules(data))
        
        # 6. Outlier detection
        issues.extend(self._check_outliers(data))
        
        # Separate errors and warnings
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        
        # Calculate scores
        completeness = self._calculate_completeness(data)
        quality = self._calculate_quality_score(issues, data)
        
        result = ValidationResult(
            is_valid=len(errors) == 0,
            issues=issues,
            errors=errors,
            warnings=warnings,
            completeness_score=completeness,
            quality_score=quality,
            validated_at=datetime.utcnow()
        )
        
        # Audit significant issues
        if self.audit and (errors or warnings):
            try:
                tenant_id = getattr(self.audit, 'tenant_id', None) or "system"
                self.audit.append_event(
                    tenant_id=tenant_id,
                    event_type="DATA_VALIDATION",
                    action="VALIDATION_ISSUES_FOUND",
                    entity_type="shipment_data",
                    entity_id=str(data.get("id", "unknown")),
                    actor_type="SYSTEM",
                    payload={
                        "context": context,
                        "error_count": len(errors),
                        "warning_count": len(warnings),
                        "completeness": completeness,
                        "quality_score": quality
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to audit validation: {e}")
        
        return result
    
    def _check_completeness(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check for missing required fields."""
        issues = []
        
        required_fields = {
            "shipment_date": "Shipment date is required",
            "origin_port": "Origin port is required",
            "destination_port": "Destination port is required",
            "cargo_type": "Cargo type is required",
            "cargo_value_usd": "Cargo value is required",
        }
        
        for field, message in required_fields.items():
            if not data.get(field):
                issues.append(ValidationIssue(
                    field=field,
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.ERROR,
                    message=message,
                    value=None,
                    expected="Non-null value",
                    suggestion=f"Provide a valid {field.replace('_', ' ')}"
                ))
        
        important_fields = {
            "carrier_code": "Carrier code improves risk accuracy",
            "container_count": "Container count affects risk calculation",
            "expected_transit_days": "Expected transit helps detect delays",
        }
        
        for field, message in important_fields.items():
            if not data.get(field):
                issues.append(ValidationIssue(
                    field=field,
                    category=ValidationCategory.COMPLETENESS,
                    severity=ValidationSeverity.WARNING,
                    message=message,
                    value=None,
                    expected="Non-null value",
                    suggestion=f"Consider providing {field.replace('_', ' ')}"
                ))
        
        return issues
    
    def _check_formats(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check field formats."""
        issues = []
        
        # Port code format
        for field in ["origin_port", "destination_port"]:
            value = data.get(field)
            if value:
                value_str = str(value).upper().strip()
                if not re.match(self.VALID_PORT_PATTERN, value_str):
                    issues.append(ValidationIssue(
                        field=field,
                        category=ValidationCategory.FORMAT,
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid port code format: {value}",
                        value=value,
                        expected="UN/LOCODE format (e.g., CNSHA, NLRTM)",
                        suggestion="Use 5-character UN/LOCODE"
                    ))
        
        # Carrier code format
        carrier = data.get("carrier_code")
        if carrier:
            carrier_str = str(carrier).upper().strip()
            if not re.match(self.VALID_CARRIER_PATTERN, carrier_str):
                issues.append(ValidationIssue(
                    field="carrier_code",
                    category=ValidationCategory.FORMAT,
                    severity=ValidationSeverity.WARNING,
                    message=f"Invalid carrier code format: {carrier}",
                    value=carrier,
                    expected="SCAC format (4 uppercase letters)",
                    suggestion="Use 4-character SCAC code"
                ))
        
        # Cargo type
        cargo_type = data.get("cargo_type")
        if cargo_type:
            cargo_upper = str(cargo_type).upper()
            if cargo_upper not in self.VALID_CARGO_TYPES:
                # Check if it's a variation we can accept
                is_variation = any(
                    valid in cargo_upper or cargo_upper in valid
                    for valid in self.VALID_CARGO_TYPES
                )
                if not is_variation:
                    issues.append(ValidationIssue(
                        field="cargo_type",
                        category=ValidationCategory.FORMAT,
                        severity=ValidationSeverity.WARNING,
                        message=f"Non-standard cargo type: {cargo_type}",
                        value=cargo_type,
                        expected=f"One of: {', '.join(sorted(self.VALID_CARGO_TYPES))}",
                        suggestion="Use a standard cargo type code"
                    ))
        
        # Date format
        shipment_date = data.get("shipment_date")
        if shipment_date:
            if isinstance(shipment_date, str):
                try:
                    datetime.strptime(shipment_date, "%Y-%m-%d")
                except ValueError:
                    # Try other formats
                    try:
                        datetime.strptime(shipment_date, "%d/%m/%Y")
                    except ValueError:
                        try:
                            datetime.strptime(shipment_date, "%m/%d/%Y")
                        except ValueError:
                            issues.append(ValidationIssue(
                                field="shipment_date",
                                category=ValidationCategory.FORMAT,
                                severity=ValidationSeverity.ERROR,
                                message=f"Invalid date format: {shipment_date}",
                                value=shipment_date,
                                expected="YYYY-MM-DD format",
                                suggestion="Use ISO date format (YYYY-MM-DD)"
                            ))
        
        return issues
    
    def _check_ranges(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check numeric value ranges."""
        issues = []
        
        # Cargo value
        cargo_value = data.get("cargo_value_usd")
        if cargo_value is not None:
            try:
                cargo_value = float(cargo_value)
                if cargo_value < self.CARGO_VALUE_MIN:
                    issues.append(ValidationIssue(
                        field="cargo_value_usd",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.WARNING,
                        message=f"Cargo value unusually low: ${cargo_value:,.2f}",
                        value=cargo_value,
                        expected=f"At least ${self.CARGO_VALUE_MIN:,.2f}",
                        suggestion="Verify cargo value is correct"
                    ))
                elif cargo_value > self.CARGO_VALUE_MAX:
                    issues.append(ValidationIssue(
                        field="cargo_value_usd",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.WARNING,
                        message=f"Cargo value unusually high: ${cargo_value:,.0f}",
                        value=cargo_value,
                        expected=f"At most ${self.CARGO_VALUE_MAX:,.0f}",
                        suggestion="Verify cargo value is correct"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    field="cargo_value_usd",
                    category=ValidationCategory.RANGE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid cargo value: {cargo_value}",
                    value=cargo_value,
                    expected="Numeric value",
                    suggestion="Provide a valid numeric cargo value"
                ))
        
        # Container count
        container_count = data.get("container_count")
        if container_count is not None:
            try:
                container_count = int(container_count)
                if container_count < 1:
                    issues.append(ValidationIssue(
                        field="container_count",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid container count: {container_count}",
                        value=container_count,
                        expected="At least 1",
                        suggestion="Provide valid container count"
                    ))
                elif container_count > self.CONTAINER_COUNT_MAX:
                    issues.append(ValidationIssue(
                        field="container_count",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.WARNING,
                        message=f"Container count unusually high: {container_count}",
                        value=container_count,
                        expected=f"At most {self.CONTAINER_COUNT_MAX}",
                        suggestion="Verify container count"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    field="container_count",
                    category=ValidationCategory.RANGE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid container count: {container_count}",
                    value=container_count,
                    expected="Integer value",
                    suggestion="Provide a valid integer container count"
                ))
        
        # Transit days
        expected_transit = data.get("expected_transit_days")
        if expected_transit is not None:
            try:
                expected_transit = int(expected_transit)
                if expected_transit < 1:
                    issues.append(ValidationIssue(
                        field="expected_transit_days",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid transit days: {expected_transit}",
                        value=expected_transit,
                        expected="At least 1 day",
                        suggestion="Provide valid transit time"
                    ))
                elif expected_transit > self.TRANSIT_DAYS_MAX:
                    issues.append(ValidationIssue(
                        field="expected_transit_days",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.WARNING,
                        message=f"Transit time unusually long: {expected_transit} days",
                        value=expected_transit,
                        expected=f"At most {self.TRANSIT_DAYS_MAX} days",
                        suggestion="Verify transit time"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    field="expected_transit_days",
                    category=ValidationCategory.RANGE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid transit days: {expected_transit}",
                    value=expected_transit,
                    expected="Integer value",
                    suggestion="Provide a valid integer transit time"
                ))
        
        # Loss percentage
        loss_pct = data.get("loss_percentage")
        if loss_pct is not None:
            try:
                loss_pct = float(loss_pct)
                if loss_pct < 0:
                    issues.append(ValidationIssue(
                        field="loss_percentage",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid loss percentage: {loss_pct}",
                        value=loss_pct,
                        expected="Non-negative value",
                        suggestion="Loss percentage cannot be negative"
                    ))
                elif loss_pct > self.LOSS_PERCENTAGE_MAX:
                    issues.append(ValidationIssue(
                        field="loss_percentage",
                        category=ValidationCategory.RANGE,
                        severity=ValidationSeverity.ERROR,
                        message=f"Loss percentage exceeds 100%: {loss_pct * 100:.1f}%",
                        value=loss_pct,
                        expected="At most 1.0 (100%)",
                        suggestion="Loss cannot exceed cargo value"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    field="loss_percentage",
                    category=ValidationCategory.RANGE,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid loss percentage: {loss_pct}",
                    value=loss_pct,
                    expected="Numeric value between 0 and 1",
                    suggestion="Provide a valid loss percentage"
                ))
        
        return issues
    
    def _check_consistency(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check logical consistency between fields."""
        issues = []
        
        # Origin != Destination
        origin = data.get("origin_port")
        destination = data.get("destination_port")
        if origin and destination:
            origin_str = str(origin).upper().strip()
            dest_str = str(destination).upper().strip()
            if origin_str == dest_str:
                issues.append(ValidationIssue(
                    field="destination_port",
                    category=ValidationCategory.CONSISTENCY,
                    severity=ValidationSeverity.ERROR,
                    message="Origin and destination ports are the same",
                    value=f"{origin} -> {destination}",
                    expected="Different origin and destination",
                    suggestion="Check port codes"
                ))
        
        # Actual transit >= expected transit (usually)
        expected = data.get("expected_transit_days")
        actual = data.get("actual_transit_days")
        if expected and actual:
            try:
                expected = int(expected)
                actual = int(actual)
                if actual < expected * 0.5:
                    # Arrived in less than half expected time - suspicious
                    issues.append(ValidationIssue(
                        field="actual_transit_days",
                        category=ValidationCategory.CONSISTENCY,
                        severity=ValidationSeverity.WARNING,
                        message=f"Actual transit ({actual} days) much faster than expected ({expected} days)",
                        value=actual,
                        expected=f"Around {expected} days",
                        suggestion="Verify transit times are correct"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Loss amount <= cargo value
        cargo_value = data.get("cargo_value_usd") or 0
        loss_amount = data.get("loss_amount_usd") or 0
        if cargo_value and loss_amount:
            try:
                cargo_value = float(cargo_value)
                loss_amount = float(loss_amount)
                if loss_amount > cargo_value * 1.1:  # Allow 10% for expenses
                    issues.append(ValidationIssue(
                        field="loss_amount_usd",
                        category=ValidationCategory.CONSISTENCY,
                        severity=ValidationSeverity.ERROR,
                        message=f"Loss amount (${loss_amount:,.0f}) exceeds cargo value (${cargo_value:,.0f})",
                        value=loss_amount,
                        expected=f"At most ${cargo_value:,.0f}",
                        suggestion="Loss cannot exceed cargo value"
                    ))
            except (ValueError, TypeError):
                pass
        
        # Outcome date >= shipment date
        shipment_date = data.get("shipment_date")
        outcome_date = data.get("outcome_date")
        if shipment_date and outcome_date:
            try:
                # Parse dates
                if isinstance(shipment_date, str):
                    ship_date = datetime.strptime(shipment_date, "%Y-%m-%d").date()
                elif isinstance(shipment_date, date):
                    ship_date = shipment_date
                elif isinstance(shipment_date, datetime):
                    ship_date = shipment_date.date()
                else:
                    ship_date = None
                
                if isinstance(outcome_date, str):
                    out_date = datetime.strptime(outcome_date, "%Y-%m-%d").date()
                elif isinstance(outcome_date, date):
                    out_date = outcome_date
                elif isinstance(outcome_date, datetime):
                    out_date = outcome_date.date()
                else:
                    out_date = None
                
                if ship_date and out_date and out_date < ship_date:
                    issues.append(ValidationIssue(
                        field="outcome_date",
                        category=ValidationCategory.CONSISTENCY,
                        severity=ValidationSeverity.ERROR,
                        message="Outcome date is before shipment date",
                        value=f"Shipment: {ship_date}, Outcome: {out_date}",
                        expected="Outcome date >= shipment date",
                        suggestion="Check date values"
                    ))
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def _check_business_rules(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check business rules and domain-specific constraints."""
        issues = []
        
        # High-value cargo should have carrier info
        cargo_value = data.get("cargo_value_usd") or 0
        try:
            cargo_value = float(cargo_value)
            if cargo_value > 1_000_000 and not data.get("carrier_code"):
                issues.append(ValidationIssue(
                    field="carrier_code",
                    category=ValidationCategory.BUSINESS_RULE,
                    severity=ValidationSeverity.WARNING,
                    message="High-value cargo (>$1M) should have carrier information",
                    value=None,
                    expected="Carrier code for high-value shipments",
                    suggestion="Add carrier information for accurate risk assessment"
                ))
        except (ValueError, TypeError):
            pass
        
        # Perishable cargo should have expected transit
        cargo_type = data.get("cargo_type")
        if cargo_type:
            cargo_upper = str(cargo_type).upper()
            if "PERISHABLE" in cargo_upper:
                if not data.get("expected_transit_days"):
                    issues.append(ValidationIssue(
                        field="expected_transit_days",
                        category=ValidationCategory.BUSINESS_RULE,
                        severity=ValidationSeverity.WARNING,
                        message="Perishable cargo should have expected transit time",
                        value=None,
                        expected="Transit time for perishable goods",
                        suggestion="Add expected transit for spoilage risk calculation"
                    ))
        
        # Hazmat should be flagged
        if cargo_type:
            cargo_upper = str(cargo_type).upper()
            if "HAZMAT" in cargo_upper or "HAZARDOUS" in cargo_upper:
                if not data.get("hazmat_class"):
                    issues.append(ValidationIssue(
                        field="hazmat_class",
                        category=ValidationCategory.BUSINESS_RULE,
                        severity=ValidationSeverity.WARNING,
                        message="Hazmat cargo should have hazmat classification",
                        value=None,
                        expected="Hazmat class code",
                        suggestion="Provide hazmat classification"
                    ))
        
        return issues
    
    def _check_outliers(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Detect statistical outliers."""
        issues = []
        
        # Check if we have baseline statistics
        cargo_type = data.get("cargo_type")
        
        # Value per container outlier detection
        cargo_value = data.get("cargo_value_usd") or 0
        containers = data.get("container_count") or 1
        
        try:
            cargo_value = float(cargo_value)
            containers = max(int(containers), 1)
            value_per_container = cargo_value / containers
            
            # Get detector for this cargo type
            detector_key = f"value_per_container:{cargo_type}"
            if detector_key in self._outlier_detectors:
                detector = self._outlier_detectors[detector_key]
                if detector.is_outlier(value_per_container):
                    issues.append(ValidationIssue(
                        field="cargo_value_usd",
                        category=ValidationCategory.OUTLIER,
                        severity=ValidationSeverity.WARNING,
                        message=f"Value per container (${value_per_container:,.0f}) is unusual for {cargo_type}",
                        value=value_per_container,
                        expected=f"Typical range: {detector.get_typical_range()}",
                        suggestion="Verify cargo value"
                    ))
        except (ValueError, TypeError):
            pass
        
        # Loss ratio outlier detection
        loss_pct = data.get("loss_percentage")
        if loss_pct and cargo_type:
            try:
                loss_pct = float(loss_pct)
                if loss_pct > 0:
                    detector_key = f"loss_pct:{cargo_type}"
                    if detector_key in self._outlier_detectors:
                        detector = self._outlier_detectors[detector_key]
                        if detector.is_outlier(loss_pct):
                            issues.append(ValidationIssue(
                                field="loss_percentage",
                                category=ValidationCategory.OUTLIER,
                                severity=ValidationSeverity.WARNING,
                                message=f"Loss percentage ({loss_pct*100:.1f}%) is unusual for {cargo_type}",
                                value=loss_pct,
                                expected=f"Typical range: {detector.get_typical_range()}",
                                suggestion="Verify loss amount"
                            ))
            except (ValueError, TypeError):
                pass
        
        return issues
    
    def _calculate_completeness(self, data: Dict[str, Any]) -> float:
        """Calculate data completeness score."""
        all_fields = [
            "shipment_date", "origin_port", "destination_port",
            "cargo_type", "cargo_value_usd", "container_count",
            "carrier_code", "expected_transit_days", "actual_transit_days",
            "weather_conditions", "port_conditions", "carrier_rating",
            "outcome", "loss_occurred", "loss_percentage"
        ]
        
        present = sum(1 for f in all_fields if data.get(f) is not None)
        return present / len(all_fields) if all_fields else 0.0
    
    def _calculate_quality_score(
        self,
        issues: List[ValidationIssue],
        data: Dict[str, Any]
    ) -> float:
        """Calculate overall data quality score."""
        base_score = 1.0
        
        # Deduct for errors
        error_count = sum(1 for i in issues if i.severity == ValidationSeverity.ERROR)
        base_score -= error_count * 0.2
        
        # Deduct for warnings
        warning_count = sum(1 for i in issues if i.severity == ValidationSeverity.WARNING)
        base_score -= warning_count * 0.05
        
        # Factor in completeness
        completeness = self._calculate_completeness(data)
        base_score *= completeness
        
        return max(0.0, min(1.0, base_score))
    
    def train_outlier_detectors(
        self,
        historical_data: List[Dict[str, Any]]
    ):
        """Train outlier detectors from historical data."""
        # Group by cargo type
        by_cargo_type: Dict[str, List[Dict[str, Any]]] = {}
        for d in historical_data:
            cargo = d.get("cargo_type", "UNKNOWN")
            if cargo not in by_cargo_type:
                by_cargo_type[cargo] = []
            by_cargo_type[cargo].append(d)
        
        # Create detectors for each cargo type
        for cargo_type, records in by_cargo_type.items():
            # Value per container
            values = []
            for r in records:
                try:
                    cargo_value = float(r.get("cargo_value_usd") or 0)
                    containers = max(int(r.get("container_count") or 1), 1)
                    if cargo_value > 0:
                        values.append(cargo_value / containers)
                except (ValueError, TypeError):
                    continue
            
            if len(values) >= 10:
                self._outlier_detectors[f"value_per_container:{cargo_type}"] = \
                    OutlierDetector.from_data(values)
            
            # Loss percentage
            loss_values = []
            for r in records:
                try:
                    loss_pct = r.get("loss_percentage")
                    if loss_pct is not None:
                        loss_pct = float(loss_pct)
                        if loss_pct > 0:
                            loss_values.append(loss_pct)
                except (ValueError, TypeError):
                    continue
            
            if len(loss_values) >= 10:
                self._outlier_detectors[f"loss_pct:{cargo_type}"] = \
                    OutlierDetector.from_data(loss_values)


# Singleton instance
data_validator: Optional[DataValidator] = None


def get_data_validator(audit: Optional[Any] = None) -> DataValidator:
    """Get or create data validator singleton."""
    global data_validator
    if data_validator is None:
        data_validator = DataValidator(audit)
    return data_validator
