"""
Trigger event lifecycle service.

Handles detection, validation, and payout proposal for trigger events.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.modules.parametric.models import (
    TriggerEvent, TriggerEventStatus, TriggerDefinition, TriggerDefinitionStatus
)
from app.modules.underwriting.models import Policy
from app.modules.parametric.models import OracleEvent
from app.core.parametric.evaluator import (
    TriggerEvaluator, EvaluationResult, ValidationResult, NoOracleEventsError
)
from app.services.oracle_event_service import OracleEventService
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class TriggerEventService:
    """Service for managing trigger events."""
    
    def __init__(
        self,
        db: Session,
        audit: Optional[AuditLedger] = None,
        oracle_service: Optional[OracleEventService] = None,
        evidence_service: Optional[Any] = None
    ):
        """
        Initialize trigger event service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
            oracle_service: Optional oracle event service
            evidence_service: Optional evidence service
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
        self.oracle_service = oracle_service
        self.evidence_service = evidence_service
        self.evaluator = TriggerEvaluator()
    
    def detect_trigger(
        self,
        policy_id: str,
        definition_id: str,
        oracle_event_ids: List[str]
    ) -> TriggerEvent:
        """
        Detect and record a potential trigger event.
        
        This creates a trigger event in DETECTED status.
        
        Args:
            policy_id: Policy ID (ULID string)
            definition_id: Trigger definition ID (ULID string)
            oracle_event_ids: List of oracle event IDs (ULID strings)
            
        Returns:
            Created TriggerEvent instance
        """
        # Get policy and definition
        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise PolicyNotFoundError(f"Policy {policy_id} not found")
        
        definition = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.id == definition_id,
            TriggerDefinition.status == TriggerDefinitionStatus.PUBLISHED
        ).first()
        if not definition:
            raise TriggerDefinitionNotFoundError(
                f"Definition {definition_id} not found or not published"
            )
        
        # Get oracle events
        oracle_events = self.db.query(OracleEvent).filter(
            OracleEvent.id.in_(oracle_event_ids)
        ).order_by(OracleEvent.captured_at).all()
        
        if not oracle_events:
            raise NoOracleEventsError("No oracle events found")
        
        # Evaluate trigger
        evaluation = self.evaluator.evaluate(definition, oracle_events)
        
        if not evaluation.triggered:
            raise TriggerNotMetError("Trigger conditions not met")
        
        # Create trigger event
        trigger_event = TriggerEvent(
            id=generate_ulid(),
            tenant_id=policy.tenant_id,
            trigger_definition_id=definition_id,
            policy_id=policy_id,
            status=TriggerEventStatus.DETECTED,
            detected_at=datetime.utcnow(),
            matched_at=datetime.utcnow(),  # Legacy field
            detection_json={
                "measured_value": evaluation.measured_value,
                "threshold": evaluation.threshold,
                "exceeded_by": evaluation.exceeded_by,
                "measurement_time": evaluation.measurement_time.isoformat(),
                "primary_oracle_event_id": evaluation.primary_oracle_event_id,
                "oracle_events_used": evaluation.oracle_events_used
            },
            evaluation_hash=evaluation.evaluation_hash,
            created_at=datetime.utcnow()
        )
        
        self.db.add(trigger_event)
        self.db.commit()
        self.db.refresh(trigger_event)
        
        # Audit
        self.audit.append_event(
            tenant_id=policy.tenant_id,
            event_type="TRIGGER_EVENT",
            action="DETECTED",
            entity_type="trigger_event",
            entity_id=trigger_event.id,
            actor_type="SYSTEM",
            actor_id=None,
            payload={
                "policy_id": policy_id,
                "definition_id": definition_id,
                "measured_value": evaluation.measured_value,
                "evaluation_hash": evaluation.evaluation_hash
            }
        )
        
        logger.info(f"Detected trigger event: {trigger_event.id} for policy {policy_id}")
        
        return trigger_event
    
    def validate_trigger(
        self,
        trigger_event_id: str,
        validated_by: Optional[str] = None
    ) -> TriggerEvent:
        """
        Validate trigger with multi-source corroboration.
        
        Args:
            trigger_event_id: Trigger event ID (ULID string)
            validated_by: Optional user ID validating (ULID string)
            
        Returns:
            Updated TriggerEvent instance
        """
        trigger_event = self._get_trigger_event(trigger_event_id)
        
        if trigger_event.status != TriggerEventStatus.DETECTED:
            raise InvalidTriggerStateError(f"Trigger is {trigger_event.status.value}, must be DETECTED")
        
        trigger_event.status = TriggerEventStatus.VALIDATING
        self.db.commit()
        
        # Get definition
        definition = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.id == trigger_event.trigger_definition_id
        ).first()
        
        # Get primary oracle event
        detection = trigger_event.detection_json or {}
        primary_event_id = detection.get('primary_oracle_event_id')
        if not primary_event_id:
            raise InvalidTriggerStateError("No primary oracle event in detection")
        
        primary_event = self.db.query(OracleEvent).filter(
            OracleEvent.id == primary_event_id
        ).first()
        
        if not primary_event:
            raise NoOracleEventsError(f"Primary oracle event {primary_event_id} not found")
        
        # Find corroborating events
        corroborating = []
        if self.oracle_service:
            corroborating = self.oracle_service.find_corroborating_events(primary_event_id)
        
        # Validate corroboration
        validation = self.evaluator.validate_corroboration(
            definition, primary_event, corroborating
        )
        
        trigger_event.validation_json = {
            "corroborating_sources": validation.corroborating_sources,
            "correlation_score": validation.correlation_score,
            "oracle_event_ids": validation.oracle_event_ids,
            "validation_passed": validation.valid,
            "validation_details": validation.validation_details
        }
        trigger_event.validated_at = datetime.utcnow()
        
        if validation.valid:
            trigger_event.status = TriggerEventStatus.VALIDATED
            
            # Create evidence bundle with oracle data if service available
            if self.evidence_service:
                try:
                    bundle = self._create_oracle_evidence_bundle(
                        trigger_event, primary_event, corroborating
                    )
                    if bundle:
                        trigger_event.evidence_bundle_id = bundle.id
                except Exception as e:
                    logger.warning(f"Failed to create evidence bundle: {e}")
        else:
            trigger_event.status = TriggerEventStatus.CORROBORATION_FAILED
        
        self.db.commit()
        self.db.refresh(trigger_event)
        
        # Audit
        self.audit.append_event(
            tenant_id=trigger_event.tenant_id,
            event_type="TRIGGER_EVENT",
            action="VALIDATED" if validation.valid else "CORROBORATION_FAILED",
            entity_type="trigger_event",
            entity_id=trigger_event_id,
            actor_type="USER" if validated_by else "SYSTEM",
            actor_id=validated_by,
            payload={
                "validation_passed": validation.valid,
                "correlation_score": validation.correlation_score,
                "sources": validation.corroborating_sources
            }
        )
        
        logger.info(
            f"Validated trigger event: {trigger_event_id} "
            f"(passed={validation.valid}, score={validation.correlation_score})"
        )
        
        return trigger_event
    
    def propose_payout(
        self,
        trigger_event_id: str,
        proposed_by: str
    ) -> TriggerEvent:
        """
        Calculate and propose payout for validated trigger.
        
        Args:
            trigger_event_id: Trigger event ID (ULID string)
            proposed_by: User ID proposing (ULID string)
            
        Returns:
            Updated TriggerEvent instance
        """
        trigger_event = self._get_trigger_event(trigger_event_id)
        
        if trigger_event.status != TriggerEventStatus.VALIDATED:
            raise InvalidTriggerStateError(
                f"Trigger must be VALIDATED, is {trigger_event.status.value}"
            )
        
        # Get definition and policy
        definition = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.id == trigger_event.trigger_definition_id
        ).first()
        
        policy = self.db.query(Policy).filter(
            Policy.id == trigger_event.policy_id
        ).first()
        
        insured_value = (policy.terms_json or {}).get('insured_value_cents', 0)
        
        # Create evaluation result from stored detection
        detection = trigger_event.detection_json or {}
        evaluation = EvaluationResult(
            triggered=True,
            measured_value=detection.get('measured_value', 0),
            threshold=detection.get('threshold', 0),
            comparison=">=",
            exceeded_by=detection.get('exceeded_by'),
            measurement_time=datetime.fromisoformat(
                detection.get('measurement_time', datetime.utcnow().isoformat())
            ),
            primary_oracle_event_id=detection.get('primary_oracle_event_id', ''),
            oracle_events_used=detection.get('oracle_events_used', []),
            evaluation_hash=trigger_event.evaluation_hash or ''
        )
        
        # Calculate payout
        payout_calc = self.evaluator.calculate_payout(
            definition, evaluation, insured_value
        )
        
        trigger_event.payout_calculation_json = {
            "payout_type": payout_calc.payout_type,
            "tier_triggered": payout_calc.tier_triggered,
            "payout_percentage": payout_calc.payout_percentage,
            "base_amount_cents": payout_calc.base_amount_cents,
            "calculated_amount_cents": payout_calc.calculated_amount_cents,
            "calculation_hash": payout_calc.calculation_hash
        }
        trigger_event.proposed_payout_cents = payout_calc.calculated_amount_cents
        trigger_event.status = TriggerEventStatus.PROPOSED_PAYOUT
        trigger_event.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(trigger_event)
        
        # Audit
        self.audit.append_event(
            tenant_id=trigger_event.tenant_id,
            event_type="TRIGGER_EVENT",
            action="PAYOUT_PROPOSED",
            entity_type="trigger_event",
            entity_id=trigger_event_id,
            actor_type="USER",
            actor_id=proposed_by,
            payload={
                "proposed_amount_cents": payout_calc.calculated_amount_cents,
                "calculation_hash": payout_calc.calculation_hash
            }
        )
        
        logger.info(
            f"Proposed payout for trigger event: {trigger_event_id} "
            f"(amount={payout_calc.calculated_amount_cents} cents)"
        )
        
        return trigger_event
    
    def approve_trigger_payout(
        self,
        trigger_event_id: str,
        approved_by: str
    ) -> TriggerEvent:
        """
        Approve trigger event for payout.
        
        Args:
            trigger_event_id: Trigger event ID (ULID string)
            approved_by: User ID approving (ULID string)
            
        Returns:
            Updated TriggerEvent instance
        """
        trigger_event = self._get_trigger_event(trigger_event_id)
        
        if trigger_event.status != TriggerEventStatus.PROPOSED_PAYOUT:
            raise InvalidTriggerStateError(
                f"Payout must be PROPOSED_PAYOUT, is {trigger_event.status.value}"
            )
        
        trigger_event.status = TriggerEventStatus.APPROVED
        trigger_event.approved_at = datetime.utcnow()
        trigger_event.approved_by_user_id = approved_by
        trigger_event.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(trigger_event)
        
        # Audit
        self.audit.append_event(
            tenant_id=trigger_event.tenant_id,
            event_type="TRIGGER_EVENT",
            action="APPROVED",
            entity_type="trigger_event",
            entity_id=trigger_event_id,
            actor_type="USER",
            actor_id=approved_by,
            payload={
                "approved_amount_cents": trigger_event.proposed_payout_cents
            }
        )
        
        logger.info(f"Approved trigger event: {trigger_event_id}")
        
        return trigger_event
    
    def _get_trigger_event(self, trigger_event_id: str) -> TriggerEvent:
        """
        Get trigger event by ID.
        
        Args:
            trigger_event_id: Trigger event ID (ULID string)
            
        Returns:
            TriggerEvent instance
            
        Raises:
            TriggerEventNotFoundError: If event not found
        """
        event = self.db.query(TriggerEvent).filter(
            TriggerEvent.id == trigger_event_id
        ).first()
        if not event:
            raise TriggerEventNotFoundError(f"Trigger event {trigger_event_id} not found")
        return event
    
    def _create_oracle_evidence_bundle(
        self,
        trigger_event: TriggerEvent,
        primary_event: OracleEvent,
        corroborating: List[OracleEvent]
    ) -> Optional[Any]:
        """
        Create evidence bundle with oracle event data.
        
        Args:
            trigger_event: Trigger event
            primary_event: Primary oracle event
            corroborating: Corroborating events
            
        Returns:
            EvidenceBundle instance or None
        """
        # Implementation would create evidence objects from oracle payloads
        # and bundle them together
        # This is a placeholder - actual implementation depends on EvidenceService API
        if not self.evidence_service:
            return None
        
        try:
            # Create evidence bundle with oracle data
            # This would typically involve:
            # 1. Creating evidence objects for each oracle event
            # 2. Bundling them together
            # 3. Sealing the bundle
            # For now, return None as placeholder
            return None
        except Exception as e:
            logger.error(f"Failed to create evidence bundle: {e}")
            return None


# Exception classes
class PolicyNotFoundError(Exception):
    """Policy not found"""
    pass


class TriggerDefinitionNotFoundError(Exception):
    """Trigger definition not found"""
    pass


class NoOracleEventsError(Exception):
    """No oracle events"""
    pass


class TriggerNotMetError(Exception):
    """Trigger conditions not met"""
    pass


class TriggerEventNotFoundError(Exception):
    """Trigger event not found"""
    pass


class InvalidTriggerStateError(Exception):
    """Invalid trigger state for operation"""
    pass
