# Engine v3 STEP 7B - Frontend Alignment Fixes

## Summary

This document describes the fixes applied to align the Results page frontend with Engine v3 STEP 7B driver derivation and reasoning rules.

## Changes Made

### 1. Engine Truth Lock (`src/adapters/adaptResultV2.ts`)

**Problem**: Adapter had fallback precedence that could override empty drivers array from engine.

**Fix**: 
- Changed logic to use `data.drivers` exclusively if it exists (even if empty array)
- Only fallback to `risk_factors`/`factors` if `drivers` field doesn't exist (undefined/null)
- Empty drivers array is now treated as valid (low-risk, diffuse risk cases)

**Code Change**:
```typescript
// BEFORE: Fallback when drivers is empty
if (Array.isArray(data.drivers) && data.drivers.length > 0) {
  canonicalDrivers = data.drivers;
}

// AFTER: Use drivers if it exists (even if empty)
if (Array.isArray(data.drivers)) {
  canonicalDrivers = data.drivers;
  canonicalDriversFrom = 'drivers';
} else {
  // Only fallback if drivers field doesn't exist
}
```

**Satisfies**: Engine v3 rule that `drivers = []` is valid and should not be overridden.

---

### 2. Impact Handling (`src/adapters/adaptResultV2.ts`)

**Problem**: 
- Used `toPercent()` normalization which could distort relative impact logic
- Rounded to 0 decimals, losing Engine v3's 1 decimal precision

**Fix**:
- Removed `toPercent()` normalization for impact
- Engine v3 impact is already 0-100 (1 decimal)
- Safe compat: if impact <= 1, treat as 0-1 scale and scale to 0-100
- Keep 1 decimal precision (round to 1 dp)
- Clamp to [0, 100]

**Code Change**:
```typescript
// BEFORE
impact: round(toPercent(driver?.impact), 0), // 0 decimals

// AFTER
let impact = toNumber(driver?.impact, 0);
if (impact <= 1.0 && impact > 0) {
  impact = impact * 100; // Scale 0-1 to 0-100
}
impact = round(clamp(impact, 0, 100), 1); // 1 decimal precision
```

**Satisfies**: Engine v3 rule that impact is relative percentage (0-100, 1 decimal).

---

### 3. Placeholder Filtering (`src/adapters/adaptResultV2.ts`)

**Problem**: Adapter created "Unknown Driver" placeholder when name was missing.

**Fix**:
- Filter out drivers with invalid/missing names
- Check for placeholder names: "unknown", "other", "misc", "n/a", "none"
- Skip drivers that don't pass validation (do NOT create placeholders)

**Code Change**:
```typescript
// BEFORE
name: toString(driver?.name, 'Unknown Driver'), // Creates placeholder

// AFTER
const driverName = driver?.name;
if (!driverName || typeof driverName !== 'string' || driverName.trim() === '') {
  continue; // Filter out, don't create placeholder
}
// Check for placeholder names
if (placeholderNames.includes(driverName.toLowerCase().trim())) {
  continue; // Filter out
}
```

**Satisfies**: Engine v3 rule "Never emit placeholder drivers".

---

### 4. Adapter Validation (`src/adapters/adaptResultV2.ts`)

**Problem**: No validation of driver count or impact sum.

**Fix**:
- Warn if `drivers.length > 3` (Engine v3 MAX_DRIVERS = 3)
- Warn if impact sum < 95% or > 105% (relative logic check)
- Filter out invalid drivers (zero impact, invalid name)

**Code Change**:
```typescript
// Validation: Warn if drivers.length > 3
if (normalizedDrivers.length > 3) {
  warnings.push(`Driver count exceeds Engine v3 limit (${normalizedDrivers.length} > 3)`);
}

// Validation: Warn if impact sum is outside 95-105%
const impactSum = normalizedDrivers.reduce((sum, d) => sum + d.impact, 0);
if (normalizedDrivers.length > 0) {
  if (impactSum < 95 || impactSum > 105) {
    warnings.push(`Driver impact sum (${impactSum.toFixed(1)}%) is outside expected range [95%, 105%]`);
  }
}
```

**Satisfies**: Engine v3 validation requirements.

---

### 5. Reasoning Explanation (`src/adapters/adaptResultV2.ts`, `src/types/resultsViewModel.ts`, `src/components/results/RiskOverview.tsx`)

**Problem**: `reasoning.explanation` from engine was not mapped to ViewModel or displayed in UI.

**Fix**:
- Added `reasoning` field to `OverviewViewModel`
- Extract `reasoning.explanation` from engine output
- Display in `RiskOverview` component

**Code Changes**:
1. **ViewModel Type** (`src/types/resultsViewModel.ts`):
```typescript
export interface OverviewViewModel {
  shipment: ShipmentViewModel;
  riskScore: RiskScoreViewModel;
  profile: RiskProfileViewModel;
  reasoning: {
    explanation: string; // Engine-generated explanation (STEP 7B.2)
  };
}
```

2. **Adapter** (`src/adapters/adaptResultV2.ts`):
```typescript
const reasoningData = (data.reasoning as { explanation?: unknown } | undefined) ?? {};
const reasoningExplanation = toString(reasoningData.explanation, '');

const reasoningViewModel = {
  explanation: reasoningExplanation,
};
```

3. **UI Component** (`src/components/results/RiskOverview.tsx`):
```typescript
{props.reasoning.explanation && (
  <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1.5em', marginTop: '1.5em' }}>
    <h3>Risk Assessment Explanation</h3>
    <p style={{ fontStyle: 'italic' }}>
      {props.reasoning.explanation}
    </p>
  </div>
)}
```

**Satisfies**: STEP 7B.2 requirement to display driver-based explanation.

---

## Test Fixtures

Four fixture payloads are provided in `src/adapters/__fixtures__/`:

1. **low-risk-empty-drivers.json**: `risk_score: 25`, `drivers: []`
   - Tests low-risk silence rule
   - Should show empty state message + explanation

2. **diffuse-risk-empty-drivers.json**: `risk_score: 45`, `drivers: []`
   - Tests diffuse risk case (no dominant drivers)
   - Should show empty state message + explanation

3. **single-dominant-driver.json**: `risk_score: 75`, 1 driver with 100% impact
   - Tests single dominant driver case
   - Should show driver + explanation referencing it

4. **three-drivers-sum-100.json**: `risk_score: 68`, 3 drivers with impacts summing to 100%
   - Tests multiple drivers with relative impacts
   - Should show all 3 drivers + explanation referencing them

---

## Verification Checklist

- ✅ Engine truth lock: Only use `data.drivers` if exists (even if empty)
- ✅ Impact handling: Keep 1 decimal, safe compat for 0-1 scale
- ✅ Placeholder filtering: No "Unknown Driver" creation
- ✅ Validation: Warn on length > 3, sum outside 95-105%
- ✅ Reasoning display: Map and render `reasoning.explanation` in UI
- ✅ Empty state: UI shows message when `drivers = []`
- ✅ All linter errors resolved

---

## Files Modified

1. `src/adapters/adaptResultV2.ts` - Core adapter logic fixes
2. `src/types/resultsViewModel.ts` - Added `reasoning` to `OverviewViewModel`
3. `src/components/results/RiskOverview.tsx` - Display reasoning explanation
4. `src/adapters/__fixtures__/` - Test fixture payloads

---

**Status**: ✅ All fixes applied and verified

