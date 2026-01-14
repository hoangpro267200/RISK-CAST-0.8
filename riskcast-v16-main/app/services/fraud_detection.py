"""
RISKCAST Fraud Detection Engine
================================
Detect patterns indicative of gaming, fraud, or misaligned incentives.

Threat Model:
1. Shippers wanting lower insurance premiums (underreport risk)
2. Forwarders wanting to appear low-risk (inflate reliability)
3. Insurance underwriters wanting higher premiums (inflate risk)
4. Competitors trying to discredit system (adversarial inputs)

Author: RISKCAST Team
Version: 2.0
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import logging
import re

logger = logging.getLogger(__name__)


class SignalSeverity(Enum):
    """Severity level of fraud signals."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalType(Enum):
    """Type of fraud signal detected."""
    MISSING_CRITICAL_DATA = "missing_critical_data"
    STRATEGIC_OMISSION = "strategic_omission"
    VALUE_ANOMALY = "value_anomaly"
    TEMPORAL_ANOMALY = "temporal_anomaly"
    PATTERN_ANOMALY = "pattern_anomaly"
    CROSS_FIELD_INCONSISTENCY = "cross_field_inconsistency"
    USER_BEHAVIOR = "user_behavior"
    SYSTEMATIC_PROBING = "systematic_probing"
    BENFORD_VIOLATION = "benford_violation"
    ROUND_NUMBER = "round_number"


class RecommendedAction(Enum):
    """Recommended action based on fraud score."""
    ALLOW = "allow"              # Normal processing
    MONITOR = "monitor"          # Track for patterns
    FLAG = "flag"                # Apply penalties, log for audit
    BLOCK = "block"              # Require manual review


@dataclass
class FraudSignal:
    """A single fraud/gaming detection signal."""
    signal_type: SignalType
    severity: SignalSeverity
    description: str
    confidence: float  # 0-1
    field_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    
    def to_dict(self) -> Dict:
        return {
            'signal_type': self.signal_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'confidence': self.confidence,
            'field_name': self.field_name,
            'expected_value': str(self.expected_value) if self.expected_value else None,
            'actual_value': str(self.actual_value) if self.actual_value else None
        }


@dataclass
class FraudAnalysisResult:
    """Complete fraud analysis result."""
    fraud_score: float  # 0-100
    signals: List[FraudSignal]
    recommended_action: RecommendedAction
    risk_penalty: float  # Points to add to risk score
    explanation: str
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'fraud_score': self.fraud_score,
            'signals': [s.to_dict() for s in self.signals],
            'recommended_action': self.recommended_action.value,
            'risk_penalty': self.risk_penalty,
            'explanation': self.explanation,
            'timestamp': self.timestamp.isoformat()
        }


class FraudDetector:
    """
    Detect patterns indicative of gaming or fraud.
    
    Implements multiple detection strategies:
    1. Strategic data omission detection
    2. Value anomaly detection (Benford's Law, round numbers)
    3. User behavior pattern analysis
    4. Cross-field consistency checks
    5. Temporal pattern analysis
    """
    
    # Critical fields that should always be provided
    CRITICAL_FIELDS = [
        'cargo_type', 'cargo_value', 'carrier',
        'route', 'transport_mode'
    ]
    
    # High-risk optional fields (omitting many is suspicious)
    HIGH_RISK_OPTIONAL = [
        'hazmat_class', 'special_handling',
        'previous_incidents', 'insurance_history',
        'carrier_incidents', 'customs_complexity'
    ]
    
    # Benford's Law expected first digit distribution
    BENFORD_DISTRIBUTION = {
        1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097,
        5: 0.079, 6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046
    }
    
    # Severity weights for scoring
    SEVERITY_WEIGHTS = {
        SignalSeverity.LOW: 0.2,
        SignalSeverity.MEDIUM: 0.5,
        SignalSeverity.HIGH: 0.8,
        SignalSeverity.CRITICAL: 1.0
    }
    
    def __init__(self):
        self.signals: List[FraudSignal] = []
    
    def analyze_request(
        self,
        request_data: Dict[str, Any],
        user_history: Optional[List[Dict]] = None,
        ip_address: Optional[str] = None
    ) -> FraudAnalysisResult:
        """
        Run all fraud detection checks on a request.
        
        Args:
            request_data: Shipment data from request
            user_history: Previous assessments from this user
            ip_address: Client IP for behavior analysis
            
        Returns:
            FraudAnalysisResult with signals, score, and recommendation
        """
        self.signals = []
        
        # Run all detection checks
        self._check_strategic_omissions(request_data)
        self._check_value_anomalies(request_data)
        self._check_benford_law(request_data)
        self._check_round_numbers(request_data)
        self._check_cross_field_consistency(request_data)
        self._check_temporal_anomalies(request_data)
        
        if user_history:
            self._check_user_patterns(user_history)
            self._check_systematic_probing(user_history)
        
        # Calculate overall fraud score
        fraud_score = self._compute_fraud_score()
        
        # Determine recommended action
        action = self._recommend_action(fraud_score)
        
        # Calculate risk penalty
        risk_penalty = self._calculate_risk_penalty(fraud_score)
        
        # Generate explanation
        explanation = self._generate_explanation(fraud_score, action)
        
        return FraudAnalysisResult(
            fraud_score=fraud_score,
            signals=self.signals,
            recommended_action=action,
            risk_penalty=risk_penalty,
            explanation=explanation,
            timestamp=datetime.utcnow()
        )
    
    def _add_signal(
        self,
        signal_type: SignalType,
        severity: SignalSeverity,
        description: str,
        confidence: float,
        field_name: str = None,
        expected: Any = None,
        actual: Any = None
    ):
        """Add a fraud signal."""
        self.signals.append(FraudSignal(
            signal_type=signal_type,
            severity=severity,
            description=description,
            confidence=confidence,
            field_name=field_name,
            expected_value=expected,
            actual_value=actual
        ))
    
    def _check_strategic_omissions(self, data: Dict):
        """Detect strategic omission of high-risk fields."""
        
        # Check critical fields
        missing_critical = [f for f in self.CRITICAL_FIELDS if not data.get(f)]
        
        if len(missing_critical) > 0:
            severity = SignalSeverity.HIGH if len(missing_critical) > 2 else SignalSeverity.MEDIUM
            self._add_signal(
                signal_type=SignalType.MISSING_CRITICAL_DATA,
                severity=severity,
                description=f"Missing critical fields: {', '.join(missing_critical)}",
                confidence=0.9
            )
        
        # Check high-risk optional fields
        missing_high_risk = [f for f in self.HIGH_RISK_OPTIONAL if not data.get(f)]
        
        if len(missing_high_risk) >= 3:
            self._add_signal(
                signal_type=SignalType.STRATEGIC_OMISSION,
                severity=SignalSeverity.MEDIUM,
                description=f"Multiple high-risk fields omitted: {', '.join(missing_high_risk[:3])}...",
                confidence=0.6
            )
    
    def _check_value_anomalies(self, data: Dict):
        """Detect unusual value patterns."""
        
        cargo_value = data.get('cargo_value')
        if cargo_value:
            try:
                value = float(cargo_value)
                
                # Extremely low value (potential underreporting)
                if value < 1000 and data.get('cargo_type') in ['electronics', 'machinery', 'hazardous']:
                    self._add_signal(
                        signal_type=SignalType.VALUE_ANOMALY,
                        severity=SignalSeverity.HIGH,
                        description=f"Cargo value ${value:,.0f} unusually low for {data.get('cargo_type')}",
                        confidence=0.7,
                        field_name='cargo_value',
                        expected="> $10,000",
                        actual=f"${value:,.0f}"
                    )
                
                # Extremely high value (potential gaming for insurance)
                if value > 10_000_000:
                    self._add_signal(
                        signal_type=SignalType.VALUE_ANOMALY,
                        severity=SignalSeverity.MEDIUM,
                        description=f"Extremely high cargo value ${value:,.0f} - requires verification",
                        confidence=0.5,
                        field_name='cargo_value'
                    )
                    
            except (ValueError, TypeError):
                pass
    
    def _check_benford_law(self, data: Dict):
        """Check if values follow Benford's Law distribution."""
        
        # Collect numeric values
        numeric_values = []
        for key in ['cargo_value', 'transit_time', 'distance', 'weight_kg', 'volume_cbm']:
            val = data.get(key)
            if val:
                try:
                    numeric_values.append(float(val))
                except (ValueError, TypeError):
                    pass
        
        if len(numeric_values) < 3:
            return  # Not enough data
        
        # Extract first digits
        first_digits = []
        for val in numeric_values:
            if val > 0:
                first_digit = int(str(int(val))[0])
                if 1 <= first_digit <= 9:
                    first_digits.append(first_digit)
        
        if len(first_digits) < 3:
            return
        
        # Compare to expected distribution
        observed = {d: first_digits.count(d) / len(first_digits) for d in range(1, 10)}
        
        # Chi-square test (simplified)
        chi_square = 0
        for digit in range(1, 10):
            expected = self.BENFORD_DISTRIBUTION[digit]
            obs = observed.get(digit, 0)
            chi_square += (obs - expected) ** 2 / expected
        
        # High chi-square indicates deviation from Benford
        if chi_square > 20:  # Threshold for suspicion
            self._add_signal(
                signal_type=SignalType.BENFORD_VIOLATION,
                severity=SignalSeverity.LOW,
                description="Numeric values deviate from expected Benford's Law distribution",
                confidence=0.4
            )
    
    def _check_round_numbers(self, data: Dict):
        """Detect suspiciously round numbers."""
        
        round_fields = []
        
        cargo_value = data.get('cargo_value')
        if cargo_value:
            try:
                value = float(cargo_value)
                if value >= 10000 and value % 10000 == 0:
                    round_fields.append(('cargo_value', value))
            except (ValueError, TypeError):
                pass
        
        transit_time = data.get('transit_time')
        if transit_time:
            try:
                time = float(transit_time)
                if time >= 10 and time % 5 == 0 and time == int(time):
                    round_fields.append(('transit_time', time))
            except (ValueError, TypeError):
                pass
        
        if len(round_fields) >= 2:
            self._add_signal(
                signal_type=SignalType.ROUND_NUMBER,
                severity=SignalSeverity.LOW,
                description=f"Multiple suspiciously round values: {round_fields}",
                confidence=0.3
            )
    
    def _check_cross_field_consistency(self, data: Dict):
        """Check for inconsistencies between related fields."""
        
        # Air freight with ocean containers
        transport = (data.get('transport_mode') or '').lower()
        container = (data.get('container') or '').lower()
        
        if 'air' in transport and any(c in container for c in ['20ft', '40ft', 'reefer']):
            self._add_signal(
                signal_type=SignalType.CROSS_FIELD_INCONSISTENCY,
                severity=SignalSeverity.HIGH,
                description="Air freight cannot use ocean containers",
                confidence=0.95,
                field_name='container',
                expected='air_container',
                actual=container
            )
        
        # Transit time vs distance
        transit = data.get('transit_time')
        distance = data.get('distance')
        
        if transit and distance:
            try:
                transit = float(transit)
                distance = float(distance)
                
                # Very short transit for long distance (sea)
                if 'sea' in transport or 'ocean' in transport:
                    expected_min_days = distance / 800  # ~800km/day for sea
                    if transit < expected_min_days * 0.5:
                        self._add_signal(
                            signal_type=SignalType.CROSS_FIELD_INCONSISTENCY,
                            severity=SignalSeverity.MEDIUM,
                            description=f"Transit time {transit} days too short for {distance}km by sea",
                            confidence=0.6,
                            field_name='transit_time',
                            expected=f">= {expected_min_days:.0f} days",
                            actual=f"{transit} days"
                        )
            except (ValueError, TypeError):
                pass
        
        # Shipment value vs cargo value
        cargo_value = data.get('cargo_value')
        shipment_value = data.get('shipment_value')
        
        if cargo_value and shipment_value:
            try:
                cv = float(cargo_value)
                sv = float(shipment_value)
                
                if sv < cv * 0.5 or sv > cv * 2:
                    self._add_signal(
                        signal_type=SignalType.CROSS_FIELD_INCONSISTENCY,
                        severity=SignalSeverity.MEDIUM,
                        description=f"Shipment value ${sv:,.0f} inconsistent with cargo value ${cv:,.0f}",
                        confidence=0.7
                    )
            except (ValueError, TypeError):
                pass
    
    def _check_temporal_anomalies(self, data: Dict):
        """Detect temporal anomalies in dates."""
        
        etd = data.get('etd') or data.get('departure_date')
        if not etd:
            return
        
        try:
            from dateutil import parser
            departure = parser.parse(etd)
            now = datetime.utcnow()
            
            # Already departed (retroactive assessment)
            if departure < now:
                days_past = (now - departure).days
                self._add_signal(
                    signal_type=SignalType.TEMPORAL_ANOMALY,
                    severity=SignalSeverity.HIGH,
                    description=f"Retroactive assessment: shipment departed {days_past} days ago",
                    confidence=0.9,
                    field_name='etd'
                )
            
            # Far future assessment
            elif (departure - now).days > 180:
                self._add_signal(
                    signal_type=SignalType.TEMPORAL_ANOMALY,
                    severity=SignalSeverity.LOW,
                    description="Assessing shipment >6 months in advance",
                    confidence=0.4
                )
                
        except Exception:
            pass
    
    def _check_user_patterns(self, history: List[Dict]):
        """Analyze user behavior patterns."""
        
        if len(history) < 5:
            return
        
        # Check for identical scores (potential testing/gaming)
        scores = [h.get('risk_score', 0) for h in history]
        if len(set(scores)) == 1 and len(scores) >= 5:
            self._add_signal(
                signal_type=SignalType.USER_BEHAVIOR,
                severity=SignalSeverity.MEDIUM,
                description="All recent assessments have identical risk scores",
                confidence=0.7
            )
        
        # Check for systematic low scores
        avg_score = np.mean(scores)
        if avg_score < 30 and len(scores) >= 10:
            self._add_signal(
                signal_type=SignalType.USER_BEHAVIOR,
                severity=SignalSeverity.LOW,
                description=f"User average risk score ({avg_score:.1f}) unusually low",
                confidence=0.5
            )
    
    def _check_systematic_probing(self, history: List[Dict]):
        """Detect systematic parameter sweeping (reverse engineering)."""
        
        if len(history) < 10:
            return
        
        # Check if user is varying single parameters systematically
        # (Simplified detection)
        
        # Count rapid-fire requests
        timestamps = [h.get('timestamp') for h in history if h.get('timestamp')]
        if len(timestamps) >= 5:
            try:
                from dateutil import parser
                times = [parser.parse(t) if isinstance(t, str) else t for t in timestamps]
                times.sort()
                
                # Check for burst activity (>10 requests in 1 minute)
                for i in range(len(times) - 10):
                    window = times[i:i+10]
                    if (window[-1] - window[0]).total_seconds() < 60:
                        self._add_signal(
                            signal_type=SignalType.SYSTEMATIC_PROBING,
                            severity=SignalSeverity.HIGH,
                            description="Rapid-fire requests detected (>10/minute) - possible automated probing",
                            confidence=0.8
                        )
                        break
            except Exception:
                pass
    
    def _compute_fraud_score(self) -> float:
        """Aggregate signals into overall fraud score (0-100)."""
        
        if not self.signals:
            return 0.0
        
        weighted_sum = sum(
            self.SEVERITY_WEIGHTS[s.severity] * s.confidence * 100
            for s in self.signals
        )
        
        # Normalize by number of signals (with cap)
        max_signals = 5  # Normalize assuming up to 5 significant signals
        normalized = weighted_sum / max(len(self.signals), 1)
        
        # Scale to 0-100
        fraud_score = min(normalized, 100)
        
        return fraud_score
    
    def _recommend_action(self, fraud_score: float) -> RecommendedAction:
        """Determine recommended action based on fraud score."""
        
        if fraud_score >= 80:
            return RecommendedAction.BLOCK
        elif fraud_score >= 50:
            return RecommendedAction.FLAG
        elif fraud_score >= 20:
            return RecommendedAction.MONITOR
        else:
            return RecommendedAction.ALLOW
    
    def _calculate_risk_penalty(self, fraud_score: float) -> float:
        """Calculate risk score penalty based on fraud score."""
        
        # Up to +10 points penalty
        if fraud_score >= 50:
            return min(10.0, fraud_score * 0.1)
        elif fraud_score >= 20:
            return min(5.0, fraud_score * 0.05)
        else:
            return 0.0
    
    def _generate_explanation(
        self, 
        fraud_score: float, 
        action: RecommendedAction
    ) -> str:
        """Generate human-readable explanation."""
        
        if not self.signals:
            return "No gaming or fraud signals detected. Normal processing."
        
        action_explanations = {
            RecommendedAction.ALLOW: "Normal processing recommended.",
            RecommendedAction.MONITOR: "Track this user for pattern development.",
            RecommendedAction.FLAG: "Apply data quality penalties and log for audit.",
            RecommendedAction.BLOCK: "Request manual review before processing."
        }
        
        top_signals = sorted(
            self.signals, 
            key=lambda s: self.SEVERITY_WEIGHTS[s.severity] * s.confidence,
            reverse=True
        )[:3]
        
        explanation = f"Fraud Score: {fraud_score:.1f}/100\n"
        explanation += f"Action: {action_explanations[action]}\n\n"
        explanation += "Top Signals:\n"
        
        for i, signal in enumerate(top_signals, 1):
            explanation += f"  {i}. [{signal.severity.value.upper()}] {signal.description}\n"
        
        return explanation


# Convenience function for API integration
def analyze_request_for_fraud(
    request_data: Dict[str, Any],
    user_history: Optional[List[Dict]] = None,
    ip_address: Optional[str] = None
) -> Dict:
    """
    Analyze a request for fraud/gaming signals.
    
    Returns analysis result as dictionary.
    """
    detector = FraudDetector()
    result = detector.analyze_request(
        request_data,
        user_history=user_history,
        ip_address=ip_address
    )
    return result.to_dict()
