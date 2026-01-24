"""
Integration Tests for Audit Ledger Integration
Tests audit events emitted by risk assessment and run services
"""
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.risk_assessment_service import RiskAssessmentService
from app.core.audit_ledger.ledger import AuditLedger
from app.models.audit import AuditEvent
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
def risk_assessment_service(db_session, audit_ledger):
    """Risk assessment service with audit ledger"""
    return RiskAssessmentService(db_session, audit=audit_ledger)


class TestRiskAssessmentAudit:
    """Tests for risk assessment audit events"""
    
    def test_create_assessment_emits_audit_event(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Creating assessment should emit audit event"""
        raw_input = {
            "cargo_value": 100000,
            "distance": 5000,
            "cargo_type": "standard",
        }
        
        # Create assessment
        assessment = risk_assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input,
        )
        
        # Verify audit event was created
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_assessment",
            entity_id=assessment.id,
        )
        
        assert len(events) == 1
        event = events[0]
        assert event.event_type == "RISK_ASSESSMENT"
        assert event.action == "CREATED"
        assert event.entity_type == "risk_assessment"
        assert event.entity_id == assessment.id
        assert event.tenant_id == tenant_id
    
    def test_audit_event_has_correct_payload(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Audit event should have correct payload"""
        raw_input = {
            "cargo_value": 100000,
            "distance": 5000,
        }
        
        assessment = risk_assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input,
            created_by_user_id="user-123",
        )
        
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_assessment",
            entity_id=assessment.id,
        )
        
        event = events[0]
        assert event.payload_json is not None
        assert "input_hash" in event.payload_json
        assert "schema_version" in event.payload_json
        assert event.payload_json["input_hash"] == assessment.input_hash
        assert event.payload_json["schema_version"] == assessment.schema_version
        assert event.actor_id == "user-123"
        assert event.actor_type == "USER"
    
    def test_duplicate_assessment_does_not_emit_new_event(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Creating duplicate assessment should not emit new audit event"""
        raw_input = {
            "cargo_value": 100000,
            "distance": 5000,
        }
        
        # Create first assessment
        assessment1 = risk_assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input,
        )
        
        # Create duplicate (should return existing)
        assessment2 = risk_assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input=raw_input,
        )
        
        # Should be same assessment
        assert assessment1.id == assessment2.id
        
        # Should have only one audit event
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_assessment",
            entity_id=assessment1.id,
        )
        
        assert len(events) == 1
    
    def test_chain_integrity_maintained(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Audit chain integrity should be maintained after assessment creation"""
        # Create multiple assessments
        for i in range(3):
            risk_assessment_service.create_assessment(
                tenant_id=tenant_id,
                raw_input={"cargo_value": 100000 + i, "distance": 5000},
            )
        
        # Verify chain integrity
        result = audit_ledger.verify_chain(tenant_id)
        
        assert result.is_valid is True
        assert result.total_events == 3
        assert result.verified_events == 3
        assert len(result.errors) == 0


class TestRiskRunAudit:
    """Tests for risk run audit events"""
    
    @pytest.fixture
    def risk_run_service(self, db_session, audit_ledger):
        """Risk run service with audit ledger"""
        from app.modules.risk_runs.service import RiskRunService
        from app.database import TenantScopedSession
        
        # Create tenant-scoped session
        tenant_id = generate_ulid()
        tenant_scoped_db = TenantScopedSession(db_session, tenant_id)
        
        return RiskRunService(tenant_scoped_db, audit=audit_ledger), tenant_id
    
    @pytest.mark.asyncio
    async def test_create_run_emits_audit_event(
        self, risk_run_service, db_session, audit_ledger
    ):
        """Creating risk run should emit audit event"""
        service, tenant_id = risk_run_service
        
        # Create assessment first
        from app.services.risk_assessment_service import RiskAssessmentService
        assessment_service = RiskAssessmentService(db_session, audit=audit_ledger)
        assessment = assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input={"cargo_value": 100000, "distance": 5000},
        )
        
        # Create run
        from app.modules.audit_ledger.schemas import AuditContext
        context = AuditContext()
        
        run = await service.create_run(
            assessment_id=assessment.id,
            user_id="user-123",
            context=context,
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
        assert created_event.entity_type == "risk_run"
        assert created_event.entity_id == run.id
    
    @pytest.mark.asyncio
    async def test_run_lifecycle_events(
        self, risk_run_service, db_session, audit_ledger
    ):
        """Run lifecycle should emit STARTED, COMPLETED, and FAILED events"""
        service, tenant_id = risk_run_service
        
        # Create assessment
        from app.services.risk_assessment_service import RiskAssessmentService
        assessment_service = RiskAssessmentService(db_session, audit=audit_ledger)
        assessment = assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input={"cargo_value": 100000, "distance": 5000},
        )
        
        # Create run
        from app.modules.audit_ledger.schemas import AuditContext
        context = AuditContext()
        
        run = await service.create_run(
            assessment_id=assessment.id,
            user_id="user-123",
            context=context,
        )
        
        # Start run
        await service.update_run_started(run.id)
        
        # Complete run
        from app.modules.risk_engine_v3.schemas import RiskEngineResultV3
        result = RiskEngineResultV3(
            risk_score=0.5,
            confidence=0.9,
            scenarios=[],
            drivers={},
        )
        await service.update_run_completed(run.id, result, "result-hash-123")
        
        # Verify all events
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_run",
            entity_id=run.id,
        )
        
        actions = [e.action for e in events]
        assert "CREATED" in actions
        assert "STARTED" in actions
        assert "COMPLETED" in actions
    
    @pytest.mark.asyncio
    async def test_run_failed_emits_event(
        self, risk_run_service, db_session, audit_ledger
    ):
        """Run failure should emit FAILED audit event"""
        service, tenant_id = risk_run_service
        
        # Create assessment
        from app.services.risk_assessment_service import RiskAssessmentService
        assessment_service = RiskAssessmentService(db_session, audit=audit_ledger)
        assessment = assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input={"cargo_value": 100000, "distance": 5000},
        )
        
        # Create and start run
        from app.modules.audit_ledger.schemas import AuditContext
        context = AuditContext()
        
        run = await service.create_run(
            assessment_id=assessment.id,
            user_id="user-123",
            context=context,
        )
        await service.update_run_started(run.id)
        
        # Fail run
        error = ValueError("Test error")
        await service.update_run_failed(run.id, error)
        
        # Verify FAILED event
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_run",
            entity_id=run.id,
        )
        
        failed_event = next(
            (e for e in events if e.action == "FAILED"), None
        )
        assert failed_event is not None
        assert failed_event.payload_json is not None
        assert "error_type" in failed_event.payload_json
        assert "error_message" in failed_event.payload_json


class TestAuditEventQuerying:
    """Tests for querying audit events by entity"""
    
    def test_query_events_by_entity_type(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Should be able to query events by entity_type"""
        # Create assessments
        for i in range(3):
            risk_assessment_service.create_assessment(
                tenant_id=tenant_id,
                raw_input={"cargo_value": 100000 + i},
            )
        
        # Query by entity_type
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_type="risk_assessment",
        )
        
        assert len(events) == 3
        assert all(e.entity_type == "risk_assessment" for e in events)
    
    def test_query_events_by_entity_id(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Should be able to query events by entity_id"""
        assessment = risk_assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input={"cargo_value": 100000},
        )
        
        # Query by entity_id
        events = audit_ledger.get_events(
            tenant_id=tenant_id,
            entity_id=assessment.id,
        )
        
        assert len(events) >= 1
        assert all(e.entity_id == assessment.id for e in events)
    
    def test_query_events_by_date_range(
        self, risk_assessment_service, tenant_id, audit_ledger
    ):
        """Should be able to query events by date range"""
        # Create assessment
        assessment = risk_assessment_service.create_assessment(
            tenant_id=tenant_id,
            raw_input={"cargo_value": 100000},
        )
        
        # Get event timestamp
        events = audit_ledger.get_events(tenant_id=tenant_id)
        event_time = events[0].created_at
        
        # Query by date range
        from_date = event_time.replace(second=0, microsecond=0)
        to_date = event_time.replace(second=59, microsecond=999999)
        
        filtered_events = audit_ledger.get_events(
            tenant_id=tenant_id,
            from_date=from_date,
            to_date=to_date,
        )
        
        assert len(filtered_events) >= 1
        assert all(from_date <= e.created_at <= to_date for e in filtered_events)
