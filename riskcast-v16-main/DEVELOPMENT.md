# Development Guide

## Project Structure

```
riskcast-v16-main/
├── app/                    # Backend application
│   ├── api/               # API endpoints
│   ├── core/              # Core business logic
│   ├── models/            # Data models
│   ├── templates/         # HTML templates
│   ├── static/            # Static files (CSS, JS)
│   └── main.py            # FastAPI app entry point
├── tests/                 # Test suite
├── logs/                  # Application logs
└── requirements.txt       # Python dependencies
```

## Development Workflow

### 1. Starting Development Server

**Quick Start (Recommended):**
```bash
# Unix/Linux/Mac
./scripts/dev.sh

# Windows PowerShell
.\scripts\dev.ps1
```

**Manual Start:**
```bash
# Activate virtual environment
source venv/bin/activate  # Windows: venv\Scripts\activate

# Backend only
python dev_run.py  # Development mode with reload
# OR
python run.py      # Production mode

# Frontend (separate terminal)
npm run dev        # Vite dev server on port 3000
```

**Access Points:**
- Backend: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/docs
- Frontend: http://localhost:3000 (if running)

### 2. Running Tests

**Quick Start:**
```bash
# Unix/Linux/Mac
./scripts/test.sh

# Windows PowerShell
.\scripts\test.ps1
```

**Manual:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/unit/test_sanitizer.py::TestSanitizeString

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/
```

### 3. Code Quality Checks

**Quick Start:**
```bash
# Linting
./scripts/lint.sh      # Unix/Linux/Mac
.\scripts\lint.ps1     # Windows PowerShell

# Formatting
./scripts/format.sh    # Unix/Linux/Mac
.\scripts\format.ps1    # Windows PowerShell
```

**Manual:**
```bash
# Python linting
flake8 app/ --max-line-length=120
# OR
ruff check app/

# Python formatting
black app/ --line-length=120

# TypeScript/JavaScript linting
npm run lint

# TypeScript type checking
npm run typecheck
```

## Key Technologies

### Backend
- **FastAPI** - Web framework
- **SQLAlchemy** - ORM (if using database)
- **Pydantic** - Data validation
- **NumPy/SciPy** - Risk calculations

### Frontend
- **React + TypeScript** - Canonical stack (Results page, new features)
- **Vue.js** - Legacy (risk-intelligence features, maintain only)
- **Vanilla JavaScript** - Legacy (input/summary pages, maintain only)

**See `docs/FRONTEND_STRATEGY.md` for frontend stack strategy.**

## Code Organization

### Backend Structure

- `app/core/engine/` - Risk calculation engines
- `app/core/services/` - Business logic services
- `app/api/` - API endpoints (versioned)
- `app/models/` - Data models
- `app/middleware/` - Middleware (error handling, security, etc.)

### Frontend Structure (v20)

- `app/static/js/v20/core/` - Core controllers
- `app/static/js/v20/modules/` - Feature modules
- `app/static/js/v20/ui/` - UI components
- `app/static/js/v20/effects/` - Visual effects

## State Management

### Frontend State

- Primary: `localStorage['RISKCAST_STATE']`
- Backup: `localStorage['rc-input-state']` (v20)
- State format: See `BAO_CAO_TRANG_INPUT.md` for details

### Backend State

- **State Sync API:** `/api/v1/state/{shipment_id}` (GET/PUT)
- File-based storage: `data/state/` (default)
- MySQL storage: Optional (if `USE_MYSQL=true`)
- Session-based: For multi-user (legacy)
- **See `docs/STATE_SYNC_API.md` for API documentation**

## API Endpoints

### Main Routes

- `GET /` - Home page
- `GET /input_v20` - Input page
- `GET /summary` - Summary page
- `GET /results` - Results page (requires build)

### API Routes

**Risk Analysis:**
- `POST /api/v1/risk/v2/analyze` - Risk analysis (canonical, recommended)
- `POST /api/v1/risk/analyze` - Risk analysis (deprecated, v14 adapter)

**State Management:**
- `GET /api/v1/state/{shipment_id}` - Get shipment state
- `PUT /api/v1/state/{shipment_id}` - Save shipment state
- `POST /api/v1/state` - Create new state
- `GET /api/v1/state` - List recent shipments

**Documentation:**
- `GET /docs` - API documentation (Swagger)
- `GET /redoc` - Alternative API docs (ReDoc)

## Environment Variables

See `.env.example` for required variables.

**Required:**
- `ANTHROPIC_API_KEY` - For AI features

**Optional:**
- `ENVIRONMENT` - development/staging/production (default: development)
- `DEBUG` - Enable debug mode (default: false)
- `SESSION_SECRET_KEY` - Session secret (change in production!)
- `ALLOWED_ORIGINS` - CORS origins (required in production)
- `DATABASE_URL` - Database connection string
- `USE_MYSQL` - Use MySQL for state storage (default: false)
- `MC_ITERATIONS` - Monte Carlo iterations (default: 50000)
- `MC_ITERATIONS_DEV` - Dev iterations (default: 5000)
- `CACHE_ENABLED` - Enable caching (default: true)
- `CACHE_TTL` - Cache TTL in seconds (default: 3600)
- `USE_REDIS` - Use Redis for caching (default: false)

**See `.env.example` for all available variables.**

## Common Tasks

### Adding a New Feature

1. Create feature branch
2. Implement feature
3. Add tests
4. Update documentation
5. Create PR

### Debugging

1. Check logs in `logs/` directory
2. Enable debug mode: `DEBUG=True` in `.env`
3. Use `print()` statements (remove before commit)
4. Use debugger: `import ipdb; ipdb.set_trace()`

### Database Migrations

If using database:

```bash
# Generate migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Troubleshooting

### Server won't start

- Check Python version (3.9+)
- Check dependencies: `pip install -r requirements.txt`
- Check `.env` file exists
- Check port 8000 is not in use

### Tests failing

- Check virtual environment is activated
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Check test data is correct

### Import errors

- Check Python path includes project root
- Check virtual environment has correct packages
- Try: `python -m pytest` instead of `pytest`

## Best Practices

1. **Write tests** - Especially for new features
2. **Document code** - Add docstrings to functions
3. **Follow style guide** - PEP 8 for Python
4. **Commit often** - Small, logical commits
5. **Review code** - Self-review before PR

## Developer Scripts

All scripts are in `scripts/` directory:

**Development:**
- `scripts/dev.sh` / `scripts/dev.ps1` - Start backend + frontend dev servers

**Testing:**
- `scripts/test.sh` / `scripts/test.ps1` - Run tests with coverage

**Code Quality:**
- `scripts/lint.sh` / `scripts/lint.ps1` - Run linters
- `scripts/format.sh` / `scripts/format.ps1` - Format code

## Documentation

- `docs/STATE_OF_THE_REPO.md` - Architecture overview
- `docs/UPGRADE_ROADMAP.md` - Upgrade plan
- `docs/FRONTEND_STRATEGY.md` - Frontend stack strategy
- `docs/DEPRECATION.md` - Deprecated endpoints
- `docs/DECISION_LOG.md` - Architectural decisions
- `docs/STATE_SYNC_API.md` - State sync API docs
- `docs/CHANGELOG_UPGRADE.md` - Upgrade changelog

## Getting Help

- Check existing documentation in `docs/`
- Review code examples in the codebase
- Check `docs/DECISION_LOG.md` for architectural rationale
- Open an issue for questions
- Check FastAPI docs: https://fastapi.tiangolo.com/

---

**Last Updated:** 2024  
**Version:** v16 (Enterprise Upgrade)


