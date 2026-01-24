# RISKCAST V3 - Modular Monolith Architecture

## Cấu Trúc Thư Mục

```
riskcast-v16-main/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application settings (Pydantic)
│   ├── database.py          # Database connection and session management
│   │
│   ├── modules/             # Domain modules (modular monolith)
│   │   ├── __init__.py
│   │   │
│   │   ├── tenancy/         # Multi-tenant isolation
│   │   │   ├── __init__.py
│   │   │   ├── models.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   ├── router.py
│   │   │   └── exceptions.py
│   │   │
│   │   ├── identity_access/ # Authentication & user management
│   │   ├── rbac_policy/     # Role-based access control
│   │   ├── risk_assessments/ # Risk assessment storage
│   │   ├── risk_runs/       # Risk calculation execution tracking
│   │   ├── risk_engine_v3/  # Deterministic risk calculation engine
│   │   ├── audit_ledger/    # Immutable audit trail
│   │   ├── observability/   # Logging, metrics, tracing
│   │   ├── model_versioning/ # Risk model version management
│   │   ├── evidence/        # Evidence attachment system
│   │   ├── underwriting/    # Underwriting workflows
│   │   ├── claims/          # Insurance claims management
│   │   └── parametric/      # Parametric insurance triggers
│   │
│   ├── shared/              # Shared utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py    # Shared exception classes
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   └── schemas.py       # Shared Pydantic schemas
│   │
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   └── v3/              # API v3
│   │       └── __init__.py  # Main v3 router (includes all module routers)
│   │
│   └── workers/             # Background workers (Celery, etc.)
│       └── __init__.py
│
├── migrations/              # Alembic database migrations
│   ├── env.py
│   └── versions/
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
│
├── alembic.ini              # Alembic configuration
├── requirements.txt         # Python dependencies
└── README_V3.md            # Documentation
```

## Module Pattern

Mỗi module tuân theo pattern nhất quán:

### 1. Models (`models.py`)
- SQLAlchemy models
- Database schema definitions
- Relationships

### 2. Schemas (`schemas.py`)
- Pydantic schemas
- Request/Response models
- Validation rules

### 3. Repository (`repository.py`)
- Data access layer
- Database queries
- CRUD operations

### 4. Service (`service.py`)
- Business logic
- Orchestration
- Domain rules

### 5. Router (`router.py`)
- FastAPI routes
- API endpoints
- Request/Response handling

### 6. Exceptions (`exceptions.py`)
- Module-specific exceptions
- Error handling

## Key Features

### Insurance-Grade Requirements

1. **Deterministic Calculations**
   - Random seed management
   - Reproducible risk scores

2. **Audit Trail**
   - Immutable audit ledger
   - Blockchain-style chain integrity

3. **Model Versioning**
   - Versioned risk models
   - Calibration tracking

4. **Multi-Tenancy**
   - Tenant isolation
   - Per-tenant configurations

5. **RBAC**
   - Role-based access control
   - Permission system

## API Structure

All API endpoints are under `/api/v3`:

- `/api/v3/tenants` - Tenant management
- `/api/v3/auth` - Authentication
- `/api/v3/rbac` - Role and permission management
- `/api/v3/risk-assessments` - Risk assessments
- `/api/v3/risk-runs` - Risk calculation runs
- `/api/v3/risk-engine` - Risk calculation
- `/api/v3/audit` - Audit trail
- `/api/v3/observability/metrics` - Prometheus metrics
- `/api/v3/model-versions` - Model versioning
- `/api/v3/evidence` - Evidence management
- `/api/v3/underwriting` - Underwriting workflows
- `/api/v3/claims` - Claims management
- `/api/v3/parametric` - Parametric insurance

## Database Models

### Core Models

- `Tenant` - Multi-tenant organizations
- `User` - User accounts
- `Session` - User sessions
- `Role` - RBAC roles
- `Permission` - RBAC permissions
- `UserRole` - User-role assignments

### Risk Models

- `RiskAssessment` - Risk assessment results
- `RiskRun` - Risk calculation execution
- `RiskModelVersion` - Model version configuration

### Insurance Models

- `UnderwritingDecision` - Underwriting decisions
- `Claim` - Insurance claims
- `ParametricTrigger` - Parametric triggers

### Compliance Models

- `AuditLedger` - Immutable audit trail
- `Evidence` - Evidence attachments

## Configuration

All configuration is managed through `app/config.py` using Pydantic Settings:

- Environment variables
- Type validation
- Default values
- Production safety checks

## Next Steps

1. Implement actual risk calculation logic in `risk_engine_v3/service.py`
2. Add real-time data integration for parametric triggers
3. Implement carrier API adapters
4. Add comprehensive test coverage
5. Set up CI/CD pipeline
