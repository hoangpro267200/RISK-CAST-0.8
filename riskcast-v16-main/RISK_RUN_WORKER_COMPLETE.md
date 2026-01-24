# ✅ Risk Run Background Worker - Hoàn Thành

## Đã Tạo Thành Công

### 1. Worker Implementation (`app/workers/risk_run_worker.py`)

#### ✅ RiskRunWorker Class

**Initialization:**
- `__init__(db_url)` - Initializes worker with database URL
- Generates unique worker ID: `{hostname}-{pid}`
- Configurable constants for polling, locking, retries

**Constants:**
- `POLL_INTERVAL = 1` - Seconds between job polls
- `LOCK_TIMEOUT = 300` - Lock timeout (5 minutes)
- `MAX_ATTEMPTS = 3` - Maximum retry attempts
- `BACKOFF_BASE = 60` - Base backoff time in seconds

**Session Management:**
- `_get_session()` - Context manager for database sessions
- Proper cleanup and error handling

#### ✅ Core Methods

**`start()`**
- Starts worker loop
- Polls for jobs continuously
- Handles interrupts and errors gracefully
- Logs worker lifecycle

**`stop()`**
- Stops worker gracefully
- Sets `running = False` to exit loop

**`_acquire_job() -> Optional[RiskRunJob]`**
- Attempts to acquire a job using `SELECT FOR UPDATE SKIP LOCKED`
- Filters for:
  - Status = QUEUED
  - available_at <= now
  - attempt_count < MAX_ATTEMPTS
- Locks job atomically:
  - Sets status to LOCKED
  - Sets locked_by to worker_id
  - Sets locked_at to now
  - Increments attempt_count
- Returns job if acquired, None otherwise
- Fallback for databases without SKIP LOCKED support

**`_process_job(job: RiskRunJob)`**
- Processes a single job
- Steps:
  1. Load run and assessment
  2. Mark run as RUNNING
  3. Execute risk engine
  4. Update run with result
  5. Mark job as DONE
  6. Emit audit event
- Error handling:
  - Updates run as FAILED on error
  - Schedules retry with exponential backoff
  - Marks job as FAILED if max attempts reached

**`_emit_audit(run, action)`**
- Emits audit event for run action
- Uses SYSTEM actor type
- Worker ID as actor_id
- Error handling (doesn't fail job processing)

### 2. Entry Point (`app/workers/__main__.py`)

#### ✅ Main Function
- Configures logging
- Creates worker instance
- Starts worker loop
- Handles interrupts and errors
- Proper shutdown

**Usage:**
```bash
python -m app.workers
# or
python app/workers/__main__.py
```

### 3. Documentation (`app/workers/README.md`)

- Usage instructions
- Environment variables
- Architecture overview
- Error handling
- Retry strategy
- Monitoring
- Scaling considerations
- Production considerations

## Key Features

### 1. Concurrent Processing
- Multiple workers can run simultaneously
- `SELECT FOR UPDATE SKIP LOCKED` prevents conflicts
- Each worker gets different jobs automatically

### 2. Retry Logic
- Exponential backoff: `BACKOFF_BASE * (2 ^ (attempt_count - 1))`
- Example: 60s, 120s, 240s for attempts 1, 2, 3
- Max attempts: 3 (configurable)
- Jobs rescheduled with `available_at` timestamp

### 3. Error Handling
- Graceful error handling with detailed logging
- Run status updated to FAILED on error
- Error details stored in `error_json`
- Job retry or failure based on attempt count

### 4. Audit Logging
- All run lifecycle events logged
- SYSTEM actor type
- Worker ID tracked
- Error handling for audit failures

### 5. Deterministic Execution
- Uses deterministic seeds from run configuration
- Same inputs produce same results
- Full reproducibility

### 6. Async/Sync Bridge
- Uses `run_in_executor` for database operations
- Async engine execution
- Proper event loop handling

## Job Lifecycle

### Successful Execution
1. **QUEUED** → Worker acquires job → **LOCKED**
2. Load run and assessment
3. Mark run as **RUNNING**
4. Execute engine
5. Update run with result → **SUCCEEDED**
6. Mark job as **DONE**
7. Emit audit event

### Failed Execution
1. **QUEUED** → Worker acquires job → **LOCKED**
2. Load run and assessment
3. Mark run as **RUNNING**
4. Engine execution fails
5. Update run → **FAILED**
6. If attempts < MAX:
   - Reschedule job → **QUEUED** (with backoff)
   - Set `available_at` for retry
7. If attempts >= MAX:
   - Mark job as **FAILED**
8. Emit audit event

## Usage Examples

### Start Worker

```bash
# Basic usage
python -m app.workers

# With environment variables
DATABASE_URL=mysql+pymysql://user:pass@localhost/db python -m app.workers
```

### Run Multiple Workers

```bash
# Terminal 1
python -m app.workers

# Terminal 2
python -m app.workers

# Terminal 3
python -m app.workers
```

Each worker will process different jobs concurrently.

### Process Management (systemd)

```ini
[Unit]
Description=Risk Run Worker
After=network.target

[Service]
Type=simple
User=riskcast
WorkingDirectory=/app
ExecStart=/usr/bin/python3 -m app.workers
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Monitoring

### Logs
- Worker lifecycle (start, stop)
- Job acquisition
- Job processing
- Errors with full traceback
- Audit event emissions

### Database Queries
```sql
-- Check job queue status
SELECT status, COUNT(*) 
FROM risk_run_jobs 
GROUP BY status;

-- Check locked jobs
SELECT * FROM risk_run_jobs 
WHERE status = 'LOCKED' 
AND locked_at < NOW() - INTERVAL 5 MINUTE;

-- Check failed jobs
SELECT * FROM risk_run_jobs 
WHERE status = 'FAILED';
```

## Files Created

1. ✅ `app/workers/risk_run_worker.py` - Worker implementation
2. ✅ `app/workers/__main__.py` - Entry point
3. ✅ `app/workers/README.md` - Documentation
4. ✅ `RISK_RUN_WORKER_COMPLETE.md` - This documentation

## Next Steps

1. **Add Health Checks**: Implement health check endpoint
2. **Add Metrics**: Prometheus metrics for monitoring
3. **Add Graceful Shutdown**: Better signal handling
4. **Add Tests**: Unit and integration tests
5. **Add Process Management**: systemd/supervisor configs
6. **Add Model Loading**: Load model payload from database

**Risk Run Background Worker hoàn thành và sẵn sàng sử dụng!** 🎉
