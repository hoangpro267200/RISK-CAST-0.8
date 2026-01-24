# Input Page Integration Guide
## Tích hợp React Input Page vào hệ thống

**Date:** January 2026  
**Status:** ✅ Integrated

---

## 🔗 Routing Integration

### Backend Routes (FastAPI)

#### `/input` → `/input_react`
- **Route:** `GET /input`
- **Action:** Redirects to `/input_react` (React Input page)
- **Location:** `app/main.py`

#### `/input_react` → React App
- **Route:** `GET /input_react`
- **Action:** Serves React app from `dist/index.html`
- **Fallback:** Shows build instructions if `dist/index.html` not found
- **Location:** `app/main.py`

#### `/input_v20` → Legacy HTML (Fallback)
- **Route:** `GET /input_v20`
- **Action:** Serves legacy HTML template
- **Purpose:** Fallback for users who need HTML version
- **Location:** `app/main.py`

#### `/input_v20/submit` → Form Submission
- **Route:** `POST /input_v20/submit`
- **Supports:**
  - HTML form data (legacy)
  - JSON payload (React form)
  - DomainCase structure (React)
- **Action:**
  1. Normalize payload
  2. Save to session (`RISKCAST_STATE`)
  3. Call `run_analysis` API
  4. Redirect to `/overview`
- **Location:** `app/main.py`

### Frontend Routes (React App)

#### App.tsx Routing
- **Path Detection:**
  - `/input` → InputPage
  - `/input_react` → InputPage
  - `/summary` → SummaryPage
  - `/results` → ResultsPage (default)

- **Location:** `src/App.tsx`

---

## 📦 Data Flow

### Submission Flow

```
React InputPage
  ↓ (User fills form)
  ↓ (mapInputFormToDomainCase)
DomainCase object
  ↓ (JSON POST to /input_v20/submit)
Backend /input_v20/submit
  ↓ (Detect DomainCase structure)
  ↓ (Convert to shipment_payload)
  ↓ (Call run_analysis API)
Analysis Engine
  ↓ (Store result)
Session + Memory
  ↓ (Redirect to /overview)
Summary Page
```

### Data Structure

**React Form State:**
```typescript
{
  route: { pol, pod, mode, ... },
  cargo: { type, weight, volume, ... },
  value: { insuranceValue, ... },
  parties: { seller: {...}, buyer: {...} },
  modules: { esg, weather, ... }
}
```

**DomainCase (after mapping):**
```typescript
{
  caseId: "CASE-...",
  pol: "SGN",
  pod: "SHA",
  transportMode: "SEA",
  cargoType: "Electronics",
  cargoValue: 85000,
  // ... full DomainCase structure
}
```

**Shipment Payload (for engine):**
```python
{
  "transport_mode": "ocean_fcl",
  "cargo_type": "electronics",
  "route": "SGN_SHA",
  "cargo_value": 85000,
  # ... engine-compatible format
}
```

---

## 🔧 Integration Points

### 1. Backend Route Setup

**File:** `app/main.py`

```python
@app.get("/input")
async def input_redirect():
    """Redirect /input to React Input page"""
    return RedirectResponse(url="/input_react")

@app.get("/input_react", response_class=HTMLResponse)
async def input_react(request: Request):
    """Serve React Input page from dist/index.html"""
    dist_index = BASE_DIR.parent / "dist" / "index.html"
    if dist_index.exists():
        with open(dist_index, 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    # Fallback...
```

### 2. Submit Endpoint Enhancement

**File:** `app/main.py` - `/input_v20/submit`

- Detects DomainCase structure from React form
- Converts to shipment_payload for engine
- Calls `run_analysis` API
- Saves to session
- Redirects to `/overview`

### 3. Frontend App Routing

**File:** `src/App.tsx`

- Detects `/input` or `/input_react` paths
- Renders `InputPage` component
- Lazy loads for code splitting

### 4. Form Submission

**File:** `src/pages/InputPage.tsx`

- Validates form using `validateDomainCase`
- Maps to DomainCase using `mapInputFormToDomainCase`
- POSTs JSON to `/input_v20/submit`
- Handles success/error with toasts
- Redirects to `/overview` on success

---

## 🚀 Deployment Steps

### 1. Build React App

```bash
cd riskcast-v16-main
npm run build
```

This creates `dist/index.html` with all React components bundled.

### 2. Verify Build

```bash
# Check dist/index.html exists
ls dist/index.html

# Check it contains React app
head -20 dist/index.html
# Should see: <div id="root"></div> and script tags
```

### 3. Start Backend Server

```bash
# Development
python dev_run.py

# Production
python run.py
```

### 4. Test Routes

- **`http://localhost:8000/input`** → Should redirect to `/input_react`
- **`http://localhost:8000/input_react`** → Should show React Input page
- **`http://localhost:8000/input_v20`** → Should show legacy HTML (fallback)

### 5. Test Form Submission

1. Fill form on `/input_react`
2. Click "Run Risk Analysis"
3. Should:
   - Show loading overlay
   - Submit to `/input_v20/submit`
   - Redirect to `/overview`
   - Show analysis results

---

## 🔄 Backward Compatibility

### Legacy HTML Form
- **Route:** `/input_v20`
- **Status:** Still available as fallback
- **Use Case:** Users who prefer HTML version

### Legacy Form Submission
- **Endpoint:** `/input_v20/submit`
- **Supports:** Both HTML form data and JSON
- **Auto-detects:** Format based on payload structure

### Data Migration
- **Old format:** Flat form fields
- **New format:** DomainCase structure
- **Mapper handles:** Both formats automatically

---

## 📝 Testing Checklist

### Route Testing
- [ ] `/input` redirects to `/input_react`
- [ ] `/input_react` serves React app
- [ ] `/input_v20` serves legacy HTML
- [ ] React app detects path correctly

### Form Submission Testing
- [ ] React form submits JSON
- [ ] Backend detects DomainCase structure
- [ ] Backend converts to shipment_payload
- [ ] Analysis runs successfully
- [ ] Redirects to `/overview`
- [ ] Summary page shows correct data

### Data Flow Testing
- [ ] Form state → DomainCase mapping works
- [ ] DomainCase → shipment_payload conversion works
- [ ] Session storage works (`RISKCAST_STATE`)
- [ ] Summary page loads from session
- [ ] Results page loads from analysis

### Error Handling
- [ ] Validation errors show correctly
- [ ] Network errors show toast
- [ ] Backend errors handled gracefully
- [ ] Fallback to legacy works

---

## 🐛 Troubleshooting

### Issue: React app not loading

**Symptoms:**
- `/input_react` shows "Build Required" message

**Solutions:**
1. Run `npm run build`
2. Check `dist/index.html` exists
3. Restart FastAPI server
4. Clear browser cache

### Issue: Form submission fails

**Symptoms:**
- Submit button does nothing
- Network error in console

**Solutions:**
1. Check backend logs for errors
2. Verify `/input_v20/submit` endpoint is accessible
3. Check CORS settings (if needed)
4. Verify JSON payload format

### Issue: Redirect doesn't work

**Symptoms:**
- Submit succeeds but no redirect
- Stays on Input page

**Solutions:**
1. Check backend redirect response
2. Verify `/overview` route exists
3. Check browser console for errors
4. Verify session storage works

---

## 📊 Integration Status

### ✅ Completed
- [x] Backend route `/input_react`
- [x] Backend route `/input` redirect
- [x] Submit endpoint supports DomainCase
- [x] Frontend App.tsx routing
- [x] Form submission flow
- [x] Error handling
- [x] Loading states
- [x] Toast notifications

### 🔄 In Progress
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Accessibility audit

### 📋 Future Enhancements
- [ ] A/B testing (React vs HTML)
- [ ] Analytics integration
- [ ] Progressive Web App (PWA)
- [ ] Offline support

---

## 🔗 Related Files

### Backend
- `app/main.py` - Routes and submit endpoint
- `app/api/analysis_api.py` - Analysis engine
- `app/api.py` - Legacy API routes

### Frontend
- `src/App.tsx` - Main routing
- `src/pages/InputPage.tsx` - Input page component
- `src/domain/case.mapper.ts` - Data transformation
- `src/domain/case.schema.ts` - DomainCase schema

### Documentation
- `docs/input-page-design-spec-v1.md` - Design specification
- `docs/input-page-implementation-summary.md` - Implementation details
- `docs/input-page-keyboard-loading-features.md` - Features documentation

---

**Integration Status:** ✅ Complete  
**Ready for:** Production deployment after testing
