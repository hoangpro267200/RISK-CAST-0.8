"""
Underwriting submission state machine.

Defines valid states, transitions, and invariants.
"""

from typing import Set, Dict, List, Callable, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.modules.underwriting.models import UnderwritingSubmission, SubmissionStatus
from app.models.evidence_bundle import EvidenceBundle


@dataclass
class TransitionRule:
    """Rule defining a valid state transition."""
    from_status: SubmissionStatus
    to_status: SubmissionStatus
    required_fields: List[str]  # Fields that must be set
    invariants: List[Callable]  # Functions that must return True
    description: str


class SubmissionStateMachine:
    """
    State machine for underwriting submissions.
    
    Enforces valid transitions and invariants.
    """
    
    # Valid transitions
    TRANSITIONS: Dict[SubmissionStatus, Set[SubmissionStatus]] = {
        SubmissionStatus.DRAFT: {SubmissionStatus.SUBMITTED},
        SubmissionStatus.SUBMITTED: {SubmissionStatus.UNDER_REVIEW, SubmissionStatus.EXPIRED},
        SubmissionStatus.UNDER_REVIEW: {
            SubmissionStatus.REQUESTED_INFO, 
            SubmissionStatus.QUOTED, 
            SubmissionStatus.DECLINED
        },
        SubmissionStatus.REQUESTED_INFO: {SubmissionStatus.UNDER_REVIEW, SubmissionStatus.EXPIRED},
        SubmissionStatus.QUOTED: {SubmissionStatus.BOUND, SubmissionStatus.DECLINED, SubmissionStatus.EXPIRED},
        SubmissionStatus.BOUND: {SubmissionStatus.CLOSED},
        SubmissionStatus.DECLINED: {SubmissionStatus.CLOSED},
        SubmissionStatus.CLOSED: set(),  # Terminal state
        SubmissionStatus.EXPIRED: set(),  # Terminal state
        SubmissionStatus.CANCELED: set(),  # Terminal state
    }
    
    # Transition rules with invariants
    RULES: List[TransitionRule] = [
        TransitionRule(
            from_status=SubmissionStatus.DRAFT,
            to_status=SubmissionStatus.SUBMITTED,
            required_fields=['risk_assessment_id', 'requested_coverage_json'],
            invariants=[
                lambda s: s.risk_assessment_id is not None,
                lambda s: s.requested_coverage_json is not None,
            ],
            description="Submit requires risk assessment and coverage request"
        ),
        TransitionRule(
            from_status=SubmissionStatus.UNDER_REVIEW,
            to_status=SubmissionStatus.QUOTED,
            required_fields=['evidence_bundle_id'],
            invariants=[
                lambda s: s.evidence_bundle_id is not None,
                # Evidence bundle must be sealed (checked in service)
            ],
            description="Quote requires sealed evidence bundle"
        ),
        TransitionRule(
            from_status=SubmissionStatus.QUOTED,
            to_status=SubmissionStatus.BOUND,
            required_fields=['decision', 'decision_by_user_id'],
            invariants=[
                lambda s, ctx: ctx.get('decision') == 'APPROVED' if ctx else False,
                # Must have at least one issued quote
                # KYC must be completed
            ],
            description="Bind requires approved decision and completed KYC"
        ),
    ]
    
    @classmethod
    def can_transition(
        cls, 
        current_status: SubmissionStatus, 
        target_status: SubmissionStatus
    ) -> bool:
        """Check if transition is valid."""
        valid_targets = cls.TRANSITIONS.get(current_status, set())
        return target_status in valid_targets
    
    @classmethod
    def get_valid_transitions(cls, current_status: SubmissionStatus) -> Set[SubmissionStatus]:
        """Get all valid target states from current state."""
        return cls.TRANSITIONS.get(current_status, set())
    
    @classmethod
    def validate_transition(
        cls,
        submission: UnderwritingSubmission,
        target_status: SubmissionStatus,
        context: Optional[Dict] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate a transition including invariants.
        
        Args:
            submission: UnderwritingSubmission instance
            target_status: Target status
            context: Optional context dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        context = context or {}
        
        current = SubmissionStatus(submission.status)
        
        # Check basic transition validity
        if not cls.can_transition(current, target_status):
            errors.append(
                f"Invalid transition: {current.value} → {target_status.value}"
            )
            return False, errors
        
        # Find and check applicable rules
        for rule in cls.RULES:
            if rule.from_status == current and rule.to_status == target_status:
                # Check required fields
                for field in rule.required_fields:
                    value = getattr(submission, field, None)
                    if value is None:
                        # Check context for fields that might be passed in context
                        if field in ['decision', 'decision_by_user_id']:
                            if field not in context or context[field] is None:
                                errors.append(f"Missing required field: {field}")
                        else:
                            errors.append(f"Missing required field: {field}")
                
                # Check invariants
                for invariant in rule.invariants:
                    try:
                        # Invariants may take submission or (submission, context)
                        import inspect
                        sig = inspect.signature(invariant)
                        if len(sig.parameters) == 2:
                            if not invariant(submission, context):
                                errors.append(f"Invariant failed for {rule.description}")
                        else:
                            if not invariant(submission):
                                errors.append(f"Invariant failed for {rule.description}")
                    except Exception as e:
                        errors.append(f"Invariant error: {str(e)}")
        
        # Additional validations
        if target_status == SubmissionStatus.BOUND:
            # Check KYC completion
            if submission.applicant_json:
                kyc_status = submission.applicant_json.get('kyc_status')
                if kyc_status != 'COMPLETED':
                    errors.append("KYC must be completed for binding")
            elif not submission.applicant_json:
                # If no applicant_json, we can't verify KYC
                errors.append("Applicant information required for binding")
        
        return len(errors) == 0, errors
    
    @classmethod
    def is_terminal(cls, status: SubmissionStatus) -> bool:
        """Check if status is terminal (no further transitions)."""
        return len(cls.TRANSITIONS.get(status, set())) == 0


# Invariant functions
def has_risk_assessment(submission) -> bool:
    """Check if submission has risk assessment."""
    return submission.risk_assessment_id is not None


def has_evidence_bundle(submission) -> bool:
    """Check if submission has evidence bundle."""
    return submission.evidence_bundle_id is not None


def evidence_bundle_sealed(submission, db) -> bool:
    """Check if evidence bundle is sealed."""
    if not submission.evidence_bundle_id:
        return False
    bundle = db.query(EvidenceBundle).filter(
        EvidenceBundle.id == submission.evidence_bundle_id
    ).first()
    return bundle and bundle.status == 'SEALED'


def kyc_completed(submission) -> bool:
    """Check if KYC is completed."""
    applicant = submission.applicant_json or {}
    return applicant.get('kyc_status') == 'COMPLETED'
