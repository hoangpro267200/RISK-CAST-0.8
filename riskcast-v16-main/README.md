# RISKCAST V3 - Enterprise Insurance Risk Intelligence Platform

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- pip or pipenv

### 1. Install Dependencies
```bash
cd riskcast-v16-main
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` (or use existing `.env` for development):
```bash
# The existing .env is configured for development:
# - SQLite database (./riskcast.db)
# - Auth enabled with dev secrets
# - Debug mode ON
```

### 3. Start the Server
```bash
python start_server.py
```

The server will start at `http://127.0.0.1:8000`

### 4. Verify Installation
- **Health Check**: http://127.0.0.1:8000/health
- **API Docs**: http://127.0.0.1:8000/docs
- **Root Info**: http://127.0.0.1:8000/
- **Metrics**: http://127.0.0.1:8000/metrics

## API Endpoints

### Health & Status
| Endpoint | Description |
|----------|-------------|
| `GET /health` | Basic health check |
| `GET /api/v3/health/live` | Kubernetes liveness probe |
| `GET /api/v3/health/ready` | Kubernetes readiness probe |
| `GET /metrics` | Prometheus metrics |

### Core API (v3)
| Endpoint | Description |
|----------|-------------|
| `GET /api/v3/risk-assessments` | List risk assessments |
| `POST /api/v3/risk-assessments` | Create risk assessment |
| `GET /api/v3/risk/runs` | List risk runs |
| `POST /api/v3/risk/runs` | Create risk run |

### GraphQL
- **Endpoint**: `POST /graphql`
- **Playground**: http://127.0.0.1:8000/graphql (when DEBUG=true)

## Environment Variables

### Required for Development
```env
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./riskcast.db
```

### Optional Features
```env
# Auth System
AUTH_ENABLED=true
SESSION_SECRET=<your-secret-min-32-chars>

# Observability (optional)
ENABLE_OPENTELEMETRY=false
ENABLE_PROMETHEUS=true

# External APIs (optional)
TOMORROW_IO_API_KEY=<key>
MARINE_TRAFFIC_API_KEY=<key>
PROJECT44_API_KEY=<key>
```

## Database

### Development (SQLite)
SQLite database is auto-created at `./riskcast.db`. No additional setup needed.

### Production (PostgreSQL)
```env
DATABASE_URL=postgresql://user:password@host:5432/riskcast
```

Run migrations:
```bash
alembic upgrade head
```

## Architecture

```
app/
├── api/v3/           # REST API endpoints
├── graphql/          # GraphQL schema and resolvers
├── modules/          # Domain modules (tenancy, auth, risk, etc.)
│   ├── audit_ledger/
│   ├── claims/
│   ├── evidence/
│   ├── identity_access/
│   ├── model_versioning/
│   ├── observability/
│   ├── parametric/
│   ├── rbac_policy/
│   ├── risk_assessments/
│   ├── risk_engine_v3/
│   ├── risk_runs/
│   ├── tenancy/
│   └── underwriting/
├── core/             # Core business logic
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/         # Business services
├── middleware/       # FastAPI middleware
├── monitoring/       # Metrics and tracing
└── workers/          # Background workers
```

## Troubleshooting

### Server Won't Start

1. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Port already in use**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /F /PID <pid>
   
   # Linux/Mac
   lsof -i :8000
   kill -9 <pid>
   ```

3. **Database connection error**
   - For SQLite: File permission issues
   - For PostgreSQL: Check connection string

### Import Errors

Most import errors are handled gracefully. Check server logs for warnings about optional modules.

Common optional dependencies:
```bash
# OpenTelemetry (for tracing)
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi

# Redis (for caching/rate limiting)
pip install redis[hiredis]

# PostgreSQL (for production)
pip install asyncpg psycopg2-binary
```

### Pydantic Warnings

If you see Pydantic V2 deprecation warnings, they don't affect functionality. These will be fixed in a future update.

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_risk_engine.py

# Run with coverage
pytest --cov=app tests/
```

## Docker (Production)

```bash
# Build
docker build -t riskcast-api .

# Run
docker-compose up -d
```

## API Examples

### Health Check
```bash
curl http://127.0.0.1:8000/health
# {"status":"healthy","version":"3.0.0","environment":"development"}
```

### Get API Info
```bash
curl http://127.0.0.1:8000/
# {"name":"RISKCAST V3","version":"3.0.0",...}
```

### GraphQL Query (example)
```bash
curl -X POST http://127.0.0.1:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'
```

## License

Proprietary - RISKCAST V3
