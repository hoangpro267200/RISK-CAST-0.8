# PHASE 4 - Remaining Tasks Plan

## Tasks to Complete

### 1. Clean and Optimize Imports Everywhere
- [ ] Check Python files for unused imports
- [ ] Check JS modules for unused imports  
- [ ] Remove duplicate imports
- [ ] Ensure import order is consistent

### 2. Clean Leftover Files from Phase 2-3
- [x] No backup files found (.backup, .old, .bak)
- [ ] Check for temporary/refactor leftover files
- [ ] Remove any Phase 2-3 intermediate files

### 3. Remove Inline CSS Style Leftovers
**Found:**
- `app/templates/results.html`: 4 inline styles
- `app/templates/input.html`: 4 inline styles
- `app/templates/home.html`: ? inline styles
- `app/templates/components/ai_panel.html`: ? inline styles
- `app/templates/pages/overview.html`: ? inline styles
- `app/templates/layouts/input_layout.html`: ? inline styles

**JS Files with .style. usage:** 29 files found
- Phase 3 modules: Need CSS classes instead
- Emergency unlock modules: Critical, keep for now
- UI updaters: Can be optimized

### 4. Minimize JS Size by Merging Utilities
- Check for duplicate utility functions
- Merge repeated date/formatting helpers
- Consolidate DOM utils
- Merge error handlers

### 5. Validate Entire App Still Works
- [ ] Test input page
- [ ] Test results page
- [ ] Test home page
- [ ] Verify all dropdowns work
- [ ] Verify neon effects work
- [ ] Verify AI sidebar loads
- [ ] Verify risk engine works
- [ ] Verify charts render

## Status: In Progress




















