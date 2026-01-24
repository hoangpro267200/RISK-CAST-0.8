"""
Unit tests for RiskAssessmentRepository.
"""
from __future__ import annotations

import pytest

from app.models.risk_assessment import RiskAssessment
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.shared.utils import generate_ulid


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return generate_ulid()


@pytest.fixture
def sample_input_data():
    """Sample input data for testing"""
    return {
        "cargo_value": 100000,
        "distance": 5000,
        "cargo_type": "standard",
    }


@pytest.fixture
def repository(db_session):
    """Repository instance"""
    return RiskAssessmentRepository(db_session)


class TestRiskAssessmentRepository:
    """Test RiskAssessmentRepository CRUD operations."""

    def test_create(self, repository, tenant_id, sample_input_data):
        """Test creating a risk assessment"""
        assessment = repository.create(
            tenant_id=tenant_id,
            input_data=sample_input_data,
            schema_version="v1",
        )
        assert assessment.id is not None
        assert assessment.tenant_id == tenant_id
        assert assessment.input_snapshot_json == sample_input_data
        assert assessment.schema_version == "v1"
        assert assessment.input_hash is not None
        assert len(assessment.input_hash) == 64  # SHA256 hex

    def test_get_by_id_found(self, repository, tenant_id, sample_input_data):
        """Test getting assessment by ID when it exists"""
        created = repository.create(
            tenant_id=tenant_id,
            input_data=sample_input_data,
            schema_version="v1",
        )
        found = repository.get_by_id(tenant_id, created.id)
        assert found is not None
        assert found.id == created.id
        assert found.tenant_id == tenant_id

    def test_get_by_id_not_found(self, repository, tenant_id):
        """Test getting assessment by ID when it doesn't exist"""
        found = repository.get_by_id(tenant_id, "nonexistent-id")
        assert found is None

    def test_get_by_id_tenant_isolation(self, repository, sample_input_data):
        """Test that tenant isolation works for get_by_id"""
        tenant1 = generate_ulid()
        tenant2 = generate_ulid()
        assessment1 = repository.create(
            tenant_id=tenant1,
            input_data=sample_input_data,
            schema_version="v1",
        )
        # Tenant 2 cannot see tenant 1's assessment
        found = repository.get_by_id(tenant2, assessment1.id)
        assert found is None
        # Tenant 1 can see their own assessment
        found = repository.get_by_id(tenant1, assessment1.id)
        assert found is not None
        assert found.id == assessment1.id

    def test_get_by_input_hash_found(self, repository, tenant_id, sample_input_data):
        """Test getting assessment by input hash when it exists"""
        created = repository.create(
            tenant_id=tenant_id,
            input_data=sample_input_data,
            schema_version="v1",
        )
        # Get the computed hash
        input_hash = created.input_hash
        found = repository.get_by_input_hash(tenant_id, input_hash)
        assert found is not None
        assert found.id == created.id
        assert found.input_hash == input_hash

    def test_get_by_input_hash_not_found(self, repository, tenant_id):
        """Test getting assessment by input hash when it doesn't exist"""
        found = repository.get_by_input_hash(tenant_id, "e" * 64)
        assert found is None

    def test_get_by_input_hash_tenant_isolation(
        self, repository, sample_input_data
    ):
        """Test that tenant isolation works for get_by_input_hash"""
        tenant1 = generate_ulid()
        tenant2 = generate_ulid()
        assessment1 = repository.create(
            tenant_id=tenant1,
            input_data=sample_input_data,
            schema_version="v1",
        )
        input_hash = assessment1.input_hash
        # Tenant 2 cannot see tenant 1's assessment
        found = repository.get_by_input_hash(tenant2, input_hash)
        assert found is None
        # Tenant 1 can see their own assessment
        found = repository.get_by_input_hash(tenant1, input_hash)
        assert found is not None
        assert found.id == assessment1.id

    def test_list_by_shipment(self, repository, tenant_id, sample_input_data):
        """Test listing assessments by shipment"""
        shipment_id = generate_ulid()
        # Create 3 assessments for the same shipment
        for i in range(3):
            repository.create(
                tenant_id=tenant_id,
                input_data={**sample_input_data, "index": i},
                schema_version="v1",
                shipment_id=shipment_id,
            )
        # Create 1 assessment for a different shipment
        repository.create(
            tenant_id=tenant_id,
            input_data=sample_input_data,
            schema_version="v1",
            shipment_id=generate_ulid(),
        )
        assessments = repository.list_by_shipment(tenant_id, shipment_id)
        assert len(assessments) == 3
        assert all(a.shipment_id == shipment_id for a in assessments)

    def test_list_by_shipment_tenant_isolation(
        self, repository, sample_input_data
    ):
        """Test that tenant isolation works for list_by_shipment"""
        tenant1 = generate_ulid()
        tenant2 = generate_ulid()
        shipment_id = generate_ulid()
        # Tenant 1 creates assessment
        repository.create(
            tenant_id=tenant1,
            input_data=sample_input_data,
            schema_version="v1",
            shipment_id=shipment_id,
        )
        # Tenant 2 cannot see tenant 1's assessment
        assessments = repository.list_by_shipment(tenant2, shipment_id)
        assert len(assessments) == 0
        # Tenant 1 can see their own assessment
        assessments = repository.list_by_shipment(tenant1, shipment_id)
        assert len(assessments) == 1
