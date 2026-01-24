"""
Example Usage of Audit Ledger Service

This file demonstrates how to use the audit logging service.
"""
from sqlalchemy.orm import Session
from app.modules.audit_ledger.service import AuditLedgerService
from app.modules.audit_ledger.schemas import AuditContext, AuditEventQuery
from app.modules.audit_ledger.models import ActorType
import asyncio


async def example_log_event(db: Session):
    """Example: Log an audit event"""
    service = AuditLedgerService(db)
    
    context = AuditContext(
        request_id="req_001",
        trace_id="trace_001",
        ip="192.168.1.1",
        user_agent="Mozilla/5.0",
        route="/api/v3/risk-assessments",
        method="POST"
    )
    
    event = await service.log_event(
        tenant_id="tenant_123",
        actor_type=ActorType.USER,
        actor_id="user_456",
        action="risk_assessment.created",
        resource_type="risk_assessment",
        resource_id="assessment_789",
        context=context,
        diff={"status": "created", "risk_score": 75.5}
    )
    
    print(f"Logged event: {event.id} - {event.action}")
    print(f"Event hash: {event.event_hash}")
    return event


async def example_query_events(db: Session, tenant_id: str):
    """Example: Query audit events"""
    service = AuditLedgerService(db)
    
    filters = AuditEventQuery(
        action="risk_assessment.created",
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        limit=50
    )
    
    events = await service.query_events(tenant_id, filters)
    print(f"Found {len(events)} events")
    return events


async def example_verify_chain(db: Session, tenant_id: str):
    """Example: Verify chain integrity"""
    service = AuditLedgerService(db)
    
    result = await service.verify_chain(tenant_id)
    print(f"Chain valid: {result.is_valid}")
    print(f"Total events: {result.total_events}")
    print(f"Message: {result.message}")
    
    if result.invalid_links:
        print(f"Invalid links: {len(result.invalid_links)}")
        for link in result.invalid_links:
            print(f"  - Event {link['event_id']}: {link.get('issue', 'prev_hash_mismatch')}")
    
    return result


if __name__ == "__main__":
    from app.database import SessionLocal
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # Example usage
        # event = asyncio.run(example_log_event(db))
        pass
    finally:
        db.close()
