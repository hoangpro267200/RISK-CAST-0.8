# RISKCAST Enterprise Risk Intelligence Platform - Audit Report

**Audit Date**: January 21, 2026  
**Audit Scope**: Full System End-to-End Review  
**Platform Version**: v19.0.0 (package.json: riskcast-7@0.0.0)

---

## 1. Executive Summary

### Maturity Ratings (0-10)

| Dimension | Score | Assessment |
|-----------|-------|------------|
| **Product UX** | 7/10 | Good UI but overcomplicated layouts, missing consistent states |
| **Correctness** | 4/10 | **CRITICAL**: Mock data generation when API fails |
| **Architecture** | 7/10 | Good adapter pattern, but multiple storage keys |
| **UX/Information Density** | 6/10 | Too verbose, needs compact SaaS density |
| **Security** | 7/10 | Proper session handling, but localStorage for data |
| **Observability** | 5/10 | Basic middleware, missing structured tracing |
| **SaaS Readiness** | 5/10 | No multi-tenant, limited audit logging |

### Top 10 Blocking Issues (MUST-FIX)

| # | Issue | Severity | File Location |
|---|-------|----------|---------------|
| 1 | **FAKE DATA GENERATION**: Summary page generates random data when API unavailable | CRITICAL | `src/components/summary/RiskcastSummary.tsx:481-610` |
| 2 | TypeScript compilation failures (100+ errors) | HIGH | Multiple files |
| 3 | Mock data used in fixtures and tests that could leak to production | HIGH | `src/fixtures/*.ts`, `src/data/mockData.ts` |
| 4 | Multiple localStorage keys for state (not single source of truth) | HIGH | `RISKCAST_STATE`, `RISKCAST_CASE_V1`, `RISKCAST_RESULTS_V2` |
| 5 | Test failures (3 failing tests in test suite) | HIGH | `src/adapters/adaptResultV2.test.ts`, `src/__tests__/*.tsx` |
| 6 | Missing schema validation on engine responses | MEDIUM | `src/adapters/adaptResultV2.ts` |
| 7 | Large bundle sizes (vendor-charts: 743KB) | MEDIUM | `vite.config.js` |
| 8 | No route-level error boundaries | MEDIUM | `src/App.tsx` |
| 9 | Inconsistent empty states across tabs | MEDIUM | `src/pages/ResultsPage.tsx` |
| 10 | No correlation ID propagation from backend | MEDIUM | Entire stack |

### Top 10 High-Impact Improvements (SHOULD-FIX)

| # | Improvement | Impact | Location |
|---|-------------|--------|----------|
| 1 | Remove all mock/random data generation from production paths | Trust | Summary/Results |
| 2 | Consolidate localStorage keys to single `RISKCAST_CASE_V1` | Consistency | Domain layer |
| 3 | Add Zod/Yup schema validation for engine responses | Safety | Adapter layer |
| 4 | Implement compact SaaS-style information density | UX | Results page |
| 5 | Add proper React Router for client-side navigation | Performance | App.tsx |
| 6 | Implement request correlation IDs end-to-end | Debugging | Middleware |
| 7 | Add chart lazy loading with intersection observer | Performance | Charts |
| 8 | Reduce vendor-charts bundle via tree-shaking | Performance | Vite config |
| 9 | Add multi-tenant org/workspace foundation | SaaS | Backend models |
| 10 | Implement comprehensive audit logging | Compliance | Backend |

---

## 2. Evidence-Based Findings

### 2.1 CRITICAL: Fake Data Generation in Summary Page

**Severity**: CRITICAL  
**Impact**: Users may make business decisions based on fabricated risk scores  
**File**: `src/components/summary/RiskcastSummary.tsx`  
**Lines**: 461-698

**Root Cause**: When the API call to `/api/v1/risk/v2/analyze` fails, the code generates RANDOM mock data:

```typescript:481:610:src/components/summary/RiskcastSummary.tsx
const riskScoreValue = Math.min(95, Math.max(15, baseRisk + Math.floor(Math.random() * 15) - 7));
// ... 
{ name: 'Mode Reliability', score: Math.floor(Math.random() * 25) + 55, ... }
{ name: 'Carrier Performance', score: Math.floor(Math.random() * 30) + 50, ... }
// ... continues for all 16 layers
```

**Evidence**:
- Line 481: `Math.random()` used for risk score
- Lines 507-517: `Math.random()` for profile factors
- Lines 568-587: `Math.random()` for ALL 16 risk layers
- Lines 600-610: `Math.random()` for timeline projections

**Proposed Fix**:
1. Remove all `Math.random()` calls from production paths
2. When API fails, show error state with "Retry" button
3. Never display fabricated data - use `null`/empty states instead
4. Add `engine_version: 'mock'` check in Results page to reject mock data

### 2.2 TypeScript Compilation Failures

**Severity**: HIGH  
**Impact**: Type safety compromised, potential runtime errors  
**Command**: `npm run typecheck`  
**Exit Code**: 2 (Failed)  
**Error Count**: 100+ errors

**Sample Errors**:

| File | Error |
|------|-------|
| `src/components/ExecutiveSummary.tsx:168` | Type '"CRITICAL"' not assignable to RiskLevel |
| `src/components/insurance/CheckoutFlow.tsx:272` | Property 'jsx' does not exist on style |
| `src/pages/input/components/*.tsx` | Property 'textDefault' does not exist on tokens |
| `src/__tests__/sprint1.test.tsx:32` | Type '"HIGH"' not assignable (should be '"High"') |

**Root Cause**: 
- RiskLevel enum inconsistency (some use 'HIGH', others use 'High')
- Missing design token properties
- Test fixtures using wrong type casing

**Proposed Fix**:
1. Standardize RiskLevel enum to Title Case: `'Low' | 'Medium' | 'High' | 'Critical'`
2. Add missing design tokens to `src/ui/design-tokens/index.ts`
3. Update test fixtures to match type definitions

### 2.3 Multiple localStorage Keys (State Fragmentation)

**Severity**: HIGH  
**Impact**: Data inconsistency between pages, stale cache issues

**Evidence (from Grep)**:

| Key | Purpose | Files Using |
|-----|---------|-------------|
| `RISKCAST_STATE` | Legacy input state | InputPage.tsx, RiskcastSummary.tsx |
| `RISKCAST_CASE_V1` | Canonical DomainCase | case.migrate.ts |
| `RISKCAST_RESULTS_V2` | Analysis results | ResultsPage.tsx, RiskcastSummary.tsx |
| `RISKCAST_DRAFT` | Autosave draft | useAutosave.ts |
| `summary_modules_state` | Module toggles | RiskcastSummary.tsx |

**Root Cause**: Incremental migration created multiple storage keys without cleanup.

**Proposed Fix**:
1. Use ONLY `RISKCAST_CASE_V1` as canonical source
2. Results should be transient (not persisted) or in `RISKCAST_CASE_V1.results`
3. Remove `RISKCAST_STATE` references after migration
4. Implement `StorageService` abstraction to prevent direct localStorage access

### 2.4 Test Failures

**Severity**: HIGH  
**Impact**: CI/CD pipeline would fail, quality regression risk  
**Test Results**: 3 failed, 123 passed (126 total)

**Failed Tests**:

1. `src/adapters/adaptResultV2.test.ts:274`
   - Expected `canonicalDriversFrom` to be `'empty'`, got `'drivers'`
   - Test expectation mismatch with current adapter behavior

2. `src/__tests__/sprint2-integration.test.tsx:148`
   - Expected `isSynthetic` to be `false`, got `true`
   - Synthetic lossCurve detection logic changed

3. `src/domain/__tests__/case.validation.test.ts:93`
   - Expected 0 critical issues, got 1
   - Validation rules stricter than test data

**Proposed Fix**:
1. Update test assertions to match current adapter contract
2. Review and align validation rules with test fixtures
3. Add test coverage for synthetic data detection

### 2.5 Missing Empty States

**Severity**: MEDIUM  
**Impact**: Poor UX when data is unavailable

**Evidence in ResultsPage.tsx**:
- Line 591: `dataReliabilityDomains` is always empty array
- Line 1274-1283: Generic empty state for scenarios
- No consistent empty state component usage

**Proposed Fix**:
1. Use `<EmptyState />` component consistently
2. Each chart/panel should have explicit empty state
3. Show "No data available" with actionable guidance

---

## 3. Data Lineage & Consistency Map

### Canonical Data Model: DomainCase

The system uses `DomainCase` (defined in `src/domain/case.schema.ts`) as the single source of truth:

```typescript
interface DomainCase {
  caseId: string;
  pol: PortCode;
  pod: PortCode;
  transportMode: TransportMode;
  containerType: string;
  etd: string;
  eta?: string;
  transitTimeDays: number;
  cargoType: string;
  cargoValue: number;
  // ... other fields
}
```

### Field Flow Tracing

| Field | Input Page Source | Summary Display | Engine Payload | Engine Response | Results Display |
|-------|-------------------|-----------------|----------------|-----------------|-----------------|
| `cargoValue` | `value.insuranceValue` | `data.value` | `shipment.cargo_value` | `shipment.cargo_value` | `viewModel.overview.shipment.cargoValue` |
| `pol` | `route.pol` | `data.trade.pol` | `shipment.pol_code` | `shipment.pol_code` | `viewModel.overview.shipment.pol` |
| `riskScore` | N/A | N/A | N/A | `profile.score` > `risk_score` > `overall_risk` | `viewModel.overview.riskScore.score` |
| `layers` | N/A | N/A | N/A | `layers[]` | `viewModel.breakdown.layers[]` |
| `expectedLoss` | N/A | N/A | Computed from `cargoValue` | `loss.expectedLoss` | `viewModel.loss.expectedLoss` |

### Adapter Precedence Rules (adaptResultV2.ts)

```
Risk Score: profile.score → risk_score → overall_risk → 0
Risk Level: profile.level → risk_level → "Unknown"
Confidence: profile.confidence → confidence → 0
Drivers: drivers → risk_factors → factors → []
```

### Storage Key Mapping

```
Input Page → localStorage['RISKCAST_STATE'] (legacy)
          → localStorage['RISKCAST_CASE_V1'] (canonical)
          
Summary → Reads RISKCAST_CASE_V1
        → Writes RISKCAST_RESULTS_V2 after analysis
        
Results → Reads RISKCAST_RESULTS_V2
        → Falls back to API /results/data
```

---

## 4. UX/IA Redesign Suggestions

### Current Problems

1. **Results Page Density**: Too much whitespace, requires scrolling
2. **Overview Tab**: ~1000 lines of JSX, monolithic
3. **Chart Overload**: All charts rendered regardless of data
4. **No Progressive Disclosure**: Everything shown at once

### Proposed Restructure

#### Overview Tab (Executive View)

```
┌─────────────────────────────────────────────────────────────┐
│ KPI ROW (single line):                                      │
│ [Risk Score: 67] [EL: $12K] [VaR95: $18K] [Confidence: 85%] │
├─────────────────────────────────────────────────────────────┤
│ KEY INSIGHT (1 sentence + action button)                    │
│ "MEDIUM risk due to port congestion. Consider timing."  [→] │
├─────────────────────────────────────────────────────────────┤
│ 2-COL GRID:                                                 │
│ ┌─────────────────┐ ┌─────────────────┐                    │
│ │ Risk Radar      │ │ Top 3 Drivers   │                    │
│ │ (compact 200px) │ │ • Carrier: +32% │                    │
│ │                 │ │ • Cargo: +28%   │                    │
│ │                 │ │ • Route: +22%   │                    │
│ └─────────────────┘ └─────────────────┘                    │
├─────────────────────────────────────────────────────────────┤
│ COLLAPSIBLE: Shipment Details (default collapsed)           │
└─────────────────────────────────────────────────────────────┘
```

#### Analytics Tab (Deep Dive)

```
┌─────────────────────────────────────────────────────────────┐
│ ACCORDION SECTIONS (expand on click):                       │
│                                                             │
│ ▼ Financial Risk Analysis                                   │
│   [Loss Distribution] [VaR Table]                          │
│                                                             │
│ ▷ Algorithm Explainability (collapsed)                      │
│                                                             │
│ ▷ Insurance Underwriting (collapsed)                        │
│                                                             │
│ ▼ Layer Breakdown                                          │
│   [LayersTable - always visible]                           │
└─────────────────────────────────────────────────────────────┘
```

#### Decisions Tab (Action Focus)

```
┌─────────────────────────────────────────────────────────────┐
│ PRIMARY ACTION CARD (highlighted):                          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 🎯 Recommended: Add Insurance Coverage                  │ │
│ │    Risk Reduction: -15 pts | Cost: $2.5K | ROI: 6.0x   │ │
│ │    [Learn More] [Apply Now]                             │ │
│ └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ COMPARISON TABLE (3 cols):                                  │
│ | Option          | Risk Δ | Cost   | Status      |        │
│ | Insurance       | -15    | $2.5K  | RECOMMENDED |        │
│ | Timing Adjust   | -10    | $0.5K  | OPTIONAL    |        │
│ | Route Change    | -12    | $1.2K  | EVALUATE    |        │
└─────────────────────────────────────────────────────────────┘
```

### Spacing & Typography Tokens

```css
/* Compact SaaS tokens */
--space-xs: 4px;   /* Reduce from 8px */
--space-sm: 8px;   /* Reduce from 12px */
--space-md: 12px;  /* Reduce from 16px */
--space-lg: 16px;  /* Reduce from 24px */

--text-xs: 10px;   /* For labels */
--text-sm: 12px;   /* For body */
--text-base: 14px; /* For emphasis */
--text-lg: 18px;   /* For headings */

--card-padding: 12px; /* Down from 16-24px */
--card-gap: 8px;      /* Down from 16px */
```

---

## 5. Roadmap

### Week 1: Stabilize Correctness + Remove Mocks + Schema Validation

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| 1-2 | **Remove fake data generation** | No `Math.random()` in production paths; API failure shows error state |
| 3 | **Fix TypeScript errors** | `npm run typecheck` exits with code 0 |
| 4 | **Consolidate storage keys** | Single `RISKCAST_CASE_V1` key; migration script for existing users |
| 5 | **Add Zod schema validation** | Engine responses validated before adapter; invalid data rejected |

**Acceptance Criteria**:
- [ ] `npm run typecheck` passes
- [ ] `npm run test:run` passes (all 126 tests)
- [ ] No `Math.random()` in src/ (except test fixtures)
- [ ] Schema validation errors logged with correlation ID

### Week 2: UX Density + Performance + Empty States

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| 1-2 | **Compact Overview tab** | KPI row + insight + 2-col grid; under 800px viewport height |
| 3 | **Progressive disclosure** | Accordion sections in Analytics; charts lazy-loaded |
| 4 | **Consistent empty states** | Every panel uses `<EmptyState />` with actionable text |
| 5 | **Bundle optimization** | vendor-charts < 500KB; total JS < 1.5MB |

**Acceptance Criteria**:
- [ ] Lighthouse Performance score > 80
- [ ] No "undefined" or blank panels
- [ ] All tabs render in < 200ms (React DevTools profiler)

### Week 3: Auth Hardening + Multi-Tenant Foundation + Observability

| Day | Task | Acceptance Criteria |
|-----|------|---------------------|
| 1-2 | **Auth token in httpOnly cookie** | No tokens in localStorage; CSRF protection enabled |
| 3 | **Add org/workspace models** | Database schema supports multi-tenant; FK constraints |
| 4 | **Correlation ID propagation** | X-Request-ID flows from frontend → backend → logs |
| 5 | **Audit logging foundation** | Critical actions logged with user_id, timestamp, action_type |

**Acceptance Criteria**:
- [ ] Session cookie has `httpOnly`, `Secure`, `SameSite=Strict`
- [ ] Audit log table populated for login/logout/analysis events
- [ ] All logs include `request_id` field

---

## 6. Definition of Done for World-Class SaaS

### Code Quality
- [ ] TypeScript strict mode passes with zero errors
- [ ] Test coverage > 80% for critical paths (adapter, domain, auth)
- [ ] No `any` types in production code
- [ ] ESLint passes with zero warnings

### Data Integrity
- [ ] Single source of truth (DomainCase) for all state
- [ ] All engine data validated before display
- [ ] No mock/fake data in production paths
- [ ] Clear data lineage documentation

### UX Excellence
- [ ] Lighthouse Performance > 85
- [ ] Lighthouse Accessibility > 90
- [ ] Consistent loading/empty/error states
- [ ] Mobile-responsive (down to 375px)
- [ ] Keyboard navigable

### Security
- [ ] Auth tokens in httpOnly cookies only
- [ ] CSRF protection enabled
- [ ] Rate limiting on all endpoints
- [ ] Input validation (frontend + backend)
- [ ] Secrets in environment variables only

### Observability
- [ ] Structured JSON logging
- [ ] Correlation IDs on all requests
- [ ] Error tracking integration (Sentry/similar)
- [ ] Performance metrics dashboard

### SaaS Readiness
- [ ] Multi-tenant data isolation
- [ ] Role-based access control (RBAC)
- [ ] Audit logging for compliance
- [ ] API versioning strategy
- [ ] Feature flags infrastructure

---

## Appendix A: File Reference Index

| Finding | Primary Files |
|---------|---------------|
| Fake data generation | `src/components/summary/RiskcastSummary.tsx` |
| Type errors | `src/components/ExecutiveSummary.tsx`, `src/components/insurance/*.tsx` |
| Mock data | `src/data/mockData.ts`, `src/fixtures/*.ts` |
| Storage keys | `src/domain/case.migrate.ts`, `src/pages/*.tsx` |
| Adapter | `src/adapters/adaptResultV2.ts` |
| Auth store | `src/store/authStore.tsx`, `src/api/auth.ts` |
| Auth config | `src/config/auth.ts`, `app/config/auth.py` |
| Backend main | `app/main.py` |
| Test failures | `src/__tests__/*.tsx`, `src/adapters/adaptResultV2.test.ts` |

## Appendix B: Command Reference

```bash
# Install dependencies (requires --legacy-peer-deps due to Storybook/Vite conflict)
npm install --legacy-peer-deps

# TypeScript check (currently FAILS with 100+ errors)
npm run typecheck

# Build (PASSES despite type errors)
npm run build

# Test (3 failing, 123 passing)
npm run test:run

# Dev server
npm run dev
```

---

**Report Prepared By**: Cursor Opus 4.5 (Principal Engineer Mode)  
**Confidence Level**: HIGH (evidence-based, code-verified)
