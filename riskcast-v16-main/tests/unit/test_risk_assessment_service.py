"""
Unit tests for RiskAssessmentService.
"""
from __future__ import annotations

import pytest

from app.models.risk_assessment import RiskAssessment
from app.services.risk_assessment_service import RiskAssessmentService
from app.shared.exceptions import NotFoundError
from app.shared.utils import generate_ulid


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return generate_ulid()


@pytest.fixture
def raw_input_data():
    """Raw input data (not canonicalized)"""
    return {
        "cargo_value": 100000.0,
        "distance": 5000,
        "cargo_type": "  standard  ",  # Has whitespace
    }


@pytest.fixture
def service(db_session):
    """Service instance"""
    return RiskAssessmentService(db_session)


class TestRiskAssessmentService:
    """Test RiskAssessmentService business logic."""

    def test_create_assessment(
        self, service, tenant_id, raw_input_data
    ):
        """Test creating a new assessment"""
        assessment = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        assert assessment.id is not None
        assert assessment.tenant_id == tenant_id
        assert assessment.schema_version == "v1"
        assert assessment.input_hash is not None
        assert len(assessment.input_hash) == 64
        # Input should be canonicalized (whitespace normalized)
        assert assessment.input_snapshot_json["cargo_type"] == "standard"

    def test_create_assessment_deduplication(
        self, service, tenant_id, raw_input_data
    ):
        """Test that duplicate inputs return the same assessment"""
        # Create first assessment
        assessment1 = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        # Create second assessment with semantically identical input
        # (different key order, whitespace, float precision)
        raw_input2 = {
            "cargo_type": "standard",  # No whitespace
            "cargo_value": 100000,  # Integer instead of float
            "distance": 5000,
        }
        assessment2 = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input2,
        )
        # Should return the same assessment (deduplication)
        assert assessment1.id == assessment2.id
        assert assessment1.input_hash == assessment2.input_hash

    def test_get_or_create_new(self, service, tenant_id, raw_input_data):
        """Test get_or_create when assessment doesn't exist"""
        assessment, was_created = service.get_or_create(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        assert was_created is True
        assert assessment.id is not None
        assert assessment.tenant_id == tenant_id

    def test_get_or_create_existing(
        self, service, tenant_id, raw_input_data
    ):
        """Test get_or_create when assessment already exists"""
        # Create first
        assessment1, was_created1 = service.get_or_create(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        assert was_created1 is True
        # Get or create again with same input
        assessment2, was_created2 = service.get_or_create(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        assert was_created2 is False
        assert assessment1.id == assessment2.id

    def test_get_assessment_found(self, service, tenant_id, raw_input_data):
        """Test getting assessment by ID when it exists"""
        created = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        found = service.get_assessment(tenant_id, created.id)
        assert found.id == created.id
        assert found.tenant_id == tenant_id

    def test_get_assessment_not_found(self, service, tenant_id):
        """Test getting assessment by ID when it doesn't exist"""
        with pytest.raises(NotFoundError):
            service.get_assessment(tenant_id, "nonexistent-id")

    def test_get_assessment_tenant_isolation(
        self, service, raw_input_data
    ):
        """Test that tenant isolation works for get_assessment"""
        tenant1 = generate_ulid()
        tenant2 = generate_ulid()
        assessment1 = service.create_assessment(
            tenant_id=tenant1,
            raw_input=raw_input_data,
        )
        # Tenant 2 cannot see tenant 1's assessment
        with pytest.raises(NotFoundError):
            service.get_assessment(tenant2, assessment1.id)
        # Tenant 1 can see their own assessment
        found = service.get_assessment(tenant1, assessment1.id)
        assert found.id == assessment1.id

    def test_list_by_shipment(
        self, service, tenant_id, raw_input_data
    ):
        """Test listing assessments by shipment"""
        shipment_id = generate_ulid()
        # Create 2 assessments for the same shipment
        for i in range(2):
            service.create_assessment(
                tenant_id=tenant_id,
                raw_input={**raw_input_data, "index": i},
                shipment_id=shipment_id,
            )
        assessments = service.list_by_shipment(tenant_id, shipment_id)
        assert len(assessments) == 2
        assert all(a.shipment_id == shipment_id for a in assessments)

    def test_list_by_shipment_tenant_isolation(
        self, service, raw_input_data
    ):
        """Test that tenant isolation works for list_by_shipment"""
        tenant1 = generate_ulid()
        tenant2 = generate_ulid()
        shipment_id = generate_ulid()
        # Tenant 1 creates assessment
        service.create_assessment(
            tenant_id=tenant1,
            raw_input=raw_input_data,
            shipment_id=shipment_id,
        )
        # Tenant 2 cannot see tenant 1's assessment
        assessments = service.list_by_shipment(tenant2, shipment_id)
        assert len(assessments) == 0
        # Tenant 1 can see their own assessment
        assessments = service.list_by_shipment(tenant1, shipment_id)
        assert len(assessments) == 1

    def test_different_inputs_different_assessments(
        self, service, tenant_id, raw_input_data
    ):
        """Test that different inputs create different assessments"""
        assessment1 = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input_data,
        )
        # Different input (different cargo_value)
        raw_input2 = {**raw_input_data, "cargo_value": 200000}
        assessment2 = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input2,
        )
        # Should be different assessments
        assert assessment1.id != assessment2.id
        assert assessment1.input_hash != assessment2.input_hash
