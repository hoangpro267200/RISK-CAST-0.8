"""
Tests for policy document generator.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock

from app.services.policy_document_generator import PolicyDocumentGenerator
from app.modules.underwriting.models import Policy, PolicyStatus


class TestPolicyDocumentGenerator:
    """Unit tests for policy document generator."""
    
    @pytest.fixture
    def generator(self):
        """Policy document generator instance."""
        return PolicyDocumentGenerator()
    
    @pytest.fixture
    def sample_policy(self):
        """Sample policy for testing."""
        policy = Mock(spec=Policy)
        policy.policy_number = "POL-20250123-000001"
        policy.status = PolicyStatus.ACTIVE
        policy.effective_from = datetime.utcnow()
        policy.effective_to = datetime.utcnow() + timedelta(days=90)
        policy.bound_at = datetime.utcnow()
        policy.model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
        policy.risk_run_id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
        policy.quote_id = "550e8400-e29b-41d4-a716-446655440000"
        policy.evidence_bundle_id = "550e8400-e29b-41d4-a716-446655440001"
        policy.policy_hash = "a" * 64  # Mock hash
        
        policy.terms_json = {
            "coverage_type": "ALL_RISK",
            "insured_value_cents": 1000000,
            "deductible_cents": 10000,
            "premium_cents": 50000,
            "currency": "USD",
            "extensions": ["DELAY", "CONTAMINATION"],
            "exclusions": ["WAR", "NUCLEAR"],
            "limits": {"per_shipment": 1000000},
            "conditions": ["Subject to survey", "Subject to inspection"]
        }
        
        policy.premium_json = {
            "total_premium_cents": 50000,
            "currency": "USD",
            "breakdown": {
                "base_premium_cents": 40000,
                "risk_loading_cents": 8000,
                "taxes_fees_cents": 2000
            },
            "payment_status": "PENDING"
        }
        
        policy.risk_snapshot_json = {
            "overall_risk_score": 0.42,
            "risk_factors": {
                "weather": 0.3,
                "route": 0.5
            },
            "var_95": 0.08,
            "var_99": 0.12,
            "expected_loss_cents": 20000
        }
        
        policy.policyholder_json = {
            "company_name": "Test Company Inc.",
            "contact_email": "contact@testcompany.com",
            "address": "123 Test St, Test City, TC 12345"
        }
        
        return policy
    
    def test_generates_document(self, generator, sample_policy):
        """Generator produces valid document bytes."""
        doc_bytes, doc_hash = generator.generate(sample_policy)
        
        assert doc_bytes is not None
        assert len(doc_bytes) > 0
        assert len(doc_hash) == 64  # SHA256
    
    def test_hash_is_deterministic(self, generator, sample_policy):
        """Same policy produces same hash."""
        _, hash1 = generator.generate(sample_policy)
        _, hash2 = generator.generate(sample_policy)
        
        assert hash1 == hash2
    
    def test_includes_policy_number(self, generator, sample_policy):
        """Document includes policy number."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if policy number is in document
        assert sample_policy.policy_number.encode() in doc_bytes
    
    def test_includes_coverage_details(self, generator, sample_policy):
        """Document includes coverage details."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if coverage type is in document
        assert b"ALL_RISK" in doc_bytes or b"all_risk" in doc_bytes.lower()
        assert b"1000000" in doc_bytes or b"10,000.00" in doc_bytes  # Insured value
    
    def test_includes_extensions(self, generator, sample_policy):
        """Document includes coverage extensions."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if extensions are in document
        assert b"DELAY" in doc_bytes or b"delay" in doc_bytes.lower()
        assert b"CONTAMINATION" in doc_bytes or b"contamination" in doc_bytes.lower()
    
    def test_includes_exclusions(self, generator, sample_policy):
        """Document includes exclusions."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if exclusions are in document
        assert b"WAR" in doc_bytes or b"war" in doc_bytes.lower()
        assert b"NUCLEAR" in doc_bytes or b"nuclear" in doc_bytes.lower()
    
    def test_includes_risk_summary(self, generator, sample_policy):
        """Document includes risk assessment summary."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if risk score is in document
        assert b"42" in doc_bytes or b"0.42" in doc_bytes
    
    def test_includes_audit_information(self, generator, sample_policy):
        """Document includes audit information."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if model version ID is in document
        assert sample_policy.model_version_id.encode() in doc_bytes
        assert sample_policy.risk_run_id.encode() in doc_bytes
    
    def test_includes_policy_hash(self, generator, sample_policy):
        """Document includes policy hash."""
        doc_bytes, _ = generator.generate(sample_policy)
        
        # Check if policy hash is in document (at least part of it)
        assert sample_policy.policy_hash[:16].encode() in doc_bytes
    
    def test_generates_certificate(self, generator, sample_policy):
        """Can generate certificate of insurance."""
        cert_bytes, cert_hash = generator.generate_certificate(sample_policy)
        
        assert cert_bytes is not None
        assert len(cert_bytes) > 0
        assert len(cert_hash) == 64
        assert b"CERTIFICATE" in cert_bytes.upper()
    
    def test_generates_endorsement(self, generator, sample_policy):
        """Can generate endorsement document."""
        changes = {
            "premium_cents": 60000,
            "deductible_cents": 15000
        }
        
        end_bytes, end_hash = generator.generate_endorsement(
            sample_policy,
            "PREMIUM_ADJUSTMENT",
            changes
        )
        
        assert end_bytes is not None
        assert len(end_bytes) > 0
        assert len(end_hash) == 64
        assert b"ENDORSEMENT" in end_bytes.upper()
    
    def test_handles_missing_fields(self, generator):
        """Generator handles missing optional fields gracefully."""
        policy = Mock(spec=Policy)
        policy.policy_number = "POL-TEST-001"
        policy.status = PolicyStatus.ACTIVE
        policy.effective_from = datetime.utcnow()
        policy.effective_to = datetime.utcnow() + timedelta(days=30)
        policy.bound_at = datetime.utcnow()
        policy.model_version_id = "01ARZ3NDEKTSV4RRFFQ69G5FAZ"
        policy.risk_run_id = "01ARZ3NDEKTSV4RRFFQ69G5FAY"
        policy.quote_id = None
        policy.evidence_bundle_id = None
        policy.policy_hash = "b" * 64
        
        # Missing optional fields
        policy.terms_json = {}
        policy.premium_json = None
        policy.risk_snapshot_json = None
        policy.policyholder_json = None
        
        # Should not raise exception
        doc_bytes, doc_hash = generator.generate(policy)
        
        assert doc_bytes is not None
        assert len(doc_hash) == 64
