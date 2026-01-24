# RISKCAST V3 - Modular Monolith Architecture

## Overview

RISKCAST V3 is a **modular monolith** FastAPI application designed for **insurance-grade** risk intelligence. This architecture provides:

- **Modularity**: Clear separation of concerns with domain modules
- **Scalability**: Can be split into microservices later if needed
- **Maintainability**: Each module is self-contained with models, schemas, services, repositories
- **Insurance-Grade**: Deterministic calculations, audit trails, model versioning

## Architecture

### Module Structure

Each module follows a consistent structure:

```
modules/<module_name>/
├── __init__.py
├── models.py      # SQLAlchemy models
├── schemas.py     # Pydantic schemas
├── service.py     # Business logic
├── repository.py  # Data access layer
├── router.py      # FastAPI routes (if needed)
└── exceptions.py  # Module-specific exceptions
```

### Modules

1. **tenancy** - Multi-tenant isolation and tenant management
2. **identity_access** - Authentication and user management
3. **rbac_policy** - Role-based access control
4. **risk_assessments** - Risk assessment storage
5. **risk_runs** - Risk calculation execution tracking
6. **risk_engine_v3** - Deterministic risk calculation engine
7. **audit_ledger** - Immutable audit trail
8. **observability** - Logging, metrics, tracing
9. **model_versioning** - Risk model version management
10. **evidence** - Evidence attachment system
11. **underwriting** - Underwriting workflows
12. **claims** - Insurance claims management
13. **parametric** - Parametric insurance triggers

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

### 3. Initialize Database

```bash
alembic upgrade head
```

### 4. Run Application

```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest tests/
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
