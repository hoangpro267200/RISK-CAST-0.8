# Risk Run Worker

Background worker for processing risk run jobs asynchronously.

## Features

- **Concurrent Processing**: Multiple workers can process jobs simultaneously using `SELECT FOR UPDATE SKIP LOCKED`
- **Retry Logic**: Automatic retries with exponential backoff
- **Error Handling**: Graceful error handling with detailed logging
- **Audit Logging**: All run lifecycle events are logged to audit ledger
- **Deterministic Execution**: Uses deterministic seeds for reproducible results

## Usage

### Run Worker

```bash
# Using Python module
python -m app.workers

# Or directly
python app/workers/__main__.py
```

### Environment Variables

- `DATABASE_URL`: Database connection string (defaults to config)
- `ENGINE_VERSION`: Engine version identifier (optional)
- `WORKER_POLL_INTERVAL`: Poll interval in seconds (default: 1)
- `WORKER_MAX_ATTEMPTS`: Maximum retry attempts (default: 3)
- `WORKER_BACKOFF_BASE`: Base backoff time in seconds (default: 60)

## Architecture

### Job Acquisition

1. Worker polls for jobs with status `QUEUED`
2. Uses `SELECT FOR UPDATE SKIP LOCKED` to prevent conflicts
3. Locks job and increments attempt count
4. Processes job

### Job Processing

1. Loads run and assessment from database
2. Marks run as `RUNNING`
3. Executes risk engine with deterministic settings
4. Updates run with results
5. Marks job as `DONE`
6. Emits audit event

### Error Handling

- If job fails:
  - Updates run status to `FAILED`
  - Stores error details in `error_json`
  - Schedules retry with exponential backoff (if attempts < MAX_ATTEMPTS)
  - Marks job as `FAILED` if max attempts reached

### Retry Strategy

- Exponential backoff: `BACKOFF_BASE * (2 ^ (attempt_count - 1))`
- Example: 60s, 120s, 240s for attempts 1, 2, 3
- Max attempts: 3 (configurable)

## Monitoring

- Worker logs all operations with INFO level
- Errors are logged with full traceback
- Audit events track all run lifecycle changes

## Scaling

- Run multiple worker processes for parallel processing
- Each worker will acquire different jobs automatically
- No coordination needed between workers (database handles locking)

## Production Considerations

1. **Process Management**: Use systemd, supervisor, or similar
2. **Health Checks**: Implement health check endpoint
3. **Metrics**: Add Prometheus metrics for monitoring
4. **Graceful Shutdown**: Handle SIGTERM/SIGINT for clean shutdown
5. **Database Connection Pooling**: Configure appropriate pool size
