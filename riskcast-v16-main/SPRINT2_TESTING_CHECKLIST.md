# SPRINT 2 TESTING CHECKLIST
## Insurance Underwriting + Logistics Realism

**Date:** 2026-01-16  
**Status:** Ready for Testing

---

## 📋 PRE-TEST VERIFICATION

### 1. Files Verification

**Insurance Components (8 files):**
- [ ] `src/components/LossDistributionHistogram.tsx`
- [ ] `src/components/BasisRiskScore.tsx`
- [ ] `src/components/TriggerProbabilityTable.tsx`
- [ ] `src/components/CoverageRecommendations.tsx`
- [ ] `src/components/PremiumLogicExplainer.tsx`
- [ ] `src/components/ExclusionsDisclosure.tsx`
- [ ] `src/components/DeductibleRecommendation.tsx`
- [ ] `src/components/InsuranceUnderwritingPanel.tsx`

**Logistics Components (5 files):**
- [ ] `src/components/CargoContainerValidation.tsx`
- [ ] `src/components/RouteSeasonalityRisk.tsx`
- [ ] `src/components/PortCongestionStatus.tsx`
- [ ] `src/components/InsuranceAttentionFlags.tsx`
- [ ] `src/components/LogisticsRealismPanel.tsx`

### 2. TypeScript Compilation

```bash
npm run build
```

**Expected:** No TypeScript errors

### 3. Linter Check

```bash
npm run lint
```

**Expected:** No linter errors (warnings about lazy loading are acceptable)

---

## 🧪 TEST CASE 1: Insurance Panel - Full Display

### Setup
1. Start development server: `npm run dev`
2. Navigate to `/input_v20` or `/analyze`
3. Enter shipment data:
   - **Cargo Type:** Electronics
   - **Container:** 40DV
   - **POL:** VNSGN
   - **POD:** USLAX
   - **Value:** $500,000
   - **ETD:** 2026-01-20
   - **ETA:** 2026-02-23
4. Run analysis
5. Navigate to `/results` → Analytics tab

### Verification Checklist

#### Insurance Underwriting Panel
- [ ] **Panel Header:**
  - [ ] Panel appears in Analytics tab
  - [ ] Header shows "Insurance Underwriting Analysis"
  - [ ] Shield icon visible
  - [ ] Description text visible

- [ ] **Loss Distribution Histogram:**
  - [ ] Chart displays histogram bars
  - [ ] CDF line overlaid on histogram
  - [ ] P50 marker visible (green line)
  - [ ] P95 marker visible (amber line)
  - [ ] P99 marker visible (red line)
  - [ ] Tooltip shows frequency and cumulative on hover
  - [ ] Percentile summary cards show P50, P95, P99 values
  - [ ] If synthetic: "ESTIMATED" badge appears
  - [ ] If synthetic: Warning message explains estimation

- [ ] **Basis Risk Score:**
  - [ ] Score displayed (0.00 - 1.00)
  - [ ] Interpretation badge shows (LOW/MODERATE/HIGH)
  - [ ] Icon matches interpretation (CheckCircle/AlertCircle/XCircle)
  - [ ] Explanation text visible
  - [ ] Interpretation guide shows all 3 levels
  - [ ] "What is Basis Risk?" expandable section exists

- [ ] **Trigger Probability Table:**
  - [ ] Table displays (if triggers exist)
  - [ ] Columns: Trigger Event, Probability, Expected Loss, Premium Est.
  - [ ] Probability bars show correct percentages
  - [ ] Color coding: Red (≥20%), Amber (≥10%), Green (<10%)
  - [ ] Summary note explains calculation

- [ ] **Coverage Recommendations:**
  - [ ] Recommendations grouped by priority
  - [ ] REQUIRED section (red badges)
  - [ ] RECOMMENDED section (amber badges)
  - [ ] OPTIONAL section (blue badges)
  - [ ] Each recommendation shows: type, clause, rationale
  - [ ] Priority badges visible

- [ ] **Premium Logic Explainer:**
  - [ ] Step 1: Expected Loss Calculation visible
  - [ ] Step 2: Load Factor Application visible
  - [ ] Step 3: Premium Calculation visible
  - [ ] Market Comparison table shows:
    - [ ] Market Rate vs RISKCAST Rate
    - [ ] Market Premium vs RISKCAST Premium
    - [ ] Savings calculation
  - [ ] "Why RISKCAST rate is lower" explanation visible

- [ ] **Deductible Recommendation:**
  - [ ] Recommended deductible highlighted (green card)
  - [ ] Deductible analysis table shows:
    - [ ] Multiple deductible options
    - [ ] Premium estimates for each
    - [ ] Break-even calculations
    - [ ] OPTIMAL badge on recommended option
  - [ ] Rationale explanation visible

- [ ] **Exclusions Disclosure:**
  - [ ] Exclusions list visible (if exclusions exist)
  - [ ] Each exclusion shows clause and reason
  - [ ] Amber warning styling
  - [ ] General note about reviewing policy

---

## 🧪 TEST CASE 2: Logistics Panel - Full Display

### Setup
Same as Test Case 1

### Verification Checklist

#### Logistics Realism Panel
- [ ] **Panel Header:**
  - [ ] Panel appears in Analytics tab
  - [ ] Header shows "Logistics Realism Analysis"
  - [ ] Package icon visible
  - [ ] Description text visible

- [ ] **Cargo-Container Validation:**
  - [ ] Status shows VALID or MISMATCH
  - [ ] Cargo Type displayed
  - [ ] Container Type displayed
  - [ ] If VALID: Green checkmark icon
  - [ ] If MISMATCH: Red X icon
  - [ ] If MISMATCH: Warning message explains issue
  - [ ] If MISMATCH: Recommended containers listed
  - [ ] If MISMATCH: Risk impact message shown
  - [ ] Additional checks for electronics (if applicable):
    - [ ] Temperature sensitivity check
    - [ ] Shock sensitivity check
    - [ ] Moisture risk check

- [ ] **Insurance Attention Flags:**
  - [ ] Flags appear based on shipment characteristics
  - [ ] HIGH VALUE flag (if cargo > $200K)
  - [ ] LONG TRANSIT flag (if transit > 30 days)
  - [ ] FRAGILE flag (if electronics/pharma)
  - [ ] WEATHER RISK flag (if route risk HIGH)
  - [ ] HANDLING RISK flag (if multiple transshipments)
  - [ ] Each flag shows: message, recommendation
  - [ ] Color coding: Red (critical), Amber (warning)

- [ ] **Route Seasonality Risk:**
  - [ ] Season displayed (Winter/Spring/Summer/Fall)
  - [ ] Risk level badge (LOW/MEDIUM/HIGH)
  - [ ] Risk factors list visible
  - [ ] Climatic Indices table shows:
    - [ ] Index name
    - [ ] Value (with +/- sign)
    - [ ] Interpretation
  - [ ] "How Seasonality Risk is Calculated" expandable section

- [ ] **Port Congestion Status:**
  - [ ] Table displays with columns:
    - [ ] Port (with POL/POD/TSP labels)
    - [ ] Dwell Time
    - [ ] Normal Dwell Time
    - [ ] Status (with color-coded badges)
    - [ ] Delta (% change)
  - [ ] POL row visible
  - [ ] POD row visible
  - [ ] Transshipment rows visible (if any)
  - [ ] High congestion alert appears (if dwell time > 1.5x normal)
  - [ ] Data source note visible

- [ ] **Packaging Recommendations:**
  - [ ] Recommendations list visible (if available)
  - [ ] Each recommendation shows:
    - [ ] Item name
    - [ ] Cost
    - [ ] Risk reduction percentage
    - [ ] Rationale

- [ ] **Delay Probabilities:**
  - [ ] Three cards display:
    - [ ] P(delay > 7 days)
    - [ ] P(delay > 14 days)
    - [ ] P(delay > 21 days)
  - [ ] Probabilities decrease: P7 > P14 > P21
  - [ ] Color coding: Amber → Orange → Red

---

## 🧪 TEST CASE 3: Cargo-Container Mismatch Detection

### Setup
1. Enter shipment data:
   - **Cargo Type:** Frozen Seafood (or Perishable)
   - **Container:** 40DV (Dry Van)
   - **Value:** $150,000
   - **POL:** VNSGN
   - **POD:** JPYOK
2. Run analysis
3. Navigate to `/results` → Analytics tab

### Verification Checklist

- [ ] **Cargo-Container Validation:**
  - [ ] Status shows **MISMATCH** (not VALID)
  - [ ] Red X icon visible
  - [ ] Warning message: "Perishable cargo requires refrigerated container"
  - [ ] Recommended containers listed:
    - [ ] 40RF (Reefer)
    - [ ] 40RH (High Cube Reefer)
  - [ ] Risk impact: "Using incorrect container increases risk by 95%"
  - [ ] Container type explanation visible

- [ ] **Insurance Attention Flags:**
  - [ ] CARGO-CONTAINER MISMATCH flag appears
  - [ ] Flag shows red/amber styling
  - [ ] Recommendation: "Review container selection"

---

## 🧪 TEST CASE 4: Insurance Flags - High Value + Long Transit

### Setup
1. Enter shipment data:
   - **Cargo Type:** Pharmaceuticals
   - **Container:** 20RF
   - **Value:** $2,000,000
   - **Transit:** 45 days
   - **POL:** DEHAM
   - **POD:** AUMEL
2. Run analysis

### Verification Checklist

- [ ] **Insurance Attention Flags:**
  - [ ] **HIGH VALUE** flag appears (red)
    - [ ] Message: "High-value cargo ($2M)"
    - [ ] Recommendation: "Full ICC(A) coverage + inland transit extension"
  - [ ] **LONG TRANSIT** flag appears (amber)
    - [ ] Message: "Extended transit (45 days)"
    - [ ] Recommendation: "Humidity indicator cards + inspection clause"
  - [ ] **FRAGILE** flag appears (amber)
    - [ ] Message: "Pharmaceuticals (Temperature/Shock Sensitive)"
    - [ ] Recommendation: "Moisture exclusion waiver, shock damage rider"
  - [ ] **TEMPERATURE SENSITIVE** flag appears (if applicable)

---

## 🧪 TEST CASE 5: Missing Data Handling

### Setup
1. Use engine output that doesn't include insurance/logistics data
2. Navigate to `/results` → Analytics tab

### Verification Checklist

- [ ] **Insurance Panel:**
  - [ ] Panel does NOT appear (conditional rendering works)
  - [ ] No console errors
  - [ ] Other panels still work

- [ ] **Logistics Panel:**
  - [ ] Panel does NOT appear (conditional rendering works)
  - [ ] No console errors
  - [ ] Other panels still work

- [ ] **Partial Data:**
  - [ ] If only insurance data exists: Insurance panel shows, Logistics panel doesn't
  - [ ] If only logistics data exists: Logistics panel shows, Insurance panel doesn't
  - [ ] Empty states show when data missing (if panels render)

---

## 🧪 TEST CASE 6: Synthetic Data Flagging

### Setup
1. Use engine output with synthetic loss distribution
2. Navigate to `/results` → Analytics tab

### Verification Checklist

- [ ] **Loss Distribution Histogram:**
  - [ ] "ESTIMATED" badge appears (amber)
  - [ ] Warning message explains:
    - [ ] "This loss curve was generated using parametric estimation"
    - [ ] "Insufficient historical data available"
  - [ ] Confidence Level: MEDIUM
  - [ ] Data Points Used: [number] similar shipments
  - [ ] Estimation Method: Log-normal fit with expert adjustment

---

## 🧪 TEST CASE 7: Port Congestion - High Congestion Alert

### Setup
1. Use route with transshipment port experiencing high congestion
2. Navigate to `/results` → Analytics tab

### Verification Checklist

- [ ] **Port Congestion Status:**
  - [ ] Singapore (or transshipment port) shows HIGH status
  - [ ] Dwell time > 1.5x normal
  - [ ] Delta shows high percentage (e.g., +113%)
  - [ ] **High Congestion Alert** appears (red box)
  - [ ] Alert message: "Expected additional delay: X days"
  - [ ] Alternative recommendation: "Consider alternative ports"

---

## 🧪 TEST CASE 8: Premium Logic - Market Comparison

### Setup
1. Use shipment with insurance data
2. Navigate to `/results` → Analytics tab → Insurance Panel

### Verification Checklist

- [ ] **Premium Logic Explainer:**
  - [ ] Step 1: Expected Loss shows correct value
  - [ ] Step 2: Load Factor shows breakdown (admin, profit, reinsurance)
  - [ ] Step 3: Premium calculation shows formula
  - [ ] Market Comparison table:
    - [ ] Market Rate column shows percentage
    - [ ] RISKCAST Rate column shows percentage (lower)
    - [ ] Market Premium shows calculated value
    - [ ] RISKCAST Premium shows calculated value
    - [ ] Savings row shows dollar amount and percentage
  - [ ] "Why RISKCAST rate is lower" explanation lists 4 reasons

---

## 🧪 TEST CASE 9: Deductible Analysis Table

### Setup
1. Use shipment with insurance data
2. Navigate to `/results` → Analytics tab → Insurance Panel

### Verification Checklist

- [ ] **Deductible Recommendation:**
  - [ ] Recommended deductible highlighted (green gradient card)
  - [ ] Analysis table shows 5 options:
    - [ ] $0 (nil)
    - [ ] $2,500
    - [ ] $5,000 (recommended - highlighted)
    - [ ] $10,000
    - [ ] $25,000
  - [ ] Each row shows:
    - [ ] Deductible amount
    - [ ] Premium estimate
    - [ ] Break-even calculation
    - [ ] OPTIMAL badge on recommended row
  - [ ] Rationale explains break-even logic

---

## 🧪 TEST CASE 10: Coverage Recommendations - Priority Grouping

### Setup
1. Use shipment with insurance data
2. Navigate to `/results` → Analytics tab → Insurance Panel

### Verification Checklist

- [ ] **Coverage Recommendations:**
  - [ ] REQUIRED section appears first (if any)
    - [ ] Red badges
    - [ ] AlertCircle icons
  - [ ] RECOMMENDED section appears second (if any)
    - [ ] Amber badges
    - [ ] CheckCircle icons
  - [ ] OPTIONAL section appears last (if any)
    - [ ] Blue badges
    - [ ] Info icons
  - [ ] Each recommendation card shows:
    - [ ] Coverage type (e.g., "ICC(A)")
    - [ ] Clause description
    - [ ] Rationale explanation
    - [ ] Priority badge

---

## 🧪 AUTOMATED TESTS

### Run Tests
```bash
npm test
# or
yarn test
```

### Test Coverage
- [ ] Insurance data structure tests pass
- [ ] Logistics data structure tests pass
- [ ] Cargo-container validation logic tests pass
- [ ] Insurance flags logic tests pass
- [ ] No test failures

---

## 🐛 DEBUGGING TIPS

### If Insurance Panel Not Showing:
1. Check console for `[Sprint1 Debug] insurance:` - should log data or undefined
2. Verify `viewModel.insurance` exists in viewModel
3. Check adapter is extracting insurance data correctly
4. Verify `viewModel.loss` exists (required for panel)

### If Logistics Panel Not Showing:
1. Check console for `[Sprint1 Debug] logistics:` - should log data or undefined
2. Verify `viewModel.logistics` exists in viewModel
3. Check adapter is extracting logistics data correctly
4. Verify cargo type and container type are provided

### If Cargo-Container Validation Not Working:
1. Check cargo type and container type are passed correctly
2. Verify validation rules match cargo type
3. Check warnings array is populated correctly

### If Synthetic Flag Not Showing:
1. Check `lossDistribution.isSynthetic` is true
2. Verify adapter marks synthetic data correctly
3. Check warning message appears

---

## ✅ ACCEPTANCE CRITERIA CHECKLIST

| # | Criterion | Test Case | Status |
|---|-----------|-----------|--------|
| **Insurance Underwriting** |
| IU-1 | Loss histogram visible | Test Case 1 | ⬜ |
| IU-2 | Synthetic flag shown | Test Case 6 | ⬜ |
| IU-3 | Basis risk score visible | Test Case 1 | ⬜ |
| IU-4 | Trigger probabilities table | Test Case 1 | ⬜ |
| IU-5 | Coverage recommendations | Test Case 10 | ⬜ |
| IU-6 | Premium logic explained | Test Case 8 | ⬜ |
| IU-7 | Deductible recommendation | Test Case 9 | ⬜ |
| **Logistics Realism** |
| LR-3 | Cargo-container validation | Test Case 3 | ⬜ |
| LR-4 | Seasonality risk shown | Test Case 2 | ⬜ |
| LR-5 | Port congestion shown | Test Case 7 | ⬜ |
| LR-6 | Insurance flags shown | Test Case 4 | ⬜ |

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
Test Case 7: ⬜ PASS ⬜ FAIL
Test Case 8: ⬜ PASS ⬜ FAIL
Test Case 9: ⬜ PASS ⬜ FAIL
Test Case 10: ⬜ PASS ⬜ FAIL

Issues Found:
1. ___________
2. ___________

Notes:
___________
```

---

## 🎯 CRITICAL TEST SCENARIOS

### Scenario A: Electronics + Winter Pacific (High Risk)
**Expected:**
- Insurance flags: HIGH VALUE, LONG TRANSIT, FRAGILE, WEATHER RISK
- Coverage: ICC(A) REQUIRED, Delay Rider RECOMMENDED
- Premium: Higher due to risk factors
- Basis risk: LOW (delay triggers reliable)

### Scenario B: Perishable + Wrong Container (FAIL)
**Expected:**
- Cargo-container: MISMATCH
- Insurance flag: CARGO-CONTAINER MISMATCH
- Coverage: Temperature monitoring REQUIRED
- Risk score: Elevated

### Scenario C: Low Value + Short Transit (Low Risk)
**Expected:**
- Insurance flags: None or minimal
- Coverage: Standard recommendations
- Premium: Lower
- Deductible: Lower recommended amount

---

**END OF TESTING CHECKLIST**
