# Financial Zero-Impact Scenario Fix

## Problem Statement

Financial visualizations (Loss Distribution, VaR/CVaR charts, Cumulative Curve, Heatmap, Timeline) were showing infinite "Loading..." state when:
- Financial data exists in backend response
- All financial metric values are zero/null
- This occurs when `cargo_value` is missing or zero

## Root Cause

Components were checking for data existence but not distinguishing between:
1. **No data** (should show loading/error)
2. **Zero-impact data** (should show empty state, not loading)

## Solution: ENGINE-FIRST Semantic Financial State

### 1. Created Financial State Utility

**File:** `app/static/js/utils/financialState.js`

**Functions:**
- `analyzeFinancialState(financialData)` - Returns semantic state object
- `isZeroImpactScenario(financialData)` - Convenience check
- `getZeroImpactEmptyState(financialState)` - Empty state UI content

**State Object:**
```javascript
{
  hasFinancialData: boolean,      // Does data structure exist?
  hasNonZeroImpact: boolean,      // Are any values non-zero?
  zeroImpactReason: string,       // Why zero-impact (if applicable)
  metrics: {...}                  // Extracted metrics
}
```

### 2. Updated FinancialHistogram Component

**File:** `app/static/js/components/FinancialHistogram.js`

**Changes:**
- Added `_isZeroImpactScenario()` method - Detects zero-impact before rendering
- Added `_renderZeroImpactState()` method - Shows proper empty state
- Updated `mount()` - Checks zero-impact BEFORE Chart.js initialization
- Updated `update()` - Re-checks on data updates, destroys chart if zero-impact
- Added empty state CSS styles

**Empty State UI:**
- Title: "No financial loss simulated"
- Description: "Cargo value not provided or equal to zero"
- Note: "Risk analysis based on operational factors only"

### 3. Updated LossCurve Component

**File:** `app/static/js/components/LossCurve.js`

**Changes:**
- Same pattern as FinancialHistogram
- Zero-impact detection before chart initialization
- Proper empty state rendering
- Chart destruction on zero-impact transition

### 4. Global Utility Loader

**File:** `app/static/js/utils/financialStateLoader.js`

- Makes utilities available via `window.RISKCAST.utils.financialState`
- Supports both module and browser script tag loading
- Ensures compatibility across different loading patterns

## Key Principles (ENGINE-FIRST)

✅ **Never recomputes financial values** - Only analyzes what engine provides
✅ **Never shows loading spinner** for zero-impact scenarios
✅ **Clear empty state messaging** - Enterprise tone
✅ **No fake data** - Respects backend response
✅ **No backend changes** - Pure frontend fix

## Zero-Impact Detection Logic

A scenario is considered zero-impact when:
1. Financial data structure exists (hasFinancialData = true)
2. All numeric metrics are zero/null:
   - `expectedLoss` / `meanLoss`
   - `var95` / `p95`
   - `cvar` / `maxLoss`
3. Distribution array (if exists) contains only zeros
4. `cargoValue` is missing, null, or zero

## Empty State UI Copy

**Standard messages:**
- **Title:** "No financial loss simulated"
- **Description:** "Cargo value not provided or equal to zero" (when cargo value missing/zero)
- **Note:** "Risk analysis based on operational factors only"

## Files Modified

1. `app/static/js/utils/financialState.js` - **NEW** - Core utility
2. `app/static/js/utils/financialStateLoader.js` - **NEW** - Global loader
3. `app/static/js/components/FinancialHistogram.js` - **UPDATED** - Zero-impact handling
4. `app/static/js/components/LossCurve.js` - **UPDATED** - Zero-impact handling

## Usage Pattern

### Component Usage

```javascript
// FinancialHistogram or LossCurve
const chart = new FinancialHistogram();

// Pass financialData for zero-impact detection
chart.mount(containerEl, {
  bins: distributionBins,
  counts: distributionCounts,
  financialData: {
    expectedLoss: summary.financial.expectedLoss,
    var95: summary.financial.var95,
    cvar: summary.financial.cvar,
    cargoValue: summary.financial.cargoValue
  }
});
```

### Direct Utility Usage

```javascript
// Check if zero-impact
const isZero = isZeroImpactScenario(financialData);

// Get full state analysis
const state = analyzeFinancialState(financialData);
if (!state.hasNonZeroImpact) {
  const emptyState = getZeroImpactEmptyState(state);
  // Render empty state UI
}
```

## Testing Scenarios

### Scenario 1: Zero cargo value
- Input: `cargo_value = 0` or missing
- Expected: Empty state with "Cargo value not provided or equal to zero"

### Scenario 2: All metrics zero
- Input: All financial metrics = 0
- Expected: Empty state with "No financial loss simulated"

### Scenario 3: Valid financial data
- Input: Non-zero metrics and distribution
- Expected: Chart renders normally

### Scenario 4: Missing financial data
- Input: No financial data structure
- Expected: Empty state or error (not loading spinner)

## Notes

- Heatmap and Timeline mentioned by user are for risk impact matrix and risk score over time, not financial data directly
- If they show loading for financial-related reasons, same pattern can be applied
- All changes are frontend-only, respecting ENGINE-FIRST architecture

