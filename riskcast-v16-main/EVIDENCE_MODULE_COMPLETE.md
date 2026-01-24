# ✅ Evidence Module - Hoàn Thành

## Đã Tạo Thành Công

### 1. Models (`app/modules/evidence/models.py`)

#### EvidenceObject Model

**Purpose:** Represents a piece of evidence (document, image, sensor data, etc.)

**Key Features:**
- ✅ Tenant-scoped (inherits TenantScopedMixin)
- ✅ Content hash for integrity verification
- ✅ Storage URI for file location
- ✅ Retention class for compliance
- ✅ PII flags for privacy compliance
- ✅ Metadata storage

**Fields:**
- `id` - ULID (String(26))
- `tenant_id` - Tenant ID (from TenantScopedMixin)
- `type` - EvidenceType enum (DOCUMENT, WEATHER_SNAPSHOT, SENSOR_SEGMENT, PORT_EVENT, IMAGE, VIDEO)
- `source` - Source identifier (UPLOAD, NOAA, CARRIER_API, etc.)
- `storage_uri` - URI to storage location
- `content_hash` - SHA256 hash of content
- `mime_type` - MIME type
- `size_bytes` - File size in bytes
- `captured_at` - When evidence was generated/captured
- `ingested_at` - When ingested into system
- `retention_class` - RetentionClass enum (STANDARD, REGULATORY, LEGAL_HOLD)
- `pii_flags_json` - PII flags (JSON)
- `metadata_json` - Safe metadata (JSON, no PII)

**Indexes:**
- `ix_evidence_tenant_type` - (tenant_id, type, captured_at)
- `ix_evidence_tenant_hash` - (tenant_id, content_hash)
- `ix_evidence_tenant_source` - (tenant_id, source)

**Relationships:**
- `links` - One-to-many with EvidenceLink

#### EvidenceLink Model

**Purpose:** Links evidence objects to resources (risk runs, claims, etc.)

**Key Features:**
- ✅ Tenant-scoped
- ✅ Links evidence to any resource type
- ✅ Relationship types (SUPPORTS, DERIVED_FROM, ATTACHED)

**Fields:**
- `id` - ULID (String(26))
- `tenant_id` - Tenant ID (from TenantScopedMixin)
- `evidence_id` - Reference to EvidenceObject
- `resource_type` - Resource type (risk_run, claim, assessment, etc.)
- `resource_id` - Resource ID (ULID or other)
- `relationship` - Relationship type (SUPPORTS, DERIVED_FROM, ATTACHED, etc.)

**Indexes:**
- `ix_evidence_links_resource` - (tenant_id, resource_type, resource_id)
- `ix_evidence_links_evidence` - (evidence_id, resource_type)

**Relationships:**
- `evidence` - Many-to-one with EvidenceObject

#### EvidenceBundle Model

**Purpose:** Collection of evidence objects with canonical manifest and bundle hash

**Key Features:**
- ✅ Tenant-scoped
- ✅ Canonical manifest (JSON)
- ✅ Bundle hash for integrity verification
- ✅ Schema versioning

**Fields:**
- `id` - ULID (String(26))
- `tenant_id` - Tenant ID (from TenantScopedMixin)
- `schema_version` - Schema version (e.g., 'evidence_bundle_v1.0')
- `manifest_json` - List of evidence refs + hashes (JSON)
- `bundle_hash` - SHA256 hash of canonical manifest
- `created_by_user_id` - User who created the bundle

**Indexes:**
- `ix_bundles_tenant_created` - (tenant_id, created_at)
- `ix_bundles_tenant_hash` - (tenant_id, bundle_hash)

**Relationships:**
- `created_by_user` - Many-to-one with User

### 2. Enums

#### EvidenceType
- `DOCUMENT` - Document files
- `WEATHER_SNAPSHOT` - Weather data snapshot
- `SENSOR_SEGMENT` - Sensor data segment
- `PORT_EVENT` - Port event data
- `IMAGE` - Image files
- `VIDEO` - Video files

#### RetentionClass
- `STANDARD` - Standard retention period
- `REGULATORY` - Extended retention for regulatory compliance
- `LEGAL_HOLD` - Legal hold - cannot be deleted

### 3. Alembic Migration (`migrations/versions/008_create_evidence_models.py`)

**Features:**
- ✅ Creates `evidence_objects` table
- ✅ Creates `evidence_links` table
- ✅ Creates `evidence_bundles` table
- ✅ Creates all indexes
- ✅ Foreign key constraints
- ✅ Enum types
- ✅ Proper downgrade function

**Revision:** `008_evidence`
**Depends on:** `007_model_versioning`

## Model Relationships

```
EvidenceObject (1) ──< (many) EvidenceLink
     │
     └──> (many-to-one) Tenant

EvidenceLink
     ├──> (many-to-one) EvidenceObject
     └──> (references) Resource (polymorphic)

EvidenceBundle
     └──> (many-to-one) User (created_by_user_id)
```

## Usage Examples

### Create Evidence Object

```python
from app.modules.evidence.models import EvidenceObject, EvidenceType, RetentionClass

evidence = EvidenceObject(
    tenant_id=tenant_id,
    type=EvidenceType.DOCUMENT,
    source="UPLOAD",
    storage_uri="s3://bucket/evidence/doc-123.pdf",
    content_hash="a1b2c3d4e5f6...",
    mime_type="application/pdf",
    size_bytes=1024000,
    captured_at=datetime.utcnow(),
    retention_class=RetentionClass.STANDARD,
    pii_flags_json={"contains_name": False, "contains_email": False},
    metadata_json={"title": "Shipping Document", "pages": 5}
)
session.add(evidence)
session.commit()
```

### Link Evidence to Resource

```python
from app.modules.evidence.models import EvidenceLink

link = EvidenceLink(
    tenant_id=tenant_id,
    evidence_id=evidence.id,
    resource_type="risk_run",
    resource_id=run_id,
    relationship="SUPPORTS"
)
session.add(link)
session.commit()
```

### Create Evidence Bundle

```python
from app.modules.evidence.models import EvidenceBundle
import hashlib
import json

# Create manifest
manifest = [
    {"evidence_id": evidence1.id, "content_hash": evidence1.content_hash},
    {"evidence_id": evidence2.id, "content_hash": evidence2.content_hash}
]

# Compute bundle hash
canonical_manifest = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
bundle_hash = hashlib.sha256(canonical_manifest.encode()).hexdigest()

bundle = EvidenceBundle(
    tenant_id=tenant_id,
    schema_version="evidence_bundle_v1.0",
    manifest_json=manifest,
    bundle_hash=bundle_hash,
    created_by_user_id=user_id
)
session.add(bundle)
session.commit()
```

## Database Schema

### evidence_objects

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | String(26) | NO | ULID primary key |
| tenant_id | String(26) | NO | Tenant ID |
| type | Enum | NO | Evidence type |
| source | String(100) | NO | Source identifier |
| storage_uri | String(500) | NO | Storage URI |
| content_hash | String(64) | NO | SHA256 hash |
| mime_type | String(100) | YES | MIME type |
| size_bytes | BigInteger | YES | File size |
| captured_at | DateTime | YES | Capture timestamp |
| ingested_at | DateTime | NO | Ingestion timestamp |
| retention_class | Enum | NO | Retention class |
| pii_flags_json | JSON | YES | PII flags |
| metadata_json | JSON | YES | Metadata |
| created_at | DateTime | NO | Creation timestamp |
| updated_at | DateTime | NO | Update timestamp |

### evidence_links

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | String(26) | NO | ULID primary key |
| tenant_id | String(26) | NO | Tenant ID |
| evidence_id | String(26) | NO | Evidence object ID |
| resource_type | String(100) | NO | Resource type |
| resource_id | String(100) | NO | Resource ID |
| relationship | String(50) | NO | Relationship type |
| created_at | DateTime | NO | Creation timestamp |
| updated_at | DateTime | NO | Update timestamp |

### evidence_bundles

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | String(26) | NO | ULID primary key |
| tenant_id | String(26) | NO | Tenant ID |
| schema_version | String(50) | NO | Schema version |
| manifest_json | JSON | NO | Manifest |
| bundle_hash | String(64) | NO | SHA256 hash |
| created_by_user_id | String(26) | YES | Creator user ID |
| created_at | DateTime | NO | Creation timestamp |
| updated_at | DateTime | NO | Update timestamp |

## Files Created

1. ✅ `app/modules/evidence/models.py` - Model definitions
2. ✅ `app/modules/evidence/__init__.py` - Module exports
3. ✅ `migrations/versions/008_create_evidence_models.py` - Alembic migration
4. ✅ `EVIDENCE_MODULE_COMPLETE.md` - This documentation

## Next Steps

1. **Create Schemas**: Pydantic schemas for API
2. **Create Repository**: Data access layer
3. **Create Service**: Business logic for evidence management
4. **Create Router**: API endpoints
5. **Add Storage Integration**: S3/local storage integration
6. **Add Tests**: Unit and integration tests

**Evidence module hoàn thành và sẵn sàng sử dụng!** 🎉
