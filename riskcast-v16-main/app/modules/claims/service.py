"""
Claims Service
Business logic for claims management with state machine
RISKCAST V3 - Modular Monolith
"""
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from datetime import datetime
import logging

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession

from app.modules.claims.models import (
    Claim,
    ClaimEvent,
    Payout,
    ClaimStatus,
    PayoutStatus
)
from app.modules.claims.state_machine import ClaimsStateMachine
from app.modules.claims.exceptions import (
    ClaimNotFoundError,
    PolicyNotFoundError,
    InvalidPolicyStatusError,
    InvalidActionError,
    InvalidTransitionError,
    PayoutNotFoundError
)
from app.modules.underwriting.models import Policy, PolicyStatus
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.models import ActorType
from app.modules.audit_ledger.schemas import AuditContext

logger = logging.getLogger(__name__)


class ClaimsService:
    """Service for claims management with state machine workflow"""
    
    def __init__(self, db: 'TenantScopedSession'):
        """
        Initialize claims service.
        
        Args:
            db: Tenant-scoped database session
        """
        self.db = db
        self.state_machine = ClaimsStateMachine()
        # Audit service needs raw session, not tenant-scoped
        self.audit = AuditLedgerService(db._raw_session)
        logger.debug(f"ClaimsService initialized for tenant_id={db.tenant_id}")
    
    async def _get_claim(self, claim_id: str) -> Claim:
        """
        Get claim by ID with tenant validation.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            Claim instance
            
        Raises:
            ClaimNotFoundError: If claim not found
        """
        claim = self.db.query(Claim).filter(
            Claim.id == claim_id,
            Claim.tenant_id == self.db.tenant_id
        ).first()
        
        if not claim:
            raise ClaimNotFoundError(claim_id)
        
        return claim
    
    async def create_fnol(
        self,
        policy_id: str,
        fnol_data: Dict[str, Any],
        user_id: str,
        context: AuditContext,
        evidence_bundle_id: Optional[str] = None
    ) -> Claim:
        """
        Create First Notice of Loss.
        
        Args:
            policy_id: Policy ID
            fnol_data: FNOL data (incident summary, time, location, alleged loss)
            user_id: User ID creating the FNOL
            context: Audit context
            evidence_bundle_id: Optional evidence bundle ID
            
        Returns:
            Claim instance
            
        Raises:
            PolicyNotFoundError: If policy not found
            InvalidPolicyStatusError: If policy is not active
        """
        # Verify policy exists and is active
        policy = self.db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == self.db.tenant_id
        ).first()
        
        if not policy:
            raise PolicyNotFoundError(policy_id)
        
        if policy.status != PolicyStatus.ACTIVE:
            raise InvalidPolicyStatusError("Policy must be active for claims")
        
        # Create claim
        claim = Claim(
            tenant_id=self.db.tenant_id,
            policy_id=policy_id,
            status=ClaimStatus.FNOL_RECEIVED,
            fnol_json=fnol_data,
            risk_run_id=policy.risk_run_id,  # Reference from underwriting
            evidence_bundle_id=evidence_bundle_id,
            created_by_user_id=user_id
        )
        
        self.db.add(claim)
        self.db.commit()
        
        # Create initial event
        await self._record_event(
            claim=claim,
            event_type='CREATED',
            from_state=None,
            to_state=ClaimStatus.FNOL_RECEIVED,
            actor_id=user_id
        )
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='claim.fnol_received',
            resource_type='claim',
            resource_id=str(claim.id),
            context=context,
            diff={
                'policy_id': policy_id,
                'fnol_data': fnol_data
            }
        )
        
        logger.info(f"FNOL created: {claim.id} for policy {policy_id}")
        return claim
    
    async def take_action(
        self,
        claim_id: str,
        action_type: str,
        user_id: str,
        context: AuditContext,
        evidence_bundle_id: Optional[str] = None,
        payout_amount_cents: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Claim:
        """
        Take action on claim (drives state transitions).
        
        Args:
            claim_id: Claim ID
            action_type: Action type (START_INVESTIGATION, REQUEST_EVIDENCE, etc.)
            user_id: User ID taking the action
            context: Audit context
            evidence_bundle_id: Optional evidence bundle ID
            payout_amount_cents: Optional payout amount (for approval)
            notes: Optional notes
            
        Returns:
            Updated Claim instance
            
        Raises:
            ClaimNotFoundError: If claim not found
            InvalidActionError: If action is unknown
            InvalidTransitionError: If transition is invalid
        """
        claim = await self._get_claim(claim_id)
        
        # Map action to target status
        action_status_map = {
            'START_INVESTIGATION': ClaimStatus.UNDER_INVESTIGATION,
            'REQUEST_EVIDENCE': ClaimStatus.AWAITING_EVIDENCE,
            'PROVIDE_EVIDENCE': ClaimStatus.UNDER_INVESTIGATION,
            'APPROVE': ClaimStatus.APPROVED,
            'DECLINE': ClaimStatus.DECLINED,
            'AUTHORIZE_PAYOUT': ClaimStatus.AUTHORIZED,
            'MARK_PAID': ClaimStatus.PAID,
            'CLOSE': ClaimStatus.CLOSED
        }
        
        target_status = action_status_map.get(action_type)
        if not target_status:
            raise InvalidActionError(f"Unknown action: {action_type}")
        
        # Build context for validation
        validation_context: Dict[str, Any] = {
            'evidence_bundle_id': evidence_bundle_id
        }
        
        # Handle payout creation for approval
        payout = None
        if target_status == ClaimStatus.APPROVED and payout_amount_cents:
            payout = await self._create_payout(claim, payout_amount_cents)
            validation_context['payout_id'] = payout.id
        
        # For authorization, get existing payout
        if target_status == ClaimStatus.AUTHORIZED:
            payout = self.db.query(Payout).filter(
                Payout.claim_id == claim_id,
                Payout.tenant_id == self.db.tenant_id,
                Payout.status == PayoutStatus.APPROVED
            ).first()
            
            if not payout:
                raise PayoutNotFoundError(f"No approved payout found for claim {claim_id}")
            
            validation_context['payout_id'] = payout.id
            validation_context['payout'] = payout
        
        # For payment, get authorized payout
        if target_status == ClaimStatus.PAID:
            payout = self.db.query(Payout).filter(
                Payout.claim_id == claim_id,
                Payout.tenant_id == self.db.tenant_id,
                Payout.status == PayoutStatus.AUTHORIZED
            ).first()
            
            if not payout:
                raise PayoutNotFoundError(f"No authorized payout found for claim {claim_id}")
            
            validation_context['payout'] = payout
        
        # Validate transition
        errors = self.state_machine.validate_transition(claim, target_status, validation_context)
        if errors:
            raise InvalidTransitionError(errors)
        
        # Record event
        old_status = claim.status
        claim.status = target_status
        
        if evidence_bundle_id:
            claim.evidence_bundle_id = evidence_bundle_id
        
        await self._record_event(
            claim=claim,
            event_type='STATE_TRANSITION',
            from_state=old_status,
            to_state=target_status,
            actor_id=user_id,
            notes=notes
        )
        
        # Handle payout status updates
        if payout:
            if target_status == ClaimStatus.APPROVED:
                payout.status = PayoutStatus.APPROVED
                payout.approved_by_user_id = user_id
            elif target_status == ClaimStatus.AUTHORIZED:
                payout.status = PayoutStatus.AUTHORIZED
                payout.approved_by_user_id = user_id
            elif target_status == ClaimStatus.PAID:
                payout.status = PayoutStatus.PAID
                payout.paid_at = datetime.utcnow()
        
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action=f'claim.{action_type.lower()}',
            resource_type='claim',
            resource_id=str(claim_id),
            context=context,
            diff={
                'from_status': str(old_status.value),
                'to_status': str(target_status.value),
                'action': action_type
            }
        )
        
        logger.info(f"Claim action taken: {claim_id} - {action_type} ({old_status.value} -> {target_status.value})")
        return claim
    
    async def _create_payout(
        self,
        claim: Claim,
        amount_cents: int
    ) -> Payout:
        """
        Create payout for claim.
        
        Args:
            claim: Claim instance
            amount_cents: Payout amount in cents
            
        Returns:
            Payout instance
        """
        payout = Payout(
            tenant_id=self.db.tenant_id,
            claim_id=claim.id,
            policy_id=claim.policy_id,
            status=PayoutStatus.PROPOSED,
            amount_cents=amount_cents,
            currency='USD'  # Default, can be made configurable
        )
        
        self.db.add(payout)
        self.db.flush()  # Flush to get ID without committing
        
        logger.info(f"Payout created: {payout.id} for claim {claim.id} ({amount_cents} cents)")
        return payout
    
    async def _record_event(
        self,
        claim: Claim,
        event_type: str,
        from_state: Optional[ClaimStatus],
        to_state: ClaimStatus,
        actor_id: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Record claim event for timeline.
        
        Args:
            claim: Claim instance
            event_type: Event type (STATE_TRANSITION, NOTE_ADDED, etc.)
            from_state: Previous status (if applicable)
            to_state: New status
            actor_id: Actor ID
            notes: Optional notes
        """
        event = ClaimEvent(
            tenant_id=self.db.tenant_id,
            claim_id=claim.id,
            event_type=event_type,
            from_state=from_state.value if from_state else None,
            to_state=to_state.value,
            actor_type='USER',
            actor_id=str(actor_id),
            payload_json={'notes': notes} if notes else None
        )
        
        self.db.add(event)
        logger.debug(f"Claim event recorded: {event.id} for claim {claim.id} ({event_type})")
    
    async def get_timeline(self, claim_id: str) -> List[ClaimEvent]:
        """
        Get claim timeline (all events).
        
        Args:
            claim_id: Claim ID
            
        Returns:
            List of ClaimEvent instances ordered by created_at
        """
        claim = await self._get_claim(claim_id)
        
        events = self.db.query(ClaimEvent).filter(
            ClaimEvent.claim_id == claim_id,
            ClaimEvent.tenant_id == self.db.tenant_id
        ).order_by(ClaimEvent.created_at).all()
        
        return events
    
    async def get_claim(self, claim_id: str) -> Claim:
        """
        Get claim by ID.
        
        Args:
            claim_id: Claim ID
            
        Returns:
            Claim instance
        """
        return await self._get_claim(claim_id)
    
    async def list_claims(
        self,
        policy_id: Optional[str] = None,
        status: Optional[ClaimStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Claim]:
        """
        List claims with optional filters.
        
        Args:
            policy_id: Optional policy ID filter
            status: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Claim instances
        """
        query = self.db.query(Claim).filter(
            Claim.tenant_id == self.db.tenant_id
        )
        
        if policy_id:
            query = query.filter(Claim.policy_id == policy_id)
        
        if status:
            query = query.filter(Claim.status == status)
        
        claims = query.order_by(Claim.created_at.desc()).limit(limit).offset(offset).all()
        
        return claims
