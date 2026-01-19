# ✅ UX REFACTOR: AI ADVISOR DOCK + HEADER ACTIONS

## 🎯 Mục tiêu đã đạt được

1. ✅ **Không còn overlap** giữa AI chat và footer actions
2. ✅ **Actions moved to header** - Back/Save Draft/Run Analysis ở top-right
3. ✅ **Premium dock pattern** - Right dock (desktop) / Bottom sheet (mobile)
4. ✅ **Responsive design** - Breakpoints và z-index management
5. ✅ **Consistent hierarchy** - Header actions luôn accessible

## 📦 Files đã tạo/sửa

### New Files
1. **`src/hooks/useAiDockState.ts`**
   - Hook quản lý dock state với localStorage persistence
   - open/close/toggle/minimize/maximize

2. **`src/components/AiAdvisorDock.tsx`**
   - AI Advisor dock component (thay thế SystemChatPanel floating)
   - Desktop: Right dock slide-in (420px width)
   - Mobile: Bottom sheet (70vh height)
   - Trigger button component cho header

3. **`src/components/summary/HeaderActions.tsx`**
   - Component chứa Back/Save Draft/Run Analysis buttons
   - Responsive labels (ẩn trên mobile)

### Modified Files
1. **`src/components/summary/Header.tsx`**
   - Thêm `actions` prop (optional)
   - Include `HeaderActions` component
   - Include `AiAdvisorTrigger` button
   - Z-index: z-[100] (highest)

2. **`src/components/summary/RiskcastSummary.tsx`**
   - Pass actions props lên Header
   - Replace `SystemChatPanel` với `AiAdvisorDock`
   - Remove `ActionFooter` (thay bằng status footer nhẹ)
   - Tính `canAnalyze` và `completeness` cho header actions

## 🎨 Design Pattern

### Desktop (≥768px)
- **AI Dock:** Right side slide-in panel (420px width, full height)
- **Trigger:** Button trong header (không floating)
- **Actions:** Header top-right (Back/Save/Run Analysis)

### Mobile (<768px)
- **AI Dock:** Bottom sheet (70vh height, rounded top)
- **Overlay:** Dark backdrop khi mở
- **Actions:** Collapse labels, giữ icons

## 🔧 Z-Index Hierarchy

```
z-[100]  - Header (highest - always on top)
z-[101]  - AI Advisor Dock (below header, above content)
z-50     - Footer status bar (below dock)
z-40     - Status footer (lowest fixed element)
```

## ✅ Acceptance Criteria

- [x] Không còn overlap giữa AI chat và action buttons
- [x] Back/Save Draft nằm trên header (top-right)
- [x] AI Advisor mở/đóng mượt (slide-in / bottom-sheet)
- [x] Responsive tốt (desktop dock, mobile sheet)
- [x] Không phá layout các cards/modules
- [x] Premium UI với glass effects và smooth transitions

## 🚀 Test Steps

1. **Hard refresh browser** (Ctrl + Shift + R)
2. **Navigate to Summary page**
3. **Check header** - Actions should be visible top-right
4. **Click "AI Advisor" button** in header
5. **Verify dock opens** - Right side (desktop) or bottom (mobile)
6. **Check no overlap** - Footer status bar không bị che
7. **Test responsive** - Resize window để test mobile/desktop

## 📝 Notes

- AI Advisor trigger button nằm trong header, không còn floating
- Dock state được persist trong localStorage
- Footer chỉ còn status bar (completeness, issues) - không có actions
- Actions đã move lên header để consistent và accessible
