"""
Underwriting Service
Business logic for underwriting workflows with state machine
RISKCAST V3 - Modular Monolith
"""
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
import logging

# Import TenantScopedSession for type hints
if TYPE_CHECKING:
    from app.database import TenantScopedSession

from app.modules.underwriting.models import (
    UnderwritingSubmission,
    UnderwritingDecision,
    Policy,
    SubmissionStatus,
    DecisionType,
    PolicyStatus
)
from app.modules.underwriting.state_machine import UnderwritingStateMachine
from app.modules.underwriting.exceptions import (
    SubmissionNotFoundError,
    InvalidTransitionError
)
from app.modules.risk_assessments.models import RiskAssessment

# Import AssessmentNotFoundError (with fallback)
try:
    from app.modules.risk_assessments.exceptions import AssessmentNotFoundError
except ImportError:
    from fastapi import HTTPException, status
    class AssessmentNotFoundError(HTTPException):
        def __init__(self, assessment_id: str):
            super().__init__(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk assessment not found: {assessment_id}"
            )
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.models import ActorType
from app.modules.audit_ledger.schemas import AuditContext

logger = logging.getLogger(__name__)


class UnderwritingService:
    """Service for underwriting workflow with state machine"""
    
    def __init__(self, db: 'TenantScopedSession'):
        """
        Initialize underwriting service.
        
        Args:
            db: Tenant-scoped database session
        """
        self.db = db
        self.state_machine = UnderwritingStateMachine()
        # Audit service needs raw session, not tenant-scoped
        self.audit = AuditLedgerService(db._raw_session)
        logger.debug(f"UnderwritingService initialized for tenant_id={db.tenant_id}")
    
    async def create_submission(
        self,
        data: Dict[str, Any],
        user_id: str,
        context: AuditContext
    ) -> UnderwritingSubmission:
        """
        Create underwriting submission.
        
        Args:
            data: Submission data (risk_assessment_id, risk_run_id, evidence_bundle_id, etc.)
            user_id: User ID creating submission
            context: Audit context
            
        Returns:
            UnderwritingSubmission instance
        """
        # Verify risk assessment exists
        assessment = self.db.query(RiskAssessment).filter(
            RiskAssessment.id == data.get('risk_assessment_id'),
            RiskAssessment.tenant_id == self.db.tenant_id
        ).first()
        
        if not assessment:
            raise AssessmentNotFoundError(data.get('risk_assessment_id'))
        
        submission = UnderwritingSubmission(
            tenant_id=self.db.tenant_id,
            status=SubmissionStatus.DRAFT,
            risk_assessment_id=data.get('risk_assessment_id'),
            risk_run_id=data.get('risk_run_id'),
            evidence_bundle_id=data.get('evidence_bundle_id'),
            requested_coverage_json=data.get('requested_coverage_json'),
            corridor_id=data.get('corridor_id'),
            product_type=data.get('product_type'),
            created_by_user_id=user_id
        )
        
        self.db.add(submission)
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='underwriting.submission.created',
            resource_type='underwriting_submission',
            resource_id=str(submission.id),
            context=context
        )
        
        logger.info(f"Underwriting submission created: {submission.id}")
        return submission
    
    async def make_decision(
        self,
        submission_id: str,
        decision: DecisionType,
        user_id: str,
        context: AuditContext,
        terms_json: Optional[Dict[str, Any]] = None,
        evidence_bundle_id: Optional[str] = None,
        risk_run_id: Optional[str] = None,
        model_version_id: Optional[str] = None,
        notes: Optional[str] = None
    ) -> tuple[UnderwritingDecision, UnderwritingSubmission]:
        """
        Make underwriting decision.
        
        Args:
            submission_id: Submission ID
            decision: Decision type (QUOTE, DECLINE, REQUEST_INFO)
            user_id: User ID making decision
            context: Audit context
            terms_json: Terms for quote
            evidence_bundle_id: Evidence bundle to pin
            risk_run_id: Risk run to pin
            model_version_id: Model version to pin
            notes: Decision notes
            
        Returns:
            Tuple of (UnderwritingDecision, UnderwritingSubmission)
        """
        submission = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.id == submission_id,
            UnderwritingSubmission.tenant_id == self.db.tenant_id
        ).first()
        
        if not submission:
            raise SubmissionNotFoundError(submission_id)
        
        # Determine target status based on decision
        if decision == DecisionType.QUOTE:
            target_status = SubmissionStatus.QUOTED
        elif decision == DecisionType.DECLINE:
            target_status = SubmissionStatus.DECLINED
        elif decision == DecisionType.REQUEST_INFO:
            target_status = SubmissionStatus.REQUESTED_INFO
        else:
            raise ValueError(f"Unknown decision type: {decision}")
        
        # Validate transition
        validation_context = {
            'terms_json': terms_json,
            'evidence_bundle_id': evidence_bundle_id,
            'model_version_id': model_version_id,
            'risk_run_id': risk_run_id
        }
        
        errors = self.state_machine.validate_transition(
            submission, target_status, validation_context
        )
        
        if errors:
            raise InvalidTransitionError(errors)
        
        # Create decision
        decision_obj = UnderwritingDecision(
            tenant_id=self.db.tenant_id,
            submission_id=submission_id,
            decided_by_user_id=user_id,
            decision=decision,
            terms_json=terms_json,
            notes=notes,
            model_version_id=model_version_id,
            risk_run_id=risk_run_id,
            evidence_bundle_id=evidence_bundle_id
        )
        
        self.db.add(decision_obj)
        
        # Update submission status
        old_status = submission.status
        submission.status = target_status
        
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action=f'underwriting.decision.{decision.value.lower()}',
            resource_type='underwriting_submission',
            resource_id=str(submission_id),
            context=context,
            diff={
                'from_status': old_status.value,
                'to_status': target_status.value,
                'decision': decision.value
            }
        )
        
        logger.info(f"Underwriting decision made: {decision_obj.id} ({decision.value})")
        return decision_obj, submission
    
    async def bind_policy(
        self,
        submission_id: str,
        user_id: str,
        context: AuditContext,
        effective_from: datetime,
        effective_to: datetime,
        policy_number: str
    ) -> Policy:
        """
        Bind policy from quoted submission.
        
        Args:
            submission_id: Submission ID
            user_id: User ID binding policy
            context: Audit context
            effective_from: Policy effective start date
            effective_to: Policy effective end date
            policy_number: Policy number
            
        Returns:
            Policy instance
        """
        submission = self.db.query(UnderwritingSubmission).filter(
            UnderwritingSubmission.id == submission_id,
            UnderwritingSubmission.tenant_id == self.db.tenant_id
        ).first()
        
        if not submission:
            raise SubmissionNotFoundError(submission_id)
        
        # Get latest decision (should be QUOTE)
        decision = self.db.query(UnderwritingDecision).filter(
            UnderwritingDecision.submission_id == submission_id,
            UnderwritingDecision.tenant_id == self.db.tenant_id
        ).order_by(UnderwritingDecision.created_at.desc()).first()
        
        if not decision or decision.decision != DecisionType.QUOTE:
            raise ValueError("Submission must have a QUOTE decision to bind policy")
        
        # Validate transition
        validation_context = {
            'policy_number': policy_number,
            'effective_from': effective_from,
            'effective_to': effective_to,
            'model_version_id': decision.model_version_id,
            'risk_run_id': decision.risk_run_id
        }
        
        errors = self.state_machine.validate_transition(
            submission, SubmissionStatus.BOUND, validation_context
        )
        
        if errors:
            raise InvalidTransitionError(errors)
        
        # Create policy
        policy = Policy(
            tenant_id=self.db.tenant_id,
            policy_number=policy_number,
            status=PolicyStatus.ACTIVE,
            submission_id=submission_id,
            bound_by_user_id=user_id,
            bound_at=datetime.utcnow(),
            effective_from=effective_from,
            effective_to=effective_to,
            model_version_id=decision.model_version_id,
            risk_run_id=decision.risk_run_id,
            terms_json=decision.terms_json
        )
        
        self.db.add(policy)
        
        # Update submission status
        submission.status = SubmissionStatus.BOUND
        
        self.db.commit()
        
        # Audit log
        await self.audit.log_event(
            tenant_id=self.db.tenant_id,
            actor_type=ActorType.USER,
            actor_id=user_id,
            action='policy.bound',
            resource_type='policy',
            resource_id=str(policy.id),
            context=context,
            diff={
                'policy_number': policy_number,
                'submission_id': submission_id
            }
        )
        
        logger.info(f"Policy bound: {policy.id} ({policy_number})")
        return policy
