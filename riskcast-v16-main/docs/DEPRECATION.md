# RISKCAST Deprecation Guide

This document lists all deprecated routes, pages, and APIs, along with their migration timeline and guides.

---

## 🚨 Deprecated Endpoints

### `/api/v1/risk/analyze` (v14 Engine)

**Status:** ⚠️ DEPRECATED  
**Deprecated Since:** 2024  
**Removal Target:** v17.0 (TBD)

**Description:**  
Legacy endpoint using v14 engine format. Still functional but uses adapter to call canonical v16 engine.

**Migration:**
- **New Endpoint:** `/api/v1/risk/v2/analyze`
- **Format:** Same request format, but uses canonical engine internally
- **Action Required:** Update clients to use `/api/v1/risk/v2/analyze` or continue using deprecated endpoint (will be removed in v17)

**Example:**
```python
# Old (deprecated)
POST /api/v1/risk/analyze
{
  "transport_mode": "ocean_fcl",
  "cargo_type": "electronics",
  ...
}

# New (recommended)
POST /api/v1/risk/v2/analyze
{
  "transport_mode": "ocean_fcl",
  "cargo_type": "electronics",
  ...
}
```

---

### `/api/analyze` (Legacy API)

**Status:** ⚠️ DEPRECATED  
**Deprecated Since:** 2024  
**Removal Target:** v17.0 (TBD)

**Description:**  
Legacy API endpoint in `app/api.py`. Uses v14 engine via adapter.

**Migration:**
- **New Endpoint:** `/api/v1/risk/v2/analyze`
- **Action Required:** Update clients to use `/api/v1/risk/v2/analyze`

---

## 📄 Deprecated Pages

### `/input_v19`

**Status:** ⚠️ DEPRECATED  
**Deprecated Since:** 2024  
**Removal Target:** v17.0 (TBD)

**Description:**  
Legacy input page v19. Replaced by v20.

**Migration:**
- **New Page:** `/input_v20` (current)
- **Action Required:** Update bookmarks/links to use `/input_v20`
- **Archive Location:** `archive/pages/input_v19/`

---

### `/overview` (Legacy)

**Status:** ⚠️ DEPRECATED  
**Deprecated Since:** 2024  
**Removal Target:** v17.0 (TBD)

**Description:**  
Legacy overview page. Now redirects to `/summary`.

**Migration:**
- **New Page:** `/summary` (summary_v400)
- **Action Required:** Update bookmarks/links to use `/summary`

---

## 🔧 Deprecated Functions

### `run_risk_engine_v14()`

**Status:** ⚠️ DEPRECATED  
**Deprecated Since:** 2024  
**Location:** `app/core/services/risk_service.py`

**Description:**  
Legacy v14 engine wrapper. Now uses adapter to call canonical v16 engine.

**Migration:**
- **New Function:** Use canonical engine interface directly
- **Action Required:** Update imports to use canonical engine
- **Note:** Function still works but logs deprecation warnings

**Example:**
```python
# Old (deprecated)
from app.core.services.risk_service import run_risk_engine_v14
result = run_risk_engine_v14(payload)

# New (recommended)
from app.core.engine.risk_engine_v16 import calculate_enterprise_risk
result = calculate_enterprise_risk(payload)
```

---

## 📦 Deprecated Modules

### `app/core/legacy/`

**Status:** ⚠️ DEPRECATED  
**Deprecated Since:** 2024  
**Removal Target:** v17.0 (TBD)

**Description:**  
Legacy engine code (v14/v15). Moved to archive.

**Migration:**
- **Archive Location:** `archive/engines/v14/`, `archive/engines/v15/`
- **Action Required:** Do not import directly. Use adapters instead.

---

## 🗓️ Timeline

### Phase 1: Deprecation (Current)
- ✅ Legacy code moved to archive
- ✅ Adapters created for backward compatibility
- ✅ Deprecation warnings logged
- ✅ Documentation created

### Phase 2: Migration Period (v16.x)
- ⏳ Clients migrate to new endpoints
- ⏳ Monitor usage of deprecated endpoints
- ⏳ Update documentation

### Phase 3: Removal (v17.0)
- ⏳ Remove deprecated endpoints
- ⏳ Remove legacy code from archive (optional)
- ⏳ Final migration guide published

---

## 📝 Migration Checklist

For each deprecated endpoint/function you use:

- [ ] Identify all usages in your codebase
- [ ] Update to use new endpoint/function
- [ ] Test thoroughly
- [ ] Update documentation
- [ ] Remove old code after migration complete

---

## ❓ Questions?

If you have questions about migration:
1. Check `docs/UPGRADE_ROADMAP.md` for detailed migration steps
2. Review `docs/STATE_OF_THE_REPO.md` for architecture overview
3. Check adapter code in `app/core/adapters/` for format conversion examples

---

**Last Updated:** 2024  
**Maintained By:** RISKCAST Engineering Team

