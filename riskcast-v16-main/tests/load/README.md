# Load Testing Suite - README

## Overview

Comprehensive load testing suite for RiskCast using **Locust**, a powerful Python-based load testing framework.

## Files

```
tests/load/
├── locustfile.py              - Main Locust test scenarios
├── run_load_tests.py          - Test runner with predefined scenarios
├── performance_requirements.py - SLA definitions and validation
├── README.md                  - This file
└── requirements.txt           - Python dependencies
```

## Installation

### Install Dependencies

```bash
pip install locust
```

Or from requirements file:

```bash
pip install -r tests/load/requirements.txt
```

## Quick Start

### 1. Run Quick Smoke Test
```bash
python tests/load/run_load_tests.py --quick
```

### 2. Run Baseline Performance Test
```bash
python tests/load/run_load_tests.py --baseline
```

### 3. Run with Web UI
```bash
cd tests/load
locust -f locustfile.py MixedWorkloadUser --host http://localhost:8000
```

Then open http://localhost:8089 in your browser.

## Test Scenarios

### 1. Quote Load Test (`QuoteLoadUser`)
**Purpose:** Test quote request and lifecycle operations

**Operations:**
- Request quotes (10x weight)
- List quotes (5x weight)
- Get quote details (3x weight)
- Accept quotes (2x weight)
- Quote analytics (1x weight)

**Wait Time:** 1-3 seconds between requests

**Command:**
```bash
python tests/load/run_load_tests.py --scenario quotes --users 50 --duration 5m
```

### 2. Risk Assessment Load Test (`RiskAssessmentUser`)
**Purpose:** Test risk assessment engine performance

**Operations:**
- Assess risk (10x weight)
- Get risk history (3x weight)
- Get risk factors (2x weight)

**Wait Time:** 0.5-2 seconds between requests

**Command:**
```bash
python tests/load/run_load_tests.py --scenario risk --users 100 --duration 5m
```

### 3. Mixed Workload Test (`MixedWorkloadUser`)
**Purpose:** Simulate realistic user behavior with mixed operations

**Operations:**
- Request quotes (5x weight)
- Assess risk (3x weight)
- View dashboard (4x weight)
- List policies (2x weight)
- View analytics (1x weight)
- Health check (2x weight)
- Check usage (1x weight)

**Wait Time:** 1-5 seconds between requests

**Command:**
```bash
python tests/load/run_load_tests.py --scenario mixed --users 50 --duration 10m
```

### 4. Spike Test (`SpikeTestUser`)
**Purpose:** Test system behavior under sudden traffic spikes

**Operations:**
- Rapid quote requests (5x weight)
- Rapid risk assessments (5x weight)
- Rapid health checks (2x weight)

**Wait Time:** 0.1-0.5 seconds (very fast!)

**Command:**
```bash
python tests/load/run_load_tests.py --spike
```

### 5. Endurance Test (`EnduranceTestUser`)
**Purpose:** Test system stability under sustained load

**Operations:**
- Sustained quote requests (3x weight)
- Sustained risk assessments (3x weight)
- Sustained list operations (2x weight)
- Sustained health checks (1x weight)

**Wait Time:** 2-5 seconds between requests

**Command:**
```bash
python tests/load/run_load_tests.py --endurance
```

## Predefined Test Profiles

### Quick Smoke Test
```bash
python tests/load/run_load_tests.py --quick
```
- **Users:** 10
- **Duration:** 1 minute
- **Purpose:** Quick validation

### Baseline Performance Test
```bash
python tests/load/run_load_tests.py --baseline
```
- **Users:** 50
- **Duration:** 5 minutes
- **Purpose:** Establish baseline metrics

### Stress Test
```bash
python tests/load/run_load_tests.py --stress
```
- **Users:** 200
- **Duration:** 10 minutes
- **Purpose:** Find breaking points

### Spike Test
```bash
python tests/load/run_load_tests.py --spike
```
- **Users:** 500
- **Spawn Rate:** 100/second
- **Duration:** 2 minutes
- **Purpose:** Test burst handling

### Endurance Test
```bash
python tests/load/run_load_tests.py --endurance
```
- **Users:** 100
- **Duration:** 1 hour
- **Purpose:** Test long-term stability

### All Scenarios
```bash
python tests/load/run_load_tests.py --all
```
Runs all test scenarios sequentially.

## Custom Tests

### Custom Parameters
```bash
python tests/load/run_load_tests.py \
  --scenario mixed \
  --users 150 \
  --spawn-rate 15 \
  --duration 15m \
  --host http://staging.riskcast.com
```

### Filter by Tags
```bash
python tests/load/run_load_tests.py \
  --scenario mixed \
  --tags "quotes,create"
```

Available tags:
- `quotes`, `create`, `list`, `get`, `accept`, `analytics`
- `risk`, `assess`, `history`, `factors`
- `mixed`, `dashboard`, `policies`, `health`, `usage`
- `spike`, `endurance`

## Distributed Testing

### Start Master
```bash
locust -f tests/load/locustfile.py \
  MixedWorkloadUser \
  --host http://localhost:8000 \
  --master
```

### Start Workers (on same or different machines)
```bash
locust -f tests/load/locustfile.py \
  --worker \
  --master-host=<master-ip>
```

### Example: 4 Workers
```bash
# Terminal 1: Master
locust -f tests/load/locustfile.py MixedWorkloadUser --host http://localhost:8000 --master

# Terminals 2-5: Workers
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
```

## Performance Requirements

### SLA Definitions

Located in `performance_requirements.py`:

| Endpoint | p50 | p95 | p99 | Max Error Rate | Min RPS |
|----------|-----|-----|-----|----------------|---------|
| Quote Request | 500ms | 1500ms | 3000ms | 1% | 50 |
| Risk Assessment | 300ms | 800ms | 1500ms | 1% | 100 |
| Quote List | 100ms | 300ms | 500ms | 0.5% | 200 |
| Dashboard | 200ms | 500ms | 1000ms | 0.5% | 100 |
| Health Check | 10ms | 50ms | 100ms | 0.1% | 1000 |

### Validate Results

After running a test:

```bash
python tests/load/performance_requirements.py \
  reports/load_tests/load_test_mixed_20260124_120000_stats.csv \
  reports/load_tests/validation_report.txt
```

Output:
```
✅ ALL PERFORMANCE REQUIREMENTS MET

or

❌ 3 PERFORMANCE VIOLATIONS DETECTED
  ❌ quote_request: p95 1850ms exceeds limit 1500ms
  ❌ risk_assessment: error rate 2.50% exceeds limit 1.00%
  ❌ dashboard: RPS 85.0 below minimum 100
```

## Reports

### Report Location
```
reports/load_tests/
├── load_test_mixed_20260124_120000.html      # HTML report
├── load_test_mixed_20260124_120000_stats.csv # Statistics
├── load_test_mixed_20260124_120000_failures.csv # Failures
└── validation_report.txt                      # SLA validation
```

### HTML Report Contents
- Request statistics
- Response time charts
- Percentile graphs
- Failure analysis
- RPS over time

### CSV Reports
- **_stats.csv:** Per-endpoint statistics
- **_failures.csv:** Failed request details
- **_exceptions.csv:** Exception stack traces

## Monitoring During Tests

### Real-time Metrics

When running headless tests, you'll see:

```
[2026-01-24 12:00:00] Type    Name                            # reqs  # fails  Avg    Min    Max    Med    RPS
[2026-01-24 12:00:00] POST    /api/v3/quotes/request          1234    5        456    89     2345   423    12.3
[2026-01-24 12:00:00] POST    /api/v3/risk/assess             2345    8        234    45     1234   212    23.4
```

### Web UI Monitoring

Access http://localhost:8089 for:
- Real-time charts
- Request distribution
- Response times
- Failure rates
- Workers status (distributed mode)

## Best Practices

### 1. Start Small
Begin with quick smoke tests before full load tests.

### 2. Incremental Load
Gradually increase users to find breaking points:
```bash
# Step 1: Baseline
python tests/load/run_load_tests.py --baseline

# Step 2: Medium Load
python tests/load/run_load_tests.py --scenario mixed --users 100 --duration 10m

# Step 3: High Load
python tests/load/run_load_tests.py --stress

# Step 4: Spike
python tests/load/run_load_tests.py --spike
```

### 3. Monitor System Resources
- CPU usage
- Memory usage
- Database connections
- Network bandwidth
- Disk I/O

### 4. Test Realistic Scenarios
Use `MixedWorkloadUser` for most realistic simulations.

### 5. Validate Results
Always run validation against performance requirements.

### 6. Test Different Times
Run tests at different times to catch time-dependent issues.

### 7. Clean Test Environment
Ensure consistent starting state between test runs.

## Troubleshooting

### Connection Errors
```
ConnectionError: HTTPConnectionPool(host='localhost', port=8000)
```

**Solution:** Ensure server is running on specified host/port.

### Rate Limiting
```
Response: 429 Too Many Requests
```

**Solution:** This is expected in spike tests. Check rate limiter configuration.

### High Failure Rate
```
Failure rate: 25.3%
```

**Solutions:**
1. Reduce spawn rate
2. Reduce number of users
3. Check server logs for errors
4. Verify server has sufficient resources

### Slow Response Times
```
p95: 5234ms (exceeds 1500ms limit)
```

**Solutions:**
1. Check database query performance
2. Review slow query logs
3. Check external API latency
4. Consider caching strategies
5. Scale server resources

### Import Errors
```
ModuleNotFoundError: No module named 'locust'
```

**Solution:**
```bash
pip install locust
```

## Advanced Usage

### Custom Event Hooks

Add custom metrics in `locustfile.py`:

```python
@events.request.add_listener
def on_request(request_type, name, response_time, **kwargs):
    if response_time > 1000:
        print(f"Slow request: {name} took {response_time}ms")
```

### Custom User Classes

Create specialized user behavior:

```python
class HighValueQuoteUser(RiskcastUser):
    """User only requesting high-value quotes."""
    
    @task
    def request_high_value_quote(self):
        payload = generate_quote_request()
        payload["cargo_value_usd"] = random.randint(1000000, 5000000)
        
        self.client.post(
            "/api/v3/quotes/request",
            json=payload,
            headers=self.headers
        )
```

### Environment Variables

Configure via environment:

```bash
export LOCUST_HOST=http://staging.riskcast.com
export LOCUST_USERS=100
export LOCUST_SPAWN_RATE=10
export LOCUST_RUN_TIME=10m

locust -f tests/load/locustfile.py MixedWorkloadUser --headless
```

## Performance Tuning Tips

### 1. Database
- Add indexes on frequently queried fields
- Optimize slow queries
- Use connection pooling
- Consider read replicas

### 2. Caching
- Cache frequently accessed data
- Use Redis for session storage
- Implement API response caching

### 3. Application
- Use async/await for I/O operations
- Profile code for bottlenecks
- Optimize serialization
- Reduce unnecessary queries

### 4. Infrastructure
- Scale horizontally (add servers)
- Use load balancer
- CDN for static assets
- Database tuning

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install locust
      
      - name: Run baseline test
        run: |
          python tests/load/run_load_tests.py \
            --baseline \
            --host ${{ secrets.STAGING_URL }}
      
      - name: Validate performance
        run: |
          python tests/load/performance_requirements.py \
            reports/load_tests/*_stats.csv \
            reports/validation.txt
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: load-test-reports
          path: reports/load_tests/
```

## Statistics

- **Test Scenarios:** 5
- **User Classes:** 5
- **Endpoints Tested:** 10+
- **Performance Requirements:** 10
- **Lines of Code:** ~700

---

**Status:** ✅ Complete and ready for execution

**Requirements:** Python 3.8+, Locust 2.0+

**Target:** RiskCast API v3
