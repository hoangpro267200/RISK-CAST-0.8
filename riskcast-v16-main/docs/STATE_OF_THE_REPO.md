# RISKCAST v16 - Current Architecture Map

**Generated:** 2024  
**Purpose:** Enterprise-grade upgrade baseline assessment

---

## 📋 Executive Summary

RISKCAST v16 is a FastAPI-based risk analytics engine with a mixed frontend stack (React + Vue + Vanilla JS). The codebase shows evidence of iterative development with multiple engine versions, page versions, and frontend approaches coexisting.

**Current Quality Estimate:** ~6.5/10  
**Target Quality:** 9.5-10/10  
**Upgrade Strategy:** Incremental, non-breaking, engine-first

---

## 🏗️ Entry Points & Routers

### Main Application Entry
- **File:** `app/main.py`
- **FastAPI App:** `app = FastAPI(title="RISKCAST Enterprise AI", version="19.0.0")`
- **Server Runners:**
  - `run.py` - Production (no reload)
  - `dev_run.py` - Development (with reload)
  - `run_server.py` - Alternative runner

### API Routers
1. **`app/api/router.py`** - Main v1 API router
   - Includes: shipment, analysis, transport, cargo, insights, kpi routers
   - Prefix: `/api/v1`

2. **`app/api_ai.py`** - AI Adviser router
   - Prefix: `/api/ai`

3. **`app/api.py`** - Legacy API (backward compatibility)
   - Prefix: `/api` (legacy)

4. **`app/routes/overview.py`** - Overview page router

5. **`app/routes/update_shipment_route_v33.py`** - Shipment update endpoint (PATCH)

6. **`app/routes/ai_endpoints_v33.py`** - AI endpoints (POST)

### Page Routes (in `main.py`)
- `/` → `home.html`
- `/input` → redirects to `/input_v20`
- `/input_v19` → `input/input_v19.html`
- `/input_v20` → `input/input_v20.html` (current)
- `/input_modules_v30` → `input_modules_v30.html`
- `/overview` → redirects to `/summary`
- `/summary` → `summary/summary_v400.html` (current)
- `/results` → React app (served from `dist/index.html`)
- `/dashboard` → `dashboard.html`

---

## 🔧 Engine Versions

### Current Engine Architecture

1. **v16 Engine (Canonical)**
   - **Location:** `app/core/engine/risk_engine_v16.py`
   - **Class:** `EnterpriseRiskEngineV16`
   - **Features:** 13 risk layers, Fuzzy AHP, Monte Carlo, VaR/CVaR
   - **Status:** ✅ Active, production-ready

2. **v14 Engine (Legacy)**
   - **Location:** `app/core/services/risk_service.py` → `run_risk_engine_v14()`
   - **Status:** ⚠️ Still referenced in:
     - `app/main.py` (import)
     - `app/api/v1/risk_routes.py` (used in `/risk/analyze`)
     - `app/api.py` (legacy endpoint)
   - **Action Required:** Create adapter to v16

3. **v15 Engine**
   - **Location:** Not explicitly found (may be in legacy folder)
   - **Status:** ❓ Needs investigation

4. **Engine v2 (Alternative)**
   - **Location:** `app/core/engine_v2/`
   - **Components:** RiskPipeline, LLMReasoner
   - **Status:** ✅ Used in `/api/v1/risk/v2/analyze`

5. **Legacy Code**
   - **Location:** `app/core/legacy/`
   - **Files:**
     - `riskcast_v14_5_climate_upgrade.py`
     - `RISKCAST_v14_5_EXECUTIVE_SUMMARY.py`
     - `riskcast_v14_5_integration_patches.py`
     - `RISKCAST_v14_5_README.py`

### Engine State Management
- **File:** `app/core/engine_state.py`
- **Storage:** In-memory (default) or MySQL (if `USE_MYSQL=true`)
- **Functions:** `get_last_result_v2()`, `set_last_result_v2()`
- **Purpose:** Shared backend state for engine results (engine-first architecture)

---

## 📄 Page Versions

### Input Pages
- **v19:** `templates/input/input_v19.html` (legacy)
- **v20:** `templates/input/input_v20.html` (current, active route)
- **v21:** Referenced in JS files (`static/js/pages/input/input_controller_v21.js`)
- **v30 (Modules):** `templates/input_modules_v30.html`

### Summary/Overview Pages
- **v400:** `templates/summary/summary_v400.html` (current, active route)
- **v100, v200, v300:** Referenced in JS/CSS but templates not found (likely archived)

### Results Page
- **React App:** `src/pages/ResultsPage.tsx` (built to `dist/index.html`)
- **Data Endpoint:** `/results/data` (returns engine results)

---

## 🎨 Frontend Technology Stack

### Primary Stack: React + TypeScript
- **Location:** `src/`
- **Build Tool:** Vite (`vite.config.js`)
- **Entry:** `src/main.tsx` → `src/App.tsx`
- **Pages:** `src/pages/ResultsPage.tsx`
- **Components:** `src/components/` (34 TSX files)
- **Status:** ✅ Active for Results page

### Secondary Stack: Vue.js
- **Location:** `src/features/` (37 Vue files, 31 JS files)
- **Status:** ⚠️ Mixed with React (fragmentation issue)

### Legacy Stack: Vanilla JavaScript
- **Location:** `app/static/js/`
- **Structure:**
  - `v20/` - Input page v20 JS
  - `pages/input/` - Input controllers
  - `summary/` - Summary page JS
  - `core/` - Core modules (state, storage)
- **Status:** ⚠️ Active but fragmented

### Build System
- **Frontend:** Vite (port 3000 in dev, builds to `dist/`)
- **Backend:** FastAPI (port 8000)
- **Package Manager:** npm (package.json)

---

## 💾 State Management

### Frontend State
1. **localStorage**
   - **Key:** `RISKCAST_STATE`
   - **Usage:** Primary storage for shipment state
   - **Files:**
     - `app/static/js/summary/summary_state_sync.js`
     - `app/static/js/pages/input/input_controller_v21.js`
     - `app/static/js/v20/core/StateManager.js`
   - **Status:** ⚠️ No backend sync (data loss risk)

2. **Backend State (Partial)**
   - **File:** `app/core/engine_state.py`
   - **Storage:** In-memory or MySQL
   - **Purpose:** Engine results only (not full shipment state)
   - **Status:** ⚠️ Incomplete (needs full state sync)

3. **Session Storage**
   - **Middleware:** `SessionMiddleware` in `main.py`
   - **Usage:** Shipment state between pages
   - **Key:** `RISKCAST_STATE`, `shipment_state`

### State Flow
```
Input Page → localStorage → Session → Backend (partial) → Results Page
```

**Issue:** No bidirectional sync, clearing browser cache loses data.

---

## 📝 Logging & Error Handling

### Current Setup

1. **Error Handler Middleware**
   - **File:** `app/middleware/error_handler_v2.py`
   - **Class:** `ErrorHandlerMiddleware`
   - **Features:**
     - Standardized error responses
     - Error tracking with unique IDs
     - Logging to `logs/errors.log`
   - **Status:** ✅ Exists but may not be fully wired

2. **Standard Responses**
   - **File:** `app/utils/standard_responses.py`
   - **Class:** `StandardResponse`
   - **Methods:** `success()`, `error()`, `validation_error()`, `server_error()`
   - **Status:** ✅ Exists

3. **Custom Exceptions**
   - **File:** `app/utils/custom_exceptions.py`
   - **Classes:** `RISKCASTException`, `ValidationError`, `RiskCalculationError`, etc.
   - **Status:** ✅ Exists

4. **Enhanced Logger**
   - **File:** `app/utils/logger_enhanced.py`
   - **Status:** ✅ Exists (needs verification of usage)

5. **Legacy Error Handler**
   - **File:** `app/middleware/error_handler.py`
   - **Status:** ⚠️ May conflict with v2

### Current Issues
- Error handler v2 exists but may not be fully integrated
- Inconsistent error response formats across endpoints
- No request_id propagation
- Frontend uses `console.log` instead of unified logger

---

## 🧪 Testing Status

### Test Structure
- **Location:** `tests/`
- **Config:** `pytest.ini`
- **Structure:**
  ```
  tests/
  ├── conftest.py
  ├── integration/
  │   ├── test_api_endpoints.py
  │   └── test_workflow.py
  └── unit/
      ├── test_sanitizer.py
      ├── test_state_management.py
      └── test_validators.py
  ```

### Test Configuration
- **Framework:** pytest
- **Markers:** `unit`, `integration`, `slow`
- **Coverage:** Commented out (needs activation)
- **Status:** ⚠️ Basic tests exist, coverage unknown

### Frontend Tests
- **Framework:** Vitest (configured in `package.json`)
- **Location:** `src/test/`
- **Status:** ⚠️ Minimal tests

---

## 🔒 Security Status

### Current Measures
1. **Security Headers Middleware**
   - **File:** `app/middleware/security_headers.py`
   - **Status:** ✅ Active in `main.py`

2. **CORS Middleware**
   - **Config:** Environment-based origins
   - **Status:** ✅ Active

3. **Session Middleware**
   - **Secret Key:** From env or default (⚠️ needs production secret)

4. **Input Sanitization**
   - **Location:** `app/validators/`
   - **Status:** ✅ Exists (needs verification of usage)

### Issues
- `.env` file handling (needs `.env.example`)
- Hardcoded secrets check required
- SQL injection protection (SQLAlchemy usage needs verification)
- XSS protection (sanitizer tests needed)

---

## 📊 Performance Considerations

### Current State
- **Monte Carlo:** 50k iterations (configurable?)
- **Caching:** No explicit caching layer found
- **Async:** FastAPI async endpoints (partial usage)
- **Database:** MySQL optional (in-memory default)

### Issues
- No caching strategy for repeated requests
- Monte Carlo iterations not configurable by environment
- No background job system for heavy computations

---

## 🗂️ Key Directories

```
riskcast-v16-main/
├── app/
│   ├── api/              # API endpoints (v1)
│   ├── core/
│   │   ├── engine/       # v16 engine (canonical)
│   │   ├── engine_v2/    # Alternative engine v2
│   │   ├── legacy/       # v14/v15 legacy code
│   │   └── services/     # Business services
│   ├── middleware/       # Error handling, security
│   ├── routes/           # Page routers
│   ├── static/           # Vanilla JS frontend
│   ├── templates/        # HTML templates
│   └── utils/            # Standard responses, exceptions
├── src/                  # React + TypeScript frontend
├── tests/                # Test suite
└── docs/                 # Documentation (to be created)
```

---

## 🚨 Critical Issues Identified

1. **Engine Version Sprawl**
   - v14, v15, v16, v2 all coexist
   - No single canonical interface

2. **Frontend Fragmentation**
   - React, Vue, and Vanilla JS all in use
   - No clear strategy

3. **State Management Gaps**
   - localStorage only (no backend sync)
   - Data loss on cache clear

4. **Error Handling Inconsistency**
   - Multiple error handlers
   - No unified response format

5. **Testing Coverage Unknown**
   - Tests exist but coverage not measured
   - No CI/CD mentioned

6. **Documentation Gaps**
   - No developer onboarding guide
   - No decision log
   - No migration strategy

---

## ✅ Strengths

1. **Modern Stack Foundation**
   - FastAPI (async-capable)
   - React + TypeScript for new code
   - Vite build system

2. **Modular Structure**
   - Clear separation of concerns
   - Service layer exists

3. **Security Awareness**
   - Security headers middleware
   - CORS configuration
   - Input validators

4. **Engine-First Architecture**
   - Backend state for engine results
   - Clear data flow

---

## 📈 Upgrade Priorities

1. **Phase 1: Legacy Cleanup** (Highest ROI)
   - Archive old engines/pages
   - Create canonical interface
   - Add adapters

2. **Phase 2: Standardized Responses**
   - Wire error handlers
   - Unified response envelope
   - Request ID propagation

3. **Phase 3: Testing**
   - Fix flaky tests
   - Add engine invariants
   - Integration tests

4. **Phase 4: Security**
   - Secrets management
   - Sanitizer tests
   - CORS hardening

5. **Phase 5: Performance**
   - Caching layer
   - Fast mode
   - Async optimization

6. **Phase 6: State Sync**
   - Backend state endpoints
   - localStorage sync

7. **Phase 7: Frontend Consolidation**
   - Choose primary stack
   - Migration strategy

8. **Phase 8: Documentation**
   - Developer guides
   - Decision log
   - Deployment docs

---

**Next Steps:** See `UPGRADE_ROADMAP.md` for detailed implementation plan.

