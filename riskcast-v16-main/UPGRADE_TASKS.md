# 🚀 RISKCAST UPGRADE TASKS BACKLOG
## Prioritized Task List for Production Readiness

**Last Updated:** 2025-01-11  
**Status:** Active Development

---

## PRIORITY LEGEND

- **P0 (Critical):** Blocks production, must fix immediately
- **P1 (High):** Important for production, fix within 1-2 weeks
- **P2 (Medium):** Nice to have, fix within 1 month
- **P3 (Low):** Future enhancement, backlog

---

## P0 - CRITICAL (Fix Immediately)

### RC-C001: Error Handler Breaks Static Files
- **Status:** 🔴 Open
- **Type:** Bug
- **Assignee:** Backend Team
- **Estimate:** 2 hours
- **Description:** ErrorHandlerMiddleware converts 404s from `/assets/*` to JSON, breaking CSS/JS loading
- **Files:** `app/middleware/error_handler_v2.py:43-57`
- **Fix:** Already implemented, needs verification
- **Acceptance:** Request `/assets/index-vfG_beiV.css` returns CSS with correct MIME type

### RC-D001: Non-Deterministic Monte Carlo
- **Status:** 🔴 Open
- **Type:** Bug
- **Assignee:** Engine Team
- **Estimate:** 4 hours
- **Description:** Monte Carlo uses random seed without persistence, same input → different output
- **Files:** `app/core/engine/risk_engine_v16.py`, `app/core/engine_v2/monte_carlo_engine.py`
- **Fix:** Use deterministic seed or save seed with result
- **Acceptance:** Same input produces identical output

### RC-D006: No Unit Tests for Scoring
- **Status:** 🔴 Open
- **Type:** Tech Debt
- **Assignee:** QA Team
- **Estimate:** 3 days
- **Description:** Risk scoring logic has no unit tests
- **Files:** `tests/unit/test_risk_scoring.py` (create)
- **Fix:** Add comprehensive unit tests for all scoring functions
- **Acceptance:** Test coverage >70% for risk engine

---

## P1 - HIGH (Fix Within 1-2 Weeks)

### RC-A001: Missing Empty States
- **Status:** 🟡 Open
- **Type:** UX Issue
- **Assignee:** Frontend Team
- **Estimate:** 4 hours
- **Description:** Results page lacks empty state when no analysis run
- **Files:** `src/pages/ResultsPage.tsx`, `src/components/states/EmptyState.tsx` (create)
- **Fix:** Add empty state component with CTA
- **Acceptance:** Empty state shown when no data, clear CTA to input page

### RC-A004: Information Density Too High
- **Status:** 🟡 Open
- **Type:** UX Issue
- **Assignee:** Frontend Team
- **Estimate:** 6 hours
- **Description:** Results page shows too much info, decision-making takes >10s
- **Files:** `src/pages/ResultsPage.tsx`, `src/components/ExecutiveSummary.tsx` (create)
- **Fix:** Add executive summary card at top with key metrics
- **Acceptance:** User can understand risk level in <3 seconds

### RC-B001: No Error Boundary on App Root
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** Frontend Team
- **Estimate:** 2 hours
- **Description:** App.tsx doesn't wrap children in ErrorBoundary
- **Files:** `src/App.tsx`, `src/components/ErrorBoundary.tsx`
- **Fix:** Wrap `<App>` children in `<ErrorBoundary>`
- **Acceptance:** Errors caught, show error UI instead of white screen

### RC-C002: Missing Input Validation
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** Backend Team
- **Estimate:** 1 day
- **Description:** Some endpoints accept invalid data without validation
- **Files:** `app/api/v1/risk_routes.py:30-72`, `app/models/shipment.py`
- **Fix:** Add Pydantic validators to all request models
- **Acceptance:** Invalid data rejected with clear error messages

### RC-C006: Inconsistent Error Response Format
- **Status:** 🟡 Open
- **Type:** Tech Debt
- **Assignee:** Backend Team
- **Estimate:** 4 hours
- **Description:** Some endpoints return StandardResponse, others return raw dicts
- **Files:** `app/utils/standard_responses.py`, all route files
- **Fix:** Standardize all endpoints to use StandardResponse
- **Acceptance:** All error responses have same format

### RC-D002: Hardcoded Magic Numbers
- **Status:** 🟡 Open
- **Type:** Tech Debt
- **Assignee:** Engine Team
- **Estimate:** 1 day
- **Description:** Risk scoring uses hardcoded weights without documentation
- **Files:** `app/core/engine/risk_scoring_engine.py`, `app/core/engine/risk_engine_v16.py`
- **Fix:** Extract to configuration file, document rationale
- **Acceptance:** All weights in config file, documented

### RC-D003: Missing Feature Contribution Validation
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** Engine Team
- **Estimate:** 4 hours
- **Description:** No validation that layer contributions sum to 100%
- **Files:** `app/core/engine/risk_scoring_engine.py:176-222`
- **Fix:** Add validation in risk calculation pipeline
- **Acceptance:** Contributions validated, errors logged if invalid

### RC-D004: No Guardrails for Missing Data
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** Engine Team
- **Estimate:** 1 day
- **Description:** Engine doesn't handle missing optional fields gracefully
- **Files:** `app/core/services/risk_service.py:6-100`
- **Fix:** Add default values and confidence adjustments
- **Acceptance:** System handles missing data, adjusts confidence

### RC-E001: Schema Not Validated
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** Backend Team
- **Estimate:** 1 day
- **Description:** Shipment schema allows invalid combinations
- **Files:** `app/models/shipment.py`, `app/validators/`
- **Fix:** Add cross-field validation in Pydantic models
- **Acceptance:** Invalid combinations rejected

### RC-F001: Prompt Not Enforced Vietnamese
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** AI Team
- **Estimate:** 2 hours
- **Description:** AI advisor may respond in English
- **Files:** `app/ai_system_advisor/prompt_templates.py`
- **Fix:** Add explicit Vietnamese requirement to all prompts
- **Acceptance:** All AI responses in Vietnamese

### RC-F002: No Source Attribution
- **Status:** 🟡 Open
- **Type:** Bug
- **Assignee:** AI Team
- **Estimate:** 4 hours
- **Description:** AI responses don't cite sources from system state
- **Files:** `app/ai_system_advisor/advisor_core.py`
- **Fix:** Add source citations to all AI responses
- **Acceptance:** AI responses cite calculation sources

### RC-G001: No Metrics Collection
- **Status:** 🟡 Open
- **Type:** Tech Debt
- **Assignee:** DevOps Team
- **Estimate:** 2 days
- **Description:** No metrics exported (latency, error rate, throughput)
- **Files:** `app/middleware/metrics.py` (create)
- **Fix:** Add metrics middleware, export to Prometheus format
- **Acceptance:** Metrics endpoint `/metrics` returns Prometheus format

### RC-G002: No Distributed Tracing
- **Status:** 🟡 Open
- **Type:** Tech Debt
- **Assignee:** DevOps Team
- **Estimate:** 2 days
- **Description:** request_id exists but not propagated consistently
- **Files:** `app/middleware/request_id.py`, all service files
- **Fix:** Add OpenTelemetry or similar, propagate request_id everywhere
- **Acceptance:** request_id in all logs, traceable across services

### RC-G003: No Alerts Configured
- **Status:** 🟡 Open
- **Type:** Tech Debt
- **Assignee:** DevOps Team
- **Estimate:** 1 day
- **Description:** No alerting system for errors, latency spikes
- **Files:** `app/utils/logger_enhanced.py`, monitoring setup
- **Fix:** Set up alerting (Sentry, PagerDuty, or custom)
- **Acceptance:** Alerts fire on error rate >5%, latency >2s

### RC-H001: Secrets in Default Values
- **Status:** 🟡 Open
- **Type:** Security Risk
- **Assignee:** Backend Team
- **Estimate:** 2 hours
- **Description:** Default secret keys in code
- **Files:** `app/main.py:124`
- **Fix:** Require secrets in production, fail startup if missing
- **Acceptance:** Production fails to start without secrets configured

### RC-H004: Dependency Vulnerabilities
- **Status:** 🟡 Open
- **Type:** Security Risk
- **Assignee:** DevOps Team
- **Estimate:** 4 hours
- **Description:** No automated dependency scanning
- **Files:** `requirements.txt`, `package.json`
- **Fix:** Add automated scanning to CI/CD, update dependencies
- **Acceptance:** CI/CD fails on known vulnerabilities

---

## P2 - MEDIUM (Fix Within 1 Month)

### RC-A002: Inconsistent Loading States
- **Status:** 🟢 Open
- **Type:** UX Issue
- **Assignee:** Frontend Team
- **Estimate:** 4 hours
- **Description:** Some components show loading, others show nothing
- **Files:** `src/pages/ResultsPage.tsx`, `src/pages/SummaryPage.tsx`
- **Fix:** Standardize loading states across all components
- **Acceptance:** All data-fetching components show loading indicator

### RC-A003: Missing Error Recovery
- **Status:** 🟢 Open
- **Type:** UX Issue
- **Assignee:** Frontend Team
- **Estimate:** 4 hours
- **Description:** Error states exist but no retry mechanism
- **Files:** `src/components/states/ErrorState.tsx`, `src/services/errorTracking.ts`
- **Fix:** Add retry logic with exponential backoff
- **Acceptance:** Users can retry failed requests

### RC-A005: Missing Accessibility Labels
- **Status:** 🟢 Open
- **Type:** UX Issue
- **Assignee:** Frontend Team
- **Estimate:** 1 day
- **Description:** Charts and interactive elements lack ARIA labels
- **Files:** `src/components/**/*.tsx` (all chart components)
- **Fix:** Add `aria-label` and `role` attributes
- **Acceptance:** Screen readers can describe all content

### RC-A006: i18n Incomplete
- **Status:** 🟢 Open
- **Type:** UX Issue
- **Assignee:** Frontend Team
- **Estimate:** 1 day
- **Description:** Some UI text still in English
- **Files:** `app/core/i18n/`, `src/components/**/*.tsx`
- **Fix:** Complete i18n translation file
- **Acceptance:** All UI text in Vietnamese

### RC-B002: Race Conditions in Data Fetching
- **Status:** 🟢 Open
- **Type:** Bug
- **Assignee:** Frontend Team
- **Estimate:** 1 day
- **Description:** Multiple components fetch `/results/data` simultaneously
- **Files:** `src/pages/ResultsPage.tsx`, `src/pages/SummaryPage.tsx`
- **Fix:** Implement request deduplication and caching
- **Acceptance:** No duplicate requests, data cached

### RC-B003: Bundle Size Not Optimized
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Frontend Team
- **Estimate:** 2 days
- **Description:** No code splitting, entire app loads upfront
- **Files:** `vite.config.js`, `src/App.tsx`
- **Fix:** Implement route-based code splitting
- **Acceptance:** Initial bundle < 500KB, lazy load heavy components

### RC-B004: Type Safety Gaps
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Frontend Team
- **Estimate:** 2 days
- **Description:** Some API responses not typed, `any` types used
- **Files:** `src/types/`, `src/services/`
- **Fix:** Add strict types for all API responses
- **Acceptance:** No `any` types, all API responses typed

### RC-B005: No Performance Monitoring
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Frontend Team
- **Estimate:** 1 day
- **Description:** Web Vitals tracked but not sent to monitoring
- **Files:** `src/utils/monitoring.ts`, `src/services/errorTracking.ts`
- **Fix:** Integrate with monitoring service
- **Acceptance:** Web Vitals sent to monitoring service

### RC-C003: No API Versioning Strategy
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Backend Team
- **Estimate:** 1 day
- **Description:** Mix of `/api/v1/` and `/api/` endpoints
- **Files:** `app/main.py`, `app/api/`
- **Fix:** Standardize on `/api/v1/`, document deprecation policy
- **Acceptance:** All endpoints under `/api/v1/`, deprecation policy documented

### RC-C004: Missing Idempotency Keys
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Backend Team
- **Estimate:** 1 day
- **Description:** Risk analysis endpoint not idempotent
- **Files:** `app/api/v1/risk_routes.py`, `app/core/services/risk_service.py`
- **Fix:** Add `idempotency_key` header, cache responses
- **Acceptance:** Duplicate requests return same result

### RC-C005: No Request Timeout
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Backend Team
- **Estimate:** 4 hours
- **Description:** Long-running analysis can hang indefinitely
- **Files:** `app/middleware/`, `app/main.py`
- **Fix:** Add timeout middleware, return 504 after threshold
- **Acceptance:** Requests timeout after 30s, return 504

### RC-D005: No Reproducibility Trace
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Engine Team
- **Estimate:** 2 days
- **Description:** Engine doesn't save "decision trace" with results
- **Files:** `app/core/engine/risk_engine_v16.py`, `app/core/engine_state.py`
- **Fix:** Add trace object to result, save to database
- **Acceptance:** Results include trace of calculation steps

### RC-E002: Data Confidence Not Calculated
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Engine Team
- **Estimate:** 1 day
- **Description:** No confidence score for input data quality
- **Files:** `app/core/services/risk_service.py`
- **Fix:** Calculate confidence based on completeness
- **Acceptance:** Results include `data_confidence` field

### RC-E003: Seed/Demo Data Mixed with Prod
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Backend Team
- **Estimate:** 4 hours
- **Description:** Demo data may be used in production
- **Files:** `app/core/services/`, `app/memory.py`
- **Fix:** Ensure demo data only loaded in development
- **Acceptance:** Production doesn't load demo data

### RC-E004: No Database Migrations
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** Backend Team
- **Estimate:** 2 days
- **Description:** MySQL schema changes not versioned
- **Files:** `app/migrations/` (create migration system)
- **Fix:** Implement Alembic or similar migration system
- **Acceptance:** Schema changes versioned and migrated

### RC-F003: No Fallback on Model Error
- **Status:** 🟢 Open
- **Type:** Bug
- **Assignee:** AI Team
- **Estimate:** 4 hours
- **Description:** If Anthropic API fails, no fallback
- **Files:** `app/ai_system_advisor/advisor_core.py`
- **Fix:** Add fallback to rule-based explanations
- **Acceptance:** AI features work even if LLM unavailable

### RC-F004: PII Not Redacted in Logs
- **Status:** 🟢 Open
- **Type:** Security Risk
- **Assignee:** AI Team
- **Estimate:** 4 hours
- **Description:** AI prompts/responses may contain PII
- **Files:** `app/ai_system_advisor/advisor_core.py`, `app/utils/logger_enhanced.py`
- **Fix:** Add PII redaction before logging
- **Acceptance:** No PII in logs

### RC-G004: No Feature Flags
- **Status:** 🟢 Open
- **Type:** Tech Debt
- **Assignee:** DevOps Team
- **Estimate:** 2 days
- **Description:** Cannot toggle features without deployment
- **Files:** `app/config/feature_flags.py` (create)
- **Fix:** Implement feature flag system
- **Acceptance:** Features can be toggled via config

### RC-H002: CORS Too Permissive in Dev
- **Status:** 🟢 Open
- **Type:** Security Risk
- **Assignee:** Backend Team
- **Estimate:** 2 hours
- **Description:** Development CORS allows localhost origins
- **Files:** `app/main.py:82-108`
- **Fix:** Validate origin format, restrict in production
- **Acceptance:** CORS properly restricted in production

### RC-H003: No Rate Limiting on All Endpoints
- **Status:** 🟢 Open
- **Type:** Security Risk
- **Assignee:** Backend Team
- **Estimate:** 1 day
- **Description:** Rate limiting exists but not applied to all endpoints
- **Files:** All route files in `app/api/`, `app/routes/`
- **Fix:** Apply rate limiting to all public endpoints
- **Acceptance:** All endpoints have rate limiting

### RC-H005: CSP Too Permissive
- **Status:** 🟢 Open
- **Type:** Security Risk
- **Assignee:** Backend Team
- **Estimate:** 1 day
- **Description:** CSP allows `unsafe-inline` and `unsafe-eval`
- **Files:** `app/middleware/security_headers.py:20-34`
- **Fix:** Remove `unsafe-inline`, use nonces or hashes
- **Acceptance:** CSP doesn't allow unsafe-inline

---

## COMPLETED TASKS ✅

### RC-C001: Error Handler Breaks Static Files
- **Status:** ✅ Fixed (needs verification)
- **Completed:** 2025-01-11
- **Notes:** Code fixed, needs testing

---

## TASK STATISTICS

- **Total Tasks:** 42
- **P0 (Critical):** 3
- **P1 (High):** 18
- **P2 (Medium):** 21
- **Completed:** 1
- **In Progress:** 0
- **Open:** 41

---

## ESTIMATED EFFORT

- **P0 Tasks:** ~3.5 days
- **P1 Tasks:** ~20 days
- **P2 Tasks:** ~25 days
- **Total:** ~48.5 days (~10 weeks)

---

## NEXT SPRINT PLANNING

### Sprint 1 (Week 1-2): Critical Fixes
- RC-C001: Error Handler (2h)
- RC-D001: Determinism (4h)
- RC-D006: Unit Tests (3d)
- RC-A001: Empty States (4h)
- RC-B001: Error Boundary (2h)
- RC-H001: Secrets (2h)

**Total:** ~4.5 days

### Sprint 2 (Week 3-4): High Priority
- RC-A004: Executive Summary (6h)
- RC-C002: Input Validation (1d)
- RC-C006: Error Format (4h)
- RC-D002: Magic Numbers (1d)
- RC-D003: Contribution Validation (4h)
- RC-D004: Missing Data (1d)
- RC-F001: Vietnamese Prompt (2h)
- RC-F002: Source Attribution (4h)

**Total:** ~5 days

---

**Last Updated:** 2025-01-11  
**Next Review:** Weekly
