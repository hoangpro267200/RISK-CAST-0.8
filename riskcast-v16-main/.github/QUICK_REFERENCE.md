# 🚀 CI/CD Quality Gates - Quick Reference

## Quick Commands

### Local Validation
```bash
# Full pipeline simulation
ruff check . && \
black --check . && \
isort --check-only . && \
mypy app/ && \
pytest tests/unit/ -v --cov=app --cov-fail-under=80 && \
pytest tests/integration/ -v && \
pytest tests/security/ -v && \
pytest tests/e2e/ -v -m e2e
```

### Individual Checks
```bash
# Linting
ruff check .
black --check .
isort --check-only .
mypy app/ --ignore-missing-imports

# Tests
pytest tests/unit/ -v --cov=app --cov-report=html
pytest tests/integration/ -v
pytest tests/security/ -v
pytest tests/e2e/ -v -m e2e

# Quality gates
python tests/quality_gates.py \
    --unit-results junit-unit.xml \
    --coverage-report htmlcov/

# Performance
python tests/load/validate_performance.py
```

---

## Pipeline Jobs (7)

| Job | Duration | Dependencies |
|-----|----------|--------------|
| **lint** | 2-3 min | None |
| **unit-tests** | 3-5 min | None |
| **integration-tests** | 5-7 min | None |
| **security-tests** | 4-6 min | None |
| **e2e-tests** | 8-10 min | unit-tests, integration-tests |
| **performance-tests** | 5-7 min | integration-tests (main only) |
| **quality-gate** | 2-3 min | All above |

**Total:** ~30-40 minutes

---

## Quality Thresholds

| Check | Threshold |
|-------|-----------|
| Unit Test Pass Rate | 100% |
| Integration Test Pass Rate | 100% |
| Security Test Pass Rate | 100% |
| E2E Test Pass Rate | 100% |
| Code Coverage | ≥80% |
| Critical Security Issues | 0 |
| High Security Issues | ≤5 |

---

## Performance SLAs

| Endpoint | P50 | P95 | P99 | Error |
|----------|-----|-----|-----|-------|
| Quote Request | 200ms | 500ms | 1s | <1% |
| Risk Assessment | 300ms | 800ms | 1.5s | <1% |
| Quote List | 100ms | 300ms | 600ms | <0.5% |
| Dashboard | 150ms | 400ms | 800ms | <0.5% |
| Health Check | 50ms | 100ms | 200ms | <0.1% |

---

## Files Created

```
.github/
├── workflows/
│   ├── test.yml                 # Main workflow (350 lines)
│   └── README.md                # Workflow docs
├── CI_CD_GUIDE.md              # Complete guide
├── CI_CD_SUMMARY.md            # Summary
└── QUICK_REFERENCE.md          # This file

tests/
├── quality_gates.py            # Quality gate script (400 lines)
└── load/
    └── validate_performance.py # Performance validation (200 lines)

pyproject.toml                  # Linter configs
```

---

## Workflow Triggers

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

---

## Services Used

### PostgreSQL 15
```yaml
postgres:
  image: postgres:15
  ports: [5432:5432]
  health-cmd: pg_isready
```

### Redis 7
```yaml
redis:
  image: redis:7
  ports: [6379:6379]
  health-cmd: redis-cli ping
```

---

## Artifacts

- **unit-test-results**: JUnit XML + HTML coverage
- **integration-test-results**: JUnit XML
- **security-reports**: Bandit + Safety + JUnit XML
- **e2e-test-results**: JUnit XML
- **performance-report**: CSV + HTML

---

## Linters

| Tool | Purpose | Config |
|------|---------|--------|
| **Ruff** | Fast linting | pyproject.toml |
| **Black** | Formatting | pyproject.toml |
| **isort** | Import sorting | pyproject.toml |
| **MyPy** | Type checking | pyproject.toml |

---

## PR Comment Format

```markdown
# 🎯 Quality Gate Results
**Overall Status:** ✅ PASSED

## 📊 Quality Checks
| Check | Threshold | Actual | Status |
|-------|-----------|--------|--------|
| Unit Test Pass Rate | 100% | 100% | ✅ Pass |
| Code Coverage | 80% | 87.5% | ✅ Pass |
...
```

---

## Troubleshooting

### Coverage Too Low
```bash
# Check coverage report
open htmlcov/index.html

# Run specific file
pytest tests/unit/test_file.py -v --cov=app.module
```

### Security Issues
```bash
# Review Bandit report
cat bandit-report.json | jq '.results'

# Check Safety report
cat safety-report.json | jq
```

### Performance Failures
```bash
# View detailed results
open performance-report.html

# Check specific endpoint
grep "quote_request" performance_stats.csv
```

### Test Failures in CI
```bash
# Check logs in GitHub Actions
# Review service health
# Verify environment variables
```

---

## Configuration Changes

### Adjust Coverage Threshold
```python
# tests/quality_gates.py
THRESHOLDS = {
    "code_coverage": 0.85,  # Change from 0.80 to 0.85
}
```

### Adjust Performance SLA
```python
# tests/load/performance_requirements.py
PERFORMANCE_REQUIREMENTS = {
    "quote_request": {
        "p50": 150,  # Change from 200
    }
}
```

### Add New Check
```python
# tests/quality_gates.py
def check_custom_metric(self, ...):
    # Add custom validation
    pass
```

---

## Statistics

| Metric | Value |
|--------|-------|
| Files Created | 8 |
| Workflows | 1 |
| Jobs | 7 |
| Quality Scripts | 2 |
| Lines of Code | ~950 |
| Criteria Met | 10/10 ✅ |

---

## Status

```
╔════════════════════════════════════╗
║                                    ║
║  ✅ PRODUCTION READY              ║
║                                    ║
║  Jobs:          7                 ║
║  Thresholds:    7                 ║
║  SLAs:          5                 ║
║  Criteria:  10/10 ✅              ║
║                                    ║
║  HOÀN THÀNH!   🎉                 ║
║                                    ║
╚════════════════════════════════════╝
```

**Date:** 2026-01-24  
**Version:** 1.0.0  
**Status:** ✅ COMPLETE
