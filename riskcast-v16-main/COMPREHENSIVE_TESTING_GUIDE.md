# COMPREHENSIVE TESTING GUIDE
## All Sprints (1, 2, 3) - Complete Testing Suite

**Date:** 2026-01-16  
**Version:** v1.0  
**Scope:** Sprint 1 (P0) + Sprint 2 (P1) + Sprint 3 (P1)

---

## 📋 TABLE OF CONTENTS

1. [Pre-Testing Setup](#pre-testing-setup)
2. [Sprint 1 Testing](#sprint-1-testing)
3. [Sprint 2 Testing](#sprint-2-testing)
4. [Sprint 3 Testing](#sprint-3-testing)
5. [Integration Testing](#integration-testing)
6. [End-to-End Scenarios](#end-to-end-scenarios)
7. [Regression Testing](#regression-testing)
8. [Performance Testing](#performance-testing)
9. [Accessibility Testing](#accessibility-testing)
10. [Browser Compatibility](#browser-compatibility)

---

## 🔧 PRE-TESTING SETUP

### Prerequisites

1. **Development Environment:**
   ```bash
   # Navigate to project root
   cd riskcast-v16-main
   
   # Install dependencies (if not already done)
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

2. **Backend Server:**
   ```bash
   # Start backend server (Python FastAPI)
   python dev_run.py
   # or
   python -m uvicorn app.main:app --reload
   ```

3. **Frontend Server:**
   ```bash
   # Start Vite dev server
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

4. **Verify Server Status:**
   - Backend: `http://localhost:8000` (or configured port)
   - Frontend: `http://localhost:3000` (or configured port)
   - API Health: `http://localhost:8000/health` (if available)

### Test Data Preparation

**Required Test Scenarios:**
1. **Full Data Scenario:** Complete engine output with all fields
2. **Partial Data Scenario:** Missing some optional fields
3. **Minimal Data Scenario:** Only required fields
4. **Edge Cases:** Empty arrays, null values, extreme numbers

**Test Shipment Configurations:**
- Electronics (high value, fragile)
- Perishable goods (temperature sensitive)
- Bulk commodities (low value, high volume)
- Pharmaceuticals (strict handling)
- Machinery (heavy, shock sensitive)

---

## 🧪 SPRINT 1 TESTING
### Algorithm Explainability + Personalized Narrative

### Test Suite 1.1: Algorithm Explainability Panel

**Location:** Analytics Tab → Algorithm Explainability Panel

#### Test Case 1.1.1: FAHP Weight Chart Display
- [ ] Navigate to `/results` → Analytics tab
- [ ] Verify: Algorithm Explainability Panel visible
- [ ] Verify: FAHP Weight Chart displays horizontal bars
- [ ] Verify: Each layer shows weight percentage
- [ ] Verify: Consistency Ratio badge visible (if CR < 0.1, shows green)
- [ ] Verify: Methodology explainer is collapsible
- [ ] **Expected:** Chart shows all risk layers with weights

#### Test Case 1.1.2: TOPSIS Breakdown Table
- [ ] Verify: TOPSIS Breakdown table visible
- [ ] Verify: Table shows columns: Alternative, D+, D-, C* (Closeness)
- [ ] Verify: Alternatives sorted by C* (descending)
- [ ] Verify: Visual bars show relative D+ and D- values
- [ ] Verify: Methodology explainer is collapsible
- [ ] **Expected:** Table shows ranking of alternatives

#### Test Case 1.1.3: Monte Carlo Explainer
- [ ] Verify: Monte Carlo Explainer section visible
- [ ] Verify: Parameters displayed: n_samples, distribution type
- [ ] Verify: Percentile Ruler shows P10, P50, P90, P95, P99
- [ ] Verify: Interpretation text explains methodology
- [ ] **Expected:** All Monte Carlo parameters visible

#### Test Case 1.1.4: Missing Algorithm Data
- [ ] Test with engine output missing `algorithm` field
- [ ] Verify: Panel shows empty state (no crash)
- [ ] Verify: Console shows no errors
- [ ] **Expected:** Graceful degradation

### Test Suite 1.2: Personalized Narrative

**Location:** Overview Tab → Executive Summary

#### Test Case 1.2.1: Narrative Personalization
- [ ] Navigate to `/results` → Overview tab
- [ ] Verify: Executive Summary narrative visible
- [ ] Verify: Narrative contains cargo type (e.g., "ELECTRONICS")
- [ ] Verify: Narrative contains origin port (e.g., "Ho Chi Minh")
- [ ] Verify: Narrative contains destination port (e.g., "Los Angeles")
- [ ] Verify: Narrative contains transit time (e.g., "34 days")
- [ ] Verify: Narrative contains risk score context
- [ ] **Expected:** Narrative is personalized, not generic

#### Test Case 1.2.2: No Generic Phrases
- [ ] Verify: Narrative does NOT contain "moderate risk"
- [ ] Verify: Narrative does NOT contain "consider insurance" (generic)
- [ ] Verify: Narrative does NOT contain placeholder text
- [ ] **Expected:** All text is context-specific

#### Test Case 1.2.3: Narrative Fallback
- [ ] Test with missing shipment data
- [ ] Verify: Narrative still generates (fallback logic)
- [ ] Verify: No console errors
- [ ] **Expected:** Fallback narrative works

### Test Suite 1.3: Shipment Details Enhancement

**Location:** Overview Tab → Route Details

#### Test Case 1.3.1: Cargo Type Display
- [ ] Verify: Route Details table shows "Cargo Type" row
- [ ] Verify: Cargo Type value matches input (e.g., "Electronics")
- [ ] **Expected:** Cargo Type visible

#### Test Case 1.3.2: Container Type Display
- [ ] Verify: Route Details table shows "Container Type" row
- [ ] Verify: Container Type value matches input (e.g., "40DV")
- [ ] **Expected:** Container Type visible

---

## 🧪 SPRINT 2 TESTING
### Insurance Underwriting + Logistics Realism

### Test Suite 2.1: Insurance Underwriting Panel

**Location:** Analytics Tab → Insurance Underwriting Panel

#### Test Case 2.1.1: Loss Distribution Histogram
- [ ] Navigate to `/results` → Analytics tab
- [ ] Verify: Insurance Underwriting Panel visible
- [ ] Verify: Loss Distribution Histogram chart displays
- [ ] Verify: Histogram shows bars with loss amounts
- [ ] Verify: CDF line overlaid on histogram
- [ ] Verify: P50, P95, P99 markers visible
- [ ] Verify: Percentile summary cards show values
- [ ] Verify: "Synthetic Data" flag if applicable
- [ ] **Expected:** Complete loss distribution visualization

#### Test Case 2.1.2: Basis Risk Score
- [ ] Verify: Basis Risk Score component visible
- [ ] Verify: Score displayed (0-1 scale)
- [ ] Verify: Interpretation shown (Low/Moderate/High)
- [ ] Verify: Explanation text visible
- [ ] Verify: Guide to understanding basis risk expandable
- [ ] **Expected:** Basis risk clearly explained

#### Test Case 2.1.3: Trigger Probability Table
- [ ] Verify: Trigger Probability Table visible
- [ ] Verify: Table shows: Event, Probability, Expected Payout, Premium
- [ ] Verify: Probability bars visualize percentages
- [ ] Verify: Summary note explains premium calculation
- [ ] **Expected:** All parametric triggers listed

#### Test Case 2.1.4: Coverage Recommendations
- [ ] Verify: Coverage Recommendations section visible
- [ ] Verify: Recommendations categorized: REQUIRED, RECOMMENDED, OPTIONAL
- [ ] Verify: Each recommendation shows: Type, Clause, Rationale
- [ ] Verify: Visual styling differs by priority
- [ ] **Expected:** Clear coverage guidance

#### Test Case 2.1.5: Premium Logic Explainer
- [ ] Verify: Premium Logic Explainer visible
- [ ] Verify: Step-by-step calculation shown
- [ ] Verify: Expected loss, load factor, final premium displayed
- [ ] Verify: Market comparison table visible
- [ ] Verify: RISKCAST rate rationale explained
- [ ] **Expected:** Premium calculation transparent

#### Test Case 2.1.6: Exclusions Disclosure
- [ ] Verify: Exclusions Disclosure section visible
- [ ] Verify: List of exclusions shown
- [ ] Verify: Each exclusion has reason and mitigation
- [ ] Verify: Warning styling applied
- [ ] **Expected:** All exclusions clearly disclosed

#### Test Case 2.1.7: Deductible Recommendation
- [ ] Verify: Deductible Recommendation visible
- [ ] Verify: Recommended amount displayed
- [ ] Verify: Analysis table compares different deductible options
- [ ] Verify: Break-even points shown
- [ ] Verify: Rationale explained
- [ ] **Expected:** Deductible guidance provided

### Test Suite 2.2: Logistics Realism Panel

**Location:** Analytics Tab → Logistics Realism Panel

#### Test Case 2.2.1: Cargo Container Validation
- [ ] Navigate to `/results` → Analytics tab
- [ ] Verify: Logistics Realism Panel visible
- [ ] Verify: Cargo Container Validation component visible
- [ ] Verify: Status shown: VALID or MISMATCH
- [ ] Verify: Warnings displayed for mismatches
- [ ] Verify: Alternative container suggestions shown (if mismatch)
- [ ] Verify: Additional checks for sensitive cargo (if applicable)
- [ ] **Expected:** Cargo-container compatibility validated

#### Test Case 2.2.2: Route Seasonality Risk
- [ ] Verify: Route Seasonality Risk component visible
- [ ] Verify: Current season displayed
- [ ] Verify: Overall risk level shown (LOW/MEDIUM/HIGH)
- [ ] Verify: Risk factors listed (e.g., storm frequency, wave height)
- [ ] Verify: Climatic indices shown (ENSO, PDO, MJO)
- [ ] Verify: Interpretations provided
- [ ] **Expected:** Seasonality risks identified

#### Test Case 2.2.3: Port Congestion Status
- [ ] Verify: Port Congestion Status component visible
- [ ] Verify: POL (Port of Loading) status shown
- [ ] Verify: POD (Port of Discharge) status shown
- [ ] Verify: Transshipment ports listed (if applicable)
- [ ] Verify: Dwell times displayed
- [ ] Verify: Normal dwell times shown for comparison
- [ ] Verify: Status badges (MILD/HIGH)
- [ ] Verify: Percentage delta calculated
- [ ] Verify: Alerts for high congestion
- [ ] **Expected:** Port congestion clearly communicated

#### Test Case 2.2.4: Delay Probabilities
- [ ] Verify: Delay Probabilities section visible
- [ ] Verify: P(7 days delay) shown
- [ ] Verify: P(14 days delay) shown
- [ ] Verify: P(21+ days delay) shown
- [ ] Verify: Probabilities formatted as percentages
- [ ] **Expected:** Delay risks quantified

#### Test Case 2.2.5: Packaging Recommendations
- [ ] Verify: Packaging Recommendations section visible
- [ ] Verify: List of recommended items shown
- [ ] Verify: Each item shows: name, cost, risk reduction %
- [ ] Verify: Rationale provided for each item
- [ ] **Expected:** Actionable packaging guidance

#### Test Case 2.2.6: Insurance Attention Flags
- [ ] Verify: Insurance Attention Flags component visible
- [ ] Verify: Flags generated based on shipment characteristics
- [ ] Verify: Common flags: HIGH VALUE, LONG TRANSIT, FRAGILE, WEATHER RISK, etc.
- [ ] Verify: Each flag has message and insurance recommendation
- [ ] **Expected:** Critical insurance considerations highlighted

### Test Suite 2.3: Missing Data Handling

#### Test Case 2.3.1: Missing Insurance Data
- [ ] Test with engine output missing `insurance` field
- [ ] Verify: Insurance panel shows empty state (no crash)
- [ ] Verify: Console shows no errors
- [ ] **Expected:** Graceful degradation

#### Test Case 2.3.2: Missing Logistics Data
- [ ] Test with engine output missing `logistics` field
- [ ] Verify: Logistics panel shows empty state (no crash)
- [ ] Verify: Console shows no errors
- [ ] **Expected:** Graceful degradation

---

## 🧪 SPRINT 3 TESTING
### Risk Disclosure + Chart Enhancements

### Test Suite 3.1: Risk Disclosure Panel

**Location:** Analytics Tab → Risk Disclosure Panel

#### Test Case 3.1.1: Latent Risks Table
- [ ] Navigate to `/results` → Analytics tab
- [ ] Verify: Risk Disclosure Panel visible
- [ ] Verify: Latent Risks Table visible
- [ ] Verify: Risks sorted by severity (HIGH first)
- [ ] Verify: Each risk shows: name, severity badge, category, probability, impact, mitigation
- [ ] Verify: Color coding: Red (HIGH), Amber (MEDIUM), Blue (LOW)
- [ ] Verify: Probability formatted as percentage
- [ ] **Expected:** All latent risks clearly displayed

#### Test Case 3.1.2: Tail Events Explainer
- [ ] Verify: Tail Events Explainer visible
- [ ] Verify: Risk Thresholds summary cards show: P95, P99, Max Loss
- [ ] Verify: Tail events list shows: event, probability, potential loss
- [ ] Verify: Historical precedent shown (if available)
- [ ] Verify: Interpretation section explains tail risk
- [ ] **Expected:** Tail risk comprehensively explained

#### Test Case 3.1.3: Actionable Mitigations
- [ ] Verify: Actionable Mitigations section visible
- [ ] Verify: Mitigations sorted by risk reduction (highest first)
- [ ] Verify: Each mitigation shows: action, cost, risk reduction %, payback period
- [ ] Verify: ROI indicator shows "Risk Reduction per $1K"
- [ ] Verify: BEST ROI badge on top mitigation
- [ ] Verify: Summary explains mitigation priority
- [ ] **Expected:** Clear mitigation guidance with ROI

### Test Suite 3.2: Chart Enhancements

#### Test Case 3.2.1: Factor Contribution Waterfall
**Location:** Overview Tab → Factor Contribution Waterfall

- [ ] Navigate to `/results` → Overview tab
- [ ] Verify: Factor Contribution Waterfall chart visible
- [ ] Verify: Chart shows base risk → layer contributions → final score
- [ ] Verify: Positive contributions shown in red (increases risk)
- [ ] Verify: Negative contributions shown in green (decreases risk)
- [ ] Verify: Base and final bars shown in gray
- [ ] Verify: Reference line at final score
- [ ] Verify: Tooltip shows contribution and running total
- [ ] Verify: Methodology explainer is collapsible
- [ ] **Expected:** Clear visualization of factor build-up

#### Test Case 3.2.2: RiskRadar Enhanced Tooltip
**Location:** Overview Tab → Risk Visualization Grid → RiskRadar

- [ ] Hover over any risk layer in RiskRadar
- [ ] Verify: Tooltip shows layer name
- [ ] Verify: Tooltip shows score and risk level
- [ ] Verify: Tooltip shows **Contribution %** (cyan text)
- [ ] Verify: Tooltip shows **FAHP Weight** (purple text)
- [ ] Verify: Interpretation text explains contribution and weight
- [ ] Verify: Mini progress bar visible
- [ ] **Expected:** Enhanced tooltip with algorithm data

#### Test Case 3.2.3: FinancialModule Tail Risk Section
**Location:** Analytics Tab → Financial Module

- [ ] Navigate to `/results` → Analytics tab
- [ ] Verify: Financial Module visible
- [ ] Verify: Tail Risk Analysis section visible (below chart)
- [ ] Verify: P95-P99 Range card shows dollar amount
- [ ] Verify: Beyond P99 card shows dollar amount
- [ ] Verify: Tail risk interpretation text visible
- [ ] **Expected:** Tail risk clearly highlighted

#### Test Case 3.2.4: LayersTable Enhanced Columns
**Location:** Analytics Tab → Layers Table

- [ ] Navigate to `/results` → Analytics tab
- [ ] Verify: Layers Table visible
- [ ] Verify: Table shows new column: **FAHP Weight**
- [ ] Verify: Table shows new column: **TOPSIS Score**
- [ ] Verify: FAHP Weight column shows percentages (purple text)
- [ ] Verify: TOPSIS Score column shows 3 decimals (cyan text)
- [ ] Verify: Shows "—" if data not available
- [ ] **Expected:** Algorithm data visible in table

---

## 🔗 INTEGRATION TESTING

### Test Suite I.1: Cross-Sprint Integration

#### Test Case I.1.1: All Panels Render Together
- [ ] Navigate to `/results` with complete engine data
- [ ] Verify: All Sprint 1 panels visible
- [ ] Verify: All Sprint 2 panels visible
- [ ] Verify: All Sprint 3 panels visible
- [ ] Verify: No layout breaks
- [ ] Verify: No console errors
- [ ] **Expected:** All components coexist harmoniously

#### Test Case I.1.2: Data Consistency
- [ ] Verify: Risk score consistent across all panels
- [ ] Verify: Cargo type consistent across panels
- [ ] Verify: Route information consistent
- [ ] Verify: Financial values consistent
- [ ] **Expected:** Single source of truth maintained

#### Test Case I.1.3: Lazy Loading Performance
- [ ] Open browser DevTools → Network tab
- [ ] Navigate to `/results`
- [ ] Verify: Components load on-demand (lazy loading)
- [ ] Verify: No unnecessary bundle size
- [ ] **Expected:** Optimal performance

### Test Suite I.2: Adapter Integration

#### Test Case I.2.1: Adapter Handles All Data
- [ ] Test with full engine output
- [ ] Verify: All ViewModel slices populated
- [ ] Verify: No data loss
- [ ] Verify: Type safety maintained
- [ ] **Expected:** Complete data transformation

#### Test Case I.2.2: Adapter Handles Missing Data
- [ ] Test with partial engine output
- [ ] Verify: Adapter uses fallback logic
- [ ] Verify: No crashes
- [ ] Verify: Empty states shown appropriately
- [ ] **Expected:** Graceful degradation

---

## 🎯 END-TO-END SCENARIOS

### Scenario E2E-1: Complete Analysis Flow

**Steps:**
1. Navigate to `/analyze`
2. Enter shipment data:
   - Cargo Type: Electronics
   - Container: 40DV
   - POL: VNSGN (Ho Chi Minh)
   - POD: USLAX (Los Angeles)
   - Value: $500,000
3. Run analysis
4. Navigate to `/results`

**Verification:**
- [ ] All panels load correctly
- [ ] Narrative is personalized
- [ ] Algorithm data visible
- [ ] Insurance recommendations shown
- [ ] Logistics validation shown
- [ ] Risk disclosure visible
- [ ] Charts render correctly

### Scenario E2E-2: High-Risk Shipment

**Steps:**
1. Enter high-risk shipment (e.g., fragile cargo, long transit, storm season)
2. Run analysis
3. Navigate to `/results`

**Verification:**
- [ ] Risk score reflects high risk
- [ ] Insurance panel shows high expected loss
- [ ] Logistics panel shows warnings
- [ ] Risk disclosure shows multiple latent risks
- [ ] Mitigations prioritized appropriately

### Scenario E2E-3: Low-Risk Shipment

**Steps:**
1. Enter low-risk shipment (e.g., bulk commodity, short transit, stable route)
2. Run analysis
3. Navigate to `/results`

**Verification:**
- [ ] Risk score reflects low risk
- [ ] Insurance panel shows lower premium
- [ ] Logistics panel shows minimal warnings
- [ ] Risk disclosure shows fewer risks
- [ ] Mitigations less critical

---

## 🔄 REGRESSION TESTING

### Test Suite R.1: Existing Functionality

#### Test Case R.1.1: Original Charts Still Work
- [ ] Verify: RiskRadar still functions
- [ ] Verify: FinancialModule still functions
- [ ] Verify: LayersTable still functions
- [ ] Verify: Timeline still functions
- [ ] **Expected:** No regressions

#### Test Case R.1.2: Original Navigation Still Works
- [ ] Verify: Tab switching works
- [ ] Verify: Panel scrolling works
- [ ] Verify: Responsive layout works
- [ ] **Expected:** No UI regressions

---

## ⚡ PERFORMANCE TESTING

### Test Suite P.1: Load Performance

#### Test Case P.1.1: Initial Page Load
- [ ] Open DevTools → Performance tab
- [ ] Record page load
- [ ] Verify: First Contentful Paint < 2s
- [ ] Verify: Time to Interactive < 5s
- [ ] **Expected:** Fast initial load

#### Test Case P.1.2: Lazy Loading Performance
- [ ] Verify: Components load on-demand
- [ ] Verify: No blocking renders
- [ ] Verify: Smooth transitions
- [ ] **Expected:** Optimal lazy loading

### Test Suite P.2: Runtime Performance

#### Test Case P.2.1: Chart Rendering
- [ ] Verify: Charts render smoothly
- [ ] Verify: No lag on hover
- [ ] Verify: Tooltips appear instantly
- [ ] **Expected:** Smooth interactions

---

## ♿ ACCESSIBILITY TESTING

### Test Suite A.1: Keyboard Navigation

- [ ] Verify: All interactive elements keyboard accessible
- [ ] Verify: Tab order logical
- [ ] Verify: Focus indicators visible
- [ ] **Expected:** Full keyboard support

### Test Suite A.2: Screen Reader

- [ ] Verify: All text readable by screen reader
- [ ] Verify: Charts have alt text or descriptions
- [ ] Verify: ARIA labels present
- [ ] **Expected:** Screen reader compatible

---

## 🌐 BROWSER COMPATIBILITY

### Test Suite B.1: Modern Browsers

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

**Verification:**
- [ ] All features work
- [ ] No console errors
- [ ] Layout consistent
- [ ] **Expected:** Cross-browser compatible

---

## 📊 TEST RESULTS TEMPLATE

### Test Execution Log

**Date:** _______________  
**Tester:** _______________  
**Environment:** _______________

| Test Suite | Test Case | Status | Notes |
|------------|-----------|--------|-------|
| 1.1 | 1.1.1 | ⬜ Pass / ⬜ Fail | |
| 1.1 | 1.1.2 | ⬜ Pass / ⬜ Fail | |
| ... | ... | ... | ... |

---

## 🐛 BUG REPORT TEMPLATE

**Title:** [Component] [Issue Description]

**Steps to Reproduce:**
1. ...
2. ...
3. ...

**Expected Result:**
...

**Actual Result:**
...

**Environment:**
- Browser: ...
- OS: ...
- Version: ...

**Screenshots:**
[Attach if applicable]

---

## ✅ SIGN-OFF CHECKLIST

Before marking testing complete:

- [ ] All Sprint 1 tests passed
- [ ] All Sprint 2 tests passed
- [ ] All Sprint 3 tests passed
- [ ] Integration tests passed
- [ ] E2E scenarios passed
- [ ] Regression tests passed
- [ ] Performance acceptable
- [ ] Accessibility verified
- [ ] Browser compatibility verified
- [ ] Documentation updated

---

**END OF COMPREHENSIVE TESTING GUIDE**
