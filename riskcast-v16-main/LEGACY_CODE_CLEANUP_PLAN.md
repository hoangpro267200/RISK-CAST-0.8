# 🧹 LEGACY CODE CLEANUP PLAN

## 🎯 MỤC TIÊU

Cleanup và organize codebase bằng cách:
1. Archive các version cũ không còn dùng
2. Giữ lại chỉ version hiện tại (active)
3. Tạo migration guides
4. Cải thiện code organization

---

## 📋 INVENTORY - VERSIONS TRONG CODEBASE

### Input Pages
- ✅ **input_v20** - ACTIVE (version hiện tại)
- ⚠️ input_v19 - LEGACY (có thể archive)
- ⚠️ input_v21 - LEGACY (có thể archive)
- ⚠️ input_v30 (modules) - LEGACY (có thể archive)

### Summary Pages
- ✅ **summary_v400** - ACTIVE (version hiện tại)
- ⚠️ summary_v100 - LEGACY (có thể archive)

### Overview Pages
- ⚠️ overview_v36 - LEGACY (redirects to /summary)
- ⚠️ overview_v80 - LEGACY (có thể archive)

### Risk Engines
- ✅ **v16** - ACTIVE (version hiện tại)
- ⚠️ v14 - LEGACY (đã có trong core/legacy/)
- ⚠️ v15 - LEGACY (có thể archive)

### API Versions
- ✅ **/api/v1/** - ACTIVE (version hiện tại)
- ⚠️ /api/ (legacy) - ACTIVE (backward compatibility, giữ lại)

---

## 📂 CLEANUP STRATEGY

### Phase 1: Archive (Không xóa, chỉ move)

**Tạo thư mục archive:**
```
archive/
├── input/
│   ├── input_v19.html
│   └── input_v21_controller.js
├── summary/
│   └── summary_v100/
├── overview/
│   ├── overview_v36/
│   └── overview_v80/
└── engines/
    ├── v14/
    └── v15/
```

### Phase 2: Update References

**1. Routes (main.py):**
- Giữ route cho version active
- Remove routes cho legacy versions
- Add redirects nếu cần (temporary)

**2. Templates:**
- Giữ template active
- Move legacy templates to archive

**3. JavaScript:**
- Giữ JS files cho version active
- Move legacy JS to archive
- Update imports nếu cần

**4. Documentation:**
- Document version hiện tại
- Archive documentation cũ

### Phase 3: Cleanup Dependencies

**1. Remove unused imports:**
- Check imports trong active code
- Remove imports to legacy code

**2. Remove unused files:**
- After moving to archive, check for unused files
- Remove only after confirmation

---

## 🔍 DETAILED CLEANUP CHECKLIST

### Input Pages

#### ✅ Keep (Active):
- `app/templates/input/input_v20.html`
- `app/static/js/v20/**` (entire v20 directory)
- Route: `/input_v20` (và redirect từ `/input`)

#### ⚠️ Archive:
- `app/templates/input/input_v19.html` → `archive/input/input_v19.html`
- `app/static/js/pages/input/input_controller_v19.js` → `archive/input/`
- `app/static/js/pages/input/input_controller_v21.js` → `archive/input/`
- `app/templates/input_modules_v30.html` → `archive/input/input_modules_v30.html`

#### Actions:
1. Move files to archive
2. Update routes (remove v19, v21 routes)
3. Update documentation

### Summary Pages

#### ✅ Keep (Active):
- `app/templates/summary/summary_v400.html`
- `app/static/js/summary_v400/**` (entire directory)
- Route: `/summary`

#### ⚠️ Archive:
- `app/static/js/summary/summary_controller.js` (v100) → `archive/summary/v100/`
- `app/static/js/summary/summary_renderer.js` → `archive/summary/v100/`
- Other v100 files → `archive/summary/v100/`

#### Actions:
1. Move v100 files to archive
2. Verify v400 is working
3. Update documentation

### Overview Pages

#### Status:
- Routes redirect to `/summary` (already done)
- Can archive old files

#### ⚠️ Archive:
- `app/static/js/overview_v80.js` → `archive/overview/`
- Old overview templates → `archive/overview/`

### Risk Engines

#### ✅ Keep (Active):
- `app/core/engine/risk_engine_v16.py`
- `app/core/risk_engine_v16.py` (nếu đang dùng)
- `app/core/engine_v2/**` (nếu đang dùng)

#### ⚠️ Already in legacy:
- `app/core/legacy/**` - Keep (for reference)

#### Actions:
- Verify which engine is actually being used
- Document engine usage
- Keep legacy/ for reference (don't delete)

### API Versions

#### ✅ Keep (Active):
- `app/api/v1/**` - Active API
- `app/api.py` - Legacy API (keep for backward compatibility)
- `app/api_ai.py` - AI API (keep)

#### Actions:
- Document API versions
- Plan migration từ legacy to v1

---

## 📝 MIGRATION GUIDES

### Input v19 → v20

**Changes:**
- New modular architecture (ES6 classes)
- StateManager instead of direct localStorage
- New UI components
- Different state structure

**Migration Steps:**
1. State format conversion (see StateManager.mapRISKCAST_STATEToFormData)
2. Update field names if changed
3. Test thoroughly

### Summary v100 → v400

**Changes:**
- New template structure
- New renderer (v400_renderer.js)
- New validator (v400_validator.js)
- New inline editor (v400_inline_editor.js)

**Migration Steps:**
1. State format is compatible (RISKCAST_STATE)
2. Just use new template
3. Test thoroughly

---

## ⚠️ RISKS & MITIGATION

### Risks:
1. **Breaking changes:** Removing code might break something
2. **Lost functionality:** Some features might be in old versions
3. **References:** Other code might reference legacy files

### Mitigation:
1. **Don't delete, archive:** Move to archive, don't delete
2. **Test thoroughly:** Test after each cleanup step
3. **Git history:** Use Git to track changes, can revert
4. **Gradual:** Cleanup gradually, not all at once
5. **Documentation:** Document what was removed and why

---

## ✅ EXECUTION PLAN

### Week 1: Preparation
1. ✅ Create archive directory structure
2. ✅ Document all versions and their status
3. ✅ Identify all references to legacy code
4. ✅ Create backup (Git commit)

### Week 2: Input Pages Cleanup
1. Move input_v19 files to archive
2. Move input_v21 files to archive
3. Update routes
4. Test input_v20 works
5. Git commit

### Week 3: Summary Pages Cleanup
1. Move summary_v100 files to archive
2. Verify summary_v400 works
3. Test thoroughly
4. Git commit

### Week 4: Overview & Others
1. Archive overview files
2. Clean up unused files
3. Update documentation
4. Final testing
5. Git commit

---

## 📊 SUCCESS METRICS

- **Code reduction:** Reduce duplicate code by 30-40%
- **Clarity:** Clear which version is active
- **Maintainability:** Easier to maintain with less legacy code
- **Documentation:** Clear migration paths

---

## 🔄 ROLLBACK PLAN

If something breaks:
1. Git revert to previous commit
2. Restore files from archive
3. Document what went wrong
4. Fix issues before retrying

---

## 📝 NOTES

- **Don't rush:** Cleanup gradually
- **Test after each step:** Don't break things
- **Keep Git history:** Use Git properly
- **Document changes:** Update documentation
- **Communication:** If working in team, communicate changes

---

**Status:** Planning Phase  
**Priority:** Medium (can be done gradually)  
**Risk Level:** Medium (can break things if not careful)

