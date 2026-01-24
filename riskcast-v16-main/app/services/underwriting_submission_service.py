"""
Underwriting submission service.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.underwriting.models import (
    UnderwritingSubmission,
    UnderwritingSubmissionEvent,
    SubmissionStatus
)
from app.models.evidence_bundle import EvidenceBundle
from app.core.underwriting.state_machine import SubmissionStateMachine
from app.core.audit_ledger.ledger import AuditLedger

import logging

logger = logging.getLogger(__name__)


class UnderwritingSubmissionService:
    """Service for managing underwriting submissions."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize underwriting submission service.
        
        Args:
            db: Database session
            audit: Optional audit ledger for event logging
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_submission(
        self,
        tenant_id: str,
        risk_assessment_id: str,
        requested_coverage: Dict[str, Any],
        created_by: str,
        applicant: Optional[Dict[str, Any]] = None,
        shipment_id: Optional[str] = None,
        corridor_id: Optional[str] = None,
        evidence_bundle_id: Optional[str] = None
    ) -> UnderwritingSubmission:
        """
        Create a new submission in DRAFT status.
        
        Args:
            tenant_id: Tenant ID (UUID string)
            risk_assessment_id: Risk assessment ID
            requested_coverage: Coverage request dictionary
            created_by: User ID creating the submission (UUID string)
            applicant: Optional applicant information
            shipment_id: Optional shipment ID
            corridor_id: Optional corridor ID
            evidence_bundle_id: Optional evidence bundle ID
            
        Returns:
            Created UnderwritingSubmission
        """
        # Generate submission number
        submission_number = self._generate_submission_number(tenant_id)
        
        submission = UnderwritingSubmission(
            tenant_id=tenant_id,
            submission_number=submission_number,
            status=SubmissionStatus.DRAFT,
            risk_assessment_id=risk_assessment_id,
            requested_coverage_json=requested_coverage,
            applicant_json=applicant,
            applicant_pii=bool(applicant),  # Assume PII if applicant data provided
            shipment_id=shipment_id,
            corridor_id=corridor_id,
            evidence_bundle_id=evidence_bundle_id,
            created_by_user_id=created_by,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30)  # Default 30 day expiry
        )
        
        self.db.add(submission)
        self.db.commit()
        self.db.refresh(submission)
        
        # Record event
        self._record_event(
            submission_id=submission.id,
            event_type="CREATED",
            to_status=SubmissionStatus.DRAFT,
            actor_type="USER",
            actor_id=created_by
        )
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="UNDERWRITING_SUBMISSION",
            action="CREATED",
            entity_type="underwriting_submission",
            entity_id=submission.id,
            actor_type="USER",
            actor_id=created_by,
            payload={"submission_number": submission_number}
        )
        
        logger.info(f"Created underwriting submission: {submission.id} ({submission_number})")
        
        return submission
    
    def transition(
        self,
        submission_id: str,
        target_status: SubmissionStatus,
        transitioned_by: str,
        reason: Optional[str] = None,
        payload: Optional[dict] = None
    ) -> UnderwritingSubmission:
        """
        Transition submission to a new status.
        
        Validates transition and invariants before applying.
        
        Args:
            submission_id: Submission ID (UUID string)
            target_status: Target status
            transitioned_by: User ID transitioning (UUID string)
            reason: Optional reason for transition
            payload: Optional additional payload
            
        Returns:
            Updated UnderwritingSubmission
            
        Raises:
            InvalidTransitionError: If transition is invalid
        """
        submission = self._get_submission(submission_id)
        current_status = SubmissionStatus(submission.status)
        
        # Validate transition
        is_valid, errors = SubmissionStateMachine.validate_transition(
            submission, target_status, payload or {}
        )
        
        if not is_valid:
            raise InvalidTransitionError(
                f"Cannot transition {current_status.value} → {target_status.value}: "
                + "; ".join(errors)
            )
        
        # Additional validation for specific transitions
        if target_status == SubmissionStatus.QUOTED:
            # Verify evidence bundle is sealed
            if submission.evidence_bundle_id:
                bundle = self.db.query(EvidenceBundle).filter(
                    EvidenceBundle.id == submission.evidence_bundle_id
                ).first()
                if bundle and bundle.status != 'SEALED':
                    raise InvalidTransitionError(
                        "Evidence bundle must be sealed before quoting"
                    )
        
        # Apply transition
        submission.status = target_status
        submission.updated_at = datetime.utcnow()
        
        # Set specific fields based on transition
        if target_status == SubmissionStatus.SUBMITTED:
            submission.submitted_at = datetime.utcnow()
        
        if target_status in [SubmissionStatus.BOUND, SubmissionStatus.DECLINED]:
            decision_value = 'APPROVED' if target_status == SubmissionStatus.BOUND else 'DECLINED'
            submission.decision = decision_value
            submission.decision_reason = reason
            submission.decision_by_user_id = transitioned_by
            submission.decision_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(submission)
        
        # Determine actor type
        actor_type = "SYSTEM" if transitioned_by == "SYSTEM" else "USER"
        
        # Record event
        self._record_event(
            submission_id=submission_id,
            event_type="STATE_TRANSITION",
            from_status=current_status,
            to_status=target_status,
            actor_type=actor_type,
            actor_id=transitioned_by if transitioned_by != "SYSTEM" else None,
            payload={"reason": reason, **(payload or {})}
        )
        
        # Audit
        self.audit.append_event(
            tenant_id=submission.tenant_id,
            event_type="UNDERWRITING_SUBMISSION",
            action="TRANSITIONED",
            entity_type="underwriting_submission",
            entity_id=submission_id,
            actor_type=actor_type,
            actor_id=transitioned_by if transitioned_by != "SYSTEM" else None,
            payload={
                "from_status": current_status.value,
                "to_status": target_status.value,
                "reason": reason
            }
        )
        
        logger.info(
            f"Transitioned submission {submission_id}: "
            f"{current_status.value} → {target_status.value}"
        )
        
        return submission
    
    def assign_underwriter(
        self,
        submission_id: str,
        underwriter_id: str,
        assigned_by: str
    ) -> UnderwritingSubmission:
        """
        Assign an underwriter to review the submission.
        
        Args:
            submission_id: Submission ID (UUID string)
            underwriter_id: Underwriter user ID (UUID string)
            assigned_by: User ID assigning (UUID string)
            
        Returns:
            Updated UnderwritingSubmission
        """
        submission = self._get_submission(submission_id)
        
        submission.assigned_to_user_id = underwriter_id
        submission.assigned_at = datetime.utcnow()
        submission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(submission)
        
        # Record event
        self._record_event(
            submission_id=submission_id,
            event_type="ASSIGNMENT_CHANGED",
            actor_type="USER",
            actor_id=assigned_by,
            payload={"underwriter_id": underwriter_id}
        )
        
        logger.info(f"Assigned underwriter {underwriter_id} to submission {submission_id}")
        
        return submission
    
    def request_info(
        self,
        submission_id: str,
        info_request: str,
        requested_by: str
    ) -> UnderwritingSubmission:
        """
        Request additional information from applicant.
        
        Args:
            submission_id: Submission ID (UUID string)
            info_request: Information request text
            requested_by: User ID requesting (UUID string)
            
        Returns:
            Updated UnderwritingSubmission
            
        Raises:
            InvalidTransitionError: If not in UNDER_REVIEW status
        """
        submission = self._get_submission(submission_id)
        
        # Must be in UNDER_REVIEW to request info
        if submission.status != SubmissionStatus.UNDER_REVIEW.value:
            raise InvalidTransitionError(
                f"Can only request info from UNDER_REVIEW status, current: {submission.status}"
            )
        
        # Transition to REQUESTED_INFO
        return self.transition(
            submission_id=submission_id,
            target_status=SubmissionStatus.REQUESTED_INFO,
            transitioned_by=requested_by,
            reason=info_request,
            payload={"info_request": info_request}
        )
    
    def attach_evidence_bundle(
        self,
        submission_id: str,
        evidence_bundle_id: str,
        attached_by: str
    ) -> UnderwritingSubmission:
        """
        Attach an evidence bundle to the submission.
        
        Args:
            submission_id: Submission ID (UUID string)
            evidence_bundle_id: Evidence bundle ID (UUID string)
            attached_by: User ID attaching (UUID string)
            
        Returns:
            Updated UnderwritingSubmission
            
        Raises:
            EvidenceBundleNotFoundError: If bundle not found
        """
        submission = self._get_submission(submission_id)
        
        # Verify bundle exists
        bundle = self.db.query(EvidenceBundle).filter(
            EvidenceBundle.id == evidence_bundle_id,
            EvidenceBundle.tenant_id == submission.tenant_id
        ).first()
        
        if not bundle:
            raise EvidenceBundleNotFoundError(f"Bundle {evidence_bundle_id} not found")
        
        submission.evidence_bundle_id = evidence_bundle_id
        submission.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(submission)
        
        # Record event
        self._record_event(
            submission_id=submission_id,
            event_type="EVIDENCE_ADDED",
            actor_type="USER",
            actor_id=attached_by,
            payload={"evidence_bundle_id": evidence_bundle_id}
        )
        
        logger.info(f"Attached evidence bundle {evidence_bundle_id} to submission {submission_id}")
        
        return submission
    
    def get_history(self, submission_id: str) -> List[UnderwritingSubmissionEvent]:
        """
        Get full history of submission events.
        
        Args:
            submission_id: Submission ID (UUID string)
            
        Returns:
            List of UnderwritingSubmissionEvent instances
        """
        return self.db.query(UnderwritingSubmissionEvent).filter(
            UnderwritingSubmissionEvent.submission_id == submission_id
        ).order_by(UnderwritingSubmissionEvent.created_at).all()
    
    def check_expirations(self) -> int:
        """
        Check and expire submissions past their expiration date.
        
        Should be run periodically (e.g., daily cron job).
        
        Returns:
            Count of expired submissions
        """
        now = datetime.utcnow()
        
        expirable_statuses = [
            SubmissionStatus.SUBMITTED.value,
            SubmissionStatus.UNDER_REVIEW.value,
            SubmissionStatus.REQUESTED_INFO.value,
            SubmissionStatus.QUOTED.value
        ]
        
        expired = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.status.in_(expirable_statuses),
            UnderwritingSubmission.expires_at < now
        ).all()
        
        for submission in expired:
            try:
                self.transition(
                    submission_id=submission.id,
                    target_status=SubmissionStatus.EXPIRED,
                    transitioned_by=None,  # System
                    reason="Submission expired"
                )
            except Exception as e:
                logger.error(f"Error expiring submission {submission.id}: {e}")
        
        logger.info(f"Expired {len(expired)} submissions")
        
        return len(expired)
    
    def _get_submission(self, submission_id: str) -> UnderwritingSubmission:
        """
        Get submission by ID.
        
        Args:
            submission_id: Submission ID (UUID string)
            
        Returns:
            UnderwritingSubmission instance
            
        Raises:
            SubmissionNotFoundError: If submission not found
        """
        submission = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.id == submission_id
        ).first()
        
        if not submission:
            raise SubmissionNotFoundError(f"Submission {submission_id} not found")
        
        return submission
    
    def _generate_submission_number(self, tenant_id: str) -> str:
        """
        Generate unique submission number.
        
        Format: SUB-YYYYMMDD-XXXXX
        
        Args:
            tenant_id: Tenant ID (UUID string)
            
        Returns:
            Submission number string
        """
        date_part = datetime.utcnow().strftime("%Y%m%d")
        
        # Get count for today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.tenant_id == tenant_id,
            UnderwritingSubmission.created_at >= today_start
        ).count()
        
        return f"SUB-{date_part}-{count + 1:05d}"
    
    def _record_event(
        self,
        submission_id: str,
        event_type: str,
        actor_type: str,
        actor_id: Optional[str] = None,
        from_status: Optional[SubmissionStatus] = None,
        to_status: Optional[SubmissionStatus] = None,
        payload: Optional[dict] = None
    ):
        """
        Record a submission event.
        
        Args:
            submission_id: Submission ID (UUID string)
            event_type: Event type
            actor_type: Actor type (USER, SYSTEM)
            actor_id: Actor ID (UUID string)
            from_status: From status (for transitions)
            to_status: To status (for transitions)
            payload: Optional payload
        """
        from app.shared.utils import generate_ulid
        
        event = UnderwritingSubmissionEvent(
            id=generate_ulid(),
            submission_id=submission_id,
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
class SubmissionNotFoundError(Exception):
    """Submission not found"""
    pass


class InvalidTransitionError(Exception):
    """Invalid state transition"""
    pass


class EvidenceBundleNotFoundError(Exception):
    """Evidence bundle not found"""
    pass
