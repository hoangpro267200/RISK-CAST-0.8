# Audit Trail Viewer API - Complete

**Date:** January 2026  
**Status:** Implementation complete  
**Feature:** Audit trail viewer API for compliance with search, export, verification, and statistics

---

## Summary

Created a **comprehensive audit trail viewer API** using `ImmutableAuditLedger` for compliance and regulatory reporting. Provides search, filtering, export, chain verification, and statistics.

---

## What Was Implemented

### 1. **`app/api/deps/__init__.py`**

- **`get_audit(db: Session)`** dependency  
  - Returns `ImmutableAuditLedger` instance  
  - Uses `create_immutable_audit_ledger(db)` factory

### 2. **`app/api/v3/audit.py`** (prefix `/audit`)

**Schemas:**
- **`AuditEventSummary`** – Summary fields (id, sequence, type, action, entity, actor, timestamp, hash)
- **`AuditEventDetail`** – Full event (includes payload, server_timestamp, prev_hash, hmac_signature, source_ip, user_agent, request_id)
- **`AuditSearchResponse`** – Paginated search results (total_count, page, page_size, events)
- **`ChainVerificationResponse`** – Verification result (is_valid, events_checked, first/last sequence, broken_at, error_message, verification_hash, verified_at)
- **`AuditExportRequest`** – Export request (start_date, end_date, event_types?, include_verification)
- **`AuditStatistics`** – Statistics (total, today/week/month counts, by_event_type, by_actor_type, chain_status, last_event_timestamp)

**Endpoints:**

- **GET /audit/events**  
  - Search with filters: `event_type`, `action`, `entity_type`, `entity_id`, `actor_type`, `actor_id`, `start_date`, `end_date`  
  - Pagination: `page`, `page_size` (1-200)  
  - Tenant-scoped (filters by `tenant_id` from context)  
  - Returns `AuditSearchResponse` with paginated events

- **GET /audit/events/{event_id}**  
  - Get full event details  
  - Returns `AuditEventDetail`  
  - 404 if not found or tenant mismatch

- **GET /audit/events/by-entity/{entity_type}/{entity_id}**  
  - All events for an entity  
  - Uses `audit.get_events_for_entity(entity_type, entity_id, tenant_id)`  
  - Returns entity info and event list

- **GET /audit/events/by-actor/{actor_type}/{actor_id}**  
  - All events by an actor (user activity reports)  
  - Optional `start_date`, `end_date`, `limit` (max 1000)  
  - Uses `audit.get_events_by_actor(actor_type, actor_id, start_time, end_time)`  
  - Tenant-filtered if context has tenant_id

- **POST /audit/verify-chain**  
  - Verify hash chain integrity  
  - Optional `start_sequence`, `end_sequence`  
  - Uses `audit.verify_chain(start_sequence, end_sequence)`  
  - Returns `ChainVerificationResponse` with verification status

- **POST /audit/export**  
  - Export for compliance/regulatory review  
  - Body: `AuditExportRequest` (start_date, end_date, event_types?, include_verification)  
  - Uses `audit.export_for_compliance(start_date, end_date, tenant_id, event_types)`  
  - Returns JSON with events and verification proof

- **GET /audit/statistics**  
  - Audit trail statistics  
  - Counts: total, today, this week, this month  
  - Grouped by event_type and actor_type  
  - Chain status check (last 10 events)  
  - Returns `AuditStatistics`

- **GET /audit/event-types**  
  - List all event types with descriptions  
  - Returns `{ event_types: [...], descriptions: {...} }`  
  - Includes all `EventType` enum values

**Helper:**
- **`_to_summary(event: AuditEventImmutable)`** – Converts to `AuditEventSummary`

**Authentication & Authorization:**
- Uses `PermissionChecker("audit:read")` for all endpoints  
- Uses `resolve_tenant_context` for tenant-scoped filtering  
- All queries filter by `tenant_id` when context provides it

---

## Acceptance Criteria

- [x] Search events with multiple filters – GET /audit/events with 8 filter params
- [x] Get event details – GET /audit/events/{event_id}
- [x] Get events by entity – GET /audit/events/by-entity/{entity_type}/{entity_id}
- [x] Get events by actor – GET /audit/events/by-actor/{actor_type}/{actor_id}
- [x] Verify chain integrity – POST /audit/verify-chain
- [x] Export for compliance – POST /audit/export
- [x] Get statistics – GET /audit/statistics
- [x] List event types with descriptions – GET /audit/event-types

---

## Usage

**Search events:**
```bash
GET /api/v3/audit/events?event_type=MODEL_VERSION&action=PUBLISHED&page=1&page_size=50
```

**Get event detail:**
```bash
GET /api/v3/audit/events/{event_id}
```

**Get events for entity:**
```bash
GET /api/v3/audit/events/by-entity/model_version/01H...
```

**Get events by actor:**
```bash
GET /api/v3/audit/events/by-actor/USER/01H...?start_date=2026-01-01T00:00:00Z&limit=100
```

**Verify chain:**
```bash
POST /api/v3/audit/verify-chain?start_sequence=1&end_sequence=1000
```

**Export:**
```bash
POST /api/v3/audit/export
Content-Type: application/json
{
  "start_date": "2026-01-01T00:00:00Z",
  "end_date": "2026-01-31T23:59:59Z",
  "event_types": ["MODEL_VERSION", "POLICY"],
  "include_verification": true
}
```

**Statistics:**
```bash
GET /api/v3/audit/statistics
```

**Event types:**
```bash
GET /api/v3/audit/event-types
```

---

## Notes

- **Tenant isolation:** All queries filter by `tenant_id` from `TenantContext` when available
- **Immutable ledger:** Uses `ImmutableAuditLedger` (hash-chained, tamper-evident)
- **Chain verification:** Verifies hash chain integrity (prev_hash links, event hash computation, HMAC signatures)
- **Export format:** Returns JSON with events and verification proof (export_id, date_range, event_count, events array, verification object)
- **Statistics:** Includes chain status check (verifies last 10 events for quick health check)
- **Pagination:** Search endpoint supports page/page_size (max 200 per page)
- **Filtering:** Multiple filters can be combined (event_type, action, entity, actor, date range)

The audit API is mounted at `/api/v3/audit` and requires `audit:read` permission.
