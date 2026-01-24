# Audit Ledger Module

Append-only, hash-chained audit trail for immutable event logging.

## Design Principles

1. **Append-Only**: No UPDATE or DELETE operations allowed at application level
2. **Hash-Chained**: Each event links to previous event via hash for integrity
3. **Immutable**: Once written, events cannot be modified
4. **Tenant-Scoped**: Events can be tenant-specific or platform-level

## Models

### AuditEvent

Immutable audit log entry with hash chaining.

**Fields:**
- `id`: ULID (26 chars) - Primary key
- `tenant_id`: FK to tenants (nullable for platform events)
- `occurred_at`: DateTime - When event occurred
- `actor_type`: Enum('USER', 'API_KEY', 'SYSTEM')
- `actor_id`: VARCHAR(100) - Actor identifier
- `action`: VARCHAR(100) - Action performed (e.g., 'risk_assessment.created')
- `resource_type`: VARCHAR(100) - Type of resource (e.g., 'risk_assessment')
- `resource_id`: VARCHAR(100) - Resource identifier
- `context_json`: JSON - Context (request_id, trace_id, ip, user_agent, route, method)
- `diff_json`: JSON - State changes (optional)
- `prev_hash`: CHAR(64) - Previous event hash (NULL for first event)
- `event_hash`: CHAR(64) - SHA-256 hash of this event

**Indexes:**
- `(tenant_id, occurred_at)` - Time-based queries
- `(tenant_id, resource_type, resource_id)` - Resource queries
- `(tenant_id, action, occurred_at)` - Action queries
- `(actor_type, actor_id, occurred_at)` - Actor queries

### AuditChainHead

Tracks the last event hash for each tenant to maintain chain integrity.

**Fields:**
- `tenant_id`: FK to tenants (PK, nullable for platform-level)
- `last_event_hash`: CHAR(64) - Last event hash in chain
- `updated_at`: DateTime - Last update timestamp

## Usage

### Create Audit Event

```python
from app.modules.audit_ledger.utils import create_audit_event_data
from app.modules.audit_ledger.models import AuditEvent
from app.modules.audit_ledger.models import ActorType

# Get previous hash from chain head
prev_hash = get_chain_head(tenant_id)

# Create event data
event_data = create_audit_event_data(
    tenant_id="tenant_123",
    actor_type=ActorType.USER,
    actor_id="user_456",
    action="risk_assessment.created",
    resource_type="risk_assessment",
    resource_id="assessment_789",
    context_json={
        "request_id": "req_001",
        "ip": "192.168.1.1",
        "user_agent": "Mozilla/5.0",
        "route": "/api/v3/risk-assessments",
        "method": "POST"
    },
    diff_json={"status": "created"},
    prev_hash=prev_hash
)

# Insert event (append-only)
event = AuditEvent(**event_data)
db.add(event)
db.commit()

# Update chain head
update_chain_head(tenant_id, event.event_hash)
```

### Verify Chain Integrity

```python
from app.modules.audit_ledger.utils import verify_chain_integrity

# Get events for a tenant
events = db.query(AuditEvent).filter(
    AuditEvent.tenant_id == tenant_id
).order_by(AuditEvent.occurred_at).all()

# Verify chain
is_valid = verify_chain_integrity(events)
```

### Query Events

```python
# Get events by tenant and time range
events = db.query(AuditEvent).filter(
    AuditEvent.tenant_id == tenant_id,
    AuditEvent.occurred_at >= start_date,
    AuditEvent.occurred_at <= end_date
).order_by(AuditEvent.occurred_at).all()

# Get events by resource
events = db.query(AuditEvent).filter(
    AuditEvent.tenant_id == tenant_id,
    AuditEvent.resource_type == "risk_assessment",
    AuditEvent.resource_id == assessment_id
).order_by(AuditEvent.occurred_at).all()

# Get events by action
events = db.query(AuditEvent).filter(
    AuditEvent.tenant_id == tenant_id,
    AuditEvent.action == "risk_assessment.created"
).order_by(AuditEvent.occurred_at).all()

# Get events by actor
events = db.query(AuditEvent).filter(
    AuditEvent.actor_type == ActorType.USER,
    AuditEvent.actor_id == user_id
).order_by(AuditEvent.occurred_at).all()
```

## Hash Calculation

The event hash is calculated from:
- tenant_id
- occurred_at
- actor_type
- actor_id
- action
- resource_type
- resource_id
- context_json
- diff_json
- prev_hash

This ensures:
1. Event integrity (any change invalidates hash)
2. Chain integrity (prev_hash links to previous event)
3. Immutability (cannot modify without breaking chain)

## Security Considerations

1. **Append-Only**: Database-level constraints should prevent UPDATE/DELETE
2. **Hash Verification**: Regularly verify chain integrity
3. **Access Control**: Limit who can read audit logs
4. **Retention**: Implement retention policies for compliance

## Migration

Migration file: `migrations/versions/002_create_audit_ledger_models.py`

To apply:
```bash
alembic upgrade head
```

## Best Practices

1. **Always use utilities**: Use `create_audit_event_data()` to ensure correct hash calculation
2. **Update chain head**: Always update chain head after inserting event
3. **Verify periodically**: Run chain integrity checks regularly
4. **Index queries**: Use indexed fields for efficient queries
5. **Batch inserts**: For high-volume, consider batching with transaction
