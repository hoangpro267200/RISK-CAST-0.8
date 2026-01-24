"""
Tests for submission state machine.
"""

import pytest
from app.modules.underwriting.models import SubmissionStatus
from app.core.underwriting.state_machine import SubmissionStateMachine
from app.models.underwriting import UnderwritingSubmission


class TestSubmissionStateMachine:
    """Unit tests for submission state machine."""
    
    def test_valid_transitions_from_draft(self):
        """DRAFT can only go to SUBMITTED."""
        valid = SubmissionStateMachine.get_valid_transitions(SubmissionStatus.DRAFT)
        assert valid == {SubmissionStatus.SUBMITTED}
    
    def test_valid_transitions_from_under_review(self):
        """UNDER_REVIEW can go to multiple states."""
        valid = SubmissionStateMachine.get_valid_transitions(SubmissionStatus.UNDER_REVIEW)
        assert SubmissionStatus.REQUESTED_INFO in valid
        assert SubmissionStatus.QUOTED in valid
        assert SubmissionStatus.DECLINED in valid
    
    def test_terminal_states(self):
        """CLOSED and EXPIRED are terminal."""
        assert SubmissionStateMachine.is_terminal(SubmissionStatus.CLOSED)
        assert SubmissionStateMachine.is_terminal(SubmissionStatus.EXPIRED)
        assert not SubmissionStateMachine.is_terminal(SubmissionStatus.DRAFT)
    
    def test_invalid_transition_rejected(self):
        """Cannot transition from DRAFT to QUOTED directly."""
        assert not SubmissionStateMachine.can_transition(
            SubmissionStatus.DRAFT,
            SubmissionStatus.QUOTED
        )
    
    def test_validate_transition_checks_invariants(self):
        """Transition validation checks required fields."""
        from unittest.mock import Mock
        
        mock_submission = Mock()
        mock_submission.status = SubmissionStatus.DRAFT
        mock_submission.risk_assessment_id = None  # Missing!
        mock_submission.requested_coverage_json = None  # Missing!
        
        is_valid, errors = SubmissionStateMachine.validate_transition(
            mock_submission,
            SubmissionStatus.SUBMITTED
        )
        
        assert not is_valid
        assert any("risk_assessment_id" in e for e in errors) or any("requested_coverage_json" in e for e in errors)
    
    def test_validate_transition_valid(self):
        """Valid transition with all required fields passes."""
        from unittest.mock import Mock
        
        mock_submission = Mock()
        mock_submission.status = SubmissionStatus.DRAFT
        mock_submission.risk_assessment_id = "test_id"
        mock_submission.requested_coverage_json = {"coverage_type": "ALL_RISK"}
        mock_submission.evidence_bundle_id = None
        mock_submission.applicant_json = None
        
        is_valid, errors = SubmissionStateMachine.validate_transition(
            mock_submission,
            SubmissionStatus.SUBMITTED
        )
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_quote_requires_evidence_bundle(self):
        """Quote transition requires evidence bundle."""
        from unittest.mock import Mock
        
        mock_submission = Mock()
        mock_submission.status = SubmissionStatus.UNDER_REVIEW
        mock_submission.evidence_bundle_id = None  # Missing!
        
        is_valid, errors = SubmissionStateMachine.validate_transition(
            mock_submission,
            SubmissionStatus.QUOTED
        )
        
        assert not is_valid
        assert any("evidence_bundle_id" in e for e in errors)
    
    def test_validate_bind_requires_approved_decision(self):
        """Bind transition requires APPROVED decision."""
        from unittest.mock import Mock
        
        mock_submission = Mock()
        mock_submission.status = SubmissionStatus.QUOTED
        mock_submission.applicant_json = {"kyc_status": "COMPLETED"}
        
        # Missing decision
        is_valid, errors = SubmissionStateMachine.validate_transition(
            mock_submission,
            SubmissionStatus.BOUND,
            context={}
        )
        
        assert not is_valid
        assert any("decision" in e for e in errors)
        
        # Wrong decision
        is_valid, errors = SubmissionStateMachine.validate_transition(
            mock_submission,
            SubmissionStatus.BOUND,
            context={"decision": "DECLINED"}
        )
        
        assert not is_valid
        assert any("APPROVED" in e for e in errors)
    
    def test_validate_bind_requires_kyc_completed(self):
        """Bind transition requires KYC completed."""
        from unittest.mock import Mock
        
        mock_submission = Mock()
        mock_submission.status = SubmissionStatus.QUOTED
        mock_submission.applicant_json = {"kyc_status": "PENDING"}  # Not completed!
        
        is_valid, errors = SubmissionStateMachine.validate_transition(
            mock_submission,
            SubmissionStatus.BOUND,
            context={"decision": "APPROVED"}
        )
        
        assert not is_valid
        assert any("KYC" in e for e in errors)
    
    def test_get_transition_path(self):
        """Can find path between states."""
        path = SubmissionStateMachine.get_transition_path(
            SubmissionStatus.DRAFT,
            SubmissionStatus.QUOTED
        )
        
        assert len(path) > 0
        assert path[0] == SubmissionStatus.DRAFT
        assert path[-1] == SubmissionStatus.QUOTED
    
    def test_get_transition_path_no_path(self):
        """Returns empty list if no path exists."""
        path = SubmissionStateMachine.get_transition_path(
            SubmissionStatus.CLOSED,
            SubmissionStatus.DRAFT
        )
        
        assert path == []
