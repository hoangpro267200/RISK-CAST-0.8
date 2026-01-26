# Celery Background Tasks

Celery infrastructure for async task processing in RiskCast V16.

## Overview

This module provides background task processing for:
- **Risk Calculations**: Quote and policy risk assessment
- **Notifications**: Email, webhook, and alert notifications
- **Report Generation**: Daily reports, portfolio analysis, claims reports
- **Data Refresh**: Exchange rates, weather data, port data, cleanup

## Architecture

### Queues

Tasks are routed to specialized queues for better resource management:

- `default`: General purpose tasks
- `risk`: Risk calculation tasks (CPU-intensive)
- `notifications`: Email/webhook delivery (I/O-intensive)
- `reports`: Report generation (CPU + I/O)
- `data`: Data refresh and sync tasks

### Workers

Each queue has dedicated workers with appropriate concurrency:
- Default: 4 workers
- Risk: 2 workers
- Notifications: 2 workers
- Reports: 2 workers
- Data: 2 workers

## Setup

### 1. Install Dependencies

```bash
pip install celery kombu flower redis
```

### 2. Configure Redis

Ensure Redis is running and accessible:

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or use existing Redis instance
export CELERY_BROKER_URL=redis://localhost:6379/1
export CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 3. Start Workers

#### Using Docker Compose

```bash
docker-compose -f docker-compose.celery.yml up -d
```

#### Using Scripts

**Linux/Mac:**
```bash
chmod +x scripts/celery_start.sh
./scripts/celery_start.sh
```

**Windows:**
```cmd
scripts\celery_start.bat
```

#### Manual Start

```bash
# Start default worker
celery -A app.tasks.celery_app worker -l info -Q default -c 4

# Start risk worker
celery -A app.tasks.celery_app worker -l info -Q risk -c 2

# Start beat scheduler
celery -A app.tasks.celery_app beat -l info

# Start Flower (monitoring)
celery -A app.tasks.celery_app flower --port=5555
```

## Usage

### Calling Tasks

```python
from app.tasks.risk_tasks import calculate_quote_risk

# Async call (returns immediately)
result = calculate_quote_risk.delay(
    quote_id="quote-123",
    cargo_data={"cargo_type": "ELECTRONICS", "cargo_value_usd": 100000},
    route_data={"origin_port": "SGSIN", "destination_port": "USLAX"}
)

# Get result (blocks until complete)
risk_result = result.get(timeout=300)
```

### Scheduled Tasks

Tasks are automatically scheduled via Celery Beat:

- **Exchange Rates**: Every 5 minutes
- **Weather Data**: Every 15 minutes
- **Expiring Quotes**: Every hour
- **Daily Reports**: Daily at 6:00 AM
- **Data Cleanup**: Daily

## Monitoring

### Flower Dashboard

Access Flower at `http://localhost:5555` to:
- View active tasks
- Monitor worker status
- Inspect task history
- View task details and results

### Task Status

```python
from app.tasks.risk_tasks import calculate_quote_risk

task = calculate_quote_risk.delay(...)

# Check status
print(task.state)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

# Get result
if task.ready():
    result = task.result
```

## Task Modules

### Risk Tasks (`risk_tasks.py`)

- `calculate_quote_risk`: Calculate risk for a new quote
- `recalculate_policy_risk`: Recalculate risk for active policy
- `batch_risk_recalculation`: Batch process multiple policies
- `analyze_portfolio_risk`: Portfolio-level risk analysis

### Notification Tasks (`notification_tasks.py`)

- `send_email`: Send email notification
- `send_webhook`: Send webhook notification
- `process_expiring_quotes`: Process and notify about expiring quotes
- `send_risk_alert`: Send risk alert to tenant

### Report Tasks (`report_tasks.py`)

- `generate_daily_risk_report`: Generate daily risk report
- `generate_portfolio_report`: Generate comprehensive portfolio report
- `generate_claims_report`: Generate claims report

### Data Tasks (`data_tasks.py`)

- `refresh_exchange_rates`: Refresh currency exchange rates
- `refresh_weather_data`: Refresh weather data for routes
- `refresh_port_data`: Refresh port congestion data
- `cleanup_old_data`: Clean up expired/old data
- `sync_external_data`: Sync data from external sources

## Configuration

### Environment Variables

```bash
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
ENABLE_FLOWER=true  # Enable Flower monitoring
```

### Task Configuration

Tasks are configured in `celery_app.py`:

- **Time Limits**: 1 hour hard limit, 55 minutes soft limit
- **Retry Policy**: 3 retries with exponential backoff
- **Rate Limiting**: 100 tasks/minute default
- **Result Expiry**: 24 hours

## Error Handling

Tasks automatically retry on failure:

```python
@celery_app.task(bind=True, max_retries=3)
def my_task(self):
    try:
        # Task logic
        pass
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60)
```

## Best Practices

1. **Idempotency**: Design tasks to be idempotent (safe to retry)
2. **Timeouts**: Set appropriate timeouts for long-running tasks
3. **Error Handling**: Always handle exceptions and retry appropriately
4. **Logging**: Use structured logging for task execution
5. **Monitoring**: Monitor task queues and worker health
6. **Resource Limits**: Set appropriate concurrency per queue

## Troubleshooting

### Workers Not Starting

1. Check Redis connection: `redis-cli ping`
2. Verify environment variables are set
3. Check worker logs for errors

### Tasks Not Executing

1. Verify workers are running: `celery -A app.tasks.celery_app inspect active`
2. Check queue routing in `celery_app.py`
3. Verify task is registered: `celery -A app.tasks.celery_app inspect registered`

### High Memory Usage

1. Reduce worker concurrency: `-c 2` instead of `-c 4`
2. Enable task result expiration
3. Use `worker_max_tasks_per_child` to recycle workers

## Production Deployment

1. Use process manager (systemd, supervisor) for workers
2. Enable Flower with authentication
3. Use Redis Sentinel for high availability
4. Monitor worker health and restart on failure
5. Set up alerting for failed tasks
6. Use separate Redis instances for broker and results
