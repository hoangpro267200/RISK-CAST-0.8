# Evidence Chain of Custody Complete

**Date:** January 2026  
**Status:** Implementation complete  
**Feature:** Complete chain of custody system for evidence bundles with hash-chained events, cryptographic sealing, and tamper detection

---

## Summary

Implemented a **Chain of Custody** system for evidence bundles that provides:
- Evidence collection with full provenance
- Secure storage with integrity verification
- Hash-chained custody events (immutable audit trail)
- Cryptographic sealing with manifest hash and HMAC signature
- Tamper detection on verification
- Complete access logging
- Full custody history export

---

## What Was Implemented

### 1. `app/evidence/chain_of_custody.py`

- **`CustodyEventModel`**  
  - Table `evidence_custody_events`.  
  - Fields: `id`, `bundle_id`, `item_id`, `event_type`, `timestamp`, `actor_type`, `actor_id`, `description`, `metadata_json`, `sequence_number`, `prev_event_hash`, `event_hash`.  
  - Hash-chained: each event links to previous via `prev_event_hash`; `event_hash` computed from event data + `prev_event_hash`.  
  - Indexes: `bundle_id`, `item_id`, `(bundle_id, sequence_number)`.

- **`ChainOfCustodyService`**
  - **`create_bundle(...)`**  
    - Creates `EvidenceBundle` (uses existing model).  
    - Records `COLLECTED` custody event (genesis hash for first event).  
    - Audits via `ImmutableAuditLedger`.
  - **`add_evidence(...)`**  
    - Computes content hash (SHA-256).  
    - Uploads via `EvidenceStorage` (sync).  
    - Creates `EvidenceObject` and `EvidenceBundleItem` (existing models).  
    - Updates bundle stats (`item_count`, `total_size_bytes`).  
    - Records `UPLOADED` custody event (hash-chained).  
    - Audits via immutable ledger.
  - **`seal_bundle(bundle_id, sealed_by_user_id)`**  
    - Verifies all items' integrity (downloads and rehashes).  
    - Computes manifest hash (SHA-256 of all item hashes joined by `|`).  
    - Signs manifest with HMAC (using `AUDIT_SIGNING_KEY`).  
    - Sets bundle status to `SEALED`, stores `manifest_hash`, `sealed_at`, `sealed_by_user_id`.  
    - Records `SEALED` custody event.  
    - Returns `SealedBundle` with manifest hash, signature, verification hash.
  - **`verify_bundle(bundle_id)`**  
    - Checks item count matches.  
    - Verifies each item's content hash (downloads and rehashes).  
    - Verifies manifest hash (if sealed).  
    - Verifies custody chain (all `prev_event_hash` links correct).  
    - Returns `{ bundle_id, verified_at, is_sealed, checks: { item_count, item_integrity, manifest_hash, custody_chain }, is_valid }`.  
    - Audits verification result.
  - **`record_access(bundle_id, accessed_by_user_id, access_reason, items_accessed?)`**  
    - Records `ACCESSED` custody event.  
    - Audits access.
  - **`get_custody_history(bundle_id)`**  
    - Returns all custody events for bundle, ordered by `sequence_number`.  
    - Includes sequence, event_type, timestamp, actor, description, metadata, event_hash.

- **Helpers**  
  - `_record_custody_event`: records hash-chained event (gets last event's hash, increments sequence).  
  - `_verify_item_integrity`: downloads content, rehashes, compares with stored hash.  
  - `_verify_custody_chain`: verifies all `prev_event_hash` links (genesis hash for first event).

- **Enums**  
  - `EvidenceStatus`: COLLECTED, VERIFIED, SEALED, ACCESSED, DISPUTED, ARCHIVED.  
  - `EvidenceType`: WEATHER_DATA, PORT_DATA, VESSEL_TRACKING, ORACLE_DATA, SENSOR_DATA, DOCUMENT, PHOTO, VIDEO, COMMUNICATION, THIRD_PARTY_REPORT.  
  - `CustodyEventType`: COLLECTED, UPLOADED, VERIFIED, ACCESSED, DOWNLOADED, SEALED, DISPUTED, RESOLVED, ARCHIVED.

- **Factory**  
  - `create_chain_of_custody_service(db, audit, storage, signing_key?)`.

### 2. Integration

- **Existing Models**  
  - Uses `EvidenceBundle`, `EvidenceBundleItem`, `EvidenceObject` from `app.models`.  
  - Works with existing bundle/item structure (no schema changes to existing tables).

- **Storage**  
  - Uses `EvidenceStorage` from `app.core.evidence.storage` (sync methods: `upload`, `download`).  
  - Supports `LocalEvidenceStorage` and `S3EvidenceStorage`.

- **Audit**  
  - Uses `ImmutableAuditLedger` for all custody operations.  
  - Events: `BUNDLE_CREATED`, `EVIDENCE_ADDED`, `BUNDLE_SEALED`, `BUNDLE_VERIFIED`, `BUNDLE_ACCESSED`.

- **Signing**  
  - Uses `AUDIT_SIGNING_KEY` from config (falls back to `SECRET_KEY`).

### 3. Migration `039_create_evidence_custody_events`

- Creates `evidence_custody_events` table.  
- Foreign keys to `evidence_bundles` and `evidence_objects` (CASCADE delete).  
- Indexes: `bundle_id`, `item_id`, `(bundle_id, sequence_number)`.  
- Downgrade drops table and indexes.

### 4. Exports

- **`app.evidence`** exports: `ChainOfCustodyService`, `CustodyEventModel`, `EvidenceStatus`, `EvidenceType`, `CustodyEventType`, `SealedBundle`, `create_chain_of_custody_service`.

---

## Acceptance Criteria

- [x] Evidence collection with provenance (who/when/how).
- [x] Secure storage with integrity verification (content hash verification).
- [x] Custody events hash-chained (each links to previous, genesis hash for first).
- [x] Cryptographic sealing (manifest hash + HMAC signature).
- [x] Manifest hash locks all content (hash of all item hashes).
- [x] Tamper detection on verify (content hash mismatch, manifest mismatch, chain break).
- [x] Access logging (record_access records ACCESSED events).
- [x] Complete custody history export (get_custody_history returns all events).

---

## Usage

```python
from app.evidence import create_chain_of_custody_service
from app.core.audit import create_immutable_audit_ledger
from app.core.evidence.storage import LocalEvidenceStorage
from app.database import SessionLocal

db = SessionLocal()
audit = create_immutable_audit_ledger(db)
storage = LocalEvidenceStorage()
custody = create_chain_of_custody_service(db, audit, storage)

# Create bundle
bundle = custody.create_bundle(
    name="Claim Evidence",
    description="Evidence for claim CLM-123",
    bundle_type="CLAIM",
    tenant_id="tenant-ulid",
    created_by_user_id="user-ulid",
)

# Add evidence
evidence = custody.add_evidence(
    bundle_id=bundle.id,
    evidence_type=EvidenceType.WEATHER_DATA,
    name="weather_snapshot.json",
    content=b'{"temp": 25.5, "wind": 15.2}',
    content_type="application/json",
    source="Tomorrow.io API",
    tenant_id=bundle.tenant_id,
)

# Seal bundle
sealed = custody.seal_bundle(bundle.id, "user-ulid")
# sealed.manifest_hash, sealed.manifest_signature, sealed.verification_hash

# Verify bundle
verification = custody.verify_bundle(bundle.id)
assert verification["is_valid"]

# Get custody history
history = custody.get_custody_history(bundle.id)
# history[0].sequence, .event_type, .timestamp, .actor_type, .event_hash, ...
```

---

## Files Touched

- **Added:** `app/evidence/__init__.py`, `app/evidence/chain_of_custody.py`
- **Added:** `migrations/versions/039_create_evidence_custody_events.py`
- **Added:** `EVIDENCE_CHAIN_OF_CUSTODY_COMPLETE.md`

---

## Notes

- **Existing Models**  
  - Works with existing `EvidenceBundle`, `EvidenceBundleItem`, `EvidenceObject` models.  
  - No changes to existing evidence tables; adds `evidence_custody_events` only.

- **Storage**  
  - `EvidenceStorage` uses sync methods (`upload`, `download`).  
  - Service methods are sync (no async/await).

- **Hash Chain**  
  - Custody events are hash-chained per bundle (separate chains per bundle).  
  - Genesis hash (`"0" * 64`) for first event in each bundle's chain.

- **Manifest Hash**  
  - Computed as SHA-256 of all item hashes joined by `|` (ordered by `added_at`).  
  - Stored in `EvidenceBundle.manifest_hash` (existing field).

- **Signing Key**  
  - Uses `AUDIT_SIGNING_KEY` from config (same as immutable audit ledger).  
  - Set in production; do not use default.

- **Verification**  
  - `verify_bundle` downloads all content and rehashes (may be slow for large bundles).  
  - Consider caching verification results or running verification asynchronously for large bundles.
