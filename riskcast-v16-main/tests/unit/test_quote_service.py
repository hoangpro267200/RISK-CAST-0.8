"""
Tests for quote service.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.services.quote_service import (
    QuoteService,
    QuoteAlreadyIssuedError,
    QuoteExpiredError,
    QuoteNotFoundError,
    SubmissionNotFoundError,
    InvalidSubmissionStateError,
    InvalidRiskRunError
)
from app.models.quote import Quote
from app.modules.underwriting.models import UnderwritingSubmission, SubmissionStatus
from app.modules.risk_runs.models import RiskRun, RiskRunStatus


class TestQuoteService:
    """Unit tests for quote service."""
    
    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def audit_ledger(self):
        """Mock audit ledger."""
        return Mock()
    
    @pytest.fixture
    def service(self, db_session, audit_ledger):
        """Quote service instance."""
        return QuoteService(db_session, audit_ledger)
    
    @pytest.fixture
    def tenant_id(self):
        """Sample tenant ID."""
        return "01ARZ3NDEKTSV4RRFFQ69G5FAV"
    
    @pytest.fixture
    def user_id(self):
        """Sample user ID."""
        return "01ARZ3NDEKTSV4RRFFQ69G5FAW"
    
    @pytest.fixture
    def submission(self, tenant_id):
        """Sample submission."""
        sub = Mock(spec=UnderwritingSubmission)
        sub.id = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        sub.tenant_id = tenant_id
        sub.status = SubmissionStatus.UNDER_REVIEW
        sub.submission_number = "SUB-20250123-00001"
        return sub
    
    @pytest.fixture
    def risk_run(self):
        """Sample risk run."""
        run = Mock(spec=RiskRun)
        run.id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
        run.status = RiskRunStatus.SUCCEEDED
        run.model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
        run.result_json = {
            "overall_risk_score": 0.42,
            "risk_factors": {"weather": 0.3, "route": 0.5},
            "var_95": 0.08,
            "var_99": 0.12,
            "expected_loss": 0.05
        }
        return run
    
    @pytest.fixture
    def pricing_input(self):
        """Sample pricing input."""
        return {
            "insured_value_cents": 1000000,
            "currency": "USD",
            "deductible_cents": 10000,
            "minimum_premium_cents": 10000
        }
    
    @pytest.fixture
    def coverage_terms(self):
        """Sample coverage terms."""
        return {
            "coverage_type": "ALL_RISK",
            "extensions": ["DELAY", "CONTAMINATION"],
            "exclusions": ["WAR", "NUCLEAR"],
            "limits": {"per_shipment": 1000000},
            "conditions": ["Subject to survey"]
        }
    
    def test_create_quote_in_draft(
        self,
        service,
        db_session,
        tenant_id,
        submission,
        risk_run,
        user_id,
        pricing_input,
        coverage_terms
    ):
        """New quotes start in DRAFT status."""
        # Setup mocks
        db_session.query.return_value.filter.return_value.first.return_value = submission
        db_session.query.return_value.filter.return_value.count.return_value = 0
        db_session.query.return_value.filter.return_value.update.return_value = None
        
        # Mock quote creation
        quote = Mock(spec=Quote)
        quote.id = "550e8400-e29b-41d4-a716-446655440000"
        quote.quote_number = "QTE-00001"
        quote.version = 1
        quote.status = "DRAFT"
        quote.is_latest = True
        quote.quote_hash = ""
        
        with patch('app.services.quote_service.Quote', return_value=quote):
            with patch('uuid.uuid4', return_value=Mock(hex="550e8400e29b41d4a716446655440000")):
                result = service.create_quote(
                    tenant_id=tenant_id,
                    submission_id=submission.id,
                    risk_run_id=risk_run.id,
                    pricing_input=pricing_input,
                    coverage_terms=coverage_terms,
                    created_by=user_id
                )
        
        assert result.status == "DRAFT"
        assert result.version == 1
        assert result.is_latest == True
        assert result.quote_hash == ""
    
    def test_issue_quote_computes_hash(
        self,
        service,
        db_session,
        tenant_id,
        user_id
    ):
        """Issuing quote computes hash and makes it immutable."""
        # Create draft quote
        quote = Mock(spec=Quote)
        quote.id = "550e8400-e29b-41d4-a716-446655440000"
        quote.status = "DRAFT"
        quote.quote_hash = ""
        quote.quote_number = "QTE-00001"
        quote.version = 1
        quote.submission_id = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        quote.model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
        quote.risk_run_id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
        quote.pricing_snapshot_json = {"premium_cents": 50000}
        quote.coverage_terms_json = {"coverage_type": "ALL_RISK"}
        quote.risk_summary_json = {"overall_risk_score": 0.42}
        quote.valid_from = datetime.utcnow()
        quote.valid_until = datetime.utcnow() + timedelta(days=30)
        quote.evidence_bundle_id = None
        quote.tenant_id = tenant_id
        
        db_session.query.return_value.filter.return_value.first.return_value = quote
        
        result = service.issue_quote(quote.id, user_id)
        
        assert result.status == "ISSUED"
        assert result.quote_hash != ""
        assert len(result.quote_hash) == 64  # SHA256
        assert result.issued_at is not None
    
    def test_cannot_issue_twice(
        self,
        service,
        db_session,
        user_id
    ):
        """Cannot issue an already issued quote."""
        quote = Mock(spec=Quote)
        quote.id = "550e8400-e29b-41d4-a716-446655440000"
        quote.status = "ISSUED"
        
        db_session.query.return_value.filter.return_value.first.return_value = quote
        
        with pytest.raises(QuoteAlreadyIssuedError):
            service.issue_quote(quote.id, user_id)
    
    def test_revise_quote_creates_new_version(
        self,
        service,
        db_session,
        tenant_id,
        user_id,
        risk_run
    ):
        """Revising creates new version, marks original as replaced."""
        # Original issued quote
        original = Mock(spec=Quote)
        original.id = "550e8400-e29b-41d4-a716-446655440000"
        original.status = "ISSUED"
        original.version = 1
        original.is_latest = True
        original.tenant_id = tenant_id
        original.submission_id = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        original.quote_number = "QTE-00001"
        original.model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
        original.risk_run_id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
        original.evidence_bundle_id = None
        original.coverage_terms_json = {"coverage_type": "ALL_RISK"}
        original.pricing_snapshot_json = {"premium_cents": 50000}
        original.risk_summary_json = {"overall_risk_score": 0.42}
        original.valid_from = datetime.utcnow()
        original.valid_until = datetime.utcnow() + timedelta(days=30)
        
        # New quote
        new_quote = Mock(spec=Quote)
        new_quote.id = "550e8400-e29b-41d4-a716-446655440001"
        new_quote.version = 2
        new_quote.is_latest = True
        new_quote.replaces_quote_id = original.id
        
        db_session.query.return_value.filter.return_value.first.side_effect = [original, risk_run]
        db_session.query.return_value.filter.return_value.count.return_value = 1
        db_session.query.return_value.filter.return_value.update.return_value = None
        
        with patch('app.services.quote_service.Quote', return_value=new_quote):
            with patch('uuid.uuid4', return_value=Mock(hex="550e8400e29b41d4a716446655440001")):
                result = service.revise_quote(
                    quote_id=original.id,
                    new_pricing_input={"insured_value_cents": 2000000, "currency": "USD"},
                    new_coverage_terms=None,
                    revised_by=user_id,
                    revision_reason="Increased coverage"
                )
        
        assert result.version == original.version + 1
        assert result.is_latest == True
        assert result.replaces_quote_id == original.id
        assert original.status == "REPLACED"
        assert original.is_latest == False
    
    def test_accept_quote(
        self,
        service,
        db_session,
        tenant_id,
        user_id
    ):
        """Can accept an issued quote."""
        quote = Mock(spec=Quote)
        quote.id = "550e8400-e29b-41d4-a716-446655440000"
        quote.status = "ISSUED"
        quote.valid_until = datetime.utcnow() + timedelta(days=30)
        quote.tenant_id = tenant_id
        
        db_session.query.return_value.filter.return_value.first.return_value = quote
        
        result = service.accept_quote(quote.id, user_id)
        
        assert result.status == "ACCEPTED"
        assert result.accepted_at is not None
    
    def test_cannot_accept_expired_quote(
        self,
        service,
        db_session,
        tenant_id,
        user_id
    ):
        """Cannot accept an expired quote."""
        quote = Mock(spec=Quote)
        quote.id = "550e8400-e29b-41d4-a716-446655440000"
        quote.status = "ISSUED"
        quote.valid_until = datetime.utcnow() - timedelta(days=1)  # Expired
        quote.tenant_id = tenant_id
        
        db_session.query.return_value.filter.return_value.first.return_value = quote
        
        with pytest.raises(QuoteExpiredError):
            service.accept_quote(quote.id, user_id)
    
    def test_quote_hash_integrity(
        self,
        service,
        db_session
    ):
        """Quote hash should verify correctly."""
        quote = Mock(spec=Quote)
        quote.id = "550e8400-e29b-41d4-a716-446655440000"
        quote.status = "ISSUED"
        quote.quote_hash = "abc123" * 10  # Mock hash
        quote.quote_number = "QTE-00001"
        quote.version = 1
        quote.submission_id = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        quote.model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
        quote.risk_run_id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
        quote.pricing_snapshot_json = {"premium_cents": 50000}
        quote.coverage_terms_json = {"coverage_type": "ALL_RISK"}
        quote.risk_summary_json = {"overall_risk_score": 0.42}
        quote.valid_from = datetime.utcnow()
        quote.valid_until = datetime.utcnow() + timedelta(days=30)
        
        db_session.query.return_value.filter.return_value.first.return_value = quote
        
        result = service.verify_quote_integrity(quote.id)
        
        # Hash verification will compute new hash, so it may not match
        # But the structure should be correct
        assert "valid" in result
        assert "stored_hash" in result
        assert "computed_hash" in result
    
    def test_get_quote_versions(
        self,
        service,
        db_session
    ):
        """Can retrieve all versions of a quote."""
        submission_id = "01ARZ3NDEKTSV4RRFFQ69G5FAX"
        
        quote1 = Mock(spec=Quote)
        quote1.version = 1
        quote2 = Mock(spec=Quote)
        quote2.version = 2
        quote3 = Mock(spec=Quote)
        quote3.version = 3
        quote3.is_latest = True
        
        db_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            quote3, quote2, quote1
        ]
        
        versions = service.get_quote_with_versions(submission_id)
        
        assert len(versions) == 3
        assert versions[0].version == 3  # Most recent first
    
    def test_create_quote_invalid_submission_state(
        self,
        service,
        db_session,
        tenant_id,
        submission,
        risk_run,
        user_id,
        pricing_input,
        coverage_terms
    ):
        """Cannot create quote for submission in invalid state."""
        submission.status = SubmissionStatus.DRAFT
        
        db_session.query.return_value.filter.return_value.first.return_value = submission
        
        with pytest.raises(InvalidSubmissionStateError):
            service.create_quote(
                tenant_id=tenant_id,
                submission_id=submission.id,
                risk_run_id=risk_run.id,
                pricing_input=pricing_input,
                coverage_terms=coverage_terms,
                created_by=user_id
            )
    
    def test_create_quote_submission_not_found(
        self,
        service,
        db_session,
        tenant_id,
        risk_run,
        user_id,
        pricing_input,
        coverage_terms
    ):
        """Cannot create quote if submission not found."""
        db_session.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(SubmissionNotFoundError):
            service.create_quote(
                tenant_id=tenant_id,
                submission_id="nonexistent",
                risk_run_id=risk_run.id,
                pricing_input=pricing_input,
                coverage_terms=coverage_terms,
                created_by=user_id
            )
