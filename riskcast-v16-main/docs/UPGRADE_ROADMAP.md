# RISKCAST v16 → Enterprise-Grade Upgrade Roadmap

**Target Quality:** 9.5-10/10  
**Strategy:** Incremental, non-breaking, engine-first  
**Timeline:** Phased approach with rollback capability

---

## 🎯 Upgrade Principles

1. **No Breaking Changes** - All existing endpoints must continue to work
2. **Engine-First** - Core engine is the source of truth
3. **Incremental** - Small, testable commits
4. **Traceable** - Every decision documented
5. **Backward Compatible** - Legacy code isolated, not deleted

---

## 📋 Phase Overview

| Phase | Focus | Risk | Effort | Rollback |
|-------|-------|------|--------|----------|
| 0 | Documentation | Low | 2h | N/A |
| 1 | Legacy Cleanup | Medium | 8h | Easy (adapters) |
| 2 | Standardized Responses | Low | 6h | Easy (middleware) |
| 3 | Testing Upgrade | Medium | 12h | Easy (tests) |
| 4 | Security Hardening | Low | 4h | Easy (config) |
| 5 | Performance | Medium | 8h | Easy (feature flags) |
| 6 | State Management | Medium | 6h | Medium (data migration) |
| 7 | Frontend Consolidation | High | 10h | Hard (requires migration) |
| 8 | Documentation & DX | Low | 4h | N/A |

**Total Estimated Effort:** ~60 hours  
**Recommended Order:** 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

---

## Phase 0: Documentation & Context ✅

**Status:** In Progress  
**Deliverables:**
- ✅ `docs/STATE_OF_THE_REPO.md` - Architecture map
- ✅ `docs/UPGRADE_ROADMAP.md` - This document

**Acceptance:**
- [x] Architecture map complete
- [x] Upgrade roadmap documented

---

## Phase 1: Legacy Cleanup (HIGHEST ROI)

**Objective:** Eliminate version sprawl, preserve history, reduce duplication

### 1A: Create Archive Structure

**Tasks:**
1. Create `archive/` folder structure:
   ```
   archive/
   ├── engines/
   │   ├── v14/
   │   └── v15/
   ├── pages/
   │   ├── input_v19/
   │   └── summary_v100/ (if exists)
   └── README.md
   ```

2. Move legacy code:
   - `app/core/legacy/` → `archive/engines/v14/`
   - `app/core/services/risk_service.py` (v14 function) → `archive/engines/v14/`
   - `templates/input/input_v19.html` → `archive/pages/input_v19/`

3. Keep imports working via thin adapters (see 1C)

**Acceptance:**
- [ ] Archive folder created
- [ ] Legacy code moved (not deleted)
- [ ] Imports still work

### 1B: Canonical Engine Interface

**Tasks:**
1. Create `app/core/engine/interface.py`:
   ```python
   from dataclasses import dataclass
   from typing import Dict, List, Optional, Any
   
   @dataclass
   class RiskRequest:
       """Standardized risk calculation request"""
       shipment_data: Dict[str, Any]
       # ... normalized fields
   
   @dataclass
   class LayerResult:
       """Single risk layer result"""
       layer_name: str
       score: float
       confidence: float
       evidence: List[EvidenceItem]
   
   @dataclass
   class RiskResult:
       """Complete risk calculation result"""
       overall_score: float
       layers: List[LayerResult]
       confidence: ConfidenceResult
       # ... other fields
   ```

2. Make `EnterpriseRiskEngineV16` implement this interface

3. Add type hints and validation

**Acceptance:**
- [ ] Interface defined with dataclasses/Pydantic
- [ ] v16 engine implements interface
- [ ] Type hints complete

### 1C: Legacy Adapters

**Tasks:**
1. Create `app/core/adapters/legacy_adapter.py`:
   ```python
   def adapt_v14_to_canonical(v14_request: Dict) -> RiskRequest:
       """Convert v14 format to canonical"""
       # Mapping logic
   
   def adapt_canonical_to_v14(canonical_result: RiskResult) -> Dict:
       """Convert canonical to v14 format for backward compat"""
       # Mapping logic
   ```

2. Update `run_risk_engine_v14()` to:
   - Accept v14 format
   - Convert to canonical via adapter
   - Call canonical engine
   - Convert result back to v14 format
   - Log deprecation warning

3. Update all v14 call sites to use adapter

**Acceptance:**
- [ ] All v14 endpoints still work
- [ ] Deprecation warnings logged
- [ ] No UI breakage

### 1D: Deprecation Documentation

**Tasks:**
1. Create `docs/DEPRECATION.md`:
   - List all deprecated routes/pages
   - Timeline for removal
   - Migration guide

2. Add deprecation headers to legacy endpoints:
   ```python
   @router.post("/risk/analyze", deprecated=True)
   ```

**Acceptance:**
- [ ] DEPRECATION.md created
- [ ] Deprecation headers added
- [ ] Migration guide included

**Rollback:** Remove adapters, restore original imports

---

## Phase 2: Standardized Responses & Error Handling

**Objective:** Consistent API responses, production-grade logs

### 2A: Wire Error Handlers

**Tasks:**
1. Verify `error_handler_v2.py` is active in `main.py` ✅ (already active)

2. Replace ad-hoc try/except with custom exceptions:
   - Use `ValidationError` for validation failures
   - Use `RiskCalculationError` for engine errors
   - Use `StandardResponse` helpers

3. Replace `console.log` in frontend with logger wrapper:
   ```javascript
   // src/utils/logger.ts
   export const logger = {
     info: (msg) => console.log(`[INFO] ${msg}`),
     error: (msg) => console.error(`[ERROR] ${msg}`),
     // ... structured logging
   };
   ```

**Acceptance:**
- [ ] All endpoints use StandardResponse
- [ ] Frontend uses logger wrapper
- [ ] Error logs are structured

### 2B: Standard Response Envelope

**Tasks:**
1. Update `StandardResponse` to match target format:
   ```python
   {
     "success": bool,
     "data": ...,
     "error": { "code": str, "message": str, "details": any } | null,
     "meta": { "request_id": str, "ts": iso, "version": "v16" }
   }
   ```

2. Add helpers:
   ```python
   def ok(data, request_id=None) -> JSONResponse:
       """Success response with envelope"""
   
   def fail(code, message, details=None, request_id=None) -> JSONResponse:
       """Error response with envelope"""
   ```

3. Update all API endpoints to use envelope

**Acceptance:**
- [ ] All endpoints return standard envelope
- [ ] `/docs` shows consistent schemas
- [ ] Backward compatibility maintained (old fields temporarily)

### 2C: Request ID Propagation

**Tasks:**
1. Create middleware `app/middleware/request_id.py`:
   ```python
   class RequestIDMiddleware:
       async def dispatch(self, request, call_next):
           request_id = str(uuid.uuid4())
           request.state.request_id = request_id
           response = await call_next(request)
           response.headers["X-Request-ID"] = request_id
           return response
   ```

2. Include request_id in:
   - Response meta
   - Log entries
   - Error responses

3. Add to logger context

**Acceptance:**
- [ ] Request ID in all responses
- [ ] Request ID in all logs
- [ ] Traceable request flow

**Rollback:** Remove middleware, keep old response format

---

## Phase 3: Testing Upgrade

**Objective:** Protect refactors, validate engine correctness

### 3A: Fix Test Infrastructure

**Tasks:**
1. Ensure pytest runs clean:
   ```bash
   pytest -q
   ```

2. Fix flaky tests (if any)

3. Add test scripts:
   - `scripts/test.sh` (Unix)
   - `scripts/test.ps1` (Windows)

4. Activate coverage:
   ```ini
   # pytest.ini
   addopts = --cov=app --cov-report=html --cov-report=term
   ```

**Acceptance:**
- [ ] `pytest -q` passes
- [ ] Test scripts work
- [ ] Coverage report generated

### 3B: Engine Invariant Tests

**Tasks:**
1. Create `tests/unit/test_engine_invariants.py`:
   ```python
   def test_risk_score_bounds():
       """Risk score must be in [0, 100]"""
   
   def test_monotonicity():
       """Worse inputs should not reduce risk"""
   
   def test_layer_results_structure():
       """All 13 layers return LayerResult with required fields"""
   
   def test_confidence_bounds():
       """Confidence in [0, 1] or [0, 100]"""
   
   def test_deterministic_seeding():
       """Monte Carlo with same seed produces same results"""
   ```

2. Use seeded RNG for Monte Carlo tests

**Acceptance:**
- [ ] All invariants tested
- [ ] Tests pass consistently
- [ ] Coverage >50% for `app/core/engine`

### 3C: Integration Tests

**Tasks:**
1. Update `tests/integration/test_api_endpoints.py`:
   - Test `/api/v1/validate`
   - Test `/api/v1/summary`
   - Test `/api/v1/results`
   - Test `/api/v1/risk/v2/analyze`
   - Validate response envelope

2. Use `TestClient` from FastAPI

**Acceptance:**
- [ ] All key endpoints tested
- [ ] Response envelope validated
- [ ] Integration tests pass

### 3D: Frontend Tests (Optional)

**Tasks:**
1. Add minimal smoke tests for React components
2. Add lint step to CI (if exists)

**Acceptance:**
- [ ] Frontend tests run
- [ ] Lint passes

**Rollback:** Revert test changes, keep old tests

---

## Phase 4: Security Hardening

**Objective:** Ship safely

### 4A: Secrets Management

**Tasks:**
1. Verify `.env` is in `.gitignore` ✅

2. Create `.env.example`:
   ```env
   ANTHROPIC_API_KEY=your_key_here
   SESSION_SECRET_KEY=change_in_production
   USE_MYSQL=false
   DEBUG=false
   ENVIRONMENT=development
   ```

3. Scan for hardcoded keys:
   ```bash
   grep -r "api_key\|secret\|password" --exclude-dir=node_modules
   ```

4. Remove any hardcoded secrets

**Acceptance:**
- [ ] `.env.example` exists
- [ ] No secrets in repo
- [ ] All secrets from env

### 4B: Input Sanitization

**Tasks:**
1. Verify sanitizer usage at API boundaries:
   - Check `app/validators/` usage
   - Ensure all endpoints use validators

2. Add sanitizer tests:
   ```python
   def test_sql_injection_prevention():
       """Test SQLi vectors"""
   
   def test_xss_prevention():
       """Test XSS vectors"""
   ```

3. Verify DB layer uses parameterized queries (SQLAlchemy)

**Acceptance:**
- [ ] Sanitizer tests pass
- [ ] All endpoints use validators
- [ ] DB queries parameterized

### 4C: CORS & Security Headers

**Tasks:**
1. Tighten CORS defaults for production:
   ```python
   allowed_origins = os.getenv(
       "ALLOWED_ORIGINS",
       "http://localhost:8000" if dev else ""  # Empty in prod
   ).split(",")
   ```

2. Document in `SECURITY.md`:
   - CORS configuration
   - Security headers
   - Environment variables

**Acceptance:**
- [ ] CORS tightened for prod
- [ ] Security headers verified
- [ ] SECURITY.md updated

**Rollback:** Revert env changes, keep old config

---

## Phase 5: Performance & Monte Carlo

**Objective:** Keep 50k iterations feasible

### 5A: Caching Strategy

**Tasks:**
1. Create `app/core/utils/cache.py`:
   ```python
   from functools import lru_cache
   import hashlib
   import json
   
   def cache_key_from_request(request: RiskRequest) -> str:
       """Generate cache key from normalized request"""
       normalized = normalize_request(request)
       return hashlib.md5(json.dumps(normalized, sort_keys=True)).hexdigest()
   
   # In-memory cache (default)
   _cache = {}
   
   # Optional Redis (if env set)
   if os.getenv("USE_REDIS") == "true":
       import redis
       cache_client = redis.Redis(...)
   ```

2. Add caching to engine:
   - Check cache before calculation
   - Store result after calculation
   - TTL configurable

**Acceptance:**
- [ ] Cache key from normalized request
- [ ] Same inputs return cached result
- [ ] TTL configurable

### 5B: Fast Mode

**Tasks:**
1. Add environment variable:
   ```env
   MC_ITERATIONS=50000  # Default
   MC_ITERATIONS_DEV=5000  # Dev mode
   ```

2. Update engine to use configurable iterations:
   ```python
   iterations = int(os.getenv("MC_ITERATIONS", 50000))
   if os.getenv("ENVIRONMENT") == "development":
       iterations = int(os.getenv("MC_ITERATIONS_DEV", 5000))
   ```

3. Include `meta.iterations_used` in response

**Acceptance:**
- [ ] Iterations configurable
- [ ] Fast mode works in dev
- [ ] Results include iterations_used

### 5C: Async Option (Future)

**Tasks:**
1. If time permits, add background job system:
   - `/api/v1/analyze/async` → returns `job_id`
   - `/api/v1/jobs/{job_id}` → polling endpoint

2. Otherwise, leave for Phase 2

**Acceptance:**
- [ ] Async endpoint works (if implemented)
- [ ] Polling endpoint works (if implemented)

**Rollback:** Disable caching, revert to fixed iterations

---

## Phase 6: State Management Sync

**Objective:** Prevent data loss, unify source of truth

### 6A: Backend State Endpoints

**Tasks:**
1. Create `app/api/v1/state_routes.py`:
   ```python
   @router.get("/state/{shipment_id}")
   async def get_state(shipment_id: str):
       """Get shipment state from backend"""
   
   @router.put("/state/{shipment_id}")
   async def save_state(shipment_id: str, state: Dict):
       """Save shipment state to backend"""
   ```

2. Store in DB or file-based initially:
   - Use existing MySQL if available
   - Fallback to file-based storage

3. Add `updated_at` timestamp

**Acceptance:**
- [ ] GET endpoint returns state
- [ ] PUT endpoint saves state
- [ ] Timestamps tracked

### 6B: Frontend Sync

**Tasks:**
1. Update frontend state manager:
   - On load: Check backend first, fallback to localStorage
   - On edit: Debounce save to backend
   - Conflict strategy: Last-write-wins with `updated_at`

2. Update `app/static/js/core/storage.js`:
   ```javascript
   async function loadState(shipmentId) {
     // Try backend first
     const backend = await fetch(`/api/v1/state/${shipmentId}`);
     if (backend.ok) {
       return await backend.json();
     }
     // Fallback to localStorage
     return loadFromLocalStorage();
   }
   ```

**Acceptance:**
- [ ] Backend-first loading
- [ ] Debounced saves
- [ ] Conflict resolution documented

**Rollback:** Revert frontend changes, keep localStorage only

---

## Phase 7: Frontend Stack Consolidation

**Objective:** Stop fragmentation

### 7A: Choose Primary Stack

**Tasks:**
1. Decision: **React + TypeScript** (already used for Results page)

2. Create `docs/FRONTEND_STRATEGY.md`:
   - What is legacy (Vue, Vanilla JS)
   - What is canonical (React + TS)
   - Migration plan

3. Add rule: New UI features must use React + TS

**Acceptance:**
- [ ] Strategy documented
- [ ] No new Vue files
- [ ] No new Vanilla JS modules (unless necessary)

### 7B: Migration Plan

**Tasks:**
1. Identify Vue files to migrate:
   - `src/features/` (37 Vue files)
   - Prioritize by usage

2. Create migration guide:
   - Step-by-step Vue → React conversion
   - Component mapping

3. Gradual migration (not big-bang)

**Acceptance:**
- [ ] Migration guide created
- [ ] At least one Vue component migrated (proof of concept)

### 7C: Build Pipeline

**Tasks:**
1. Ensure Vite build works:
   ```bash
   npm run build
   ```

2. Add lint step:
   ```json
   "lint": "eslint . --ext .ts,.tsx"
   ```

3. Document in `DEVELOPMENT.md`

**Acceptance:**
- [ ] Build works
- [ ] Lint passes
- [ ] Docs updated

**Rollback:** Keep Vue files, no migration

---

## Phase 8: Documentation & Developer Experience

**Objective:** Onboarding in <30 minutes

### 8A: Update Existing Docs

**Tasks:**
1. Update `DEVELOPMENT.md`:
   - Setup instructions
   - Run instructions
   - Environment variables
   - Test instructions

2. Update `DEPLOYMENT.md`:
   - Production environment
   - Reverse proxy config
   - Database setup

**Acceptance:**
- [ ] DEVELOPMENT.md complete
- [ ] DEPLOYMENT.md complete

### 8B: New Documentation

**Tasks:**
1. Create `docs/DECISION_LOG.md`:
   - Document architectural decisions
   - Rationale for choices
   - Alternatives considered

2. Create `docs/CHANGELOG_UPGRADE.md`:
   - Summary of all changes
   - Breaking changes (if any)
   - Migration notes

**Acceptance:**
- [ ] Decision log created
- [ ] Changelog created

### 8C: Developer Scripts

**Tasks:**
1. Create scripts:
   - `scripts/dev.sh` / `scripts/dev.ps1`
   - `scripts/lint.sh` / `scripts/lint.ps1`
   - `scripts/format.sh` / `scripts/format.ps1`
   - `scripts/test.sh` / `scripts/test.ps1`

2. Add pre-commit hooks (optional):
   - Lint on commit
   - Format on commit

**Acceptance:**
- [ ] Scripts created
- [ ] Scripts work on Windows and Unix
- [ ] Pre-commit hooks optional

**Rollback:** N/A (docs only)

---

## 📝 Commit Strategy

Each phase should be committed separately:

```
feat(core): canonical engine interface
refactor(legacy): move legacy to archive with adapters
test(core): add engine invariants
chore(security): env + sanitizer tests
perf(engine): caching + fast mode
feat(state): backend state sync
docs: strategy and onboarding
```

---

## ✅ Final Acceptance Criteria

- [ ] All existing endpoints work
- [ ] No UI breakage
- [ ] Tests pass (>50% coverage on core)
- [ ] Documentation complete
- [ ] Security hardened
- [ ] Performance acceptable
- [ ] State sync working
- [ ] Frontend strategy clear

---

## 🚨 Safety Rules

1. **Never remove a route/page without deprecation + adapter**
2. **No breaking response format changes without versioning**
3. **Keep UI visual behavior intact**
4. **Prefer small PRs; keep changes local**
5. **Every change must pass tests before commit**

---

**Status:** Phase 0 Complete ✅  
**Next:** Phase 1 (Legacy Cleanup)

