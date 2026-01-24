"""
Tests for claims state machine.
"""

import pytest
from app.modules.claims.models import ClaimStatus
from app.core.claims.state_machine import ClaimStateMachine


class TestClaimStateMachine:
    """Unit tests for claim state machine."""
    
    def test_valid_transitions_from_fnol(self):
        """FNOL_RECEIVED can go to UNDER_INVESTIGATION or WITHDRAWN."""
        valid = ClaimStateMachine.get_valid_transitions(ClaimStatus.FNOL_RECEIVED)
        assert ClaimStatus.UNDER_INVESTIGATION in valid
        assert ClaimStatus.WITHDRAWN in valid
    
    def test_valid_transitions_from_under_investigation(self):
        """UNDER_INVESTIGATION can go to multiple states."""
        valid = ClaimStateMachine.get_valid_transitions(ClaimStatus.UNDER_INVESTIGATION)
        assert ClaimStatus.AWAITING_EVIDENCE in valid
        assert ClaimStatus.APPROVED in valid
        assert ClaimStatus.DECLINED in valid
    
    def test_terminal_states(self):
        """CLOSED and WITHDRAWN are terminal."""
        assert ClaimStateMachine.is_terminal(ClaimStatus.CLOSED)
        assert ClaimStateMachine.is_terminal(ClaimStatus.WITHDRAWN)
        assert not ClaimStateMachine.is_terminal(ClaimStatus.FNOL_RECEIVED)
    
    def test_invalid_transition_rejected(self):
        """Cannot transition from FNOL_RECEIVED to APPROVED directly."""
        assert not ClaimStateMachine.can_transition(
            ClaimStatus.FNOL_RECEIVED,
            ClaimStatus.APPROVED
        )
    
    def test_validate_transition_checks_invariants(self):
        """Transition validation checks required fields."""
        from unittest.mock import Mock
        
        mock_claim = Mock()
        mock_claim.status = ClaimStatus.FNOL_RECEIVED
        mock_claim.assigned_adjuster_id = None  # Missing!
        mock_claim.evidence_bundle_id = None
        
        is_valid, errors = ClaimStateMachine.validate_transition(
            mock_claim,
            ClaimStatus.UNDER_INVESTIGATION
        )
        
        assert not is_valid
        assert any("assigned_adjuster_id" in e for e in errors)
    
    def test_validate_approval_requires_evidence(self):
        """Approval transition requires evidence bundle."""
        from unittest.mock import Mock
        
        mock_claim = Mock()
        mock_claim.status = ClaimStatus.UNDER_INVESTIGATION
        mock_claim.evidence_bundle_id = None  # Missing!
        mock_claim.approved_amount_cents = None
        mock_claim.adjudication_json = None
        
        is_valid, errors = ClaimStateMachine.validate_transition(
            mock_claim,
            ClaimStatus.APPROVED
        )
        
        assert not is_valid
        assert any("evidence_bundle_id" in e for e in errors) or any("Evidence bundle" in e for e in errors)
    
    def test_validate_paid_requires_payout_id(self):
        """Paid transition requires payout_id."""
        from unittest.mock import Mock
        
        mock_claim = Mock()
        mock_claim.status = ClaimStatus.AUTHORIZED
        mock_claim.payout_id = None  # Missing!
        mock_claim.evidence_bundle_id = "bundle-id"
        
        is_valid, errors = ClaimStateMachine.validate_transition(
            mock_claim,
            ClaimStatus.PAID
        )
        
        assert not is_valid
        assert any("payout_id" in e for e in errors)
    
    def test_requires_authorization(self):
        """AUTHORIZED status requires authorization control."""
        assert ClaimStateMachine.requires_authorization(ClaimStatus.AUTHORIZED)
        assert not ClaimStateMachine.requires_authorization(ClaimStatus.APPROVED)
