# ✅ Risk Run Orchestration Service - Hoàn Thành

## Đã Tạo Thành Công

### 1. Service (`app/modules/risk_runs/service.py`)

#### ✅ RiskRunService Class

**Initialization:**
- Takes `TenantScopedSession` as dependency
- Creates `RiskEngineV3` instance
- Creates `AuditLedgerService` with raw session
- Logs initialization for debugging

**Constants:**
- `DEFAULT_ITERATIONS = 10000` - Default Monte Carlo iterations

#### ✅ Core Methods

**`create_run(...) -> RiskRun`**
- Creates and enqueues a new risk run
- Loads assessment and validates
- Determines iterations (default or provided)
- Computes seed based on strategy:
  - `DETERMINISTIC_INPUT_HASH`: Computes from input hash
  - `USER_PROVIDED`: Uses provided seed
- Creates `RiskRun` record with QUEUED status
- Creates `RiskRunJob` record for async processing
- Emits audit event
- Returns created run

**`get_run(run_id) -> RiskRun`**
- Gets run by ID (tenant-scoped automatically)
- Raises `RunNotFoundError` if not found
- Returns run instance

**`update_run_started(run_id) -> None`**
- Marks run as RUNNING
- Sets `started_at` timestamp
- Validates run is in QUEUED status

**`update_run_completed(run_id, result, result_hash) -> None`**
- Marks run as SUCCEEDED
- Stores result JSON and hash
- Sets `completed_at` timestamp
- Validates run is in RUNNING status

**`update_run_failed(run_id, error) -> None`**
- Marks run as FAILED
- Stores error JSON (type, message)
- Sets `completed_at` timestamp

**`cancel_run(run_id, user_id, context) -> None`**
- Cancels a queued or running run
- Sets status to CANCELED
- Emits audit event

**`list_runs(assessment_id, status, skip, limit) -> List[RiskRun]`**
- Lists runs for tenant
- Supports filtering by assessment_id and status
- Supports pagination
- Returns list of runs

### 2. Schemas (`app/modules/risk_runs/schemas.py`)

#### ✅ RiskRunCreate
- **Fields**:
  - `assessment_id`: Risk assessment ID
  - `model_version_id`: Optional model version ID
  - `iterations`: Optional number of iterations
  - `seed_strategy`: Seed strategy (default: DETERMINISTIC_INPUT_HASH)
  - `seed`: Optional user-provided seed
  - `options`: Optional additional options

#### ✅ RiskRunResponse
- **Fields**: All model fields as response schema
- **Computed Fields**:
  - `result`: Parsed `RiskEngineResultV3` (if available)
  - `duration_seconds`: Duration in seconds (if completed)
- **Method**: `from_orm_with_result(run)` - Creates response with parsed result

#### ✅ RiskRunListResponse
- **Fields**: Paginated list response with items, total, page, page_size, has_next, has_prev

### 3. Exceptions (`app/modules/risk_runs/exceptions.py`)

- `RunNotFoundError` - When run not found
- `RunValidationError` - When validation fails
- `RunExecutionError` - When execution fails

## Key Features

### 1. Seed Strategy Support
- **DETERMINISTIC_INPUT_HASH**: Computes seed from input hash, model version, iterations
- **USER_PROVIDED**: Uses user-provided seed for custom scenarios
- Validation ensures seed is provided when needed

### 2. Run Lifecycle Management
- **QUEUED** → **RUNNING** → **SUCCEEDED/FAILED/CANCELED**
- Status transitions validated
- Timestamps tracked (started_at, completed_at)

### 3. Job Queue Integration
- Automatically creates `RiskRunJob` when run is created
- Job can be picked up by workers for async processing

### 4. Result Storage
- Stores result JSON and hash
- Parses result into `RiskEngineResultV3` for response
- Computes duration from timestamps

### 5. Audit Logging
- Logs run creation (queued)
- Logs run cancellation
- Error handling for audit failures (doesn't fail operations)

### 6. Tenant Scoping
- Uses `TenantScopedSession` for automatic tenant isolation
- All queries automatically filtered by tenant_id

## Usage Examples

### Create Run

```python
from app.modules.risk_runs.service import RiskRunService
from app.modules.risk_runs.schemas import RiskRunCreate
from app.modules.risk_runs.models import SeedStrategy
from app.modules.audit_ledger.schemas import AuditContext
from app.database import get_tenant_scoped_db
from app.shared.dependencies import resolve_tenant_context

@router.post("/risk-assessments/{assessment_id}/runs")
async def create_run(
    assessment_id: str,
    data: RiskRunCreate,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskRunService(db)
    
    audit_context = AuditContext(
        request_id=request.state.request_id,
        route=f"/api/v3/risk-assessments/{assessment_id}/runs",
        method="POST"
    )
    
    run = await service.create_run(
        assessment_id=assessment_id,
        user_id=context.user_id,
        context=audit_context,
        model_version_id=data.model_version_id,
        iterations=data.iterations,
        seed_strategy=data.seed_strategy,
        seed=data.seed,
        options=data.options
    )
    
    return run
```

### Get Run

```python
@router.get("/risk-runs/{run_id}")
async def get_run(
    run_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskRunService(db)
    run = await service.get_run(run_id)
    return RiskRunResponse.from_orm_with_result(run)
```

### Update Run Status

```python
# In worker/background task
async def execute_run(run_id: str):
    service = RiskRunService(db)
    
    # Mark as started
    await service.update_run_started(run_id)
    
    try:
        # Execute engine
        result, result_hash = await engine.run(input_dto, config)
        
        # Mark as completed
        await service.update_run_completed(run_id, result, result_hash)
    except Exception as e:
        # Mark as failed
        await service.update_run_failed(run_id, e)
```

### List Runs

```python
@router.get("/risk-runs")
async def list_runs(
    assessment_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskRunService(db)
    
    status_enum = RiskRunStatus(status) if status else None
    runs = await service.list_runs(
        assessment_id=assessment_id,
        status=status_enum,
        skip=skip,
        limit=limit
    )
    
    return [RiskRunResponse.from_orm_with_result(run) for run in runs]
```

## Integration Points

### 1. With Risk Assessment Service
- Loads assessment to get input_hash
- Uses assessment for seed computation

### 2. With Risk Engine V3
- Uses engine to compute deterministic seed
- Receives engine results and stores them

### 3. With Job Queue
- Creates `RiskRunJob` for async processing
- Workers can pick up jobs and execute runs

### 4. With Audit Ledger
- Logs run lifecycle events
- Tracks who created/canceled runs

## Files Created/Updated

1. ✅ `app/modules/risk_runs/service.py` - RiskRunService implementation
2. ✅ `app/modules/risk_runs/schemas.py` - Updated schemas
3. ✅ `app/modules/risk_runs/exceptions.py` - Custom exceptions
4. ✅ `RISK_RUN_SERVICE_COMPLETE.md` - This documentation

## Next Steps

1. **Create Router**: Implement FastAPI routes using the service
2. **Create Worker**: Background worker for processing jobs
3. **Add Tests**: Unit and integration tests
4. **Add Monitoring**: Track run execution metrics
5. **Add Retry Logic**: Automatic retry for failed runs

**Risk Run Orchestration Service hoàn thành và sẵn sàng sử dụng!** 🎉
