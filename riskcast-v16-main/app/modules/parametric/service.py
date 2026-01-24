"""
Parametric Service
Business logic for parametric insurance triggers and oracle events
RISKCAST V3 - Modular Monolith
"""
import hashlib
import json
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime, timedelta
import logging

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession

from app.modules.parametric.models import (
    TriggerDefinition,
    OracleEvent,
    TriggerEvent,
    TriggerDefinitionStatus,
    TriggerEventStatus
)
from app.modules.parametric.exceptions import (
    TriggerDefinitionNotFoundError,
    TriggerAlreadyPublishedError,
    TriggerEventNotFoundError,
    InvalidTransitionError as ParametricInvalidTransitionError
)
from app.modules.underwriting.models import Policy, PolicyStatus
from app.modules.claims.models import Payout, PayoutStatus
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.models import ActorType
from app.modules.audit_ledger.schemas import AuditContext

logger = logging.getLogger(__name__)


class ParametricService:
    """Service for parametric insurance triggers and oracle events"""
    
    def __init__(self, db: 'TenantScopedSession'):
        """
        Initialize parametric service.
        
        Args:
            db: Tenant-scoped database session
        """
        self.db = db
        # Audit service needs raw session, not tenant-scoped
        self.audit = AuditLedgerService(db._raw_session)
        logger.debug(f"ParametricService initialized for tenant_id={db.tenant_id}")
    
    async def _get_trigger(self, trigger_id: str) -> TriggerDefinition:
        """
        Get trigger definition by ID with tenant validation.
        
        Args:
            trigger_id: Trigger definition ID
            
        Returns:
            TriggerDefinition instance
            
        Raises:
            TriggerDefinitionNotFoundError: If trigger not found
        """
        trigger = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.id == trigger_id,
            TriggerDefinition.tenant_id == self.db.tenant_id
        ).first()
        
        if not trigger:
            raise TriggerDefinitionNotFoundError(trigger_id)
        
        return trigger
    
    async def _get_trigger_event(self, trigger_event_id: str) -> TriggerEvent:
        """
        Get trigger event by ID with tenant validation.
        
        Args:
            trigger_event_id: Trigger event ID
            
        Returns:
            TriggerEvent instance
            
        Raises:
            TriggerEventNotFoundError: If trigger event not found
        """
        trigger_event = self.db.query(TriggerEvent).filter(
            TriggerEvent.id == trigger_event_id,
            TriggerEvent.tenant_id == self.db.tenant_id
        ).first()
        
        if not trigger_event:
            raise TriggerEventNotFoundError(trigger_event_id)
        
        return trigger_event
    
    async def create_trigger_definition(
        self,
        trigger_type: str,
        params: Dict[str, Any],
        user_id: str,
        context: AuditContext
    ) -> TriggerDefinition:
        """
        Create draft trigger definition.
        
        Args:
            trigger_type: Trigger type (TEMP_EXCURSION, DELAY_THRESHOLD, etc.)
            params: Trigger parameters (threshold, window, corridor, corroboration rules)
            user_id: User ID creating the trigger
            context: Audit context
            
        Returns:
            TriggerDefinition instance
        """
        # Get next version for this type
        latest = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.type == trigger_type,
            TriggerDefinition.tenant_id == self.db.tenant_id
        ).order_by(TriggerDefinition.version.desc()).first()
        
        version = (latest.version + 1) if latest else 1
        
        trigger = TriggerDefinition(
            tenant_id=self.db.tenant_id,
            type=trigger_type,
            version=version,
            status=TriggerDefinitionStatus.DRAFT,
            params_json=params,
            created_by_user_id=user_id
        )
        
        self.db.add(trigger)
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='trigger_definition.created',
            resource_type='trigger_definition',
            resource_id=str(trigger.id),
            context=context,
            diff={
                'type': trigger_type,
                'version': version,
                'status': TriggerDefinitionStatus.DRAFT.value
            }
        )
        
        logger.info(f"Trigger definition created: {trigger.id} ({trigger_type} v{version})")
        return trigger
    
    async def publish_trigger(
        self,
        trigger_id: str,
        user_id: str,
        context: AuditContext
    ) -> TriggerDefinition:
        """
        Publish trigger definition (makes it immutable).
        
        Args:
            trigger_id: Trigger definition ID
            user_id: User ID publishing the trigger
            context: Audit context
            
        Returns:
            Updated TriggerDefinition instance
            
        Raises:
            TriggerAlreadyPublishedError: If trigger is already published
            ValidationError: If corroboration rules are missing
        """
        trigger = await self._get_trigger(trigger_id)
        
        if trigger.status != TriggerDefinitionStatus.DRAFT:
            raise TriggerAlreadyPublishedError(trigger_id)
        
        # Validate corroboration rules present
        if not trigger.params_json.get('corroboration_rules'):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corroboration rules required for publishing"
            )
        
        # Compute immutable hash
        canonical = json.dumps(trigger.params_json, sort_keys=True, separators=(',', ':'))
        trigger.immutable_hash = hashlib.sha256(canonical.encode()).hexdigest()
        trigger.status = TriggerDefinitionStatus.PUBLISHED
        trigger.published_at = datetime.utcnow()
        
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='trigger_definition.published',
            resource_type='trigger_definition',
            resource_id=str(trigger_id),
            context=context,
            diff={
                'status': TriggerDefinitionStatus.PUBLISHED.value,
                'immutable_hash': trigger.immutable_hash[:16] + '...'  # Truncate for audit
            }
        )
        
        logger.info(f"Trigger definition published: {trigger_id} (hash: {trigger.immutable_hash[:16]}...)")
        return trigger
    
    async def ingest_oracle_event(
        self,
        source: str,
        captured_at: datetime,
        payload: Dict[str, Any],
        context: AuditContext,
        tenant_id: Optional[str] = None
    ) -> OracleEvent:
        """
        Ingest oracle event from external source.
        
        Args:
            source: Event source (NOAA, CARRIER_API, IOT_PROVIDER, etc.)
            captured_at: When event was captured
            payload: Event payload data
            context: Audit context
            tenant_id: Optional tenant ID (None for global events)
            
        Returns:
            OracleEvent instance
        """
        # Compute payload hash for deduplication
        canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        payload_hash = hashlib.sha256(canonical.encode()).hexdigest()
        
        # Check for duplicate
        existing = self.db.query(OracleEvent).filter(
            OracleEvent.payload_hash == payload_hash
        ).first()
        
        if existing:
            logger.info(f"Oracle event deduplication: Found existing event {existing.id} with hash {payload_hash[:16]}...")
            return existing
        
        # Use tenant_id from session if not provided
        event_tenant_id = tenant_id or self.db.tenant_id
        
        event = OracleEvent(
            tenant_id=event_tenant_id,
            source=source,
            captured_at=captured_at,
            payload_json=payload,
            payload_hash=payload_hash
        )
        
        self.db.add(event)
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=event_tenant_id,
            actor_type=ActorType.SYSTEM,
            actor_id='system',
            action='oracle_event.ingested',
            resource_type='oracle_event',
            resource_id=str(event.id),
            context=context,
            diff={
                'source': source,
                'captured_at': captured_at.isoformat() + 'Z'
            }
        )
        
        logger.info(f"Oracle event ingested: {event.id} from {source}")
        return event
    
    async def evaluate_triggers(self, lookback_hours: int = 24) -> List[TriggerEvent]:
        """
        Evaluate active triggers against recent oracle events.
        Called by scheduled worker.
        
        Args:
            lookback_hours: Hours to look back for oracle events (default: 24)
            
        Returns:
            List of detected TriggerEvent instances
        """
        # Get published triggers
        triggers = self.db.query(TriggerDefinition).filter(
            TriggerDefinition.status == TriggerDefinitionStatus.PUBLISHED,
            TriggerDefinition.tenant_id == self.db.tenant_id
        ).all()
        
        if not triggers:
            logger.debug("No published triggers found for evaluation")
            return []
        
        # Get recent oracle events
        cutoff_time = datetime.utcnow() - timedelta(hours=lookback_hours)
        oracle_events = self.db.query(OracleEvent).filter(
            OracleEvent.captured_at >= cutoff_time
        ).order_by(OracleEvent.captured_at.desc()).all()
        
        if not oracle_events:
            logger.debug(f"No oracle events found in last {lookback_hours} hours")
            return []
        
        detected_events = []
        
        for trigger in triggers:
            # Get active policies with this trigger type
            policies = await self._get_policies_with_trigger(trigger)
            
            for policy in policies:
                # Evaluate trigger against oracle events
                match = await self._evaluate_trigger_for_policy(trigger, policy, oracle_events)
                
                if match:
                    trigger_event = await self._create_trigger_event(
                        trigger, policy, match
                    )
                    detected_events.append(trigger_event)
        
        logger.info(f"Trigger evaluation completed: {len(detected_events)} events detected")
        return detected_events
    
    async def _get_policies_with_trigger(self, trigger: TriggerDefinition) -> List[Policy]:
        """
        Get active policies that have this trigger type configured.
        
        Args:
            trigger: Trigger definition
            
        Returns:
            List of Policy instances
        """
        # For now, return all active policies
        # In production, this would check policy terms_json for trigger configuration
        policies = self.db.query(Policy).filter(
            Policy.tenant_id == self.db.tenant_id,
            Policy.status == PolicyStatus.ACTIVE
        ).all()
        
        return policies
    
    async def _evaluate_trigger_for_policy(
        self,
        trigger: TriggerDefinition,
        policy: Policy,
        oracle_events: List[OracleEvent]
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluate trigger against oracle events for a policy.
        
        Args:
            trigger: Trigger definition
            policy: Policy instance
            oracle_events: List of oracle events to evaluate
            
        Returns:
            Match dictionary if trigger matches, None otherwise
        """
        # Simple evaluation logic (can be extended)
        # Check if any oracle event matches trigger parameters
        params = trigger.params_json
        
        for event in oracle_events:
            # Check if event matches trigger criteria
            if self._event_matches_trigger(event, trigger, policy):
                return {
                    'oracle_event_id': event.id,
                    'matched_at': event.captured_at,
                    'validation': {
                        'source': event.source,
                        'payload': event.payload_json
                    }
                }
        
        return None
    
    def _event_matches_trigger(
        self,
        event: OracleEvent,
        trigger: TriggerDefinition,
        policy: Policy
    ) -> bool:
        """
        Check if oracle event matches trigger criteria.
        
        This is a simplified implementation. In production, this would:
        - Check thresholds
        - Validate corridors
        - Apply corroboration rules
        - Check policy effective dates
        
        Args:
            event: Oracle event
            trigger: Trigger definition
            policy: Policy instance
            
        Returns:
            True if event matches trigger, False otherwise
        """
        # Simplified matching logic
        # In production, implement full trigger evaluation
        params = trigger.params_json
        
        # Check if event is within policy effective period
        if event.captured_at < policy.effective_from or event.captured_at > policy.effective_to:
            return False
        
        # Check trigger type-specific logic
        if trigger.type == 'TEMP_EXCURSION':
            # Check temperature threshold
            temp = event.payload_json.get('temperature')
            threshold = params.get('threshold')
            if temp and threshold and temp > threshold:
                return True
        
        elif trigger.type == 'DELAY_THRESHOLD':
            # Check delay threshold
            delay_hours = event.payload_json.get('delay_hours')
            threshold = params.get('threshold')
            if delay_hours and threshold and delay_hours > threshold:
                return True
        
        return False
    
    async def _create_trigger_event(
        self,
        trigger: TriggerDefinition,
        policy: Policy,
        match: Dict[str, Any]
    ) -> TriggerEvent:
        """
        Create trigger event from match.
        
        Args:
            trigger: Trigger definition
            policy: Policy instance
            match: Match dictionary from evaluation
            
        Returns:
            TriggerEvent instance
        """
        trigger_event = TriggerEvent(
            tenant_id=self.db.tenant_id,
            trigger_definition_id=trigger.id,
            policy_id=policy.id,
            status=TriggerEventStatus.DETECTED,
            matched_at=match['matched_at'],
            validation_json=match['validation']
        )
        
        self.db.add(trigger_event)
        self.db.commit()
        
        logger.info(f"Trigger event created: {trigger_event.id} for policy {policy.id}")
        return trigger_event
    
    async def approve_payout(
        self,
        trigger_event_id: str,
        user_id: str,
        context: AuditContext
    ) -> TriggerEvent:
        """
        Approve payout for trigger event.
        
        Args:
            trigger_event_id: Trigger event ID
            user_id: User ID approving the payout
            context: Audit context
            
        Returns:
            Updated TriggerEvent instance
            
        Raises:
            TriggerEventNotFoundError: If trigger event not found
            ParametricInvalidTransitionError: If status is invalid
        """
        event = await self._get_trigger_event(trigger_event_id)
        
        if event.status != TriggerEventStatus.PROPOSED_PAYOUT:
            raise ParametricInvalidTransitionError(
                ["Must be in PROPOSED_PAYOUT status"]
            )
        
        if not event.payout_id:
            raise ParametricInvalidTransitionError(
                ["Payout ID required for approval"]
            )
        
        # Update payout status
        payout = self.db.query(Payout).filter(
            Payout.id == event.payout_id,
            Payout.tenant_id == self.db.tenant_id
        ).first()
        
        if not payout:
            from app.modules.claims.exceptions import PayoutNotFoundError
            raise PayoutNotFoundError(event.payout_id)
        
        payout.status = PayoutStatus.AUTHORIZED
        payout.approved_by_user_id = user_id
        
        event.status = TriggerEventStatus.APPROVED
        
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='trigger_payout.approved',
            resource_type='trigger_event',
            resource_id=str(trigger_event_id),
            context=context,
            diff={
                'payout_id': str(event.payout_id),
                'status': TriggerEventStatus.APPROVED.value
            }
        )
        
        logger.info(f"Trigger payout approved: {trigger_event_id} (payout: {event.payout_id})")
        return event
