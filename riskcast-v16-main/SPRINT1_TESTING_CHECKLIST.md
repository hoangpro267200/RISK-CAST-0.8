# SPRINT 1 TESTING CHECKLIST
## Algorithm Explainability + Personalized Narrative

**Date:** 2026-01-16  
**Status:** Ready for Testing

---

## 📋 PRE-TEST VERIFICATION

### 1. Files Verification

Run verification script:
```powershell
.\verify-sprint1-files.ps1
```

**Expected Output:**
```
✓ ALL FILES EXIST
Sprint 1 files verification: PASSED
```

### 2. TypeScript Compilation

```bash
npm run build
# or
yarn build
```

**Expected:** No TypeScript errors

### 3. Linter Check

```bash
npm run lint
# or
yarn lint
```

**Expected:** No linter errors

---

## 🧪 TEST CASE 1: Basic Flow (Electronics Shipment)

### Setup
1. Start development server:
   ```bash
   npm run dev
   # or
   yarn dev
   ```

2. Navigate to `/input_v20` or `/analyze`

3. Enter shipment data:
   - **Cargo Type:** Electronics
   - **Container:** 40DV
   - **POL:** VNSGN (Ho Chi Minh)
   - **POD:** USLAX (Los Angeles)
   - **Value:** $500,000
   - **Carrier:** Ocean Carrier
   - **ETD:** 2026-01-20
   - **ETA:** 2026-02-23

4. Run analysis

### Verification Checklist

#### Overview Tab
- [ ] **Executive Narrative:**
  - [ ] Does NOT contain "moderate risk" or generic text
  - [ ] Contains "ELECTRONICS" (uppercase)
  - [ ] Contains "Ho Chi Minh"
  - [ ] Contains "Los Angeles"
  - [ ] Contains "Ocean Carrier"
  - [ ] Contains "34 days" or transit time
  - [ ] Contains loss expectations ($12K, $45K, $78K)

- [ ] **Route Details Section:**
  - [ ] "Cargo Type" row exists
  - [ ] "Cargo Type" shows "Electronics"
  - [ ] "Container Type" row exists
  - [ ] "Container Type" shows "40DV"

#### Analytics Tab
- [ ] **Algorithm Explainability Panel:**
  - [ ] Panel appears at top of Analytics tab
  - [ ] Panel header shows "Algorithm Explainability"
  - [ ] Panel has Brain icon

- [ ] **FAHP Weight Chart:**
  - [ ] Chart displays horizontal bars
  - [ ] Each layer has a bar
  - [ ] Consistency Ratio badge visible
  - [ ] Badge shows CR value (e.g., "Consistent (CR: 0.08)")
  - [ ] Tooltip shows weight and contribution on hover
  - [ ] "How FAHP Works" expandable section exists

- [ ] **TOPSIS Breakdown:**
  - [ ] Table displays (if alternatives exist)
  - [ ] Columns: Rank, Scenario, D+, D-, C*
  - [ ] D+ and D- show as bars
  - [ ] C* values are color-coded
  - [ ] "How TOPSIS Works" expandable section exists

- [ ] **Monte Carlo Explainer:**
  - [ ] Simulation Parameters card visible
  - [ ] Shows n_samples (e.g., "10,000 iterations")
  - [ ] Shows distribution type
  - [ ] Percentile ruler displays P10, P50, P90, P95, P99
  - [ ] Interpretation section explains percentiles
  - [ ] "How Monte Carlo Simulation Works" expandable section exists

#### Console Debug Output
Open browser DevTools Console, verify:
- [ ] `[Sprint1 Debug] viewModel:` - logs viewModel object
- [ ] `[Sprint1 Debug] algorithm:` - logs algorithm data (or undefined)
- [ ] `[Sprint1 Debug] cargoType:` - logs "Electronics"
- [ ] `[Sprint1 Debug] containerType:` - logs "40DV"
- [ ] `[Sprint1 Debug] narrativeViewModel:` - logs narrative object
- [ ] `[Sprint1 Debug] personalizedSummary:` - logs full narrative text

---

## 🧪 TEST CASE 2: Missing Algorithm Data

### Setup
1. Use engine output that doesn't include algorithm data
2. Navigate to `/results`

### Verification Checklist

- [ ] **Algorithm Panel:**
  - [ ] Panel shows empty state (not crash)
  - [ ] Empty state message: "Algorithm explainability data unavailable"
  - [ ] No console errors

- [ ] **Narrative:**
  - [ ] Narrative still generated (fallback to existing logic)
  - [ ] Uses engine explanation if available
  - [ ] No errors in console

- [ ] **Other Components:**
  - [ ] Other analytics charts still work
  - [ ] Route Details still displays
  - [ ] No broken UI elements

---

## 🧪 TEST CASE 3: Generic Narrative Check

### Verification
Check that narrative does NOT contain:
- [ ] "moderate risk"
- [ ] "consider insurance"
- [ ] "your shipment has"
- [ ] "risk assessment complete" (unless followed by specific details)

Check that narrative DOES contain:
- [ ] Specific cargo type (e.g., "ELECTRONICS")
- [ ] Specific route (e.g., "from Ho Chi Minh to Los Angeles")
- [ ] Specific carrier name
- [ ] Top 3 risk drivers with percentages
- [ ] Actionable recommendations with cost/benefit

---

## 🧪 TEST CASE 4: Type Safety

### Verification
- [ ] No TypeScript compilation errors
- [ ] No runtime type errors in console
- [ ] pol/pod handling works for both:
  - String: `"VNSGN"`
  - Object: `{ code: "VNSGN", name: "Ho Chi Minh" }`
- [ ] cargoValue handling works for both:
  - Number: `500000`
  - Object: `{ amount: 500000, currency: "USD" }`

---

## 🧪 TEST CASE 5: Empty States

### Verification
- [ ] **Algorithm Panel Empty State:**
  - [ ] Shows when `viewModel.algorithm` is undefined
  - [ ] Shows Brain icon
  - [ ] Shows helpful message
  - [ ] No crash

- [ ] **FAHP Chart Empty State:**
  - [ ] Shows when `fahpData.weights` is empty
  - [ ] Shows Info icon
  - [ ] Shows "FAHP weights unavailable" message

- [ ] **TOPSIS Empty State:**
  - [ ] Shows when `topsisData.alternatives` is empty
  - [ ] Shows "TOPSIS breakdown unavailable" message

- [ ] **Monte Carlo Empty State:**
  - [ ] Shows when `monteCarloData.nSamples === 0`
  - [ ] Shows "Monte Carlo simulation data unavailable" message

---

## 🧪 TEST CASE 6: Backend Data Format

### Check Engine Output
Verify backend returns (or adapter extracts):

```json
{
  "algorithm": {
    "fahp": {
      "weights": [
        { "layerId": "1", "layerName": "Climate Risk", "weight": 0.28, "contributionPercent": 28 }
      ],
      "consistencyRatio": 0.08,
      "consistencyStatus": "acceptable"
    },
    "topsis": {
      "alternatives": [...],
      "methodology": "..."
    },
    "monteCarlo": {
      "nSamples": 10000,
      "distributionType": "log-normal",
      "parameters": {...},
      "percentiles": {...},
      "methodology": "..."
    }
  },
  "shipment": {
    "cargo_type": "Electronics",
    "container_type": "40DV"
  }
}
```

### Verification
- [ ] Adapter extracts algorithm data correctly
- [ ] Adapter handles missing fields gracefully
- [ ] Adapter normalizes data types correctly

---

## 🧪 AUTOMATED TESTS

### Run Tests
```bash
npm test
# or
yarn test
```

### Test Coverage
- [ ] Narrative personalization tests pass
- [ ] Type export tests pass
- [ ] No test failures

---

## 🐛 DEBUGGING TIPS

### If Algorithm Panel Not Showing:
1. Check console for `[Sprint1 Debug] algorithm:` - should log data or undefined
2. Verify `viewModel.algorithm` exists in viewModel
3. Check adapter is extracting algorithm data correctly

### If Narrative Not Personalized:
1. Check console for `[Sprint1 Debug] narrativeViewModel:`
2. Verify `generateNarrativeViewModel()` is called
3. Check narrative contains cargo type and route

### If Cargo/Container Type Not Showing:
1. Check console for `[Sprint1 Debug] cargoType:` and `containerType:`
2. Verify adapter extracts `cargo_type` and `container_type` from engine
3. Check Route Details section renders correctly

---

## ✅ ACCEPTANCE CRITERIA CHECKLIST

| # | Criterion | Test Case | Status |
|---|-----------|-----------|--------|
| AE-1 | FAHP weights visible | Test Case 1 | ⬜ |
| AE-2 | FAHP CR displayed | Test Case 1 | ⬜ |
| AE-3 | TOPSIS breakdown visible | Test Case 1 | ⬜ |
| AE-4 | Monte Carlo params visible | Test Case 1 | ⬜ |
| AE-6 | Methodology tooltips | Test Case 1 | ⬜ |
| NP-1 | Cargo type mentioned | Test Case 1, 3 | ⬜ |
| NP-2 | Route mentioned | Test Case 1, 3 | ⬜ |
| NP-3 | Top 3 drivers mentioned | Test Case 1, 3 | ⬜ |
| NP-4 | Actions have cost/benefit | Test Case 1, 3 | ⬜ |
| NP-5 | Loss expectations included | Test Case 1, 3 | ⬜ |
| NP-6 | No generic phrases | Test Case 3 | ⬜ |
| DR-1 | Cargo type displayed | Test Case 1 | ⬜ |
| DR-2 | Container type displayed | Test Case 1 | ⬜ |
| DR-3 | Algorithm panel in Analytics | Test Case 1 | ⬜ |

---

## 📝 TEST RESULTS TEMPLATE

```
Test Date: ___________
Tester: ___________
Environment: ___________

Test Case 1: ⬜ PASS ⬜ FAIL
Test Case 2: ⬜ PASS ⬜ FAIL
Test Case 3: ⬜ PASS ⬜ FAIL
Test Case 4: ⬜ PASS ⬜ FAIL
Test Case 5: ⬜ PASS ⬜ FAIL
Test Case 6: ⬜ PASS ⬜ FAIL

Issues Found:
1. ___________
2. ___________

Notes:
___________
```

---

**END OF TESTING CHECKLIST**
