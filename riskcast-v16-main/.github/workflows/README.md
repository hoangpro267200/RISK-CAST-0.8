# GitHub Actions CI/CD Configuration

This directory contains the CI/CD workflows for RiskCast.

## Workflows

### test.yml
Main test and quality gates workflow that runs on push and pull requests.

**Jobs:**
1. **lint** - Code style and linting (Ruff, Black, isort, MyPy)
2. **unit-tests** - Unit tests with coverage reporting
3. **integration-tests** - Integration tests with PostgreSQL and Redis
4. **security-tests** - Security scans (Bandit, Safety) and security tests
5. **e2e-tests** - End-to-end tests
6. **performance-tests** - Performance benchmarks (main branch only)
7. **quality-gate** - Aggregated quality gate validation

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

## Performance SLAs

| Endpoint | P50 | P95 | P99 | Error Rate |
|----------|-----|-----|-----|------------|
| Quote Request | 200ms | 500ms | 1000ms | <1% |
| Risk Assessment | 300ms | 800ms | 1500ms | <1% |
| Quote List | 100ms | 300ms | 600ms | <0.5% |
| Dashboard | 150ms | 400ms | 800ms | <0.5% |
| Health Check | 50ms | 100ms | 200ms | <0.1% |

## Artifacts

Each job uploads relevant artifacts:

- **unit-test-results**: JUnit XML + HTML coverage report
- **integration-test-results**: JUnit XML
- **security-reports**: Bandit JSON, Safety JSON, JUnit XML
- **e2e-test-results**: JUnit XML
- **performance-report**: CSV stats + HTML report

## PR Comments

The quality gate job automatically comments on pull requests with:
- Overall pass/fail status
- Individual check results
- Detailed messages for failures
- Quality threshold reference

## Running Locally

### Run all checks:
```bash
# Linting
ruff check .
black --check .
isort --check-only .
mypy app/

# Tests
pytest tests/unit/ -v --cov=app --cov-report=html
pytest tests/integration/ -v
pytest tests/security/ -v
pytest tests/e2e/ -v -m e2e

# Quality gates
python tests/quality_gates.py \
    --unit-results junit-unit.xml \
    --integration-results junit-integration.xml \
    --coverage-report htmlcov/
```

### Run performance tests:
```bash
# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run Locust
locust -f tests/load/locustfile.py MixedWorkloadUser \
    --host http://localhost:8000 \
    --users 20 \
    --spawn-rate 5 \
    --run-time 2m \
    --headless \
    --csv performance

# Validate
python tests/load/validate_performance.py
```

## Troubleshooting

### Coverage not meeting threshold
- Check `htmlcov/index.html` for uncovered lines
- Add tests for missing coverage

### Security issues found
- Review `bandit-report.json` for details
- Fix or add `# nosec` comments with justification

### Performance SLA violations
- Check `performance-report.html` for detailed metrics
- Optimize slow endpoints
- Consider caching strategies

### Test failures
- Check JUnit XML files for failure details
- Review test logs in GitHub Actions

## Customization

To adjust quality thresholds, edit `tests/quality_gates.py`:

```python
THRESHOLDS = {
    "unit_test_pass_rate": 1.0,        # 100%
    "code_coverage": 0.80,              # 80%
    "critical_security_issues": 0,      # 0
    "high_security_issues": 5,          # Max 5
}
```

To adjust performance SLAs, edit `tests/load/performance_requirements.py`:

```python
PERFORMANCE_REQUIREMENTS = {
    "quote_request": {"p50": 200, "p95": 500, "p99": 1000, "error_rate": 0.01},
    # ...
}
```

## Status Badges

Add to README.md:

```markdown
![Tests](https://github.com/your-org/riskcast/actions/workflows/test.yml/badge.svg)
[![codecov](https://codecov.io/gh/your-org/riskcast/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/riskcast)
```
