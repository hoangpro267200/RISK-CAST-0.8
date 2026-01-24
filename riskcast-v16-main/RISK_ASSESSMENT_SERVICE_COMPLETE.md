# ✅ Risk Assessment Service - Hoàn Thành

## Đã Tạo Thành Công

### 1. Service Implementation (`app/modules/risk_assessments/service.py`)

#### ✅ RiskAssessmentService Class

**Initialization:**
- Takes `TenantScopedSession` as dependency
- Creates `AuditLedgerService` with raw session (for audit logging)
- Logs initialization for debugging

**Constants:**
- `INPUT_SCHEMA_VERSION = "risk_input_v3.0"` - Current input schema version

#### ✅ Input Hashing Methods

**`_canonicalize_input(input_data: dict) -> str`**
- Canonical JSON serialization for stable hashing
- Uses `sort_keys=True` for consistent key ordering
- Uses `separators=(',', ':')` for no whitespace
- Uses `default=str` for consistent numeric formatting

**`_compute_input_hash(canonical_input: str) -> str`**
- Computes SHA256 hash of canonical input
- Returns hex digest (64 characters)
- Used for deduplication

#### ✅ Core Methods

**`create_assessment(data, user_id, context) -> RiskAssessment`**
- Validates and normalizes input
- Canonicalizes and hashes input
- Creates assessment with status READY
- Stores assessment in database
- Emits audit event (with error handling)
- Returns created assessment

**`get_assessment(assessment_id) -> RiskAssessment`**
- Gets assessment by ID
- Automatically filtered by tenant_id (TenantScopedSession)
- Raises `AssessmentNotFoundError` if not found
- Returns assessment instance

**`list_assessments(skip, limit, status) -> List[RiskAssessment]`**
- Lists assessments for tenant
- Automatically filtered by tenant_id
- Supports pagination (skip, limit)
- Supports status filtering (DRAFT, READY, ARCHIVED)
- Returns list of assessments

**`update_assessment_status(assessment_id, new_status, user_id, context) -> RiskAssessment`**
- Updates assessment status
- Validates status enum
- Emits audit event with diff
- Returns updated assessment

**`archive_assessment(assessment_id, user_id, context) -> RiskAssessment`**
- Convenience method to archive assessment
- Sets status to ARCHIVED
- Returns archived assessment

**`find_by_input_hash(input_hash) -> Optional[RiskAssessment]`**
- Finds assessment by input hash
- Used for deduplication
- Returns assessment if found, None otherwise

### 2. Exceptions (`app/modules/risk_assessments/exceptions.py`)

#### ✅ Custom Exceptions

**`AssessmentNotFoundError(NotFoundError)`**
- Raised when assessment not found
- Includes assessment_id in error

**`AssessmentValidationError(ValidationError)`**
- Raised when validation fails
- Includes optional field name

**`DuplicateAssessmentError(ValidationError)`**
- Raised when duplicate assessment exists (same input hash)
- Includes input_hash and existing_assessment_id

### 3. Integration Features

#### ✅ Tenant Scoping
- Uses `TenantScopedSession` for automatic tenant isolation
- All queries automatically filtered by tenant_id
- No manual tenant_id filtering needed

#### ✅ Audit Logging
- Integrates with `AuditLedgerService`
- Logs assessment creation events
- Logs status update events with diffs
- Error handling for audit failures (doesn't fail assessment operations)

#### ✅ Input Validation
- Uses Pydantic schemas for validation
- `RiskAssessmentInputV3` with `extra='forbid'`
- Validates status enum values

## Usage Examples

### Create Assessment

```python
from app.modules.risk_assessments.service import RiskAssessmentService
from app.modules.risk_assessments.schemas import RiskAssessmentCreate, RiskAssessmentInputV3
from app.modules.audit_ledger.schemas import AuditContext
from app.database import get_tenant_scoped_db
from app.shared.dependencies import resolve_tenant_context

@router.post("/risk-assessments")
async def create_assessment(
    data: RiskAssessmentCreate,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskAssessmentService(db)
    
    audit_context = AuditContext(
        request_id=request.state.request_id,
        trace_id=request.state.trace_id,
        ip=request.client.host,
        user_agent=request.headers.get("user-agent"),
        route="/api/v3/risk-assessments",
        method="POST"
    )
    
    assessment = await service.create_assessment(
        data=data,
        user_id=context.user_id,
        context=audit_context
    )
    
    return assessment
```

### Get Assessment

```python
@router.get("/risk-assessments/{assessment_id}")
async def get_assessment(
    assessment_id: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskAssessmentService(db)
    assessment = await service.get_assessment(assessment_id)
    return assessment
```

### List Assessments

```python
@router.get("/risk-assessments")
async def list_assessments(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskAssessmentService(db)
    assessments = await service.list_assessments(
        skip=skip,
        limit=limit,
        status=status
    )
    return assessments
```

### Update Status

```python
@router.patch("/risk-assessments/{assessment_id}/status")
async def update_status(
    assessment_id: str,
    new_status: str,
    context: TenantContext = Depends(resolve_tenant_context),
    db: TenantScopedSession = Depends(get_tenant_scoped_db)
):
    service = RiskAssessmentService(db)
    
    audit_context = AuditContext(
        request_id=request.state.request_id,
        route=f"/api/v3/risk-assessments/{assessment_id}/status",
        method="PATCH"
    )
    
    assessment = await service.update_assessment_status(
        assessment_id=assessment_id,
        new_status=new_status,
        user_id=context.user_id,
        context=audit_context
    )
    
    return assessment
```

## Key Features

### 1. Input Hashing
- Canonical JSON serialization for stable hashing
- SHA256 hash for deduplication
- Consistent across different input formats

### 2. Tenant Isolation
- Automatic tenant scoping via TenantScopedSession
- No manual tenant_id filtering needed
- Prevents cross-tenant data access

### 3. Audit Trail
- All operations logged to audit ledger
- Includes context information (request_id, trace_id, etc.)
- Status changes include diffs

### 4. Error Handling
- Custom exceptions for different error types
- Graceful handling of audit failures
- Detailed error messages

### 5. Status Management
- Three states: DRAFT, READY, ARCHIVED
- Enum validation
- Convenience method for archiving

## Files Created/Updated

1. ✅ `app/modules/risk_assessments/service.py` - Service implementation
2. ✅ `app/modules/risk_assessments/exceptions.py` - Custom exceptions
3. ✅ `app/modules/risk_assessments/service_example.py` - Usage examples
4. ✅ `RISK_ASSESSMENT_SERVICE_COMPLETE.md` - This documentation

## Next Steps

1. **Create Router**: Implement FastAPI routes using the service
2. **Add Repository**: Implement repository layer if needed (currently using direct queries)
3. **Add Tests**: Unit and integration tests
4. **Add Validation**: Additional business logic validation
5. **Add Deduplication**: Enable duplicate checking in create_assessment

**Risk Assessment Service hoàn thành và sẵn sàng sử dụng!** 🎉
