# RiskCast - CI/CD Quality Gates

## Overview

Comprehensive CI/CD pipeline with automated quality gates, security scanning, and performance validation.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitHub Actions Pipeline                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Lint       │  Ruff, Black, isort, MyPy
└──────┬───────┘
       │
       ├──────────────────────────────────────────────────────────┐
       │                                                          │
┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐  ┌────────▼──────┐
│ Unit Tests   │  │ Integration  │  │  Security    │  │   E2E Tests   │
│ (Coverage)   │  │   Tests      │  │   Tests      │  │               │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────┬──────┘
       │                 │                 │                    │
       └─────────────────┴─────────────────┴────────────────────┘
                                  │
                         ┌────────▼──────────┐
                         │  Quality Gate     │
                         │  Aggregation      │
                         └────────┬──────────┘
                                  │
                         ┌────────▼──────────┐
                         │  PR Comment       │
                         │  (Results)        │
                         └───────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  Performance Tests (main branch only)                            │
│  - Load testing with Locust                                      │
│  - SLA validation                                                │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quality Gates

### 1. Linting & Code Style ✅

**Tools:**
- **Ruff**: Fast Python linter
- **Black**: Code formatting
- **isort**: Import sorting
- **MyPy**: Static type checking

**Threshold:** All checks must pass

### 2. Unit Tests ✅

**Coverage:** ≥80% required

**Metrics:**
- Line coverage
- Branch coverage
- Function coverage

**Reports:**
- JUnit XML (test results)
- Coverage XML (for Codecov)
- HTML report (artifacts)

### 3. Integration Tests ✅

**Services:**
- PostgreSQL 15
- Redis 7

**Pass Rate:** 100% required

**Tests:**
- API endpoints
- Database operations
- External service mocks

### 4. Security Tests 🔒

**Tools:**
- **Bandit**: Security linting
- **Safety**: Dependency vulnerability checking
- **Custom security tests**: SQL injection, XSS, auth bypass

**Thresholds:**
- Critical issues: 0
- High severity: ≤5

### 5. E2E Tests 🎭

**Pass Rate:** 100% required

**Flows:**
- Quote to policy
- Claims processing
- Customer onboarding
- Model calibration

### 6. Performance Tests 🚀

**Run:** Main branch only

**SLAs:**

| Endpoint | P50 | P95 | P99 | Error Rate |
|----------|-----|-----|-----|------------|
| Quote Request | 200ms | 500ms | 1000ms | <1% |
| Risk Assessment | 300ms | 800ms | 1500ms | <1% |
| Quote List | 100ms | 300ms | 600ms | <0.5% |
| Dashboard | 150ms | 400ms | 800ms | <0.5% |
| Health Check | 50ms | 100ms | 200ms | <0.1% |

---

## Workflow Jobs

### Job 1: Lint (2-3 min)
```yaml
- Ruff check
- Black format check
- isort check
- MyPy type check
```

### Job 2: Unit Tests (3-5 min)
```yaml
- Install dependencies
- Run pytest with coverage
- Upload to Codecov
- Store artifacts
```

### Job 3: Integration Tests (5-7 min)
```yaml
- Start PostgreSQL + Redis
- Run migrations
- Run integration tests
- Store results
```

### Job 4: Security Tests (4-6 min)
```yaml
- Run Bandit scan
- Run Safety check
- Run security tests
- Store reports
```

### Job 5: E2E Tests (8-10 min)
```yaml
- Start services
- Setup database
- Run E2E tests
- Store results
```

### Job 6: Performance Tests (5-7 min)
**Condition:** main branch only
```yaml
- Start API server
- Run Locust load tests
- Validate SLAs
- Store reports
```

### Job 7: Quality Gate (2-3 min)
```yaml
- Download all artifacts
- Run quality_gates.py
- Generate summary
- Comment on PR
```

---

## Quality Gate Script

### `tests/quality_gates.py`

**Features:**
- Parse JUnit XML test results
- Check code coverage
- Validate security scans
- Generate markdown reports
- Exit with appropriate code

**Usage:**
```bash
python tests/quality_gates.py \
    --unit-results junit-unit.xml \
    --integration-results junit-integration.xml \
    --security-results junit-security.xml \
    --e2e-results junit-e2e.xml \
    --coverage-report htmlcov/ \
    --bandit-report bandit-report.json
```

**Output:**
- Console summary
- `quality-gate-summary.md` (for PR comment)
- Exit code 0 (pass) or 1 (fail)

---

## Performance Validation

### `tests/load/validate_performance.py`

**Features:**
- Parse Locust CSV results
- Compare against SLAs
- Generate detailed reports
- Exit with pass/fail status

**Usage:**
```bash
python tests/load/validate_performance.py
```

**Input:** `performance_stats.csv` (from Locust)

**Output:**
- Results table
- SLA comparison
- Violations list
- Exit code 0/1

---

## PR Comments

Automatic PR comments include:

```markdown
# 🎯 Quality Gate Results

**Overall Status:** ✅ PASSED

## 📊 Quality Checks

| Check | Threshold | Actual | Status |
|-------|-----------|--------|--------|
| Unit Test Pass Rate | 100% | 100% | ✅ Pass |
| Integration Test Pass Rate | 100% | 100% | ✅ Pass |
| Security Test Pass Rate | 100% | 100% | ✅ Pass |
| E2E Test Pass Rate | 100% | 100% | ✅ Pass |
| Code Coverage | 80% | 87.5% | ✅ Pass |
| Security Issues | Critical: 0, High: ≤5 | Critical: 0, High: 2 | ✅ Pass |

## 📝 Details

✅ **Unit Test Pass Rate**: 45/45 tests passed (100%)
✅ **Integration Test Pass Rate**: 28/28 tests passed (100%)
✅ **Security Test Pass Rate**: 15/15 tests passed (100%)
✅ **E2E Test Pass Rate**: 18/18 tests passed (100%)
✅ **Code Coverage**: 87.5% coverage (threshold: 80%)
✅ **Security Issues**: 0 critical, 2 high severity issues found

## 🎉 Success

All quality gates have passed! This PR meets all quality standards.
```

---

## Artifacts

### unit-test-results/
- `junit-unit.xml` - Test results
- `htmlcov/` - Coverage report

### integration-test-results/
- `junit-integration.xml` - Test results

### security-reports/
- `bandit-report.json` - Security scan
- `safety-report.json` - Vulnerability check
- `junit-security.xml` - Test results

### e2e-test-results/
- `junit-e2e.xml` - Test results

### performance-report/
- `performance_stats.csv` - Locust results
- `performance-report.html` - Visual report

---

## Running Locally

### Full Pipeline Simulation

```bash
# 1. Linting
ruff check .
black --check .
isort --check-only .
mypy app/ --ignore-missing-imports

# 2. Unit tests
pytest tests/unit/ -v --cov=app --cov-report=xml --cov-report=html --cov-fail-under=80 --junitxml=junit-unit.xml

# 3. Integration tests (requires Docker)
docker-compose up -d postgres redis
pytest tests/integration/ -v --junitxml=junit-integration.xml

# 4. Security tests
bandit -r app/ -f json -o bandit-report.json
safety check --json > safety-report.json
pytest tests/security/ -v --junitxml=junit-security.xml

# 5. E2E tests
pytest tests/e2e/ -v -m e2e --junitxml=junit-e2e.xml

# 6. Quality gates
python tests/quality_gates.py \
    --unit-results junit-unit.xml \
    --integration-results junit-integration.xml \
    --security-results junit-security.xml \
    --e2e-results junit-e2e.xml \
    --coverage-report htmlcov/ \
    --bandit-report bandit-report.json
```

### Performance Tests

```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Run load tests
locust -f tests/load/locustfile.py MixedWorkloadUser \
    --host http://localhost:8000 \
    --users 20 \
    --spawn-rate 5 \
    --run-time 2m \
    --headless \
    --csv performance \
    --html performance-report.html

# Validate
python tests/load/validate_performance.py
```

---

## Configuration

### Adjust Quality Thresholds

Edit `tests/quality_gates.py`:

```python
THRESHOLDS = {
    "unit_test_pass_rate": 1.0,        # 100% pass rate
    "integration_test_pass_rate": 1.0,  # 100% pass rate
    "security_test_pass_rate": 1.0,     # 100% pass rate
    "e2e_test_pass_rate": 1.0,          # 100% pass rate
    "code_coverage": 0.80,              # 80% coverage
    "critical_security_issues": 0,      # No critical
    "high_security_issues": 5,          # Max 5 high
}
```

### Adjust Performance SLAs

Edit `tests/load/performance_requirements.py`:

```python
PERFORMANCE_REQUIREMENTS = {
    "quote_request": {
        "p50": 200,
        "p95": 500,
        "p99": 1000,
        "error_rate": 0.01
    },
    # ...
}
```

---

## Troubleshooting

### Coverage Below Threshold

**Problem:** Coverage at 75%, threshold is 80%

**Solution:**
1. Check `htmlcov/index.html` for uncovered lines
2. Add unit tests for missing coverage
3. Focus on high-impact files first

### Security Issues Found

**Problem:** Bandit reports 3 high severity issues

**Solution:**
1. Review `bandit-report.json` for details
2. Fix genuine security issues
3. Add `# nosec` comments for false positives with justification

### Performance SLA Violations

**Problem:** Quote request P95 is 650ms, SLA is 500ms

**Solution:**
1. Profile slow database queries
2. Add database indexes
3. Implement caching (Redis)
4. Optimize computation logic

### Test Failures in CI but Not Locally

**Problem:** Tests pass locally but fail in GitHub Actions

**Solution:**
1. Check service availability (PostgreSQL, Redis)
2. Review environment variables
3. Check for timing issues (add waits)
4. Review GitHub Actions logs

---

## Best Practices

### 1. Write Tests First
- TDD approach ensures quality
- Tests document expected behavior

### 2. Keep Coverage High
- Aim for 80%+ coverage
- Focus on critical paths

### 3. Monitor Performance
- Regular performance tests
- Track trends over time

### 4. Security First
- Run security scans regularly
- Fix issues immediately

### 5. Fast Feedback
- Optimize CI runtime
- Fail fast on critical issues

---

## Metrics & Monitoring

### Test Execution Time

| Job | Typical Duration |
|-----|------------------|
| Lint | 2-3 min |
| Unit Tests | 3-5 min |
| Integration Tests | 5-7 min |
| Security Tests | 4-6 min |
| E2E Tests | 8-10 min |
| Performance Tests | 5-7 min |
| Quality Gate | 2-3 min |
| **Total** | **~30-40 min** |

### Success Metrics

- **Pass Rate:** Target >95%
- **Coverage:** Maintain ≥80%
- **Performance:** Meet all SLAs
- **Security:** 0 critical issues

---

## Integration with Other Tools

### Codecov
- Automatic coverage tracking
- PR coverage diff
- Coverage trends

### GitHub
- Status checks on PRs
- Required checks before merge
- Branch protection rules

### Slack/Discord (Future)
- Build notifications
- Failure alerts
- Daily summaries

---

**Version:** 1.0.0  
**Date:** 2026-01-24  
**Status:** ✅ Production Ready
