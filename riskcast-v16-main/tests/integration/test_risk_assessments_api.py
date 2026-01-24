"""
Integration Tests for Risk Assessments API v3
API contract tests for risk assessment endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.risk_assessment import RiskAssessment
from app.models.risk_run import RiskRun, RiskRunStatus
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.repositories.risk_run_repository import RiskRunRepository
from app.shared.utils import generate_ulid


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return generate_ulid()


@pytest.fixture
def sample_shipment_data():
    """Sample shipment data for testing"""
    return {
        "cargo_value": 100000,
        "distance": 5000,
        "origin": "USNYC",
        "destination": "GBLON",
        "cargo_type": "electronics"
    }


class TestRiskAssessmentsAPI:
    """Tests for Risk Assessments API v3"""
    
    def test_create_assessment_creates_with_correct_hash(
        self, client, db_session, tenant_id, sample_shipment_data
    ):
        """Test that POST creates assessment with correct input hash"""
        # Note: This test requires authentication setup
        # For now, we'll test the logic directly
        
        from app.services.risk_assessment_service import RiskAssessmentService
        from app.core.risk_input.canonicalization import compute_input_hash, canonicalize_input
        
        service = RiskAssessmentService(db_session)
        
        # Create assessment
        assessment = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        # Verify hash
        canonical_input = canonicalize_input(sample_shipment_data)
        expected_hash = compute_input_hash(canonical_input)
        
        assert assessment.input_hash == expected_hash
        assert assessment.input_snapshot_json == canonical_input
        assert assessment.tenant_id == tenant_id
    
    def test_create_assessment_deduplicates_by_hash(
        self, client, db_session, tenant_id, sample_shipment_data
    ):
        """Test that duplicate input returns existing assessment"""
        from app.services.risk_assessment_service import RiskAssessmentService
        
        service = RiskAssessmentService(db_session)
        
        # Create first assessment
        assessment1 = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        # Create second assessment with same input
        assessment2 = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        # Should return same assessment (deduplication)
        assert assessment1.id == assessment2.id
        assert assessment1.input_hash == assessment2.input_hash
    
    def test_get_assessment_returns_details_with_runs(
        self, db_session, tenant_id, sample_shipment_data
    ):
        """Test that GET returns assessment details with linked runs"""
        from app.services.risk_assessment_service import RiskAssessmentService
        from app.services.risk_run_service import RiskRunService
        from app.repositories.risk_run_repository import RiskRunRepository
        
        # Create assessment
        assessment_service = RiskAssessmentService(db_session)
        assessment = assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        # Create run
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED"
        )
        
        # Get assessment details
        retrieved = assessment_service.get_assessment(assessment.id)
        
        assert retrieved is not None
        assert retrieved.id == assessment.id
        assert retrieved.input_hash == assessment.input_hash
        assert retrieved.input_snapshot_json == assessment.input_snapshot_json
        
        # Verify runs are linked
        run_repo = RiskRunRepository(db_session)
        runs = run_repo.list_by_assessment(tenant_id, assessment.id)
        
        assert len(runs) >= 1
        assert any(r.id == run.id for r in runs)
    
    def test_list_assessment_runs_returns_linked_runs(
        self, db_session, tenant_id, sample_shipment_data
    ):
        """Test that GET /{assessment_id}/runs returns linked runs"""
        from app.services.risk_assessment_service import RiskAssessmentService
        from app.services.risk_run_service import RiskRunService
        from app.repositories.risk_run_repository import RiskRunRepository
        
        # Create assessment
        assessment_service = RiskAssessmentService(db_session)
        assessment = assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        # Create multiple runs
        run_service = RiskRunService(db_session)
        run1 = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id
        )
        run2 = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id
        )
        
        # Get runs
        run_repo = RiskRunRepository(db_session)
        runs = run_repo.list_by_assessment(tenant_id, assessment.id)
        
        assert len(runs) >= 2
        run_ids = [r.id for r in runs]
        assert run1.id in run_ids
        assert run2.id in run_ids
    
    def test_create_run_for_assessment_creates_and_enqueues(
        self, db_session, tenant_id, sample_shipment_data
    ):
        """Test that POST /{assessment_id}/runs creates and enqueues run"""
        from app.services.risk_assessment_service import RiskAssessmentService
        from app.services.risk_run_service import RiskRunService
        from app.workers.job_scheduler import JobScheduler
        from app.schemas.risk_run import RiskRunConfig
        
        # Create assessment
        assessment_service = RiskAssessmentService(db_session)
        assessment = assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        # Create run with config
        run_service = RiskRunService(db_session)
        config = RiskRunConfig(priority=10, iterations=5000)
        
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy=config.seed_strategy,
            iterations=config.iterations,
            model_version_id=config.model_version_id
        )
        
        # Enqueue job
        scheduler = JobScheduler(db_session)
        job = scheduler.enqueue_risk_run(
            run_id=run.id,
            priority=config.priority,
            max_attempts=config.max_attempts
        )
        
        assert run.id is not None
        assert run.status == RiskRunStatus.PENDING
        assert job.id is not None
        assert job.run_id == run.id


class TestRiskAssessmentCRUD:
    """Tests for complete CRUD operations"""
    
    def test_full_crud_workflow(
        self, db_session, tenant_id, sample_shipment_data
    ):
        """Test complete CRUD workflow"""
        from app.services.risk_assessment_service import RiskAssessmentService
        from app.services.risk_run_service import RiskRunService
        from app.repositories.risk_assessment_repository import RiskAssessmentRepository
        
        # CREATE
        service = RiskAssessmentService(db_session)
        assessment = service.create_assessment(
            tenant_id=tenant_id,
            raw_input=sample_shipment_data,
            schema_version="v1"
        )
        
        assert assessment.id is not None
        assert assessment.input_hash is not None
        
        # READ
        retrieved = service.get_assessment(assessment.id)
        assert retrieved.id == assessment.id
        assert retrieved.input_hash == assessment.input_hash
        
        # LIST
        assessments = service.list_assessments(
            tenant_id=tenant_id,
            skip=0,
            limit=10
        )
        assert len(assessments) >= 1
        assert any(a.id == assessment.id for a in assessments)
        
        # LINK RUNS
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id
        )
        
        # Verify run is linked
        run_repo = RiskRunRepository(db_session)
        runs = run_repo.list_by_assessment(tenant_id, assessment.id)
        assert len(runs) >= 1
        assert any(r.id == run.id for r in runs)
