# Phase 1 — HTML Refactoring Progress

## Status: IN PROGRESS

This document tracks the progress of Phase 1 HTML template refactoring.

---

## ✅ Completed Tasks

### 1. Layout Files Created
- ✅ `templates/layouts/base.html` - Base layout with head, content, and scripts blocks
- ✅ `templates/components/navbar.html` - Navbar component extracted

### 2. Components Created
- ✅ `templates/components/navbar.html` - Global navigation bar
- ✅ `templates/components/ai_panel.html` - AI chat widget component

---

## 📋 Remaining Tasks

### Layouts (HIGH PRIORITY)
- ⏳ `templates/layouts/input_layout.html` - Needs creation
  - Should extend base.html
  - Add input-specific CSS includes
  - Add progress tracker block
  - Set page_type = "input"
  
- ⏳ `templates/layouts/dashboard_layout.html` - Needs creation
  - Should extend base.html  
  - Include sidebar component
  - Dashboard-specific styling

### Components (HIGH PRIORITY)
- ⏳ `templates/components/sidebar.html` - Extract from dashboard.html
  - Contains sidebar navigation menu
  - Used in dashboard layout

- ⏳ `templates/components/stats_card.html` - Extract stats card markup
  - Reusable stats card component
  - Used in dashboard.html

- ⏳ `templates/components/progress_tracker.html` - Extract progress bar
  - Progress bar container
  - Used in input page

### Page Templates (HIGH PRIORITY)
- ⏳ Move `templates/home.html` → `templates/pages/home.html`
  - Should extend base.html (no layout)
  - Update all paths

- ⏳ Move `templates/input.html` → `templates/pages/input.html`
  - Should extend input_layout.html
  - Extract components
  - Remove inline CSS/JS

- ⏳ Move `templates/dashboard.html` → `templates/pages/dashboard.html`
  - Should extend dashboard_layout.html
  - Use sidebar component
  - Extract stats cards

- ⏳ Move `templates/results.html` → `templates/pages/results.html`
  - Should extend base.html
  - Clean up structure

- ⏳ Move `templates/overview.html` → `templates/pages/overview.html`
  - Already extends base.html
  - Update paths

---

## 🔧 Files Requiring Updates

### Templates to Update:
1. `app/main.py` - Update template paths for page routes
2. All page templates - Update {% extends %} and {% include %} paths
3. Remove old template files after migration

---

## 📝 Next Steps

1. **Complete Layout Creation**
   - Create input_layout.html
   - Create dashboard_layout.html
   
2. **Extract Remaining Components**
   - Sidebar component
   - Stats card component
   - Progress tracker component

3. **Migrate Pages**
   - Move all page templates to templates/pages/
   - Update extends/include paths
   - Clean up inline CSS/JS (move to external files in Phase 2)

4. **Update Route Handlers**
   - Update app/main.py to point to new template paths

5. **Verify & Test**
   - Test all pages load correctly
   - Verify no broken includes
   - Check navbar and sidebar work

---

## ⚠️ Important Notes

- **Keep inline styles for now** - CSS extraction will happen in Phase 2
- **Keep inline scripts for now** - JS extraction will happen in Phase 2  
- **Functionality must remain identical** - Only structure changes
- **All form names/IDs must remain unchanged**

---

**Last Updated**: During Phase 1 refactoring
**Next Milestone**: Complete layout and component extraction





















