# QUICK TESTING REFERENCE
## Fast Testing Checklist for All Sprints

**Quick Reference for Manual Testing Sessions**

---

## 🚀 QUICK START

1. **Start Servers:**
   ```bash
   # Terminal 1: Backend
   cd riskcast-v16-main
   python dev_run.py
   
   # Terminal 2: Frontend
   npm run dev
   ```

2. **Open Browser:**
   - Navigate to: `http://localhost:3000`
   - Go to `/analyze` → Enter test data → Run analysis
   - Navigate to `/results`

---

## ✅ SPRINT 1: Quick Checks

### Algorithm Panel (Analytics Tab)
- [ ] FAHP Weight Chart: Bars visible, CR badge shown
- [ ] TOPSIS Table: Alternatives ranked, D+/D-/C* columns
- [ ] Monte Carlo: Percentiles ruler (P10-P99)

### Narrative (Overview Tab)
- [ ] Contains: Cargo type, POL, POD, transit time
- [ ] Does NOT contain: "moderate risk", generic phrases
- [ ] Route Details: Cargo Type + Container Type rows visible

**Time:** ~2 minutes

---

## ✅ SPRINT 2: Quick Checks

### Insurance Panel (Analytics Tab)
- [ ] Loss Distribution: Histogram + CDF, P50/P95/P99 markers
- [ ] Basis Risk: Score + interpretation
- [ ] Triggers: Table with probabilities
- [ ] Coverage: REQUIRED/RECOMMENDED/OPTIONAL
- [ ] Premium: Step-by-step calculation
- [ ] Exclusions: List with mitigations
- [ ] Deductible: Recommendation + analysis table

### Logistics Panel (Analytics Tab)
- [ ] Cargo-Container: VALID/MISMATCH status
- [ ] Seasonality: Season + risk level + factors
- [ ] Port Congestion: POL/POD/transshipments with dwell times
- [ ] Delays: P(7d), P(14d), P(21d+)
- [ ] Packaging: Recommendations with cost/benefit
- [ ] Flags: Insurance attention flags

**Time:** ~5 minutes

---

## ✅ SPRINT 3: Quick Checks

### Risk Disclosure Panel (Analytics Tab)
- [ ] Latent Risks: Table sorted by severity (HIGH first)
- [ ] Tail Events: P95/P99/Max Loss cards + events list
- [ ] Mitigations: Sorted by risk reduction, ROI shown

### Chart Enhancements
- [ ] **Factor Waterfall** (Overview): Base → layers → final score
- [ ] **RiskRadar Tooltip** (Overview): Hover → shows contribution % + FAHP weight
- [ ] **Financial Tail** (Analytics): P95-P99 range + beyond P99
- [ ] **LayersTable** (Analytics): FAHP Weight + TOPSIS Score columns

**Time:** ~3 minutes

---

## 🔍 CRITICAL CHECKS

### Must Pass (P0)
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] All panels render (even with missing data)
- [ ] Empty states show gracefully
- [ ] Navigation works (tabs, scrolling)

### Should Pass (P1)
- [ ] All data displays correctly
- [ ] Charts render smoothly
- [ ] Tooltips work
- [ ] Responsive layout works

---

## 🐛 COMMON ISSUES

| Issue | Check |
|-------|-------|
| Panel not showing | Check `viewModel` has data |
| Chart not rendering | Check container size > 0 |
| Tooltip not showing | Check hover event |
| Type errors | Check adapter output types |

---

## 📝 TEST DATA QUICK REFERENCE

### Full Data Test
```json
{
  "cargo_type": "Electronics",
  "container": "40DV",
  "pol": "VNSGN",
  "pod": "USLAX",
  "value": 500000
}
```

### Missing Data Test
- Remove `algorithm` field → Check empty states
- Remove `insurance` field → Check empty states
- Remove `logistics` field → Check empty states

---

## ⏱️ ESTIMATED TESTING TIME

- **Sprint 1:** 2 minutes
- **Sprint 2:** 5 minutes
- **Sprint 3:** 3 minutes
- **Integration:** 5 minutes
- **Total:** ~15 minutes per full test run

---

## 🎯 PRIORITY ORDER

1. **Critical (P0):** No crashes, errors, or regressions
2. **High (P1):** All panels display, data correct
3. **Medium (P2):** Performance, accessibility, polish

---

**For detailed test cases, see:** `COMPREHENSIVE_TESTING_GUIDE.md`
