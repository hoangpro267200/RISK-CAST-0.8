"""
Deterministic trigger evaluator.

Evaluates oracle events against trigger definitions.
All evaluation is deterministic and reproducible.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import json
from dataclasses import dataclass

from app.modules.parametric.models import OracleEvent, TriggerDefinition


@dataclass
class EvaluationResult:
    """Result of trigger evaluation."""
    triggered: bool
    measured_value: float
    threshold: float
    comparison: str
    exceeded_by: Optional[float]
    measurement_time: datetime
    primary_oracle_event_id: str
    oracle_events_used: List[str]
    evaluation_hash: str


@dataclass
class ValidationResult:
    """Result of corroboration validation."""
    valid: bool
    corroborating_sources: List[str]
    correlation_score: float
    oracle_event_ids: List[str]
    validation_details: Dict[str, Any]


@dataclass
class PayoutCalculation:
    """Calculated payout amount."""
    payout_type: str
    tier_triggered: Optional[int]
    payout_percentage: float
    base_amount_cents: int
    calculated_amount_cents: int
    calculation_hash: str


class TriggerEvaluator:
    """
    Deterministic trigger evaluation engine.
    
    All evaluation logic must be:
    - Deterministic (same inputs = same outputs)
    - Reproducible (can replay with stored data)
    - Auditable (all decisions logged)
    """
    
    def evaluate(
        self,
        definition: TriggerDefinition,
        oracle_events: List[OracleEvent],
        evaluation_time: Optional[datetime] = None
    ) -> EvaluationResult:
        """
        Evaluate if trigger condition is met.
        
        Args:
            definition: The trigger definition
            oracle_events: Oracle events to evaluate (sorted by time)
            evaluation_time: Time of evaluation (for reproducibility)
            
        Returns:
            EvaluationResult with trigger status
        """
        if not oracle_events:
            raise NoOracleEventsError("No oracle events to evaluate")
        
        params = definition.params_json or {}
        threshold = params.get('threshold_value', 0)
        comparison = params.get('comparison', '>=')
        aggregation = params.get('aggregation', 'MAX')
        duration_hours = params.get('duration_hours', 0)
        
        # Extract values from oracle events
        trigger_type = definition.trigger_type or definition.type or 'RAINFALL'
        values = self._extract_values(oracle_events, trigger_type)
        
        if not values:
            raise NoOracleEventsError("No valid values extracted from oracle events")
        
        # Aggregate based on method
        measured_value = self._aggregate(values, aggregation)
        
        # Compare against threshold
        triggered = self._compare(measured_value, threshold, comparison)
        
        # Check duration requirement if specified
        if triggered and duration_hours > 0:
            triggered = self._check_duration(
                oracle_events, threshold, comparison, duration_hours, trigger_type
            )
        
        # Build evaluation hash for reproducibility
        definition_hash = definition.immutable_hash or ""
        evaluation_hash = self._compute_evaluation_hash(
            definition_hash=definition_hash,
            oracle_event_hashes=[e.payload_hash for e in oracle_events],
            measured_value=measured_value,
            triggered=triggered
        )
        
        exceeded_by = measured_value - threshold if triggered and measured_value > threshold else None
        
        return EvaluationResult(
            triggered=triggered,
            measured_value=measured_value,
            threshold=threshold,
            comparison=comparison,
            exceeded_by=exceeded_by,
            measurement_time=oracle_events[-1].captured_at,
            primary_oracle_event_id=oracle_events[0].id,
            oracle_events_used=[e.id for e in oracle_events],
            evaluation_hash=evaluation_hash
        )
    
    def validate_corroboration(
        self,
        definition: TriggerDefinition,
        primary_event: OracleEvent,
        corroborating_events: List[OracleEvent]
    ) -> ValidationResult:
        """
        Validate trigger with multi-source corroboration.
        
        For parametric payouts, we require confirmation from multiple
        independent data sources.
        
        Args:
            definition: Trigger definition
            primary_event: Primary oracle event
            corroborating_events: List of corroborating events
            
        Returns:
            ValidationResult with validation status
        """
        corroboration = definition.corroboration_json or {}
        required_sources = corroboration.get('required_sources', 2)
        correlation_threshold = corroboration.get('correlation_threshold', 0.7)
        
        # Get unique sources
        all_events = [primary_event] + corroborating_events
        sources = list(set(e.source for e in all_events))
        
        # Check source count requirement
        if len(sources) < required_sources:
            return ValidationResult(
                valid=False,
                corroborating_sources=sources,
                correlation_score=0,
                oracle_event_ids=[e.id for e in all_events],
                validation_details={
                    "error": f"Need {required_sources} sources, got {len(sources)}",
                    "sources": sources
                }
            )
        
        # Calculate correlation score
        correlation_score = self._calculate_correlation(primary_event, corroborating_events)
        
        if correlation_score < correlation_threshold:
            return ValidationResult(
                valid=False,
                corroborating_sources=sources,
                correlation_score=correlation_score,
                oracle_event_ids=[e.id for e in all_events],
                validation_details={
                    "error": f"Correlation {correlation_score} below threshold {correlation_threshold}",
                    "sources": sources
                }
            )
        
        return ValidationResult(
            valid=True,
            corroborating_sources=sources,
            correlation_score=correlation_score,
            oracle_event_ids=[e.id for e in all_events],
            validation_details={
                "sources_used": sources,
                "events_count": len(all_events),
                "correlation_score": correlation_score
            }
        )
    
    def calculate_payout(
        self,
        definition: TriggerDefinition,
        evaluation: EvaluationResult,
        insured_value_cents: int
    ) -> PayoutCalculation:
        """
        Calculate payout amount based on trigger result.
        
        Deterministic calculation based on payout structure.
        
        Args:
            definition: Trigger definition
            evaluation: Evaluation result
            insured_value_cents: Insured value in cents
            
        Returns:
            PayoutCalculation with calculated amount
        """
        if not evaluation.triggered:
            return PayoutCalculation(
                payout_type="NONE",
                tier_triggered=None,
                payout_percentage=0,
                base_amount_cents=insured_value_cents,
                calculated_amount_cents=0,
                calculation_hash=""
            )
        
        payout_structure = definition.payout_structure_json or {}
        payout_type = payout_structure.get('type', 'FIXED')
        
        if payout_type == 'FIXED':
            amount = payout_structure.get('fixed_amount_cents', 0)
            pct = amount / insured_value_cents if insured_value_cents > 0 else 0
            tier = None
            
        elif payout_type == 'PERCENTAGE':
            pct = payout_structure.get('percentage', 0)
            amount = int(insured_value_cents * pct)
            tier = None
            
        elif payout_type == 'TIERED':
            tiers = payout_structure.get('tiers', [])
            # Find applicable tier
            tier = None
            pct = 0
            for i, t in enumerate(sorted(tiers, key=lambda x: x.get('threshold', 0), reverse=True)):
                if evaluation.measured_value >= t.get('threshold', 0):
                    tier = i + 1
                    pct = t.get('payout_pct', 0)
                    break
            amount = int(insured_value_cents * pct) if pct > 0 else 0
            
        else:
            raise InvalidPayoutStructureError(f"Unknown payout type: {payout_type}")
        
        # Compute calculation hash
        definition_hash = definition.immutable_hash or ""
        calc_hash = self._compute_calculation_hash(
            definition_hash=definition_hash,
            evaluation_hash=evaluation.evaluation_hash,
            amount=amount
        )
        
        return PayoutCalculation(
            payout_type=payout_type,
            tier_triggered=tier,
            payout_percentage=pct,
            base_amount_cents=insured_value_cents,
            calculated_amount_cents=amount,
            calculation_hash=calc_hash
        )
    
    def _extract_values(
        self,
        events: List[OracleEvent],
        trigger_type: str
    ) -> List[float]:
        """
        Extract relevant values from oracle events.
        
        Args:
            events: List of oracle events
            trigger_type: Trigger type
            
        Returns:
            List of extracted values
        """
        value_keys = {
            'RAINFALL': ['rainfall_mm', 'precipitation_mm', 'rainfall'],
            'WIND_SPEED': ['wind_speed_kmh', 'wind_speed_ms', 'wind_speed'],
            'TEMPERATURE': ['temperature_c', 'temp_c', 'temperature'],
            'FLOOD': ['flood_depth_m', 'water_level_m', 'flood_depth'],
            'DELAY': ['delay_hours', 'delay_minutes', 'delay']
        }
        
        keys = value_keys.get(trigger_type, [trigger_type.lower()])
        values = []
        
        for event in events:
            payload = event.payload_json or {}
            for key in keys:
                if key in payload:
                    try:
                        val = float(payload[key])
                        values.append(val)
                        break
                    except (ValueError, TypeError):
                        continue
        
        return values
    
    def _aggregate(self, values: List[float], method: str) -> float:
        """
        Aggregate values using specified method.
        
        Args:
            values: List of values
            method: Aggregation method (MAX, MIN, AVG, SUM, ANY)
            
        Returns:
            Aggregated value
        """
        if not values:
            return 0
        
        if method == 'MAX':
            return max(values)
        elif method == 'MIN':
            return min(values)
        elif method == 'AVG':
            return sum(values) / len(values)
        elif method == 'SUM':
            return sum(values)
        elif method == 'ANY':
            return max(values)  # Any exceedance
        else:
            return max(values)  # Default to MAX
    
    def _compare(self, value: float, threshold: float, comparison: str) -> bool:
        """
        Compare value against threshold.
        
        Args:
            value: Value to compare
            threshold: Threshold value
            comparison: Comparison operator
            
        Returns:
            True if condition met
        """
        if comparison == '>=':
            return value >= threshold
        elif comparison == '>':
            return value > threshold
        elif comparison == '<=':
            return value <= threshold
        elif comparison == '<':
            return value < threshold
        elif comparison == '==':
            return abs(value - threshold) < 0.001
        elif comparison == '!=':
            return abs(value - threshold) >= 0.001
        else:
            return value >= threshold  # Default
    
    def _check_duration(
        self,
        events: List[OracleEvent],
        threshold: float,
        comparison: str,
        duration_hours: int,
        trigger_type: str
    ) -> bool:
        """
        Check if condition sustained for duration.
        
        Args:
            events: Oracle events
            threshold: Threshold value
            comparison: Comparison operator
            duration_hours: Required duration in hours
            trigger_type: Trigger type
            
        Returns:
            True if condition sustained
        """
        if len(events) < 2:
            return True  # Single event, assume sustained
        
        # Check time span
        start = min(e.captured_at for e in events)
        end = max(e.captured_at for e in events)
        span_hours = (end - start).total_seconds() / 3600
        
        if span_hours < duration_hours:
            return False  # Not enough data
        
        # Check all events meet threshold
        values = self._extract_values(events, trigger_type)
        for val in values:
            if not self._compare(val, threshold, comparison):
                return False
        
        return True
    
    def _calculate_correlation(
        self,
        primary: OracleEvent,
        corroborating: List[OracleEvent]
    ) -> float:
        """
        Calculate correlation score between events.
        
        Args:
            primary: Primary oracle event
            corroborating: List of corroborating events
            
        Returns:
            Correlation score (0-1)
        """
        if not corroborating:
            return 0
        
        # Extract primary value
        primary_payload = primary.payload_json or {}
        primary_values = [v for v in primary_payload.values() if isinstance(v, (int, float))]
        if not primary_values:
            return 0
        
        primary_val = float(primary_values[0])
        
        correlations = []
        for event in corroborating:
            event_payload = event.payload_json or {}
            event_values = [v for v in event_payload.values() if isinstance(v, (int, float))]
            if event_values:
                event_val = float(event_values[0])
                if primary_val > 0:
                    # Calculate similarity
                    diff = abs(primary_val - event_val)
                    correlation = 1 - (diff / max(primary_val, abs(event_val)))
                    correlations.append(max(0, min(1, correlation)))
                elif primary_val == event_val:
                    correlations.append(1.0)
        
        return sum(correlations) / len(correlations) if correlations else 0
    
    def _compute_evaluation_hash(
        self,
        definition_hash: str,
        oracle_event_hashes: List[str],
        measured_value: float,
        triggered: bool
    ) -> str:
        """
        Compute deterministic evaluation hash.
        
        Args:
            definition_hash: Definition immutable hash
            oracle_event_hashes: List of oracle event payload hashes
            measured_value: Measured value
            triggered: Whether trigger was met
            
        Returns:
            SHA256 hash string
        """
        hashable = {
            "definition_hash": definition_hash,
            "oracle_hashes": sorted(oracle_event_hashes),
            "measured_value": round(measured_value, 6),  # Round for consistency
            "triggered": triggered
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def _compute_calculation_hash(
        self,
        definition_hash: str,
        evaluation_hash: str,
        amount: int
    ) -> str:
        """
        Compute deterministic calculation hash.
        
        Args:
            definition_hash: Definition immutable hash
            evaluation_hash: Evaluation hash
            amount: Calculated amount in cents
            
        Returns:
            SHA256 hash string
        """
        hashable = {
            "definition_hash": definition_hash,
            "evaluation_hash": evaluation_hash,
            "amount_cents": amount
        }
        canonical = json.dumps(hashable, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(canonical.encode()).hexdigest()


# Exception classes
class NoOracleEventsError(Exception):
    """No oracle events provided"""
    pass


class InvalidPayoutStructureError(Exception):
    """Invalid payout structure"""
    pass
