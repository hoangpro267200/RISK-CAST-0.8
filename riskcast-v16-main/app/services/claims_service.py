"""
Claims management service.

Handles claims lifecycle with state machine pattern.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.modules.claims.models import Claim, ClaimEvent, ClaimStatus
from app.modules.underwriting.models import Policy, PolicyStatus
from app.models.evidence_bundle import EvidenceBundle
from app.core.claims.state_machine import ClaimStateMachine
from app.core.audit_ledger.ledger import AuditLedger

logger = logging.getLogger(__name__)


class ClaimsService:
    """Service for managing claims."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize claims service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def file_claim(
        self,
        tenant_id: str,
        policy_id: str,
        fnol: Dict[str, Any],
        filed_by: str
    ) -> Claim:
        """
        File a new claim (FNOL - First Notice of Loss).
        
        FNOL is immutable once filed.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            policy_id: Policy ID (ULID string)
            fnol: FNOL data dictionary
            filed_by: User ID filing (ULID string)
            
        Returns:
            Created Claim instance
        """
        # Verify policy exists and is active
        policy = self.db.query(Policy).filter(
            Policy.id == policy_id,
            Policy.tenant_id == tenant_id
        ).first()
        
        if not policy:
            raise PolicyNotFoundError(f"Policy {policy_id} not found")
        
        if policy.status not in [PolicyStatus.ACTIVE, PolicyStatus.CLAIMED]:
            raise PolicyNotActiveError(f"Policy is {policy.status.value}, cannot file claim")
        
        # Verify loss date is within coverage period
        loss_date_str = fnol.get('loss_date')
        if loss_date_str:
            try:
                loss_date = datetime.fromisoformat(loss_date_str.replace('Z', '+00:00'))
                if loss_date < policy.effective_from or loss_date > policy.effective_to:
                    raise LossOutsideCoverageError("Loss date is outside coverage period")
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse loss_date: {loss_date_str}")
        
        # Generate claim number
        claim_number = self._generate_claim_number(tenant_id)
        
        # Create FNOL snapshot
        fnol_snapshot = {
            "loss_date": fnol.get('loss_date'),
            "loss_location": fnol.get('loss_location'),
            "loss_description": fnol.get('loss_description'),
            "loss_type": fnol.get('loss_type'),
            "estimated_loss_cents": fnol.get('estimated_loss_cents', 0),
            "currency": fnol.get('currency') or (policy.terms_json or {}).get('currency', 'USD'),
            "reported_by": fnol.get('reported_by'),
            "reported_at": datetime.utcnow().isoformat()
        }
        
        # Create claim
        from app.shared.utils import generate_ulid
        
        claim = Claim(
            id=generate_ulid(),
            tenant_id=tenant_id,
            claim_number=claim_number,
            policy_id=policy_id,
            status=ClaimStatus.FNOL_RECEIVED,
            fnol_json=fnol_snapshot,
            created_by_user_id=filed_by,
            created_at=datetime.utcnow()
        )
        
        self.db.add(claim)
        
        # Update policy status if first claim
        if policy.status == PolicyStatus.ACTIVE:
            policy.status = PolicyStatus.CLAIMED
        
        self.db.commit()
        self.db.refresh(claim)
        
        # Record event
        self._record_event(
            claim_id=claim.id,
            tenant_id=tenant_id,
            event_type="FNOL_FILED",
            to_status=ClaimStatus.FNOL_RECEIVED,
            actor_type="USER",
            actor_id=filed_by,
            payload={"fnol": fnol_snapshot}
        )
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="CLAIM",
            action="FILED",
            entity_type="claim",
            entity_id=claim.id,
            actor_type="USER",
            actor_id=filed_by,
            payload={
                "claim_number": claim_number,
                "policy_id": policy_id,
                "loss_type": fnol.get('loss_type'),
                "estimated_loss_cents": fnol.get('estimated_loss_cents', 0)
            }
        )
        
        logger.info(f"Filed claim: {claim.id} ({claim_number})")
        
        return claim
    
    def assign_adjuster(
        self,
        claim_id: str,
        adjuster_id: str,
        assigned_by: str
    ) -> Claim:
        """
        Assign an adjuster to a claim.
        
        Args:
            claim_id: Claim ID (ULID string)
            adjuster_id: Adjuster user ID (ULID string)
            assigned_by: User ID assigning (ULID string)
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        
        claim.assigned_adjuster_id = adjuster_id
        claim.assigned_at = datetime.utcnow()
        claim.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(claim)
        
        self._record_event(
            claim_id=claim_id,
            tenant_id=claim.tenant_id,
            event_type="ASSIGNMENT_CHANGED",
            actor_type="USER",
            actor_id=assigned_by,
            payload={"adjuster_id": adjuster_id}
        )
        
        logger.info(f"Assigned adjuster {adjuster_id} to claim {claim_id}")
        
        return claim
    
    def begin_investigation(
        self,
        claim_id: str,
        started_by: str
    ) -> Claim:
        """
        Begin claim investigation.
        
        Args:
            claim_id: Claim ID (ULID string)
            started_by: User ID starting (ULID string)
            
        Returns:
            Updated Claim instance
        """
        return self._transition(
            claim_id=claim_id,
            target_status=ClaimStatus.UNDER_INVESTIGATION,
            transitioned_by=started_by
        )
    
    def request_evidence(
        self,
        claim_id: str,
        evidence_request: str,
        requested_by: str
    ) -> Claim:
        """
        Request additional evidence from claimant.
        
        Args:
            claim_id: Claim ID (ULID string)
            evidence_request: Evidence request text
            requested_by: User ID requesting (ULID string)
            
        Returns:
            Updated Claim instance
        """
        claim = self._transition(
            claim_id=claim_id,
            target_status=ClaimStatus.AWAITING_EVIDENCE,
            transitioned_by=requested_by,
            payload={"evidence_request": evidence_request}
        )
        
        self._record_event(
            claim_id=claim_id,
            tenant_id=claim.tenant_id,
            event_type="INFO_REQUESTED",
            actor_type="USER",
            actor_id=requested_by,
            payload={"request": evidence_request}
        )
        
        return claim
    
    def submit_evidence(
        self,
        claim_id: str,
        evidence_bundle_id: str,
        submitted_by: str
    ) -> Claim:
        """
        Submit evidence and return to investigation.
        
        Args:
            claim_id: Claim ID (ULID string)
            evidence_bundle_id: Evidence bundle ID (UUID string)
            submitted_by: User ID submitting (ULID string)
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        
        # Verify bundle exists and is sealed
        bundle = self.db.query(EvidenceBundle).filter(
            EvidenceBundle.id == evidence_bundle_id
        ).first()
        
        if not bundle or bundle.status != 'SEALED':
            raise EvidenceBundleError("Evidence bundle must be sealed")
        
        claim.evidence_bundle_id = evidence_bundle_id
        claim.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        self._record_event(
            claim_id=claim_id,
            tenant_id=claim.tenant_id,
            event_type="EVIDENCE_ADDED",
            actor_type="USER",
            actor_id=submitted_by,
            payload={"evidence_bundle_id": evidence_bundle_id}
        )
        
        # Transition back to investigation if was awaiting
        if claim.status == ClaimStatus.AWAITING_EVIDENCE.value:
            return self._transition(
                claim_id=claim_id,
                target_status=ClaimStatus.UNDER_INVESTIGATION,
                transitioned_by=submitted_by
            )
        
        return claim
    
    def adjudicate(
        self,
        claim_id: str,
        adjudication: Dict[str, Any],
        adjudicated_by: str
    ) -> Claim:
        """
        Adjudicate a claim - approve or decline.
        
        Requires evidence bundle to be attached.
        
        Args:
            claim_id: Claim ID (ULID string)
            adjudication: Adjudication data dictionary
            adjudicated_by: User ID adjudicating (ULID string)
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        
        if not claim.evidence_bundle_id:
            raise EvidenceRequiredError("Evidence bundle required for adjudication")
        
        # Get policy for coverage check
        policy = self.db.query(Policy).filter(Policy.id == claim.policy_id).first()
        
        # Build adjudication record
        adjudication_json = {
            "coverage_applies": adjudication.get('coverage_applies', True),
            "deductible_applied_cents": (policy.terms_json or {}).get('deductible_cents', 0),
            "exclusions_checked": adjudication.get('exclusions_checked', []),
            "calculation_method": adjudication.get('calculation_method'),
            "adjustments": adjudication.get('adjustments', []),
            "notes": adjudication.get('notes')
        }
        
        decision = adjudication.get('decision', 'APPROVED')
        
        claim.adjudication_json = adjudication_json
        claim.decision = decision
        claim.decision_reason = adjudication.get('reason')
        claim.decision_by_user_id = adjudicated_by
        claim.decision_at = datetime.utcnow()
        
        # Update loss experience record
        try:
            from app.services.loss_analytics_service import LossAnalyticsService
            loss_service = LossAnalyticsService(self.db)
            loss_service.update_from_claim(claim.id)
        except Exception as e:
            logger.warning(f"Could not update loss experience from claim: {e}")
        
        if decision == 'APPROVED':
            # Calculate approved amount
            approved_amount = adjudication.get('approved_amount_cents')
            if approved_amount is None:
                # Default: claimed amount minus deductible
                estimated = claim.fnol_json.get('estimated_loss_cents', 0)
                deductible = (policy.terms_json or {}).get('deductible_cents', 0)
                approved_amount = max(0, estimated - deductible)
            
            claim.approved_amount_cents = approved_amount
            claim.approved_currency = claim.fnol_json.get('currency', 'USD')
            target_status = ClaimStatus.APPROVED
        else:
            target_status = ClaimStatus.DECLINED
        
        self.db.commit()
        
        # Record adjudication event
        self._record_event(
            claim_id=claim_id,
            tenant_id=claim.tenant_id,
            event_type="ADJUDICATION",
            actor_type="USER",
            actor_id=adjudicated_by,
            payload={
                "decision": decision,
                "reason": adjudication.get('reason'),
                "approved_amount_cents": claim.approved_amount_cents
            }
        )
        
        # Transition
        return self._transition(
            claim_id=claim_id,
            target_status=target_status,
            transitioned_by=adjudicated_by,
            payload={"adjudication": adjudication_json}
        )
    
    def authorize_payout(
        self,
        claim_id: str,
        authorized_by: str,
        authorization_notes: Optional[str] = None
    ) -> Claim:
        """
        Authorize payout for an approved claim.
        
        This is a separate control step - may require higher authority.
        
        Args:
            claim_id: Claim ID (ULID string)
            authorized_by: User ID authorizing (ULID string)
            authorization_notes: Optional authorization notes
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        
        if claim.status != ClaimStatus.APPROVED.value:
            raise InvalidClaimStateError(f"Can only authorize APPROVED claims")
        
        # Record authorization
        self._record_event(
            claim_id=claim_id,
            tenant_id=claim.tenant_id,
            event_type="PAYOUT_AUTHORIZED",
            actor_type="USER",
            actor_id=authorized_by,
            payload={
                "amount_cents": claim.approved_amount_cents,
                "notes": authorization_notes
            }
        )
        
        # Audit (separate for authorization)
        self.audit.append_event(
            tenant_id=claim.tenant_id,
            event_type="CLAIM",
            action="PAYOUT_AUTHORIZED",
            entity_type="claim",
            entity_id=claim_id,
            actor_type="USER",
            actor_id=authorized_by,
            payload={
                "amount_cents": claim.approved_amount_cents,
                "authorized_by": authorized_by
            }
        )
        
        return self._transition(
            claim_id=claim_id,
            target_status=ClaimStatus.AUTHORIZED,
            transitioned_by=authorized_by
        )
    
    def record_payment(
        self,
        claim_id: str,
        payout_id: str,
        recorded_by: str
    ) -> Claim:
        """
        Record that payment has been made.
        
        Args:
            claim_id: Claim ID (ULID string)
            payout_id: Payout ID (UUID string)
            recorded_by: User ID recording (ULID string)
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        
        if claim.status != ClaimStatus.AUTHORIZED.value:
            raise InvalidClaimStateError("Claim must be AUTHORIZED to record payment")
        
        claim.payout_id = payout_id
        
        return self._transition(
            claim_id=claim_id,
            target_status=ClaimStatus.PAID,
            transitioned_by=recorded_by,
            payload={"payout_id": payout_id}
        )
    
    def close_claim(
        self,
        claim_id: str,
        closed_by: str,
        closing_notes: Optional[str] = None
    ) -> Claim:
        """
        Close a claim (after payment or decline).
        
        Args:
            claim_id: Claim ID (ULID string)
            closed_by: User ID closing (ULID string)
            closing_notes: Optional closing notes
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        
        valid_for_close = [ClaimStatus.PAID.value, ClaimStatus.DECLINED.value]
        if claim.status not in valid_for_close:
            raise InvalidClaimStateError(f"Cannot close claim in {claim.status} status")
        
        claim.closed_at = datetime.utcnow()
        
        return self._transition(
            claim_id=claim_id,
            target_status=ClaimStatus.CLOSED,
            transitioned_by=closed_by,
            payload={"closing_notes": closing_notes}
        )
    
    def get_claim_history(self, claim_id: str) -> List[ClaimEvent]:
        """
        Get full history of claim events.
        
        Args:
            claim_id: Claim ID (ULID string)
            
        Returns:
            List of ClaimEvent instances
        """
        return self.db.query(ClaimEvent).filter(
            ClaimEvent.claim_id == claim_id
        ).order_by(ClaimEvent.created_at).all()
    
    def get_claims_for_policy(self, policy_id: str) -> List[Claim]:
        """
        Get all claims for a policy.
        
        Args:
            policy_id: Policy ID (ULID string)
            
        Returns:
            List of Claim instances
        """
        return self.db.query(Claim).filter(
            Claim.policy_id == policy_id
        ).order_by(Claim.created_at.desc()).all()
    
    def list_claims(
        self,
        tenant_id: str,
        policy_id: Optional[str] = None,
        status: Optional[str] = None,
        assigned_to: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Claim]:
        """
        List claims with filters.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            policy_id: Optional policy ID filter
            status: Optional status filter
            assigned_to: Optional adjuster ID filter
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            List of Claim instances
        """
        query = self.db.query(Claim).filter(Claim.tenant_id == tenant_id)
        
        if policy_id:
            query = query.filter(Claim.policy_id == policy_id)
        
        if status:
            query = query.filter(Claim.status == ClaimStatus(status))
        
        if assigned_to:
            query = query.filter(Claim.assigned_adjuster_id == assigned_to)
        
        return query.order_by(Claim.created_at.desc()).offset(offset).limit(limit).all()
    
    def get_claim_detail(self, claim_id: str) -> Claim:
        """
        Get claim with full details.
        
        Args:
            claim_id: Claim ID (ULID string)
            
        Returns:
            Claim instance
            
        Raises:
            ClaimNotFoundError: If claim not found
        """
        return self._get_claim(claim_id)
    
    def _transition(
        self,
        claim_id: str,
        target_status: ClaimStatus,
        transitioned_by: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Claim:
        """
        Execute a state transition.
        
        Args:
            claim_id: Claim ID (ULID string)
            target_status: Target status
            transitioned_by: User ID transitioning (ULID string)
            payload: Optional payload
            
        Returns:
            Updated Claim instance
        """
        claim = self._get_claim(claim_id)
        current_status = ClaimStatus(claim.status)
        
        # Validate
        is_valid, errors = ClaimStateMachine.validate_transition(claim, target_status, payload or {})
        if not is_valid:
            raise InvalidTransitionError(
                f"Cannot transition {current_status.value} → {target_status.value}: " +
                "; ".join(errors)
            )
        
        # Apply
        claim.status = target_status
        claim.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(claim)
        
        # Record event
        self._record_event(
            claim_id=claim_id,
            tenant_id=claim.tenant_id,
            event_type="STATE_TRANSITION",
            from_status=current_status,
            to_status=target_status,
            actor_type="USER",
            actor_id=transitioned_by,
            payload=payload
        )
        
        # Audit
        self.audit.append_event(
            tenant_id=claim.tenant_id,
            event_type="CLAIM",
            action="TRANSITIONED",
            entity_type="claim",
            entity_id=claim_id,
            actor_type="USER",
            actor_id=transitioned_by,
            payload={
                "from_status": current_status.value,
                "to_status": target_status.value,
                **(payload or {})
            }
        )
        
        logger.info(
            f"Transitioned claim {claim_id}: {current_status.value} → {target_status.value}"
        )
        
        return claim
    
    def _get_claim(self, claim_id: str) -> Claim:
        """
        Get claim by ID.
        
        Args:
            claim_id: Claim ID (ULID string)
            
        Returns:
            Claim instance
            
        Raises:
            ClaimNotFoundError: If claim not found
        """
        claim = self.db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            raise ClaimNotFoundError(f"Claim {claim_id} not found")
        return claim
    
    def _generate_claim_number(self, tenant_id: str) -> str:
        """
        Generate unique claim number.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            
        Returns:
            Claim number string
        """
        date_part = datetime.utcnow().strftime("%Y%m%d")
        count = self.db.query(Claim).filter(
            Claim.tenant_id == tenant_id
        ).count()
        return f"CLM-{date_part}-{count + 1:06d}"
    
    def _record_event(
        self,
        claim_id: str,
        tenant_id: str,
        event_type: str,
        actor_type: str,
        actor_id: Optional[str] = None,
        from_status: Optional[ClaimStatus] = None,
        to_status: Optional[ClaimStatus] = None,
        payload: Optional[Dict[str, Any]] = None
    ):
        """
        Record a claim event.
        
        Args:
            claim_id: Claim ID (ULID string)
            tenant_id: Tenant ID (ULID string)
            event_type: Event type
            actor_type: Actor type (USER, SYSTEM)
            actor_id: Actor ID (ULID string)
            from_status: From status (for transitions)
            to_status: To status (for transitions)
            payload: Event payload
        """
        from app.shared.utils import generate_ulid
        
        event = ClaimEvent(
            id=generate_ulid(),
            tenant_id=tenant_id,
            claim_id=claim_id,
            event_type=event_type,
            from_status=from_status.value if from_status else None,
            to_status=to_status.value if to_status else None,
            actor_type=actor_type,
            actor_id=actor_id,
            payload_json=payload,
            created_at=datetime.utcnow()
        )
        self.db.add(event)
        self.db.commit()


# Exception classes
class ClaimNotFoundError(Exception):
    """Claim not found"""
    pass


class PolicyNotFoundError(Exception):
    """Policy not found"""
    pass


class PolicyNotActiveError(Exception):
    """Policy not active"""
    pass


class LossOutsideCoverageError(Exception):
    """Loss date outside coverage period"""
    pass


class InvalidClaimStateError(Exception):
    """Invalid claim state for operation"""
    pass


class InvalidTransitionError(Exception):
    """Invalid state transition"""
    pass


class EvidenceRequiredError(Exception):
    """Evidence required"""
    pass


class EvidenceBundleError(Exception):
    """Evidence bundle error"""
    pass
