"""
Underwriting State Machine
State machine for underwriting workflow with transition validation
RISKCAST V3 - Modular Monolith
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum

from app.modules.underwriting.models import (
    UnderwritingSubmission,
    SubmissionStatus
)
from app.modules.risk_runs.models import RiskRunStatus


class UnderwritingStateMachine:
    """
    State machine for underwriting workflow.
    Validates transitions and enforces preconditions.
    """
    
    VALID_TRANSITIONS = {
        SubmissionStatus.DRAFT: {SubmissionStatus.SUBMITTED},
        SubmissionStatus.SUBMITTED: {SubmissionStatus.UNDER_REVIEW, SubmissionStatus.EXPIRED},
        SubmissionStatus.UNDER_REVIEW: {
            SubmissionStatus.REQUESTED_INFO,
            SubmissionStatus.QUOTED,
            SubmissionStatus.DECLINED
        },
        SubmissionStatus.REQUESTED_INFO: {SubmissionStatus.UNDER_REVIEW, SubmissionStatus.EXPIRED},
        SubmissionStatus.QUOTED: {SubmissionStatus.BOUND, SubmissionStatus.DECLINED, SubmissionStatus.EXPIRED},
        SubmissionStatus.BOUND: {SubmissionStatus.CLOSED},  # Can close bound policies
        SubmissionStatus.DECLINED: {SubmissionStatus.CLOSED},  # Can close declined
        SubmissionStatus.CLOSED: set(),  # Terminal
        SubmissionStatus.EXPIRED: set(),  # Terminal
        SubmissionStatus.CANCELED: set(),  # Terminal
    }
    
    @classmethod
    def can_transition(cls, from_status: SubmissionStatus, to_status: SubmissionStatus) -> bool:
        """
        Check if transition is allowed.
        
        Args:
            from_status: Current status
            to_status: Target status
            
        Returns:
            True if transition is valid, False otherwise
        """
        valid_targets = cls.VALID_TRANSITIONS.get(from_status, set())
        return to_status in valid_targets
    
    @classmethod
    def get_valid_transitions(cls, current_status: SubmissionStatus) -> set:
        """Get all valid target states from current state."""
        return cls.VALID_TRANSITIONS.get(current_status, set())
    
    @classmethod
    def is_terminal(cls, status: SubmissionStatus) -> bool:
        """Check if status is terminal (no further transitions)."""
        return len(cls.VALID_TRANSITIONS.get(status, set())) == 0
    
    @classmethod
    def validate_transition(
        cls,
        submission: UnderwritingSubmission,
        to_status: SubmissionStatus,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[bool, List[str]]:
        """
        Validate transition preconditions.
        
        Args:
            submission: Underwriting submission instance
            to_status: Target status
            context: Additional context (terms_json, evidence_bundle_id, etc.)
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        context = context or {}
        
        # Check if transition is allowed
        if not cls.can_transition(submission.status, to_status):
            errors.append(
                f"Invalid transition from {submission.status.value} to {to_status.value}. "
                f"Valid transitions from {submission.status.value}: "
                f"{[s.value for s in cls.VALID_TRANSITIONS.get(submission.status, set())]}"
            )
            return False, errors  # Return early if transition is invalid
        
        # Transition-specific validations
        if to_status == SubmissionStatus.SUBMITTED:
            if not submission.risk_run_id:
                errors.append("risk_run_id required for submission")
            else:
                # Check if risk run exists and is SUCCEEDED
                # Note: risk_run relationship may need to be loaded
                if hasattr(submission, 'risk_run') and submission.risk_run:
                    if submission.risk_run.status != RiskRunStatus.SUCCEEDED:
                        errors.append(
                            f"Risk run must be SUCCEEDED to submit. "
                            f"Current status: {submission.risk_run.status.value}"
                        )
                # If relationship not loaded, we can't validate here
                # This should be validated in the service layer
            
            if not submission.evidence_bundle_id:
                errors.append("evidence_bundle_id required for submission")
        
        elif to_status == SubmissionStatus.QUOTED:
            if not submission.evidence_bundle_id:
                errors.append("evidence_bundle_id required for quote")
            # Evidence bundle must be sealed (checked in service)
        
        elif to_status == SubmissionStatus.BOUND:
            if submission.status != SubmissionStatus.QUOTED:
                errors.append("Can only bind from QUOTED status")
            
            if not context.get('decision'):
                errors.append("decision required for binding")
            elif context.get('decision') != 'APPROVED':
                errors.append("decision must be APPROVED for binding")
            
            # KYC must be completed (checked via applicant_json)
            if submission.applicant_json:
                kyc_status = submission.applicant_json.get('kyc_status')
                if kyc_status != 'COMPLETED':
                    errors.append("KYC must be completed for binding")
        
        elif to_status == SubmissionStatus.UNDER_REVIEW:
            # No specific preconditions for UNDER_REVIEW
            pass
        
        elif to_status == SubmissionStatus.REQUESTED_INFO:
            if not context.get('notes'):
                errors.append("notes required when requesting information")
        
        elif to_status == SubmissionStatus.DECLINED:
            if not context.get('notes'):
                errors.append("notes required when declining")
        
        return len(errors) == 0, errors
    
    
    @classmethod
    def get_transition_path(
        cls,
        from_status: SubmissionStatus,
        to_status: SubmissionStatus
    ) -> List[SubmissionStatus]:
        """
        Get shortest path between two statuses (if possible).
        
        This is a simple implementation. For complex workflows,
        consider using graph algorithms.
        
        Args:
            from_status: Starting status
            to_status: Target status
            
        Returns:
            List of statuses in transition path, or empty list if no path exists
        """
        if from_status == to_status:
            return [from_status]
        
        if cls.can_transition(from_status, to_status):
            return [from_status, to_status]
        
        # Simple BFS to find path
        from collections import deque
        
        queue = deque([(from_status, [from_status])])
        visited = {from_status}
        
        while queue:
            current, path = queue.popleft()
            
            for next_status in cls.get_valid_transitions(current):
                if next_status == to_status:
                    return path + [next_status]
                
                if next_status not in visited:
                    visited.add(next_status)
                    queue.append((next_status, path + [next_status]))
        
        return []  # No path found
