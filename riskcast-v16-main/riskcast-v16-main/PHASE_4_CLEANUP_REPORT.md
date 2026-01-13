# PHASE 4 — CLEANUP REPORT

## ✅ COMPLETED FIXES

### 1. Python Import Fixes (3 files)
- ✅ `app/core/legacy/riskcast_v14_5_integration_patches.py`
- ✅ `app/core/legacy/riskcast_v14_5_climate_demo.py`
- ✅ `app/core/legacy/RISKCAST_v14_5_README.py`
- **Fix**: Updated imports from `app.core.riskcast_v14_5_climate_upgrade` → `app.core.legacy.riskcast_v14_5_climate_upgrade`

### 2. JavaScript Import Fixes (6 template files)
- ✅ `app/templates/pages/overview.html` - Fixed `riskcast_data_store.js` path
- ✅ `app/templates/overview.html` - Fixed `riskcast_data_store.js` path
- ✅ `app/templates/layouts/dashboard_layout.html` - Consolidated translations
- ✅ `app/templates/results.html` - Consolidated translations + streaming path
- ✅ `app/templates/dashboard.html` - Consolidated translations
- ✅ `app/templates/input.html` - Fixed streaming + data store paths

**Changes Made:**
- `/static/js/riskcast_data_store.js` → `/static/js/core/riskcast_data_store.js`
- `/static/js/streaming.js` → `/static/js/core/streaming.js`
- `/static/js/translations_vi.js` + `/static/js/translations_en.js` + `/static/js/common_lang.js` → `/static/js/core/translations.js`

## 📋 TEMPLATE STATUS ANALYSIS

### Templates in Use (by main.py):
1. ✅ `home.html` - Standalone (no extends)
2. ✅ `input.html` - Standalone (no extends)
3. ✅ `results.html` - Standalone (no extends)
4. ✅ `dashboard.html` - Standalone (no extends)
5. ✅ `pages/overview.html` - Extends `layouts/base.html` ✅

### Duplicate Templates Found:
1. **`base.html`** (root) vs **`layouts/base.html`** (new structure)
   - Root `base.html`: Large file with inline styles and navbar
   - `layouts/base.html`: Clean structure with new CSS imports
   - **Status**: Root `base.html` appears to be old version
   - **Action**: Verify usage, then remove if unused

2. **`overview.html`** (root) vs **`pages/overview.html`** (new structure)
   - Root `overview.html`: Extends `base.html` (old)
   - `pages/overview.html`: Extends `layouts/base.html` (new) ✅
   - `main.py` uses: `pages/overview.html` ✅
   - **Action**: Root `overview.html` can be removed

## 🗂️ FILES TO REMOVE (After Verification)

### Old Translation Files (Consolidated):
- `app/static/js/translations_vi.js` → Consolidated into `core/translations.js`
- `app/static/js/translations_en.js` → Consolidated into `core/translations.js`
- `app/static/js/common_lang.js` → Consolidated into `core/translations.js`

### Duplicate Templates (After Verification):
- `app/templates/overview.html` → Duplicate of `pages/overview.html`
- `app/templates/base.html` → Duplicate of `layouts/base.html` (verify first)

## 📊 REMAINING JS FILES (Not yet moved)

**22 JS files still in root `app/static/js/`:**
- `ai_adviser.js` (31.69 KB)
- `ai_chat.js` (25.06 KB)
- `booking_summary.js` (26.07 KB)
- `climate_data_2025.js` (1.57 KB)
- `common_lang.js` (8.36 KB) ⚠️ **CONSOLIDATED - CAN REMOVE**
- `dashboard.js` (24.96 KB)
- `enterprise.js` (2.3 KB)
- `enterprise_input.js` (17.42 KB)
- `home.js` (7.79 KB)
- `input.js` (6.05 KB)
- `input_form.js` (209.85 KB) ⚠️ **LARGE - NEEDS ANALYSIS**
- `input_summary_init.js` (1.75 KB)
- `logistics_data.js` (77.21 KB)
- `overview.js` (25.51 KB)
- `packing_list.js` (14.17 KB)
- `premium_input_tracker.js` (12.19 KB)
- `results.js` (11.1 KB)
- `smart_input.js` (142.96 KB) ⚠️ **LARGE**
- `smart_progress_tracker.js` (20.82 KB)
- `summary.js` (17.16 KB)
- `translations_en.js` (10.98 KB) ⚠️ **CONSOLIDATED - CAN REMOVE**
- `translations_vi.js` (13.21 KB) ⚠️ **CONSOLIDATED - CAN REMOVE**

## 🔍 DUPLICATE CODE IDENTIFIED

### Progress Tracking (2 files):
- `smart_progress_tracker.js` (20.82 KB)
- `premium_input_tracker.js` (12.19 KB)
- **Action**: Merge into `modules/progress_tracker.js`

### Summary Logic (2 files):
- `input_summary_init.js` (1.75 KB)
- `summary.js` (17.16 KB)
- **Action**: Merge into `modules/input_summary.js`

### Translation System (3 files):
- `translations_vi.js` (13.21 KB) ✅ **CONSOLIDATED**
- `translations_en.js` (10.98 KB) ✅ **CONSOLIDATED**
- `common_lang.js` (8.36 KB) ✅ **CONSOLIDATED**

## 🎯 NEXT PRIORITIES

1. **Remove old translation files** (3 files) - Safe to delete
2. **Remove duplicate `overview.html`** - Safe to delete
3. **Verify and remove duplicate `base.html`** - Check first
4. **Continue JS refactor** - Move remaining files to modules/pages
5. **Clean console.log statements** - Found 25+ instances

## 📝 NOTES

- Most templates (`home.html`, `input.html`, `results.html`, `dashboard.html`) are standalone and don't extend layouts yet
- Phase 1 refactoring created new layout structure but old templates still exist
- Need to migrate old templates to use new layout system or verify they're intentionally standalone





















