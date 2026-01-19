# UI SYNCHRONIZATION REPORT
## Input / Summary / Results Pages - Data Model & Design Alignment

**Date**: 2026-01-16  
**Author**: System Architecture Analysis  
**Priority**: P0 (Critical - Blocks Consistency & User Experience)  
**Scope**: Frontend UI/UX synchronization across 3 main pages

---

## EXECUTIVE SUMMARY

- **Critical Finding**: 3 pages (Input/Summary/Results) use **incompatible data schemas** and **different design systems**, causing data loss, confusion, and poor UX flow
- **Root Cause**: 
  - Input: HTML form → backend transform → `shipment_payload` (flat dict)
  - Summary: React component → `ShipmentData` type (nested structure)
  - Results: React component → `ResultsViewModel` (normalized from engine)
- **Impact**: Users enter data in Input but see **different values** in Summary/Results; labels/units inconsistent; no traceability
- **Solution**: Implement **Single Source of Truth** (Case/Domain Schema) + unified mapper layer + shared design tokens
- **Timeline**: 4-6 PRs, sequential implementation to avoid breaking changes
- **Risk**: Medium - requires careful migration to avoid regressions

---

## PHẦN A — CHẨN ĐOÁN (VẤN ĐỀ HIỆN TẠI)

### A1. Data Flow Analysis (Input → Summary → Results)

#### Input Page (HTML Template + JS Controller)
- **Source**: `/app/templates/input/input_v20.html` + JS controller
- **State**: Form fields → POST `/input_v20/submit`
- **Backend Transform**: `app/main.py:278-347` → builds `shipment_payload` dict
- **Payload Schema** (from `main.py`):
  ```python
  {
    "transport_mode": str,  # "ocean_fcl"
    "cargo_type": str,      # "general"
    "route": str,           # "VNSGN_CNSHA"
    "pol_code": str,        # "VNSGN"
    "pod_code": str,        # "CNSHA"
    "incoterm": str,        # "FOB"
    "container": str,       # "40HC"
    "packaging": str,       # "palletized"
    "priority": str,        # "speed"
    "packages": int,        # 0
    "etd": str,             # date string
    "eta": str,             # date string
    "transit_time": float,  # 0.0
    "cargo_value": float,   # OR "insuranceValue" OR "shipment_value"
    "carrier_rating": float,
    "weather_risk": float,
    "port_risk": float,
    "container_match": float,
    "shipper": str,
    "consignee": str,
    "forwarder": str,
    "risk_score": float,    # placeholder 7.2
    "risk_level": str,      # "Medium"
  }
  ```
- **Storage**: `session["shipment_state"]` + `session["RISKCAST_STATE"]` + `memory_system.set("latest_shipment")`
- **Redirect**: `/overview` (Summary page)

#### Summary Page (React Component)
- **Source**: `src/pages/SummaryPage.tsx` → `src/components/summary/RiskcastSummary.tsx`
- **State Source**: `localStorage.getItem('RISKCAST_STATE')` OR `initialData` prop
- **Schema**: `ShipmentData` type (`src/components/summary/types.ts`)
  ```typescript
  {
    shipmentId: string;
    trade: {
      pol: string; polName: string; polCity: string; polCountry: string;
      pod: string; podName: string; podCity: string; podCountry: string;
      mode: 'AIR' | 'SEA' | 'ROAD' | 'RAIL' | 'MULTIMODAL';
      service_route: string; carrier: string; container_type: string;
      etd: string; eta: string; transit_time_days: number;
      incoterm: string; incoterm_location: string; priority: string;
    };
    cargo: {
      cargo_type: string; cargo_category: string;
      hs_code: string; hs_chapter: string;
      packing_type: string; packages: number;
      gross_weight_kg: number; net_weight_kg: number; volume_cbm: number;
      stackability: boolean; temp_control_required: boolean; is_dg: boolean;
    };
    seller: { name, company, email, phone, country, city, address, tax_id };
    buyer: { name, company, email, phone, country, city, address, tax_id };
    value: number;
  }
  ```
- **Transform Logic**: `transformInputStateToSummary()` in `RiskcastSummary.tsx:173-266`
  - Maps `state.transport.pol` → `trade.pol`
  - Maps `cargo.insuranceValue || cargo.value || cargo.cargo_value` → `value`
  - Manual port code → name/city/country mapping (hardcoded dict)
- **Actions**: Inline editing, save draft, **Run Analysis** → POST to `/api/v1/risk/v2/analyze`
- **Output**: Stores `RISKCAST_RESULTS_V2` in `localStorage`, redirects to `/results`

#### Results Page (React Component)
- **Source**: `src/pages/ResultsPage.tsx`
- **State Source**: `localStorage.getItem('RISKCAST_RESULTS_V2')` OR `/results/data` API
- **Schema**: `ResultsViewModel` (`src/types/resultsViewModel.ts`)
  ```typescript
  {
    overview: {
      shipment: ShipmentViewModel;  // Different from ShipmentData!
      riskScore: RiskScoreViewModel;
      profile: RiskProfileViewModel;
      reasoning: { explanation: string };
    };
    breakdown: { layers, factors };
    algorithm?: AlgorithmExplainabilityData;
    timeline: TimelineViewModel;
    decisions: DecisionsViewModel;
    loss: LossViewModel | null;
    drivers: RiskDriverViewModel[];
    scenarios: ScenarioViewModel[];
    meta: ResultsMetaViewModel;
  }
  ```
- **Transform Logic**: `adaptResultV2()` in `src/adapters/adaptResultV2.ts`
  - Maps engine output → `ResultsViewModel`
  - `ShipmentViewModel` has: `{ id, route, pol, pod, carrier, etd, eta, transitTime, container, cargo, cargoType, containerType, packaging, incoterm, cargoValue }`
- **Display**: Uses `ResultsViewModel` directly (no additional transform)

### A2. Data Gap Analysis (Field Mismatches)

| Field | Input (shipment_payload) | Summary (ShipmentData) | Results (ShipmentViewModel) | Root Cause | Impact |
|-------|--------------------------|------------------------|-----------------------------|------------|--------|
| **POL/POD** | `pol_code`, `pod_code` (codes only) | `trade.pol`, `trade.pod` (codes) + `polName`, `polCity`, `polCountry` | `overview.shipment.pol`, `pod` (string or `{code, name}`) | Summary uses hardcoded port mapping; Results may have object | **HIGH**: Port display inconsistent |
| **Transport Mode** | `transport_mode` ("ocean_fcl") | `trade.mode` ("SEA") | `overview.shipment.route` (derived) | Input uses snake_case; Summary uses UPPERCASE enum | **MEDIUM**: Mode mapping errors |
| **Cargo Value** | `cargo_value` OR `insuranceValue` OR `shipment_value` | `value` (number) | `overview.shipment.cargoValue` (number or `{amount, currency}`) | Multiple field names in Input; no validation | **HIGH**: Value may be 0 if field name mismatch |
| **Cargo Type** | `cargo_type` (string) | `cargo.cargo_type` (string) | `overview.shipment.cargoType` (string) | Mostly consistent | **LOW** |
| **Container** | `container` ("40HC") | `trade.container_type` ("40HC") | `overview.shipment.container`, `containerType` | Field name differs | **MEDIUM**: Display inconsistency |
| **Packages** | `packages` (int) | `cargo.packages` (int) | Not in ShipmentViewModel | Missing in Results | **LOW**: Not shown in Results |
| **Weight/Volume** | Not captured | `cargo.gross_weight_kg`, `volume_cbm` | Not in ShipmentViewModel | Missing in Input and Results | **MEDIUM**: Data loss |
| **ETD/ETA** | `etd`, `eta` (date strings) | `trade.etd`, `trade.eta` (date strings) | `overview.shipment.etd`, `eta` (ISO or undefined) | Date validation differs | **MEDIUM**: Invalid dates handled differently |
| **Incoterm** | `incoterm` ("FOB") | `trade.incoterm` ("FOB") | `overview.shipment.incoterm` ("FOB") | Consistent | **LOW** |
| **Incoterm Location** | Not captured | `trade.incoterm_location` (string) | Not in ShipmentViewModel | Missing in Input/Results | **LOW** |
| **Transit Time** | `transit_time` (float, days) | `trade.transit_time_days` (number) | `overview.shipment.transitTime` (number, days) | Unit naming differs | **LOW**: Semantically same |
| **HS Code** | Not captured | `cargo.hs_code`, `hs_chapter` | Not in ShipmentViewModel | Missing in Input/Results | **MEDIUM**: Important for risk calculation |
| **Seller/Buyer** | `shipper`, `consignee`, `forwarder` (strings) | `seller.*`, `buyer.*` (full objects with name, company, email, phone, country, city, address, tax_id) | Not in ShipmentViewModel | Input has minimal fields; Summary has full structure | **HIGH**: Party info lost in Results |
| **Priority** | `priority` ("speed") | `trade.priority` ("normal") | Not in ShipmentViewModel | Default values differ | **LOW** |

### A3. UI/UX Gap Analysis

#### Layout & Grid
- **Input**: Custom CSS grid in `input_v20.css` (2-column form layout), sidebar navigation
- **Summary**: React component with Tailwind-style classes, card-based sections, no grid system consistency
- **Results**: React component with Tailwind classes, tab-based layout (overview/analytics/decisions)
- **Gap**: No shared grid system; spacing units differ (Input uses custom vars, Summary/Results use Tailwind)

#### Typography
- **Input**: `--font-family`, `--font-h1`, `--font-h2`, `--font-body` (CSS vars in `tokens.css`)
- **Summary**: Uses Tailwind text classes (`text-2xl`, `text-sm`) - NOT using design tokens
- **Results**: Uses Tailwind text classes - NOT using design tokens
- **Gap**: Typography scale defined but not enforced; inconsistent font sizes

#### Spacing
- **Input**: `--space-4`, `--space-8`, `--space-12`, etc. (CSS vars)
- **Summary**: Tailwind spacing (`p-4`, `mb-6`, etc.)
- **Results**: Tailwind spacing
- **Gap**: Design tokens exist but not used in React components

#### Component Styles
- **Input**: Glass morphism cards (`rc-glass-card`), neon accents, VisionOS-style
- **Summary**: Glass cards (`GlassCard` component), similar aesthetic but different implementation
- **Results**: Glass cards (`GlassCard` component), same as Summary
- **Gap**: Input uses CSS classes; Summary/Results use React components (better consistency)

#### Empty/Loading/Error States
- **Input**: No explicit empty state; form always has defaults
- **Summary**: Validation issues shown inline; `canAnalyze` calculated from completeness
- **Results**: `EmptyState` component with message; loading skeleton (`SkeletonResultsPage`); error message in state
- **Gap**: Inconsistent error handling and empty states

#### Colors & Status
- **Input**: Uses CSS vars (`--color-primary-neon`, `--status-success`, etc.)
- **Summary**: Uses Tailwind colors (`bg-blue-500`, `text-green-500`) - NOT using tokens
- **Results**: Uses Tailwind colors - NOT using tokens
- **Gap**: Color tokens defined but not used consistently

### A4. Interaction Flow Gaps

#### Step Order & Navigation
- **Input**: Form submission → `/overview` (Summary page)
- **Summary**: Inline editing → Save Draft → **Run Analysis** → `/results`
- **Results**: No back button to Summary; breadcrumb navigation exists
- **Gap**: Missing back navigation; no stepper/wizard UI

#### CTA Consistency
- **Input**: Submit button → "Submit" or "Run Analysis" (unclear)
- **Summary**: "Run Analysis" (primary), "Save Draft" (secondary)
- **Results**: "Refresh" (secondary), "Export" (menu)
- **Gap**: Primary action not consistent across pages

#### Autosave/Draft Behavior
- **Input**: No autosave; form state lost on refresh
- **Summary**: `saveState` tracked (`'saved' | 'saving' | 'unsaved' | 'error'`); saves to `localStorage`
- **Results**: No save functionality (read-only)
- **Gap**: Autosave only in Summary; Input needs draft persistence

#### Validation
- **Input**: HTML5 validation; no custom validation logic visible
- **Summary**: `getValidationIssues()` checks required fields; `completeness` calculated (20% minimum for analysis)
- **Results**: Validates data integrity (layer contributions, driver impact sum) but no user-facing validation
- **Gap**: Validation rules not shared; different thresholds

#### Back/Forward Behavior
- **Input**: Form reset button; no browser back/forward handling
- **Summary**: Browser back/forward may lose unsaved changes
- **Results**: URL-synced tab state (`useUrlTabState`); browser navigation works
- **Gap**: No unified navigation state management

### A5. Tác Hại (User Symptoms)

1. **Data Loss**: User enters cargo value as `insuranceValue` in Input → backend doesn't find it → Summary shows `0` → Results shows `0`
2. **Field Confusion**: User sees "POL/POD" in Input → "Origin/Destination" in Summary → "Route" in Results (different labels)
3. **Value Mismatch**: User enters `transport_mode = "air"` → Summary shows `mode = "AIR"` (OK) → Results shows route string (loss of mode info)
4. **Missing Fields**: User enters seller/buyer in Summary → Results doesn't display party info (data lost in transform)
5. **Validation Inconsistency**: Input allows empty cargo value → Summary requires 20% completeness → Results expects valid data (confusing)
6. **No Traceability**: User can't trace "where did this value come from?" - no run ID, version, timestamp displayed prominently

---

## PHẦN B — BÁO CÁO TÁI CẤU TRÚC

### B1. Current Architecture Snapshot

#### Data Contracts
1. **Input Payload** (`main.py:shipment_payload`)
   - Flat dictionary
   - Field names: `pol_code`, `cargo_value`, `transport_mode`
   - Backend transforms to `RISKCAST_STATE` (session storage)

2. **Summary View Model** (`ShipmentData` type)
   - Nested structure: `{ trade, cargo, seller, buyer, value }`
   - Field names: `trade.pol`, `cargo.cargo_type`
   - Stored in `localStorage` as `RISKCAST_STATE`

3. **Results Payload** (`ResultsViewModel`)
   - Slice-based: `{ overview, breakdown, timeline, decisions, loss, ... }`
   - Field names: `overview.shipment.pol`, `overview.shipment.cargoType`
   - Source: Engine output via `adaptResultV2()`

#### Component Tree & State Ownership

```
Input Page (HTML/JS)
  └─ Form fields (local DOM state)
      └─ POST /input_v20/submit
          └─ Backend: session["shipment_state"] + localStorage (client)

Summary Page (React)
  └─ RiskcastSummary component
      └─ State: ShipmentData (useState)
          └─ Source: localStorage.getItem('RISKCAST_STATE')
          └─ Transform: transformInputStateToSummary()
          └─ Save: localStorage.setItem('RISKCAST_STATE')
          └─ Action: POST /api/v1/risk/v2/analyze
              └─ Store: localStorage.setItem('RISKCAST_RESULTS_V2')

Results Page (React)
  └─ ResultsPage component
      └─ State: ResultsViewModel | null (useState)
          └─ Source: localStorage.getItem('RISKCAST_RESULTS_V2') OR /results/data
          └─ Transform: adaptResultV2()
          └─ Display: Direct use of viewModel
```

**Problem**: 3 separate state stores (session, localStorage `RISKCAST_STATE`, localStorage `RISKCAST_RESULTS_V2`) with no unified schema.

### B2. Gap Analysis Table

| Item | Input | Summary | Results | Root Cause | Fix Strategy | Priority |
|------|-------|---------|---------|------------|--------------|----------|
| **POL/POD** | `pol_code`, `pod_code` | `trade.pol`, `pod` + names | `overview.shipment.pol`, `pod` | Different field paths; Summary has hardcoded port mapping | Create `PortCode` type + lookup utility | **P0** |
| **Cargo Value** | `cargo_value` OR `insuranceValue` OR `shipment_value` | `value` | `overview.shipment.cargoValue` | Multiple field names in Input | Unify to single field name + validation | **P0** |
| **Container** | `container` | `trade.container_type` | `overview.shipment.container`, `containerType` | Field name mismatch | Unify to `containerType` | **P1** |
| **Packages/Weight/Volume** | Missing | `cargo.packages`, `gross_weight_kg`, `volume_cbm` | Missing | Not captured in Input | Add to Input form + domain schema | **P1** |
| **Seller/Buyer** | `shipper`, `consignee` (strings) | Full objects | Missing in Results | Input minimal; Results doesn't display | Add to domain schema + Results display | **P1** |
| **HS Code** | Missing | `cargo.hs_code`, `hs_chapter` | Missing | Not in Input | Add to Input form | **P2** |
| **Layout Grid** | Custom CSS grid | Tailwind classes | Tailwind classes | No shared system | Use design tokens + shared grid utility | **P1** |
| **Typography** | CSS vars | Tailwind text-* | Tailwind text-* | Tokens exist but not used | Enforce design tokens in React | **P1** |
| **Spacing** | CSS vars | Tailwind spacing | Tailwind spacing | Tokens exist but not used | Use CSS vars or Tailwind config aligned with tokens | **P1** |
| **Colors** | CSS vars | Tailwind colors | Tailwind colors | Tokens exist but not used | Use CSS vars or Tailwind theme aligned | **P1** |
| **Validation** | HTML5 only | Custom `getValidationIssues()` | Data integrity checks | Rules not shared | Create shared validation schema | **P1** |
| **Navigation** | Form submit → redirect | Run Analysis → redirect | No back button | No unified flow | Add stepper/wizard UI | **P2** |
| **Autosave** | None | localStorage | None | Inconsistent | Add autosave to Input; unified draft system | **P2** |
| **Traceability** | No run ID | No run ID | `meta.analysisId`, `meta.timestamp` | Only in Results | Add run ID to all pages | **P2** |

### B3. Proposed Target Design (North Star)

#### Single Source of Truth: Case/Domain Schema

Create `/src/domain/case.schema.ts`:

```typescript
import { z } from 'zod';

/**
 * Domain Case Schema - Single Source of Truth for all pages
 * This schema defines the canonical data structure for a risk analysis case.
 * All transforms (Input → Summary → Results) must use this as the contract.
 */

// Port code with lookup
export const PortCodeSchema = z.string().min(3).max(10);
export type PortCode = z.infer<typeof PortCodeSchema>;

// Party information
export const PartySchema = z.object({
  name: z.string().optional(),
  company: z.string().min(1, "Company name required"),
  email: z.string().email(),
  phone: z.string().min(1),
  country: z.string().min(2),
  city: z.string().optional(),
  address: z.string().optional(),
  tax_id: z.string().optional(),
});

// Domain Case Schema
export const DomainCaseSchema = z.object({
  // Metadata
  caseId: z.string().default(() => `CASE-${Date.now()}`),
  runId: z.string().optional(),
  version: z.string().default('1.0'),
  createdAt: z.string().datetime(),
  lastModified: z.string().datetime(),
  
  // Route & Transport
  pol: PortCodeSchema,
  pod: PortCodeSchema,
  transportMode: z.enum(['AIR', 'SEA', 'ROAD', 'RAIL', 'MULTIMODAL']),
  containerType: z.string().min(1, "Container type required"),
  serviceRoute: z.string().optional(),
  carrier: z.string().optional(),
  
  // Dates & Transit
  etd: z.string().datetime().or(z.string().regex(/^\d{4}-\d{2}-\d{2}$/)),
  eta: z.string().datetime().or(z.string().regex(/^\d{4}-\d{2}-\d{2}$/)).optional(),
  transitTimeDays: z.number().min(0).default(0),
  
  // Cargo
  cargoType: z.string().min(1, "Cargo type required"),
  cargoCategory: z.string().optional(),
  hsCode: z.string().optional(),
  packaging: z.string().optional(),
  packages: z.number().min(1, "Packages must be > 0"),
  grossWeightKg: z.number().min(0).optional(),
  netWeightKg: z.number().min(0).optional(),
  volumeCbm: z.number().min(0).optional(),
  
  // Value
  cargoValue: z.number().min(0, "Cargo value must be >= 0").default(0),
  currency: z.enum(['USD', 'VND']).default('USD'),
  
  // Terms
  incoterm: z.string().optional(),
  incotermLocation: z.string().optional(),
  priority: z.enum(['normal', 'express', 'urgent']).default('normal'),
  
  // Parties
  seller: PartySchema,
  buyer: PartySchema,
  forwarder: PartySchema.partial().optional(),
  
  // Modules (for analysis)
  modules: z.object({
    esg: z.boolean().default(true),
    weather: z.boolean().default(true),
    portCongestion: z.boolean().default(true),
    carrierPerformance: z.boolean().default(true),
    marketScanner: z.boolean().default(false),
    insurance: z.boolean().default(true),
  }).default({}),
});

export type DomainCase = z.infer<typeof DomainCaseSchema>;
```

#### Shared Case Schema + Validation + Formatting Utilities

Create `/src/domain/case.mapper.ts`:

```typescript
import type { DomainCase } from './case.schema';
import type { ShipmentData } from '@/components/summary/types';
import type { ResultsViewModel } from '@/types/resultsViewModel';

/**
 * Mapper Layer - Centralized Transformations
 * 
 * Rules:
 * - Input form state → DomainCase (normalize field names, validate, add defaults)
 * - DomainCase → ShipmentData (Summary view model)
 * - DomainCase → ShipmentViewModel (Results view model slice)
 * - Engine output → ResultsViewModel (via adaptResultV2, but uses DomainCase for shipment data)
 */

// Input form state (from HTML form or React state) → DomainCase
export function mapInputFormToDomainCase(formData: Record<string, unknown>): DomainCase {
  // Normalize field names
  // - pol_code → pol
  // - cargo_value OR insuranceValue OR shipment_value → cargoValue
  // - transport_mode → transportMode (enum conversion)
  // Validate with DomainCaseSchema
  // Return validated DomainCase
}

// DomainCase → ShipmentData (for Summary page)
export function mapDomainCaseToShipmentData(domainCase: DomainCase): ShipmentData {
  // Direct mapping with lookup for port names/cities/countries
}

// DomainCase → ShipmentViewModel (for Results page)
export function mapDomainCaseToShipmentViewModel(domainCase: DomainCase): ShipmentViewModel {
  // Map to ResultsViewModel.overview.shipment structure
}
```

Create `/src/domain/case.validation.ts`:

```typescript
import { DomainCaseSchema } from './case.schema';
import type { ValidationIssue } from '@/lib/validation';

export function validateDomainCase(caseData: unknown): {
  valid: boolean;
  issues: ValidationIssue[];
  case?: DomainCase;
} {
  // Use Zod schema to validate
  // Return structured validation issues
}

export function getCompletenessScore(caseData: Partial<DomainCase>): number {
  // Calculate 0-100 completeness based on required fields
}
```

Create `/src/ui/design-tokens/index.ts`:

```typescript
/**
 * Unified Design Tokens
 * Import CSS vars or export as TS constants for React components
 */

export const designTokens = {
  spacing: {
    xs: 'var(--space-4)',
    sm: 'var(--space-8)',
    md: 'var(--space-12)',
    lg: 'var(--space-16)',
    xl: 'var(--space-24)',
    // ... map all CSS vars
  },
  typography: {
    fontFamily: 'var(--font-family)',
    h1: 'var(--font-h1)',
    h2: 'var(--font-h2)',
    body: 'var(--font-body)',
    // ...
  },
  colors: {
    primary: 'var(--color-primary-neon)',
    success: 'var(--status-success)',
    // ...
  },
  // ... export all tokens
};
```

#### View-Model Layer (Clear Separation)

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                       │
│  InputPage   │   SummaryPage   │   ResultsPage              │
│  (Form UI)   │   (Card UI)     │   (Tab UI)                 │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      VIEW MODEL LAYER                        │
│  InputFormState  │  ShipmentData  │  ResultsViewModel       │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       DOMAIN LAYER                           │
│                    DomainCase (Schema)                       │
│                  + Validation + Mapping                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       ENGINE/API LAYER                       │
│              Engine Output / Backend Response                │
└─────────────────────────────────────────────────────────────┘
```

**Rules**:
- UI components ONLY consume View Models (not DomainCase directly)
- All transforms happen in mapper layer (`case.mapper.ts`)
- DomainCase is the contract between pages (stored in unified store/API)

#### Navigation/Stepper Logic

Create `/src/hooks/useCaseWizard.ts`:

```typescript
/**
 * Unified Wizard State Management
 * Manages navigation between Input → Summary → Results
 */

export type WizardStep = 'input' | 'summary' | 'results';

export function useCaseWizard() {
  const [currentStep, setCurrentStep] = useState<WizardStep>('input');
  const [caseData, setCaseData] = useState<DomainCase | null>(null);
  
  // Navigation handlers
  // - handleNext() → validate current step → save case → navigate
  // - handleBack() → navigate with preserved case data
  // - handleSaveDraft() → persist to localStorage + backend
}
```

### B4. Implementation Plan

#### Phase 1: Foundation (PR #1)
**Goal**: Create domain schema + mapper utilities (no UI changes yet)

**Tasks**:
1. Create `/src/domain/case.schema.ts` with Zod schema
2. Create `/src/domain/case.mapper.ts` with mapping functions
3. Create `/src/domain/case.validation.ts` with validation utilities
4. Create `/src/ui/design-tokens/index.ts` (export CSS vars as TS)
5. **Tests**: Unit tests for mapper functions (input → domain → view models)

**Acceptance Criteria**:
- ✅ DomainCase schema validates input correctly
- ✅ Mapper functions transform without data loss
- ✅ Validation returns structured issues

**Risk**: Low - new files only, no breaking changes

---

#### Phase 2: Summary Page Migration (PR #2)
**Goal**: Update Summary page to use DomainCase + mapper

**Tasks**:
1. Update `RiskcastSummary` to use `mapDomainCaseToShipmentData()` instead of `transformInputStateToSummary()`
2. On load: `localStorage.RISKCAST_STATE` → parse as DomainCase → map to ShipmentData
3. On save: ShipmentData → map to DomainCase → save to `localStorage.RISKCAST_STATE`
4. Use design tokens in Summary component (replace Tailwind classes with token imports)
5. **Tests**: Integration test (load case → display → save → reload)

**Acceptance Criteria**:
- ✅ Summary displays data correctly from DomainCase
- ✅ Save/load preserves all fields
- ✅ Design tokens used (typography, spacing, colors)

**Risk**: Medium - may affect existing data in localStorage (backward compat needed)

---

#### Phase 3: Input Page Migration (PR #3)
**Goal**: Update Input form to emit DomainCase (not flat dict)

**Tasks**:
1. **Option A** (Recommended): Create React version of Input page
   - New component: `src/pages/InputPage.tsx`
   - Use form library (React Hook Form + Zod resolver)
   - On submit: validate → `mapInputFormToDomainCase()` → save DomainCase → redirect
2. **Option B** (Incremental): Update HTML form submission
   - Backend: `main.py` → validate form data → `mapInputFormToDomainCase()` → save DomainCase
   - Keep HTML template but change backend transform
3. Add autosave (debounced save to localStorage + backend draft endpoint)
4. Use design tokens in Input page CSS/React
5. Add stepper/wizard UI (show progress: Input → Summary → Results)
6. **Tests**: E2E test (fill form → submit → verify Summary shows correct data)

**Acceptance Criteria**:
- ✅ Input form emits DomainCase (validated)
- ✅ All field names match domain schema
- ✅ Autosave works (draft persistence)
- ✅ Design tokens used

**Risk**: High - Input page is critical; needs careful testing

---

#### Phase 4: Results Page Alignment (PR #4)
**Goal**: Ensure Results page uses DomainCase for shipment data consistency

**Tasks**:
1. Update `adaptResultV2()` to use `mapDomainCaseToShipmentViewModel()` if DomainCase available
2. If DomainCase not in localStorage, fallback to current engine output mapping
3. Display run ID, version, timestamp prominently (from DomainCase or ResultsViewModel.meta)
4. Add back navigation to Summary page
5. **Tests**: Verify Results displays shipment data correctly from DomainCase

**Acceptance Criteria**:
- ✅ Results shows consistent shipment data (matches Summary)
- ✅ Run ID/timestamp visible
- ✅ Back navigation works

**Risk**: Low - Results page already uses adapter pattern

---

#### Phase 5: Design Tokens Unification (PR #5)
**Goal**: Enforce design tokens across all 3 pages

**Tasks**:
1. Update Summary/Results components to use `designTokens` from `/src/ui/design-tokens/index.ts`
2. Replace Tailwind classes with token-based styles (or configure Tailwind to use tokens)
3. Create shared `EmptyState`, `LoadingState`, `ErrorState` components (with tokens)
4. **Tests**: Visual regression tests (screenshots before/after)

**Acceptance Criteria**:
- ✅ Typography consistent (same font sizes)
- ✅ Spacing consistent (same margins/paddings)
- ✅ Colors consistent (same status colors)
- ✅ No Tailwind classes in React components (or Tailwind config uses tokens)

**Risk**: Medium - visual changes; needs QA

---

#### Phase 6: Navigation & UX Polish (PR #6)
**Goal**: Add wizard/stepper UI + unified navigation

**Tasks**:
1. Implement `useCaseWizard` hook (stepper state management)
2. Add stepper UI component (shows: Input → Summary → Results)
3. Add back/forward buttons on all pages
4. Add "Save Draft" button on Input page (consistent with Summary)
5. Add run ID + last saved timestamp to all pages (subtle UI)
6. **Tests**: E2E test (full flow: Input → Summary → Results → back)

**Acceptance Criteria**:
- ✅ Stepper shows current step
- ✅ Back/forward navigation works (preserves data)
- ✅ Draft saved on all pages
- ✅ Run ID visible (traceability)

**Risk**: Low - UX improvements only

---

### B5. Test Strategy

#### Unit Tests (Mapper Layer)
```typescript
describe('case.mapper', () => {
  test('mapInputFormToDomainCase normalizes field names', () => {
    const formData = { pol_code: 'SGN', cargo_value: 1000 };
    const domainCase = mapInputFormToDomainCase(formData);
    expect(domainCase.pol).toBe('SGN');
    expect(domainCase.cargoValue).toBe(1000);
  });
  
  test('mapDomainCaseToShipmentData preserves all fields', () => {
    const domainCase = createTestDomainCase();
    const shipmentData = mapDomainCaseToShipmentData(domainCase);
    expect(shipmentData.trade.pol).toBe(domainCase.pol);
    expect(shipmentData.value).toBe(domainCase.cargoValue);
  });
});
```

#### Integration Tests (Flow)
```typescript
describe('Input → Summary → Results flow', () => {
  test('data flows correctly through all pages', async () => {
    // 1. Fill Input form
    // 2. Submit → verify DomainCase saved
    // 3. Navigate to Summary → verify ShipmentData displays correctly
    // 4. Run Analysis → verify Results shows consistent data
    // 5. Go back to Summary → verify data unchanged
  });
});
```

#### Snapshot Tests (UI States)
```typescript
describe('UI consistency', () => {
  test('Summary and Results use same typography tokens', () => {
    const summaryStyles = getComputedStyle(summaryHeading);
    const resultsStyles = getComputedStyle(resultsHeading);
    expect(summaryStyles.fontSize).toBe(resultsStyles.fontSize);
  });
});
```

### B6. Telemetry/Trace

Add logging to mapper layer:

```typescript
export function mapInputFormToDomainCase(formData: Record<string, unknown>): DomainCase {
  console.log('[CaseMapper] Input form data:', formData);
  
  const normalized = normalizeFormData(formData);
  const validated = DomainCaseSchema.parse(normalized);
  
  console.log('[CaseMapper] DomainCase created:', {
    caseId: validated.caseId,
    runId: validated.runId,
    version: validated.version,
  });
  
  return validated;
}
```

Add trace headers to API calls:
```typescript
fetch('/api/v1/risk/v2/analyze', {
  headers: {
    'X-Case-Id': domainCase.caseId,
    'X-Run-Id': domainCase.runId,
    'X-Version': domainCase.version,
  },
});
```

### B7. Acceptance Criteria (Quantified)

- ✅ **100% fields consistent**: Same field names, types, defaults across all 3 pages (measured by mapper tests)
- ✅ **Deterministic flow**: Same input → same summary → same results (verified by integration tests)
- ✅ **No scattered transforms**: All transforms in `case.mapper.ts` (verified by grep: no transform logic in components)
- ✅ **Design tokens used**: 100% of typography/spacing/colors from tokens (verified by linting rule or code review)
- ✅ **Traceability**: Run ID + timestamp visible on all pages (visual check)
- ✅ **Backward compatibility**: Old localStorage data still loads (migration function in PR #2)

---

## PHẦN C — PROMPT CHO FIGMA (REDESIGN INPUT PAGE)

### Figma Design Prompt

**Context**: RISKCAST is an enterprise risk analysis platform. The Input page is the first step where users enter shipment details (route, cargo, parties) before running risk analysis. It must be decision-first, low cognitive load, and match the visual language of Summary/Results pages.

**Design Requirements**:

#### 1. Visual System Alignment
- **Grid**: Use 12-column grid (matches Summary/Results)
- **Typography Scale**: 
  - H1: 32px/1.15 (section headers)
  - H2: 24px/1.2 (subsection headers)
  - Body: 16px/1.55 (form labels, descriptions)
  - Caption: 13px/1.4 (hints, help text)
- **Spacing Scale**: 4px base unit (4, 8, 12, 16, 20, 24, 32, 40, 48px)
- **Colors**: 
  - Background: `#05070d` (bg-0)
  - Glass cards: `rgba(255, 255, 255, 0.08)` (glass-1)
  - Primary: `#6ef3ff` (primary-neon)
  - Text: `#f7fbff` (text-strong), `#c7d2e2` (text-muted)
  - Status: Success `#5be8a9`, Warning `#f7c948`, Danger `#ff6b6b`
- **Component Style**: Glass morphism cards (backdrop blur, subtle border), same as Summary/Results

#### 2. Layout Structure

**Desktop (1440px+)**:
- **Left Column (60%)**: Main form with sections
- **Right Column (40%)**: "Preview Summary" panel (real-time preview of what Summary page will show)

**Tablet (768px - 1439px)**:
- Stacked layout (form full width, preview below or collapsible)

**Mobile (< 768px)**:
- Step-based wizard (1 section per screen, back/next buttons)

#### 3. Form Sections (Progressive Disclosure)

**Basic (Always Visible)**:
- **Section 1: Transport Setup**
  - Trade Lane (dropdown with search)
  - Mode of Transport (radio/pill group: AIR, SEA, ROAD, RAIL)
  - Container Type (dropdown, filtered by mode)
  - POL/POD (autocomplete with port database)
  - ETD (date picker)
  - Transit Time (number input, days, auto-calculated from ETA if provided)

- **Section 2: Cargo & Value**
  - Cargo Type (dropdown with search)
  - Cargo Value (number input, currency selector: USD/VND)
  - Packages (number input)
  - Gross Weight (number input, kg)
  - Volume (number input, CBM)
  - HS Code (text input, 6-10 digits, optional)

**Advanced (Collapsible)**:
- **Section 3: Parties**
  - Seller (company, email, phone, country, city)
  - Buyer (company, email, phone, country, city)
  - Forwarder (optional)

- **Section 4: Terms & Modules**
  - Incoterm (dropdown: EXW, FOB, CIF, etc.)
  - Incoterm Location (text input, conditional)
  - Priority (pill group: Normal, Express, Urgent)
  - Algorithm Modules (checkboxes: ESG, Weather, Port Congestion, etc.)

#### 4. Form Field Design

**Standard Input**:
- Label: 12px, `text-muted`, above input
- Input: 16px body font, `bg-glass-1`, border `rgba(255,255,255,0.1)`, padding 12px, radius 8px
- Hint: 13px caption, `text-soft`, below input (optional)
- Unit: Displayed inline right of input (e.g., "kg", "USD", "days")
- Validation: Red border + icon + message below on error

**Autocomplete (POL/POD)**:
- Shows dropdown with port code + name + city (e.g., "SGN - Tan Son Nhat - Ho Chi Minh City")
- Searchable, keyboard navigation

**Date Picker**:
- Calendar icon, opens calendar popup
- Format: YYYY-MM-DD (ISO)

#### 5. "Preview Summary" Panel (Right Column)

**Purpose**: Show real-time preview of what Summary page will display

**Content**:
- Mini card showing:
  - Route: "SGN → LAX" (with port names below)
  - Mode: "AIR" badge
  - Cargo: "Electronics - $125,000" (type + value)
  - ETD/ETA: "Jan 20 → Jan 23 (3 days)"
  - Completeness: Progress bar (0-100%)
- Updates as user types (debounced)
- Collapsible on tablet/mobile

#### 6. States & Interactions

**Empty State**:
- Form shows defaults (SGN → LAX, AIR mode, etc.)
- Hints visible ("Enter cargo value to see risk analysis")

**Draft Autosaved**:
- Subtle indicator: "Draft saved • 2 minutes ago" (top right, small text)
- Auto-save on blur (debounced 1 second)

**Validation Error**:
- Red border on field
- Error message below: "Cargo value must be greater than 0"
- Inline validation (not on submit)

**Submitting**:
- Disable form, show spinner on "Run Analysis" button
- Loading state: "Analyzing shipment..."

**Success**:
- Redirect to Summary page (after analysis completes)

**Server Error**:
- Toast notification: "Failed to save. Retry?"
- Error message in panel (non-blocking)

#### 7. CTAs (Consistent Across Pages)

**Primary**: "Run Analysis" (or "Calculate Risk")
- Position: Bottom right, sticky on scroll
- Style: Primary button (neon accent, bold)

**Secondary**: "Save Draft"
- Position: Next to primary, or top right
- Style: Ghost button (outline)

**Tertiary**: "Reset Form"
- Position: Top left, in section header
- Style: Ghost button, small

#### 8. Metadata (Subtle)

**Run ID / Version**:
- Display: "Run #ABC123 • v1.0" (bottom left, 12px, `text-disabled`)

**Last Saved**:
- Display: "Saved 2m ago" (top right, 12px, `text-soft`)

#### 9. Responsive Behavior

**Desktop**:
- 2-column layout (form + preview)
- Sidebar navigation (optional, collapsible)

**Tablet**:
- Single column, preview below or collapsible
- Touch-friendly inputs (min 44px height)

**Mobile**:
- Step-based wizard (swipe between sections)
- Bottom navigation: "Back" / "Next" / "Run Analysis"
- Preview as modal overlay

#### 10. Accessibility

- Labels associated with inputs (for screen readers)
- Keyboard navigation (Tab, Enter, Escape)
- Focus states visible (outline on focus)
- ARIA labels on icons/buttons
- Error messages announced to screen readers

#### 11. Design Principles

- **Decision-First**: Primary action ("Run Analysis") always visible
- **Low Cognitive Load**: Progressive disclosure, clear section headers
- **Enterprise-Grade**: Professional, no "colorful" design; focus on clarity
- **Traceability**: Run ID, version, timestamp always visible
- **No Dashboard Aesthetics**: Not a dashboard; it's a form with preview

**Deliverables**:
1. Desktop layout (1440px)
2. Tablet layout (768px)
3. Mobile layout (375px)
4. Component library (inputs, buttons, cards, preview panel)
5. States mockups (empty, validation error, submitting, success)
6. Design tokens reference (typography, spacing, colors)

---

## PHẦN D — CHECKLIST TRIỂN KHAI (PR ORDER)

### PR #1: Domain Schema + Mapper Foundation
- [ ] Create `/src/domain/case.schema.ts` with Zod schema
- [ ] Create `/src/domain/case.mapper.ts` with mapping functions
- [ ] Create `/src/domain/case.validation.ts` with validation utilities
- [ ] Create `/src/ui/design-tokens/index.ts` (export CSS vars)
- [ ] Write unit tests for mapper functions
- [ ] Write unit tests for validation

### PR #2: Summary Page Migration
- [ ] Update `RiskcastSummary` to use `mapDomainCaseToShipmentData()`
- [ ] Add backward compatibility (migrate old localStorage data)
- [ ] Replace Tailwind classes with design tokens (typography, spacing, colors)
- [ ] Write integration test (load → display → save → reload)

### PR #3: Input Page Migration
- [ ] **Option A**: Create React InputPage component (recommended)
  - [ ] Use React Hook Form + Zod resolver
  - [ ] Implement `mapInputFormToDomainCase()` on submit
  - [ ] Add autosave (debounced localStorage + backend)
- [ ] **Option B**: Update backend transform (if keeping HTML)
  - [ ] Update `main.py` to use `mapInputFormToDomainCase()`
  - [ ] Validate form data before transform
- [ ] Use design tokens in Input page
- [ ] Add stepper/wizard UI (progress indicator)
- [ ] Write E2E test (fill form → submit → verify Summary)

### PR #4: Results Page Alignment
- [ ] Update `adaptResultV2()` to use `mapDomainCaseToShipmentViewModel()` if DomainCase available
- [ ] Add back navigation to Summary page
- [ ] Display run ID + timestamp prominently
- [ ] Write test (verify Results displays consistent shipment data)

### PR #5: Design Tokens Unification
- [ ] Update Summary/Results components to use `designTokens` import
- [ ] Replace remaining Tailwind classes with token-based styles
- [ ] Create shared `EmptyState`, `LoadingState`, `ErrorState` components
- [ ] Configure Tailwind to use design tokens (if keeping Tailwind)
- [ ] Write visual regression tests

### PR #6: Navigation & UX Polish
- [ ] Implement `useCaseWizard` hook
- [ ] Add stepper UI component (shows: Input → Summary → Results)
- [ ] Add back/forward buttons on all pages
- [ ] Add "Save Draft" to Input page
- [ ] Add run ID + last saved timestamp to all pages (subtle)
- [ ] Write E2E test (full flow: Input → Summary → Results → back)

---

## TÓM TẮT & NEXT STEPS

**Chẩn đoán ngắn**:
- 3 trang dùng schema khác nhau → data loss, confusion
- Design tokens tồn tại nhưng không được enforce → UI inconsistent
- Transform logic rải rác → khó maintain, không traceable

**Kế hoạch refactor**:
1. Tạo DomainCase schema (single source of truth)
2. Tạo mapper layer (centralized transforms)
3. Migrate từng page tuần tự (Summary → Input → Results)
4. Enforce design tokens (thay Tailwind bằng tokens)
5. Thêm navigation/wizard UI

**Prompt Figma** (in riêng):
- Decision-first, enterprise-grade, low cognitive load
- 2-column desktop (form + preview panel)
- Progressive disclosure (Basic → Advanced)
- Cùng grid, typography, spacing, colors với Summary/Results
- Preview Summary panel real-time
- States: empty, draft saved, validation error, submitting, success

**PR Checklist** (6 PRs, sequential):
- PR #1: Foundation (schema + mapper)
- PR #2: Summary migration
- PR #3: Input migration (critical)
- PR #4: Results alignment
- PR #5: Design tokens
- PR #6: Navigation/UX polish

---

**End of Report**
