# RISKCAST Frontend Strategy

**Decision Date:** 2024  
**Status:** Active  
**Review Cycle:** Quarterly

---

## 🎯 Executive Summary

RISKCAST frontend uses a **mixed stack** (React, Vue, Vanilla JS). This document establishes the **canonical frontend approach** and migration strategy.

**Decision:** **React + TypeScript** is the canonical frontend stack for all new development.

---

## 📊 Current State

### Stack Distribution

1. **React + TypeScript** (Canonical ✅)
   - **Location:** `src/`
   - **Usage:** Results page, core components
   - **Files:** 34+ TSX components
   - **Status:** Active, production-ready
   - **Build:** Vite + React SWC

2. **Vue.js** (Legacy ⚠️)
   - **Location:** `src/features/risk-intelligence/`
   - **Usage:** Risk intelligence dashboard features
   - **Files:** 37 Vue components
   - **Status:** Legacy, maintain but don't extend
   - **Migration:** Gradual to React

3. **Vanilla JavaScript** (Legacy ⚠️)
   - **Location:** `app/static/js/`
   - **Usage:** Input pages, summary pages, legacy features
   - **Files:** 150+ JS files
   - **Status:** Legacy, maintain but don't extend
   - **Migration:** Gradual to React (where feasible)

---

## ✅ Canonical Stack: React + TypeScript

### Why React + TypeScript?

1. **Already in Production**
   - Results page uses React + TS
   - 34+ components already built
   - Type safety with TypeScript

2. **Modern Tooling**
   - Vite for fast builds
   - React SWC for fast compilation
   - Vitest for testing
   - Storybook for component development

3. **Ecosystem**
   - Large community and resources
   - Strong TypeScript support
   - Rich component libraries

4. **Consistency**
   - Results page already React
   - Easier to maintain one stack
   - Better developer experience

### Technology Stack

- **Framework:** React 18.3.1
- **Language:** TypeScript 5.6.3
- **Build Tool:** Vite 7.0.4
- **Styling:** Tailwind CSS 3.4.17
- **Charts:** Recharts 3.1.2
- **Icons:** Lucide React
- **Animation:** Motion 12.23.12
- **Testing:** Vitest + Testing Library

### File Structure

```
src/
├── components/        # React components (TSX)
├── pages/            # Page components (TSX)
├── hooks/            # React hooks (TS)
├── services/         # API services (TS)
├── utils/            # Utilities (TS/JS)
├── types/            # TypeScript types
└── features/         # Feature modules (mixed - Vue legacy)
```

---

## ⚠️ Legacy Stacks

### Vue.js (Legacy)

**Location:** `src/features/risk-intelligence/`

**Status:** 
- ⚠️ **DO NOT** create new Vue components
- ✅ Maintain existing Vue components
- 🔄 Migrate to React when feasible
- 📦 **Summary components archived** (see [Summary Page Strategy](./SUMMARY_PAGE_STRATEGY.md))

**Migration Priority:**
1. Low priority (features work)
2. Migrate when:
   - Component needs major refactor
   - New feature requires integration
   - Performance issues arise

**Migration Guide:**
See "Vue → React Migration" section below.

**Special Case - Summary Page:**
- Vue summary components have been archived
- Summary page uses Vanilla JS business logic in `app/static/js/summary/`
- See [Summary Page Strategy](./SUMMARY_PAGE_STRATEGY.md) for details

### Vanilla JavaScript (Legacy)

**Location:** `app/static/js/`

**Status:**
- ⚠️ **DO NOT** create new vanilla JS modules
- ✅ Maintain existing JS files
- 🔄 Migrate to React when feasible

**Migration Priority:**
1. Very low priority (many legacy pages)
2. Migrate when:
   - Page needs major redesign
   - New feature requires modern stack
   - Maintenance burden too high

---

## 📋 Development Rules

### For New Development

1. **MUST use React + TypeScript** for:
   - New pages
   - New components
   - New features
   - Major refactors

2. **MUST NOT** create:
   - New Vue components
   - New vanilla JS modules (unless absolutely necessary)
   - Mixed stack features

3. **File Naming:**
   - React components: `ComponentName.tsx`
   - TypeScript utilities: `utilityName.ts`
   - Types: `types.ts` or `*.types.ts`

4. **Component Structure:**
   ```typescript
   // ComponentName.tsx
   import React from 'react';
   import { ComponentProps } from './types';
   
   export function ComponentName(props: ComponentProps) {
     // Component implementation
   }
   ```

### For Legacy Code

1. **Maintenance:**
   - Fix bugs in Vue/vanilla JS
   - Keep existing functionality working
   - No new features in legacy code

2. **Refactoring:**
   - When refactoring, consider migrating to React
   - Evaluate effort vs. benefit
   - Document migration decision

---

## 🔄 Migration Strategy

### Vue → React Migration

#### Step 1: Component Analysis
1. Identify Vue component dependencies
2. Map Vue props → React props
3. Map Vue state → React state/hooks
4. Map Vue lifecycle → React useEffect

#### Step 2: Create React Component
```typescript
// Before (Vue)
<template>
  <div class="card">
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
  </div>
</template>

<script>
export default {
  props: ['title', 'description']
}
</script>

// After (React)
import React from 'react';

interface CardProps {
  title: string;
  description: string;
}

export function Card({ title, description }: CardProps) {
  return (
    <div className="card">
      <h2>{title}</h2>
      <p>{description}</p>
    </div>
  );
}
```

#### Step 3: Replace Usage
1. Update imports
2. Update component usage
3. Test thoroughly
4. Remove Vue component

#### Migration Checklist
- [ ] Component functionality preserved
- [ ] Props/types defined
- [ ] State management migrated
- [ ] Lifecycle hooks converted
- [ ] Styling preserved
- [ ] Tests updated
- [ ] Documentation updated

### Vanilla JS → React Migration

#### Approach
1. Identify page/feature to migrate
2. Create React page component
3. Migrate functionality incrementally
4. Keep legacy JS until migration complete
5. Remove legacy JS after verification

#### Example: Input Page Migration
- Current: `app/static/js/v20/` (vanilla JS)
- Target: `src/pages/InputPage.tsx` (React)
- Strategy: Gradual migration, feature by feature

---

## 🏗️ Build & Development

### Development

```bash
# Start Vite dev server (React)
npm run dev

# Type checking
npm run typecheck

# Linting
npm run lint

# Testing
npm run test
```

### Production Build

```bash
# Build React app
npm run build

# Output: dist/ folder
# Served by FastAPI at /results
```

### File Organization

**React Components:**
- `src/components/` - Reusable components
- `src/pages/` - Page components
- `src/hooks/` - Custom React hooks
- `src/services/` - API services
- `src/types/` - TypeScript types

**Legacy (Maintain Only):**
- `src/features/risk-intelligence/` - Vue components (legacy)
- `app/static/js/` - Vanilla JS (legacy)

---

## 📝 Component Guidelines

### React Component Best Practices

1. **Functional Components:**
   ```typescript
   export function ComponentName(props: Props) {
     // Implementation
   }
   ```

2. **TypeScript Types:**
   ```typescript
   interface ComponentProps {
     title: string;
     optional?: number;
   }
   ```

3. **Hooks:**
   ```typescript
   import { useState, useEffect } from 'react';
   
   export function Component() {
     const [state, setState] = useState<string>('');
     useEffect(() => { /* ... */ }, []);
   }
   ```

4. **Styling:**
   - Use Tailwind CSS classes
   - Component-specific styles in CSS modules if needed
   - Avoid inline styles

---

## 🚫 What NOT to Do

1. ❌ **Don't create new Vue components**
2. ❌ **Don't create new vanilla JS modules** (unless absolutely necessary)
3. ❌ **Don't mix stacks in same feature**
4. ❌ **Don't duplicate functionality** across stacks
5. ❌ **Don't break existing functionality** during migration

---

## 📅 Migration Timeline

### Phase 1: Strategy (Current) ✅
- [x] Document current state
- [x] Define canonical stack
- [x] Create migration guidelines

### Phase 2: Stabilization (Ongoing)
- [ ] Ensure all new features use React
- [ ] Maintain legacy code
- [ ] Monitor migration opportunities

### Phase 3: Gradual Migration (Future)
- [ ] Migrate Vue components when refactoring
- [ ] Migrate vanilla JS pages when redesigning
- [ ] Prioritize high-value migrations

### Phase 4: Completion (Future)
- [ ] All new code in React
- [ ] Legacy code maintained but not extended
- [ ] Full React stack

---

## 🔍 Decision Log

### Why React over Vue?

1. **Already in use** - Results page is React
2. **TypeScript support** - Better type safety
3. **Ecosystem** - Larger community, more resources
4. **Consistency** - One stack easier to maintain

### Why not keep Vue?

1. **Fragmentation** - Two frameworks harder to maintain
2. **Team knowledge** - React more common
3. **Integration** - React components easier to integrate
4. **Future-proof** - React has stronger long-term support

### Why not migrate everything now?

1. **Risk** - Big-bang migration too risky
2. **Effort** - Gradual migration more manageable
3. **Stability** - Legacy code works, don't break it
4. **ROI** - Migrate when refactoring anyway

---

## 📚 Resources

### React + TypeScript
- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Documentation](https://vitejs.dev)

### Migration Guides
- [Vue to React Migration Guide](https://react.dev/learn/thinking-in-react)
- Internal migration examples (to be added)

---

## ✅ Acceptance Criteria

- [x] Canonical stack defined (React + TypeScript)
- [x] Legacy stacks documented (Vue, Vanilla JS)
- [x] Development rules established
- [x] Migration strategy defined
- [ ] All new features use React
- [ ] Legacy code maintained but not extended

---

**Last Updated:** 2024  
**Next Review:** Q2 2024  
**Maintained By:** RISKCAST Engineering Team

