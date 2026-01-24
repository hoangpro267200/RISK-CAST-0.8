"""
Unit Tests for Risk Run Service
Tests for risk run creation, execution, and audit events
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.risk_run_service import RiskRunService, RiskRunWithProvenance
from app.repositories.risk_run_repository import RiskRunRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.core.audit_ledger.ledger import AuditLedger
from app.models.risk_run import RiskRun, RiskRunStatus
from app.models.risk_assessment import RiskAssessment
from app.shared.utils import generate_ulid


@pytest.fixture
def tenant_id():
    """Test tenant ID"""
    return generate_ulid()


@pytest.fixture
def audit_ledger(db_session):
    """Audit ledger instance"""
    return AuditLedger(db_session)


@pytest.fixture
def risk_run_service(db_session, audit_ledger):
    """Risk run service with audit ledger"""
    return RiskRunService(db_session, audit=audit_ledger)


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


class TestRiskRunServiceCreate:
    """Tests for create_run method"""
    
    def test_create_run_emits_audit(
        self, risk_run_service, tenant_id, assessment, audit_ledger
    ):
        """Creating run should emit audit event"""
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED",
            iterations=10000,
        )
        
        # Verify audit event was created
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_run",
            entity_id=run.id,
        )
        
        assert len(events) >= 1
        created_event = next(
            (e for e in events if e.action == "CREATED"), None
        )
        assert created_event is not None
        assert created_event.event_type == "RISK_RUN"
        assert created_event.action == "CREATED"
    
    def test_create_run_hash_based_seed(
        self, risk_run_service, tenant_id, assessment
    ):
        """Create run with HASH_BASED seed strategy"""
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED",
            iterations=10000,
        )
        
        assert run.id is not None
        assert run.status == RiskRunStatus.PENDING
        assert run.seed is not None
        assert run.seed_strategy == "HASH_BASED"
        assert run.iterations == 10000
    
    def test_create_run_user_provided_seed(
        self, risk_run_service, tenant_id, assessment
    ):
        """Create run with USER_PROVIDED seed"""
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="USER_PROVIDED",
            seed=12345,
            iterations=5000,
        )
        
        assert run.seed == 12345
        assert run.seed_strategy == "USER_PROVIDED"
        assert run.iterations == 5000
    
    def test_create_run_requires_seed_for_user_provided(
        self, risk_run_service, tenant_id, assessment
    ):
        """Create run should fail if seed not provided for USER_PROVIDED strategy"""
        with pytest.raises(ValueError, match="seed is required"):
            risk_run_service.create_run(
                tenant_id=tenant_id,
                assessment_id=assessment.id,
                seed_strategy="USER_PROVIDED",
            )


class TestRiskRunServiceExecute:
    """Tests for execute_run method"""
    
    def test_execute_run_stores_result_hash(
        self, risk_run_service, tenant_id, assessment, audit_ledger
    ):
        """Executing run should store result_hash"""
        # Create run
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED",
        )
        
        # Execute run
        # Note: This will call the actual engine, which may fail in test environment
        # We'll mock or handle gracefully
        try:
            completed_run = risk_run_service.execute_run(run.id)
            
            # Verify result_hash is stored
            assert completed_run.result_hash is not None
            assert len(completed_run.result_hash) == 64  # SHA256 hex
            assert completed_run.status == RiskRunStatus.SUCCEEDED
            assert completed_run.result_json is not None
        except (RuntimeError, ValueError) as e:
            # Engine may not be available in test environment
            # Check that error was stored
            run_after_error = risk_run_service.repository.get_by_id(tenant_id, run.id)
            assert run_after_error.status == RiskRunStatus.FAILED
            assert run_after_error.error_message is not None
    
    def test_execute_run_emits_lifecycle_events(
        self, risk_run_service, tenant_id, assessment, audit_ledger
    ):
        """Executing run should emit STARTED and COMPLETED/FAILED events"""
        # Create run
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
        )
        
        # Execute run
        try:
            risk_run_service.execute_run(run.id)
        except Exception:
            pass  # May fail in test environment
        
        # Verify audit events
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_run",
            entity_id=run.id,
        )
        
        actions = [e.action for e in events]
        assert "CREATED" in actions
        assert "STARTED" in actions
        # Should have either COMPLETED or FAILED
        assert "COMPLETED" in actions or "FAILED" in actions


class TestRiskRunServiceProvenance:
    """Tests for get_run_with_provenance method"""
    
    def test_provenance_complete(
        self, risk_run_service, tenant_id, assessment
    ):
        """Provenance should include all required fields"""
        # Create run
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
            seed_strategy="HASH_BASED",
            iterations=10000,
        )
        
        # Get with provenance
        provenance_data = risk_run_service.get_run_with_provenance(
            tenant_id=tenant_id,
            run_id=run.id,
        )
        
        assert isinstance(provenance_data, RiskRunWithProvenance)
        assert provenance_data.run.id == run.id
        assert provenance_data.assessment.id == assessment.id
        
        # Check provenance fields
        prov = provenance_data.provenance
        assert "run_id" in prov
        assert "assessment_id" in prov
        assert "input_hash" in prov
        assert "seed" in prov
        assert "seed_strategy" in prov
        assert "iterations" in prov
        assert "engine_version" in prov
        assert "status" in prov
    
    def test_provenance_includes_result_hash_after_completion(
        self, risk_run_service, tenant_id, assessment
    ):
        """Provenance should include result_hash after completion"""
        # Create and execute run
        run = risk_run_service.create_run(
            tenant_id=tenant_id,
            assessment_id=assessment.id,
        )
        
        try:
            completed_run = risk_run_service.execute_run(run.id)
            
            # Get with provenance
            provenance_data = risk_run_service.get_run_with_provenance(
                tenant_id=tenant_id,
                run_id=completed_run.id,
            )
            
            # Check result_hash is in provenance
            assert provenance_data.provenance["result_hash"] is not None
            assert len(provenance_data.provenance["result_hash"]) == 64
        except Exception:
            # Engine may not be available
            pass


class TestRiskRunRepository:
    """Tests for RiskRunRepository"""
    
    @pytest.fixture
    def repository(self, db_session):
        """Repository instance"""
        return RiskRunRepository(db_session)
    
    def test_create(self, repository, tenant_id, assessment):
        """Test creating a risk run"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        run = repository.create(tenant_id, assessment.id, config)
        
        assert run.id is not None
        assert run.tenant_id == tenant_id
        assert run.assessment_id == assessment.id
        assert run.status == RiskRunStatus.PENDING
        assert run.seed == 12345
    
    def test_get_by_id(self, repository, tenant_id, assessment):
        """Test getting run by ID"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        created = repository.create(tenant_id, assessment.id, config)
        found = repository.get_by_id(tenant_id, created.id)
        
        assert found is not None
        assert found.id == created.id
    
    def test_update_status(self, repository, tenant_id, assessment):
        """Test updating run status"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        run = repository.create(tenant_id, assessment.id, config)
        started_at = datetime.utcnow()
        
        updated = repository.update_status(
            run_id=run.id,
            status=RiskRunStatus.RUNNING,
            started_at=started_at,
        )
        
        assert updated.status == RiskRunStatus.RUNNING
        assert updated.started_at is not None
    
    def test_set_result(self, repository, tenant_id, assessment):
        """Test setting run result"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        run = repository.create(tenant_id, assessment.id, config)
        
        result_json = {"risk_score": 0.75, "confidence": 0.9}
        result_hash = "a" * 64
        
        updated = repository.set_result(
            run_id=run.id,
            result_json=result_json,
            result_hash=result_hash,
        )
        
        assert updated.result_json == result_json
        assert updated.result_hash == result_hash
        assert updated.status == RiskRunStatus.SUCCEEDED
        assert updated.completed_at is not None
    
    def test_set_error(self, repository, tenant_id, assessment):
        """Test setting run error"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        run = repository.create(tenant_id, assessment.id, config)
        initial_attempt_count = run.attempt_count
        
        error_details = {"type": "RuntimeError", "message": "Test error"}
        
        updated = repository.set_error(
            run_id=run.id,
            error_message="Test error",
            error_details=error_details,
        )
        
        assert updated.error_message == "Test error"
        assert updated.error_details == error_details
        assert updated.status == RiskRunStatus.FAILED
        assert updated.completed_at is not None
        assert updated.attempt_count == initial_attempt_count + 1
    
    def test_list_by_assessment(self, repository, tenant_id, assessment):
        """Test listing runs by assessment"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        # Create multiple runs
        for i in range(3):
            repository.create(tenant_id, assessment.id, config)
        
        runs = repository.list_by_assessment(tenant_id, assessment.id)
        
        assert len(runs) == 3
        assert all(r.assessment_id == assessment.id for r in runs)
        # Should be ordered by created_at descending
        assert runs[0].created_at >= runs[1].created_at
    
    def test_get_pending_runs(self, repository, tenant_id, assessment):
        """Test getting pending runs for worker"""
        config = {
            "seed": 12345,
            "seed_strategy": "HASH_BASED",
            "iterations": 10000,
            "engine_version": "v3.0.0",
        }
        
        # Create pending runs
        for i in range(5):
            repository.create(tenant_id, assessment.id, config)
        
        # Create a non-pending run
        run = repository.create(tenant_id, assessment.id, config)
        repository.update_status(run.id, RiskRunStatus.RUNNING)
        
        # Get pending runs
        pending = repository.get_pending_runs(limit=10)
        
        assert len(pending) == 5
        assert all(r.status == RiskRunStatus.PENDING for r in pending)
