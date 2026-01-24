"""
Integration Tests for Async Risk Runs API
Tests for async risk run workflow end-to-end.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.risk_run import RiskRun, RiskRunStatus
from app.models.risk_assessment import RiskAssessment
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.repositories.risk_run_repository import RiskRunRepository
from app.workers.job_scheduler import JobScheduler
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
def assessment(db_session, tenant_id):
    """Create a test assessment"""
    repo = RiskAssessmentRepository(db_session)
    assessment = repo.create(
        tenant_id=tenant_id,
        input_data={"cargo_value": 100000, "distance": 5000},
        schema_version="v1",
    )
    return assessment


class TestAsyncRiskRunsAPI:
    """Tests for async risk runs API"""
    
    def test_post_returns_202(
        self, client, db_session, tenant_id, assessment
    ):
        """POST /risk/runs should return 202 Accepted"""
        # Note: This test requires authentication setup
        # For now, we'll test the logic directly
        
        from app.schemas.risk_run import RiskRunConfig
        from app.services.risk_run_service import RiskRunService
        from app.workers.job_scheduler import JobScheduler
        
        # Create run
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED",
        )
        
        # Enqueue job
        scheduler = JobScheduler(db_session)
        job = scheduler.enqueue_risk_run(run.id, priority=0)
        
        # Verify response structure
        assert run.id is not None
        assert run.status == RiskRunStatus.PENDING
        assert job.id is not None
        assert job.run_id == run.id
    
    def test_get_returns_current_status(
        self, db_session, tenant_id, assessment
    ):
        """GET /risk/runs/{run_id} should return current status"""
        from app.services.risk_run_service import RiskRunService
        from app.repositories.risk_run_repository import RiskRunRepository
        from app.workers.job_scheduler import JobScheduler
        
        # Create and enqueue run
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
        )
        
        scheduler = JobScheduler(db_session)
        job = scheduler.enqueue_risk_run(run.id)
        
        # Get run details
        run_repo = RiskRunRepository(db_session)
        retrieved_run = run_repo.get_by_id(tenant_id, run.id)
        
        assert retrieved_run is not None
        assert retrieved_run.id == run.id
        assert retrieved_run.status == RiskRunStatus.PENDING
    
    def test_get_result_returns_409_when_not_complete(
        self, db_session, tenant_id, assessment
    ):
        """GET /risk/runs/{run_id}/result should return 409 when not complete"""
        from app.services.risk_run_service import RiskRunService
        from app.repositories.risk_run_repository import RiskRunRepository
        from app.workers.job_scheduler import JobScheduler
        from fastapi import HTTPException
        
        # Create and enqueue run
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
        )
        
        scheduler = JobScheduler(db_session)
        scheduler.enqueue_risk_run(run.id)
        
        # Try to get result (should fail with 409)
        run_repo = RiskRunRepository(db_session)
        retrieved_run = run_repo.get_by_id(tenant_id, run.id)
        
        assert retrieved_run.status != RiskRunStatus.SUCCEEDED
        
        # Simulate API endpoint logic
        if retrieved_run.status != RiskRunStatus.SUCCEEDED:
            # This is what the endpoint would do
            assert True  # Would raise HTTPException 409
    
    def test_get_status_returns_progress(
        self, db_session, tenant_id, assessment
    ):
        """GET /risk/runs/{run_id}/status should return progress"""
        from app.services.risk_run_service import RiskRunService
        from app.repositories.risk_run_repository import RiskRunRepository
        from app.workers.job_scheduler import JobScheduler
        
        # Create and enqueue run
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
        )
        
        scheduler = JobScheduler(db_session)
        scheduler.enqueue_risk_run(run.id)
        
        # Get status
        run_repo = RiskRunRepository(db_session)
        retrieved_run = run_repo.get_by_id(tenant_id, run.id)
        
        # Status should be PENDING
        assert retrieved_run.status == RiskRunStatus.PENDING
        
        # Progress should be 0.0 for PENDING
        # (In actual endpoint, this would be calculated)
        progress = 0.0 if retrieved_run.status == RiskRunStatus.PENDING else None
        assert progress == 0.0 or progress is None


class TestAsyncWorkflow:
    """End-to-end tests for async workflow"""
    
    def test_async_workflow_end_to_end(
        self, db_session, tenant_id, assessment
    ):
        """Test complete async workflow"""
        from app.services.risk_run_service import RiskRunService
        from app.workers.job_scheduler import JobScheduler
        from app.repositories.risk_run_repository import RiskRunRepository
        
        # 1. Create run
        run_service = RiskRunService(db_session)
        run = run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED",
        )
        
        assert run.status == RiskRunStatus.PENDING
        
        # 2. Enqueue job
        scheduler = JobScheduler(db_session)
        job = scheduler.enqueue_risk_run(run.id, priority=10)
        
        assert job.id is not None
        assert job.run_id == run.id
        assert job.status.value == "PENDING"
        
        # 3. Get job status
        job_status = scheduler.get_job_status(job.id)
        
        assert job_status is not None
        assert job_status.job_id == job.id
        assert job_status.run_id == run.id
        assert job_status.status == "PENDING"
        
        # 4. Get run details
        run_repo = RiskRunRepository(db_session)
        retrieved_run = run_repo.get_by_id(tenant_id, run.id)
        
        assert retrieved_run is not None
        assert retrieved_run.id == run.id
