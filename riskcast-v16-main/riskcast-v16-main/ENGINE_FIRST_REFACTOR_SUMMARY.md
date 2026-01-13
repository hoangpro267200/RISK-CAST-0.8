# ENGINE-FIRST Architecture Refactor - Data Flow Fix

## 🎯 Goal
Ensure Results page ALWAYS renders data that has passed through the CORE RISK ENGINE, not from localStorage/sessionStorage.

## ❌ Previous Problem

**Architecture Violation:**
- Summary page calls `POST /api/v1/risk/v2/analyze` → engine runs correctly ✅
- Engine result is saved to localStorage (`RISKCAST_RESULTS_V2`, `RISKCAST_SUMMARY_STATE`) ✅
- Results page tries to call `GET /results/data` ❌
- BUT `/results/data` returns `LAST_RESULT` (global variable)
- `LAST_RESULT` is ONLY set by old endpoint (`/api/analyze`), NOT by v2 endpoint
- Therefore Results page mostly falls back to storage → **ARCHITECTURE VIOLATION**

## ✅ Solution Implemented

### 1️⃣ Backend: Shared State for v2 Results

**File:** `app/core/engine_state.py` (NEW)
- Created dedicated module for shared backend state
- Provides `set_last_result_v2()` and `get_last_result_v2()` functions
- Stores Engine v2 results in-memory (authoritative source)

**File:** `app/api/v1/risk_routes.py`
- Updated `POST /api/v1/risk/v2/analyze` endpoint
- After engine execution, stores result in shared state via `set_last_result_v2()`
- Builds complete result payload including shipment data for UI mapping

**File:** `app/main.py`
- Updated `GET /results/data` endpoint
- Priority 1: Returns `LAST_RESULT_V2` (from Engine v2)
- Priority 2: Falls back to `LAST_RESULT` (legacy)
- Priority 3: Returns empty payload (not demo data) if no engine result exists

### 2️⃣ Frontend: Strict API-First Priority

**File:** `app/static/js/state.js`
- Updated `loadFromBackendAPI()` with clear logging:
  - `[ResultsOS] Data source: backend_api_v2 (Engine v2 result)`
  - `[ResultsOS] Backend API returned empty payload`
  - `[ResultsOS] Failed to load from backend API`
- Updated `loadSummaryStateWithAPI()` with strict priority:
  - **Priority 1:** Backend API (authoritative, Engine v2 result)
  - **Priority 2:** Storage fallback (legacy support only)
  - Clear logging for each path

**File:** `app/static/js/main.js`
- Added architecture documentation comment
- Confirms Results page NEVER triggers engine execution
- Engine is executed ONLY in Summary page

## 📊 Data Flow (After Fix)

```
┌─────────────────┐
│  Summary Page   │
│  (User clicks   │
│   "Confirm")    │
└────────┬────────┘
         │
         │ POST /api/v1/risk/v2/analyze
         ▼
┌─────────────────────────────┐
│  Engine v2 Execution        │
│  (FAHP + TOPSIS + Climate)  │
└────────┬────────────────────┘
         │
         │ Store result
         ▼
┌─────────────────────────────┐
│  Shared Backend State       │
│  (LAST_RESULT_V2)           │
│  - Authoritative source     │
│  - In-memory storage         │
└────────┬────────────────────┘
         │
         │ (Optional: Save to localStorage for legacy)
         │
         │ GET /results/data
         ▼
┌─────────────────────────────┐
│  Results Page               │
│  - Reads from shared state  │
│  - NEVER triggers engine    │
│  - Falls back to storage    │
│    only if API fails        │
└─────────────────────────────┘
```

## 🔒 Architecture Guarantees

### ✅ No Duplicate Engine Execution
- Engine is executed **ONLY** in Summary page (`POST /api/v1/risk/v2/analyze`)
- Results page **NEVER** triggers engine (only reads via `GET /results/data`)

### ✅ Results Page Always Uses Engine Data
- Results page **ALWAYS** tries backend API first (authoritative source)
- Storage fallback is **ONLY** for legacy support or offline scenarios
- Clear logging shows data source path

### ✅ No UI-Side Computation
- `state.js` remains **PURE MAPPING ONLY**
- No business logic, no risk computation, no insurance decisions
- All computation happens in backend engine

### ✅ Single Source of Truth
- Backend shared state (`LAST_RESULT_V2`) is the authoritative source
- Storage is **ONLY** a fallback, not the primary source

## 📝 Files Changed

### Backend
1. **NEW:** `app/core/engine_state.py` - Shared state module
2. **MODIFIED:** `app/api/v1/risk_routes.py` - Store result in shared state
3. **MODIFIED:** `app/main.py` - Return v2 result from `/results/data`

### Frontend
4. **MODIFIED:** `app/static/js/state.js` - Strict API-first priority with logging
5. **MODIFIED:** `app/static/js/main.js` - Architecture documentation

## 🧪 Testing Checklist

- [ ] Summary page calls engine → result stored in shared state
- [ ] Results page loads → reads from shared state via API
- [ ] Results page shows correct data (from engine, not storage)
- [ ] Console logs show: `[ResultsOS] Data source: backend_api_v2`
- [ ] If API fails, fallback to storage works (legacy support)
- [ ] No duplicate engine execution
- [ ] Results page never triggers engine

## 🎉 Result

**ENGINE-FIRST architecture is now enforced:**
- ✅ Results page ALWAYS renders engine-computed data when available
- ✅ Storage is ONLY a fallback for legacy/offline scenarios
- ✅ Clear logging shows data source path
- ✅ No architecture violations
- ✅ Auditable, traceable data flow


