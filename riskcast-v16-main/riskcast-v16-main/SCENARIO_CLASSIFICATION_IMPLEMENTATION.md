# Scenario Classification Implementation

## Overview

Implemented scenario classification layer for ResultsOS to properly handle "Operational Risk Only" scenarios where operational risk exists but financial loss exposure is zero.

## Problem Statement

Previously, when `cargo_value` was missing or zero:
- Financial visualizations showed infinite "Loading..." state
- No clear distinction between "no data" vs "operational risk only"
- Missing context about why financial metrics are zero

## Solution: Scenario Classification

### Scenario Types

1. **FULL_RISK_AND_LOSS**
   - Operational risk exists AND financial loss exposure exists
   - Risk score > 0 AND financial metrics > 0

2. **OPERATIONAL_RISK_ONLY**
   - Operational risk exists BUT no financial loss exposure
   - Risk score > 0 AND all financial metrics === 0 or null
   - This is a VALID scenario, not an error

3. **NO_RISK_DETECTED**
   - No operational risk detected
   - Risk score === 0 or null

## Implementation Details

### 1. Scenario Classifier Utility

**File:** `app/static/js/utils/scenarioClassifier.js`

**Functions:**
- `classifyScenario(data)` - Classifies scenario based on risk score and financial metrics
- `getScenarioBadge(scenario)` - Returns badge configuration for UI
- `getFinancialEmptyState(scenario)` - Returns scenario-aware empty state messages

**Detection Logic:**
```javascript
const hasOperationalRisk = riskScore > 0;
const hasFinancialExposure = financialMetrics.some(v => v > 0);

if (hasOperationalRisk && hasFinancialExposure) → FULL_RISK_AND_LOSS
if (hasOperationalRisk && !hasFinancialExposure) → OPERATIONAL_RISK_ONLY
if (!hasOperationalRisk) → NO_RISK_DETECTED
```

### 2. Hero Zone Scenario Badge

**Updated:** `app/static/js/resultsRenderer.js`

**Changes:**
- Added `classifyScenarioForSummary()` - Classifies scenario from summary data
- Added `renderScenarioBadge()` - Renders scenario badge in hero zone
- Updated `renderHeroZone()` - Includes scenario classification and badge rendering

**UI Elements:**
- Badge displayed below risk-level-badge
- Icon + label (e.g., "⚙️ Operational Risk Only")
- Optional subtitle for context
- Description text explaining the scenario

### 3. Financial Component Updates

**Updated Files:**
- `app/static/js/components/FinancialHistogram.js`
- `app/static/js/components/LossCurve.js`

**Changes:**
- Accept `scenario` parameter in `mount()` and `update()`
- Pass scenario to `_renderZeroImpactState()` for scenario-aware messaging
- Empty states now show appropriate messages based on scenario type

**OPERATIONAL_RISK_ONLY Empty State:**
- Title: "Financial loss simulation not applicable"
- Description: "This scenario involves operational risk factors only"
- Note: "No financial loss exposure detected. Risk analysis focuses on operational factors such as delays, routing complexity, and service quality."

### 4. CSS Styles

**Updated:** `app/static/css/results.css`

**Added Styles:**
- `.scenario-badge-container` - Container for badge and description
- `.scenario-badge` - Base badge styles
- `.scenario-badge-operational` - Operational risk only styling (cyan/teal)
- `.scenario-badge-full` - Full risk & loss styling (yellow/amber)
- `.scenario-badge-none` - No risk styling (cyan/teal)
- Enhanced empty state styles for operational risk scenario

## Enterprise Tone & Messaging

### Key Principles

✅ **Calm & Confident** - Not an error state
✅ **Academic/Professional** - Clear, precise language
✅ **Non-judgmental** - Valid business scenario
✅ **Informative** - Explains why financial simulation doesn't apply

### Message Examples

**Badge Label:**
- "Operational Risk Only"

**Subtitle:**
- "No financial loss exposure detected for this shipment"

**Empty State:**
- "Financial loss simulation not applicable"
- "This scenario involves operational risk factors only"
- "Risk analysis focuses on operational factors such as delays, routing complexity, and service quality."

## ENGINE-FIRST Compliance

✅ **Never recomputes** financial values
✅ **Never infers** missing data
✅ **Never modifies** backend logic
✅ **Only analyzes** what engine provides
✅ **Respects** backend's financial calculations (or lack thereof)

## Files Modified

1. `app/static/js/utils/scenarioClassifier.js` - **NEW** - Scenario classification logic
2. `app/static/js/resultsRenderer.js` - **UPDATED** - Hero zone with scenario badge
3. `app/static/js/components/FinancialHistogram.js` - **UPDATED** - Scenario-aware empty states
4. `app/static/js/components/LossCurve.js` - **UPDATED** - Scenario-aware empty states
5. `app/static/css/results.css` - **UPDATED** - Scenario badge styles

## Usage Example

```javascript
// Scenario is automatically classified in renderResults()
const summary = {
  overall: { riskScore: 6.5 },
  financial: {
    expectedLoss: 0,
    var95: 0,
    cvar: 0,
    cargoValue: null
  }
};

// Classification happens automatically
renderResults(summary);
// → Classifies as OPERATIONAL_RISK_ONLY
// → Shows badge: "⚙️ Operational Risk Only"
// → Shows subtitle: "No financial loss exposure detected for this shipment"
// → Financial charts show: "Financial loss simulation not applicable"
```

## Testing Scenarios

### Scenario 1: Operational Risk Only
**Input:**
- `risk_score = 6.5`
- `cargo_value = null` or `0`
- All financial metrics = `0` or `null`

**Expected:**
- Badge: "⚙️ Operational Risk Only"
- Subtitle: "No financial loss exposure detected for this shipment"
- Charts: Empty state with "Financial loss simulation not applicable"

### Scenario 2: Full Risk & Loss
**Input:**
- `risk_score = 7.2`
- `cargo_value = 500000`
- Financial metrics > 0

**Expected:**
- Badge: "📊 Full Risk & Loss"
- Charts: Render normally with financial data

### Scenario 3: No Risk Detected
**Input:**
- `risk_score = 0` or `null`

**Expected:**
- Badge: "✓ No Risk Detected"
- Charts: Appropriate empty/neutral state

## Visual Design

### Scenario Badge Colors

- **Full Risk & Loss:** Amber/Yellow (`#ffcc00`) - Standard risk indication
- **Operational Risk Only:** Cyan/Teal (`#00ffc8`) - Operational/neutral
- **No Risk:** Cyan/Teal (`#00ffc8`) - Positive/neutral

### Badge Positioning

- Located in `.risk-orb-container`
- Below `.risk-level-badge` (48px margin-top)
- Centered alignment
- Includes icon, label, subtitle (if applicable), and description

## Integration Notes

- Scenario classification happens automatically in `renderResults()`
- Scenario object is stored in summary for component access
- Components can access scenario via `window.RISKCAST.utils.scenarioClassifier`
- Fallback logic included if utility not loaded

## Backward Compatibility

- ✅ Works with existing summary formats
- ✅ Graceful degradation if utility not available
- ✅ Fallback classification logic included
- ✅ No breaking changes to existing APIs

