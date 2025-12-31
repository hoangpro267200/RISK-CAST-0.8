# PHASE 4 — CLEANUP PLAN

## 🔍 ISSUES IDENTIFIED

### 1. BROKEN JS IMPORTS
- ❌ `/static/js/riskcast_data_store.js` → ✅ `/static/js/core/riskcast_data_store.js`
- ❌ `/static/js/streaming.js` → ✅ `/static/js/core/streaming.js`
- ❌ `/static/js/translations_vi.js` → ✅ `/static/js/core/translations.js` (consolidated)
- ❌ `/static/js/translations_en.js` → ✅ `/static/js/core/translations.js` (consolidated)
- ❌ `/static/js/common_lang.js` → ✅ `/static/js/core/translations.js` (consolidated)

**Files to fix:**
- `app/templates/pages/overview.html`
- `app/templates/overview.html`
- `app/templates/layouts/dashboard_layout.html`
- `app/templates/input.html`
- `app/templates/results.html`
- `app/templates/dashboard.html`

### 2. DUPLICATE TEMPLATES
- `base.html` (root) vs `layouts/base.html` → Keep `layouts/base.html`, remove root
- `overview.html` (root) vs `pages/overview.html` → Keep `pages/overview.html`, remove root

### 3. BROKEN PYTHON IMPORTS
- `app/core/legacy/riskcast_v14_5_integration_patches.py` references `app.core.riskcast_v14_5_climate_upgrade` but should be `app.core.legacy.riskcast_v14_5_climate_upgrade`
- `app/core/legacy/riskcast_v14_5_climate_demo.py` - same issue
- `app/core/legacy/RISKCAST_v14_5_README.py` - same issue

### 4. OLD CSS PATHS
- Some templates still reference old CSS files that should use new structure

### 5. TEMPLATE PATH ISSUES
- `main.py` references `pages/overview.html` ✅ Correct
- But `overview.html` in root may be duplicate

## 🎯 FIX ORDER

1. Fix Python imports (quick)
2. Fix JS imports in templates
3. Remove duplicate templates
4. Update CSS paths
5. Clean up dead code
6. Remove console.log statements





















