# ✅ Underwriting Module - Hoàn Thành

## Đã Tạo Thành Công

### 1. Models (`app/modules/underwriting/models.py`)

#### UnderwritingSubmission Model

**Purpose:** Represents a submission for underwriting review with state machine workflow

**Key Features:**
- ✅ Tenant-scoped (inherits TenantScopedMixin)
- ✅ Status tracking with state machine
- ✅ Links to risk assessment, risk run, and evidence bundle
- ✅ Coverage request details (JSON)

**Fields:**
- `id` - ULID (String(26))
- `tenant_id` - Tenant ID (from TenantScopedMixin)
- `status` - SubmissionStatus enum (DRAFT, SUBMITTED, UNDER_REVIEW, REQUESTED_INFO, QUOTED, BOUND, DECLINED, CANCELED)
- `created_by_user_id` - User who created submission
- `risk_assessment_id` - Reference to RiskAssessment
- `risk_run_id` - Reference to RiskRun (optional)
- `evidence_bundle_id` - Reference to EvidenceBundle (optional)
- `requested_coverage_json` - Coverage request (limits, deductible, duration)
- `corridor_id` - Corridor identifier
- `product_type` - Product type

**Status Flow:**
```
DRAFT → SUBMITTED → UNDER_REVIEW → [REQUESTED_INFO | QUOTED | DECLINED]
                                         ↓
                                    UNDER_REVIEW
                                         ↓
                                    QUOTED → BOUND
                                         ↓
                                    CANCELED
```

#### UnderwritingDecision Model

**Purpose:** Represents a decision made during underwriting review

**Key Features:**
- ✅ Tenant-scoped
- ✅ Pinned references for audit trail (model_version_id, risk_run_id, evidence_bundle_id)
- ✅ Decision types (QUOTE, DECLINE, REQUEST_INFO)
- ✅ Terms and notes

**Fields:**
- `id` - ULID (String(26))
- `tenant_id` - Tenant ID
- `submission_id` - Reference to UnderwritingSubmission
- `decided_by_user_id` - User who made decision
- `decision` - DecisionType enum (QUOTE, DECLINE, REQUEST_INFO)
- `terms_json` - Terms (premium, limits, exclusions)
- `notes` - Decision notes
- `model_version_id` - Pinned model version (immutable)
- `risk_run_id` - Pinned risk run (immutable)
- `evidence_bundle_id` - Pinned evidence bundle (immutable)

#### Policy Model

**Purpose:** Represents a bound insurance policy

**Key Features:**
- ✅ Tenant-scoped
- ✅ Unique policy number per tenant
- ✅ Pinned references (model_version_id, risk_run_id) with RESTRICT delete
- ✅ Effective period tracking
- ✅ Status tracking (ACTIVE, CANCELED, EXPIRED)

**Fields:**
- `id` - ULID (String(26))
- `tenant_id` - Tenant ID
- `policy_number` - Unique policy number (per tenant)
- `status` - PolicyStatus enum (ACTIVE, CANCELED, EXPIRED)
- `submission_id` - Reference to UnderwritingSubmission
- `bound_by_user_id` - User who bound the policy
- `bound_at` - Binding timestamp
- `effective_from` - Policy effective start date
- `effective_to` - Policy effective end date
- `model_version_id` - Pinned model version (RESTRICT delete)
- `risk_run_id` - Pinned risk run (RESTRICT delete)
- `terms_json` - Policy terms

**Constraints:**
- Unique constraint: `(tenant_id, policy_number)`
- Foreign key RESTRICT on `model_version_id` and `risk_run_id` (prevents deletion of pinned references)

### 2. State Machine (`app/modules/underwriting/state_machine.py`)

#### UnderwritingStateMachine Class

**Purpose:** Validates state transitions and enforces preconditions

**Key Features:**
- ✅ Valid transition rules
- ✅ Precondition validation
- ✅ Terminal state detection
- ✅ Transition path finding

**Valid Transitions:**
```python
DRAFT → [SUBMITTED]
SUBMITTED → [UNDER_REVIEW, CANCELED]
UNDER_REVIEW → [REQUESTED_INFO, QUOTED, DECLINED]
REQUESTED_INFO → [UNDER_REVIEW]
QUOTED → [BOUND, CANCELED]
BOUND → []  # Terminal
DECLINED → []  # Terminal
CANCELED → []  # Terminal
```

**Methods:**
- `can_transition(from_status, to_status)` - Check if transition is allowed
- `validate_transition(submission, to_status, context)` - Validate preconditions
- `get_valid_transitions(from_status)` - Get valid target statuses
- `is_terminal(status)` - Check if status is terminal
- `get_transition_path(from_status, to_status)` - Find shortest path (BFS)

**Precondition Validations:**

**SUBMITTED:**
- `risk_run_id` required
- Risk run status must be SUCCEEDED
- `evidence_bundle_id` required

**QUOTED:**
- `terms_json` required
- `evidence_bundle_id` must be pinned
- `model_version_id` must be pinned
- `risk_run_id` must be pinned

**BOUND:**
- Must be from QUOTED status
- `policy_number` required
- `effective_from` required
- `effective_to` required
- `model_version_id` must be pinned
- `risk_run_id` must be pinned

**REQUESTED_INFO:**
- `notes` required

**DECLINED:**
- `notes` required

### 3. Enums

#### SubmissionStatus
- `DRAFT` - Initial draft state
- `SUBMITTED` - Submitted for review
- `UNDER_REVIEW` - Under review
- `REQUESTED_INFO` - Information requested
- `QUOTED` - Quote provided
- `BOUND` - Policy bound (terminal)
- `DECLINED` - Declined (terminal)
- `CANCELED` - Canceled (terminal)

#### DecisionType
- `QUOTE` - Quote decision
- `DECLINE` - Decline decision
- `REQUEST_INFO` - Request information

#### PolicyStatus
- `ACTIVE` - Active policy
- `CANCELED` - Canceled policy
- `EXPIRED` - Expired policy

### 4. Alembic Migration (`migrations/versions/009_create_underwriting_models.py`)

**Features:**
- ✅ Creates `underwriting_submissions` table
- ✅ Creates `underwriting_decisions` table
- ✅ Creates `policies` table
- ✅ Creates all indexes
- ✅ Foreign key constraints
- ✅ Unique constraint on `(tenant_id, policy_number)`
- ✅ Enum types
- ✅ Proper downgrade function

**Revision:** `009_underwriting`
**Depends on:** `008_evidence`

## Model Relationships

```
UnderwritingSubmission (1) ──< (many) UnderwritingDecision
     │
     ├──> (many-to-one) RiskAssessment
     ├──> (many-to-one) RiskRun
     ├──> (many-to-one) EvidenceBundle
     └──> (many-to-one) User (created_by)

UnderwritingDecision
     ├──> (many-to-one) UnderwritingSubmission
     ├──> (many-to-one) RiskModelVersion (pinned)
     ├──> (many-to-one) RiskRun (pinned)
     └──> (many-to-one) EvidenceBundle (pinned)

Policy
     ├──> (many-to-one) UnderwritingSubmission
     ├──> (many-to-one) RiskModelVersion (pinned, RESTRICT)
     └──> (many-to-one) RiskRun (pinned, RESTRICT)
```

## State Machine Workflow

```
┌─────────┐
│  DRAFT  │
└────┬────┘
     │ (risk_run_id, evidence_bundle_id required)
     ↓
┌───────────┐
│ SUBMITTED │
└─────┬─────┘
      │
      ├───→ CANCELED (terminal)
      │
      ↓
┌──────────────┐
│ UNDER_REVIEW │
└──────┬───────┘
       │
       ├───→ REQUESTED_INFO ──→ UNDER_REVIEW
       │
       ├───→ QUOTED ──→ BOUND (terminal)
       │              └──→ CANCELED (terminal)
       │
       └───→ DECLINED (terminal)
```

## Usage Examples

### Create Submission

```python
from app.modules.underwriting.models import UnderwritingSubmission, SubmissionStatus

submission = UnderwritingSubmission(
    tenant_id=tenant_id,
    status=SubmissionStatus.DRAFT,
    risk_assessment_id=assessment_id,
    created_by_user_id=user_id,
    requested_coverage_json={
        "limits": {"per_occurrence": 1000000, "aggregate": 5000000},
        "deductible": 50000,
        "duration_days": 365
    },
    corridor_id="asia-pacific",
    product_type="cargo"
)
session.add(submission)
session.commit()
```

### Submit for Review

```python
from app.modules.underwriting.state_machine import UnderwritingStateMachine

sm = UnderwritingStateMachine()

# Validate transition
errors = sm.validate_transition(
    submission=submission,
    to_status=SubmissionStatus.SUBMITTED,
    context={}
)

if errors:
    raise ValueError(f"Validation errors: {errors}")

# Update status
submission.status = SubmissionStatus.SUBMITTED
submission.risk_run_id = run_id
submission.evidence_bundle_id = bundle_id
session.commit()
```

### Create Decision (Quote)

```python
from app.modules.underwriting.models import UnderwritingDecision, DecisionType

decision = UnderwritingDecision(
    tenant_id=tenant_id,
    submission_id=submission.id,
    decided_by_user_id=user_id,
    decision=DecisionType.QUOTE,
    terms_json={
        "premium": 125000,
        "limits": {"per_occurrence": 1000000, "aggregate": 5000000},
        "deductible": 50000,
        "exclusions": ["war", "nuclear"]
    },
    notes="Standard quote based on risk assessment",
    model_version_id=model_version_id,
    risk_run_id=run_id,
    evidence_bundle_id=bundle_id
)
session.add(decision)

# Update submission status
submission.status = SubmissionStatus.QUOTED
session.commit()
```

### Bind Policy

```python
from app.modules.underwriting.models import Policy, PolicyStatus
from datetime import datetime, timedelta

# Validate transition
errors = sm.validate_transition(
    submission=submission,
    to_status=SubmissionStatus.BOUND,
    context={
        "policy_number": "POL-2024-001",
        "effective_from": datetime.utcnow(),
        "effective_to": datetime.utcnow() + timedelta(days=365),
        "model_version_id": model_version_id,
        "risk_run_id": run_id
    }
)

if errors:
    raise ValueError(f"Validation errors: {errors}")

# Create policy
policy = Policy(
    tenant_id=tenant_id,
    policy_number="POL-2024-001",
    status=PolicyStatus.ACTIVE,
    submission_id=submission.id,
    bound_by_user_id=user_id,
    bound_at=datetime.utcnow(),
    effective_from=datetime.utcnow(),
    effective_to=datetime.utcnow() + timedelta(days=365),
    model_version_id=model_version_id,
    risk_run_id=run_id,
    terms_json=decision.terms_json
)
session.add(policy)

# Update submission status
submission.status = SubmissionStatus.BOUND
session.commit()
```

## Database Schema

### underwriting_submissions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | String(26) | NO | ULID primary key |
| tenant_id | String(26) | NO | Tenant ID |
| status | Enum | NO | Submission status |
| created_by_user_id | String(26) | YES | Creator user ID |
| risk_assessment_id | String(26) | NO | Risk assessment ID |
| risk_run_id | String(26) | YES | Risk run ID |
| evidence_bundle_id | String(26) | YES | Evidence bundle ID |
| requested_coverage_json | JSON | YES | Coverage request |
| corridor_id | String(100) | YES | Corridor ID |
| product_type | String(100) | YES | Product type |
| created_at | DateTime | NO | Creation timestamp |
| updated_at | DateTime | NO | Update timestamp |

### underwriting_decisions

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | String(26) | NO | ULID primary key |
| tenant_id | String(26) | NO | Tenant ID |
| submission_id | String(26) | NO | Submission ID |
| decided_by_user_id | String(26) | YES | Decision maker user ID |
| decision | Enum | NO | Decision type |
| terms_json | JSON | YES | Terms |
| notes | Text | YES | Notes |
| model_version_id | String(26) | YES | Pinned model version |
| risk_run_id | String(26) | YES | Pinned risk run |
| evidence_bundle_id | String(26) | YES | Pinned evidence bundle |
| created_at | DateTime | NO | Creation timestamp |
| updated_at | DateTime | NO | Update timestamp |

### policies

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| id | String(26) | NO | ULID primary key |
| tenant_id | String(26) | NO | Tenant ID |
| policy_number | String(100) | NO | Policy number (unique per tenant) |
| status | Enum | NO | Policy status |
| submission_id | String(26) | YES | Submission ID |
| bound_by_user_id | String(26) | YES | User who bound policy |
| bound_at | DateTime | YES | Binding timestamp |
| effective_from | DateTime | NO | Effective start date |
| effective_to | DateTime | NO | Effective end date |
| model_version_id | String(26) | NO | Pinned model version (RESTRICT) |
| risk_run_id | String(26) | NO | Pinned risk run (RESTRICT) |
| terms_json | JSON | YES | Policy terms |
| created_at | DateTime | NO | Creation timestamp |
| updated_at | DateTime | NO | Update timestamp |

## Files Created

1. ✅ `app/modules/underwriting/models.py` - Model definitions
2. ✅ `app/modules/underwriting/state_machine.py` - State machine implementation
3. ✅ `app/modules/underwriting/__init__.py` - Module exports
4. ✅ `migrations/versions/009_create_underwriting_models.py` - Alembic migration
5. ✅ `UNDERWRITING_MODULE_COMPLETE.md` - This documentation

## Key Features

1. **State Machine**: Enforced workflow with validation
2. **Pinned References**: Immutable references for audit trail
3. **Tenant Isolation**: All operations scoped to tenant
4. **Terminal States**: BOUND, DECLINED, CANCELED are terminal
5. **Precondition Validation**: Transition-specific validations
6. **Policy Protection**: RESTRICT delete on pinned references

## Next Steps

1. **Create Service**: Business logic for underwriting operations
2. **Create Schemas**: Pydantic schemas for API
3. **Create Router**: API endpoints
4. **Add Tests**: Unit and integration tests
5. **Add Notifications**: Email/notification system for status changes

**Underwriting module hoàn thành và sẵn sàng sử dụng!** 🎉
