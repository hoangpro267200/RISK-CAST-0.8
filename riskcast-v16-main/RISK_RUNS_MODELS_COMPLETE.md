# ✅ Risk Runs Models - Hoàn Thành

## Đã Tạo Thành Công

### 1. Models (`app/modules/risk_runs/models.py`)

#### ✅ Enums

**RiskRunStatus:**
- `QUEUED` - Job queued, waiting for execution
- `RUNNING` - Currently executing
- `SUCCEEDED` - Execution completed successfully
- `FAILED` - Execution failed
- `CANCELED` - Execution was canceled

**SeedStrategy:**
- `DETERMINISTIC_INPUT_HASH` - Seed derived from input hash (reproducible)
- `USER_PROVIDED` - Seed provided by user

**RiskRunJobStatus:**
- `QUEUED` - Job in queue, available for pickup
- `LOCKED` - Job locked by a worker
- `DONE` - Job completed
- `FAILED` - Job failed (after retries)

#### ✅ RiskRun Model

**Inherits:**
- `BaseMixin` (ULID ID, timestamps)
- `TenantScopedMixin` (tenant_id, tenant scoping)

**Fields:**
- **ID & Tenant**: Inherited from mixins (ULID String(26))
- **Association**: `risk_assessment_id` (FK to risk_assessments, CASCADE delete)
- **Status**: `status` (Enum: QUEUED, RUNNING, SUCCEEDED, FAILED, CANCELED)
- **Versioning**:
  - `engine_version` (String(100)) - Git SHA or semver+build
  - `model_version_id` (String(26), nullable) - FK to risk_model_versions (Stage 2)
  - `result_schema_version` (String(50)) - e.g., 'risk_result_v3.0'
- **Seed Configuration**:
  - `seed_strategy` (Enum: DETERMINISTIC_INPUT_HASH, USER_PROVIDED)
  - `seed` (BigInteger) - Random seed for reproducibility
  - `iterations` (Integer) - Number of Monte Carlo iterations
- **Options**: `options_json` (JSON, nullable) - scenario_set_id, toggles, etc.
- **Results**:
  - `result_json` (JSON, nullable) - Full result payload
  - `result_hash` (String(64), nullable) - SHA256 of canonical result
  - `error_json` (JSON, nullable) - Error details (on failure)
- **Timestamps**:
  - `started_at` (DateTime, nullable)
  - `completed_at` (DateTime, nullable)
  - `created_at`, `updated_at` (inherited from BaseMixin)

**Relationships:**
- `assessment` - Many-to-one with RiskAssessment

**Indexes:**
- Single column: tenant_id, created_at, updated_at, risk_assessment_id, status, engine_version, model_version_id, result_hash, started_at, completed_at
- Composite:
  - `ix_risk_runs_tenant_assessment` - (tenant_id, risk_assessment_id, created_at)
  - `ix_risk_runs_tenant_status` - (tenant_id, status)
  - `ix_risk_runs_assessment_status` - (risk_assessment_id, status)

#### ✅ RiskRunJob Model

**Inherits:**
- `BaseMixin` (ULID ID, timestamps)
- **Not** using TenantScopedMixin (to allow cross-tenant job processing)

**Fields:**
- **ID**: Inherited from BaseMixin (ULID String(26))
- **Tenant**: `tenant_id` (FK to tenants, CASCADE delete)
- **Association**: `risk_run_id` (FK to risk_runs, unique, CASCADE delete)
- **Status**: `status` (Enum: QUEUED, LOCKED, DONE, FAILED)
- **Locking**:
  - `locked_by` (String(100), nullable) - Worker identity
  - `locked_at` (DateTime, nullable)
- **Retry Logic**:
  - `attempt_count` (Integer, default=0)
  - `available_at` (DateTime) - For retry backoff
- **Timestamps**: `created_at`, `updated_at` (inherited from BaseMixin)

**Relationships:**
- `risk_run` - One-to-one with RiskRun

**Indexes:**
- Single column: tenant_id, created_at, updated_at, risk_run_id (unique), status, available_at
- Composite:
  - `ix_risk_run_jobs_status_available` - (status, available_at) - For job queue queries
  - `ix_risk_run_jobs_tenant_status` - (tenant_id, status)

### 2. Alembic Migration (`migrations/versions/005_create_risk_runs_models.py`)

#### ✅ Migration Details
- **Revision ID**: `005_risk_runs`
- **Down Revision**: `004_risk_assessments`
- **Tables**: `risk_runs`, `risk_run_jobs`

#### ✅ risk_runs Table
- All model fields with proper types and constraints
- Foreign keys to `tenants.id` (CASCADE) and `risk_assessments.id` (CASCADE)
- Enum types for status and seed_strategy
- All indexes created (single column and composite)

#### ✅ risk_run_jobs Table
- All model fields with proper types and constraints
- Foreign keys to `tenants.id` (CASCADE) and `risk_runs.id` (CASCADE)
- Unique constraint on `risk_run_id` (one job per run)
- Enum type for status
- All indexes created (single column and composite)

#### ✅ Downgrade Function
- Properly drops all indexes and tables in reverse order

## Key Features

### 1. Tenant Scoping
- `RiskRun` uses `TenantScopedMixin` for automatic tenant isolation
- All queries automatically filtered by tenant_id
- Works with `TenantScopedSession`

### 2. Job Queue Pattern
- `RiskRunJob` implements job queue for async execution
- Status-based workflow: QUEUED → LOCKED → DONE/FAILED
- Locking mechanism for worker coordination
- Retry logic with backoff (attempt_count, available_at)

### 3. Reproducibility
- Seed strategy enum for different seed generation methods
- Deterministic seed from input hash for reproducibility
- User-provided seed option for custom scenarios

### 4. Versioning
- Engine version tracking (Git SHA or semver+build)
- Model version ID (for future model versioning)
- Result schema versioning

### 5. Result Hashing
- `result_hash` for result deduplication
- SHA256 hash of canonical result JSON

## Usage Examples

### Create Risk Run

```python
from app.modules.risk_runs.models import RiskRun, RiskRunStatus, SeedStrategy
from app.database import TenantScopedSession

# Create risk run
risk_run = RiskRun(
    tenant_id=context.tenant_id,  # Auto-set by TenantScopedSession
    risk_assessment_id=assessment.id,
    status=RiskRunStatus.QUEUED,
    engine_version="v3.0.0+abc123",
    result_schema_version="risk_result_v3.0",
    seed_strategy=SeedStrategy.DETERMINISTIC_INPUT_HASH,
    seed=1234567890,  # Derived from input hash
    iterations=10000
)

db.add(risk_run)
db.commit()
```

### Create Job

```python
from app.modules.risk_runs.models import RiskRunJob, RiskRunJobStatus

# Create job for async execution
job = RiskRunJob(
    tenant_id=context.tenant_id,
    risk_run_id=risk_run.id,
    status=RiskRunJobStatus.QUEUED,
    available_at=datetime.utcnow()
)

db.add(job)
db.commit()
```

### Query Jobs for Processing

```python
# Get next available job
job = db.query(RiskRunJob).filter(
    RiskRunJob.status == RiskRunJobStatus.QUEUED,
    RiskRunJob.available_at <= datetime.utcnow()
).order_by(RiskRunJob.available_at).first()

if job:
    # Lock the job
    job.status = RiskRunJobStatus.LOCKED
    job.locked_by = worker_id
    job.locked_at = datetime.utcnow()
    job.attempt_count += 1
    db.commit()
```

## Files Created/Updated

1. ✅ `app/modules/risk_runs/models.py` - RiskRun and RiskRunJob models
2. ✅ `migrations/versions/005_create_risk_runs_models.py` - Alembic migration
3. ✅ `RISK_RUNS_MODELS_COMPLETE.md` - This documentation

## Next Steps

1. **Create Schemas**: Pydantic schemas for RiskRun and RiskRunJob
2. **Create Repository**: Data access layer for risk runs
3. **Create Service**: Business logic for risk run management
4. **Create Router**: FastAPI routes for risk runs
5. **Create Worker**: Background worker for processing jobs
6. **Add Tests**: Unit and integration tests

**Risk Runs Models hoàn thành và sẵn sàng sử dụng!** 🎉
