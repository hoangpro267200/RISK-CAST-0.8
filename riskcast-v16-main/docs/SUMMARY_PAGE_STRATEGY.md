# Summary Page Strategy - Tách Biệt JS Logic và Vue UI

**Ngày tạo:** 2024  
**Mục đích:** Hướng dẫn cách giữ lại JS logic của summary page trong khi tách biệt hoặc loại bỏ Vue components

---

## 📊 Tình Huống Hiện Tại

### File Vue (UI Components)
**Location:** `src/features/risk-intelligence/components/summary/`

- `RiskSummarySection.vue` - Main summary section component
- `OverallRiskCard.vue` - Overall risk display
- `LayerScoresCard.vue` - Layer scores display
- `CategoryBreakdownCard.vue` - Category breakdown
- `ESGScoreCard.vue` - ESG score display
- `MonteCarloCard.vue` - Monte Carlo visualization
- `DelayPredictionCard.vue` - Delay prediction
- `ShockScenariosCard.vue` - Shock scenarios

**Mục đích:** UI components cho risk intelligence features (Vue-based)

### File JavaScript (Business Logic) ✅ CẦN GIỮ LẠI
**Location:** `app/static/js/summary/`

- `summary_controller.js` - **Core controller** (orchestration, button handlers)
- `summary_state_sync.js` - **State management** (localStorage sync)
- `summary_validator.js` - **Validation logic** (business rules)
- `summary_renderer.js` - **Rendering logic** (DOM manipulation)
- `summary_smart_editor.js` - **Smart editor** (inline editing)
- `summary_dataset_loader.js` - **Data loading** (expert datasets)
- `summary_expert_rules.js` - **Expert rules** (business logic)

**Mục đích:** Core business logic cho summary page (Vanilla JS - đang hoạt động)

---

## ✅ Giải Pháp Đề Xuất

### Option 1: Giữ Nguyên JS, Archive Vue (Khuyến Nghị) ⭐

**Cách làm:**
1. **Giữ nguyên** tất cả JS files trong `app/static/js/summary/`
2. **Move Vue components** vào `archive/frontend/vue-summary-components/`
3. **Update documentation** để rõ ràng về việc không dùng Vue cho summary

**Ưu điểm:**
- ✅ JS logic vẫn hoạt động bình thường
- ✅ Không ảnh hưởng đến production
- ✅ Có thể khôi phục Vue nếu cần
- ✅ Code rõ ràng, dễ maintain

**Cách thực hiện:**

```bash
# 1. Tạo thư mục archive
mkdir -p archive/frontend/vue-summary-components

# 2. Move Vue components
mv src/features/risk-intelligence/components/summary/*.vue \
   archive/frontend/vue-summary-components/

# 3. Tạo README trong archive
echo "# Vue Summary Components (Archived)
These components are archived but preserved for reference.
Current summary page uses Vanilla JS in app/static/js/summary/
" > archive/frontend/vue-summary-components/README.md
```

### Option 2: Giữ Cả Hai, Tách Biệt Rõ Ràng

**Cách làm:**
1. **Giữ nguyên** JS files (production)
2. **Giữ nguyên** Vue components nhưng **không import/use**
3. **Document rõ ràng** trong code comments

**Ưu điểm:**
- ✅ Có thể reference Vue components khi cần
- ✅ Không cần move files
- ⚠️ Có thể gây confusion

**Cách thực hiện:**

Thêm comment vào đầu mỗi Vue file:
```vue
<!--
  ARCHIVED: This component is not currently used.
  Summary page uses Vanilla JS in app/static/js/summary/
  Keep for reference only.
-->
```

### Option 3: Tạo Adapter Layer (Nếu Cần Tích Hợp)

**Cách làm:**
1. **Giữ nguyên** JS logic
2. **Tạo adapter** để bridge JS logic với Vue components
3. **Wrap Vue components** để sử dụng JS logic

**Ưu điểm:**
- ✅ Có thể dùng Vue UI với JS logic
- ✅ Tách biệt rõ ràng
- ⚠️ Phức tạp hơn, cần maintain adapter

**Cách thực hiện:**

Tạo `src/adapters/summary-adapter.ts`:
```typescript
// Adapter to bridge Vanilla JS summary logic with Vue components
import { SummaryController } from '../../app/static/js/summary/summary_controller';

export function useSummaryAdapter() {
  // Expose JS controller methods to Vue
  return {
    init: () => SummaryController.init(),
    getState: () => SummaryController.getState(),
    // ... other methods
  };
}
```

---

## 🎯 Khuyến Nghị: Option 1 (Archive Vue)

### Lý Do

1. **JS Logic là Core Business Logic**
   - `summary_controller.js` điều phối toàn bộ flow
   - `summary_validator.js` chứa business rules quan trọng
   - `summary_state_sync.js` quản lý state với localStorage
   - **Không thể thay thế** bằng Vue components

2. **Vue Components chỉ là UI**
   - Chỉ là presentation layer
   - Có thể rebuild bằng React nếu cần
   - Không chứa business logic

3. **Theo Frontend Strategy**
   - React + TypeScript là canonical
   - Vue là legacy (maintain but don't extend)
   - Vanilla JS cho summary page vẫn hoạt động tốt

### Steps Thực Hiện

1. **Backup Vue components** (đã có trong git)
2. **Move vào archive**
3. **Update .gitignore** nếu cần
4. **Update documentation**
5. **Test summary page** vẫn hoạt động

---

## 📝 Checklist

### Trước Khi Archive

- [ ] Backup Vue components (git commit)
- [ ] Test summary page hoạt động với JS
- [ ] Document dependencies (nếu Vue components import từ đâu)
- [ ] Check imports trong codebase (grep cho Vue summary components)

### Sau Khi Archive

- [ ] Verify summary page vẫn hoạt động
- [ ] Update FRONTEND_STRATEGY.md
- [ ] Update DEPRECATION.md nếu cần
- [ ] Remove unused imports (nếu có)
- [ ] Test build process

---

## 🔍 Kiểm Tra Dependencies

### Check Vue Components Usage

```bash
# Tìm nơi import Vue summary components
grep -r "RiskSummarySection" src/
grep -r "OverallRiskCard" src/
grep -r "from.*summary" src/

# Tìm trong HTML templates
grep -r "risk-summary" templates/
```

### Check JS Summary Usage

```bash
# Tìm nơi sử dụng JS summary
grep -r "summary_controller" app/
grep -r "SummaryController" app/
grep -r "summary/" templates/
```

---

## 📚 File Structure Sau Khi Archive

```
riskcast-v16-main/
├── app/
│   └── static/
│       └── js/
│           └── summary/          ✅ GIỮ LẠI (Business Logic)
│               ├── summary_controller.js
│               ├── summary_state_sync.js
│               ├── summary_validator.js
│               ├── summary_renderer.js
│               ├── summary_smart_editor.js
│               ├── summary_dataset_loader.js
│               └── summary_expert_rules.js
│
├── archive/
│   └── frontend/
│       └── vue-summary-components/  📦 ARCHIVED (UI Only)
│           ├── RiskSummarySection.vue
│           ├── OverallRiskCard.vue
│           ├── LayerScoresCard.vue
│           └── ... (other Vue components)
│
└── src/
    └── features/
        └── risk-intelligence/
            └── components/
                └── summary/        ❌ REMOVED (moved to archive)
```

---

## ⚠️ Lưu Ý Quan Trọng

1. **KHÔNG XÓA JS FILES**
   - JS logic là core business logic
   - Đang được sử dụng trong production
   - Không thể thay thế

2. **Vue Components chỉ là UI**
   - Có thể rebuild bằng React nếu cần
   - Không chứa business logic
   - Có thể archive an toàn

3. **Test Kỹ Trước Khi Archive**
   - Đảm bảo summary page vẫn hoạt động
   - Check không có dependencies bị break
   - Verify build process

4. **Document Rõ Ràng**
   - Update FRONTEND_STRATEGY.md
   - Add note trong archive README
   - Document lý do archive

---

## 🚀 Quick Start

### Archive Vue Components

```bash
# 1. Tạo archive directory
mkdir -p archive/frontend/vue-summary-components

# 2. Move Vue components
mv src/features/risk-intelligence/components/summary/*.vue \
   archive/frontend/vue-summary-components/

# 3. Tạo README
cat > archive/frontend/vue-summary-components/README.md << EOF
# Vue Summary Components (Archived)

These Vue components were used for risk intelligence summary UI.
They have been archived because:
- Summary page uses Vanilla JS in app/static/js/summary/
- React + TypeScript is the canonical frontend stack
- Vue components only contain UI, no business logic

## Business Logic Location
- Core logic: app/static/js/summary/summary_controller.js
- State sync: app/static/js/summary/summary_state_sync.js
- Validation: app/static/js/summary/summary_validator.js
- Rendering: app/static/js/summary/summary_renderer.js

## Restoration
If needed, these components can be restored from git history.
EOF

# 4. Commit
git add archive/frontend/vue-summary-components/
git commit -m "refactor: archive Vue summary components, keep JS logic"
```

### Verify Summary Page

```bash
# Start server
python dev_run.py

# Test summary page
# Navigate to http://localhost:8000/summary
# Verify all functionality works
```

---

## 📖 References

- [Frontend Strategy](./FRONTEND_STRATEGY.md) - Canonical stack decision
- [Deprecation Guide](./DEPRECATION.md) - Deprecation process
- [State of the Repo](./STATE_OF_THE_REPO.md) - Current architecture

---

**Last Updated:** 2024  
**Status:** Active Strategy

