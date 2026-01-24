"""
Prometheus Metrics
RISKCAST V3 - Modular Monolith
"""
from prometheus_client import Counter, Histogram, Gauge, Summary
from typing import Optional

# Risk run metrics
RISK_RUN_LATENCY = Histogram(
    'risk_run_latency_seconds',
    'Risk run execution latency in seconds',
    ['tenant_id', 'status', 'engine_version'],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

RISK_RUN_QUEUE_DEPTH = Gauge(
    'risk_run_queue_depth',
    'Number of queued risk runs',
    ['tenant_id']
)

RISK_RUN_FAILURES = Counter(
    'risk_run_failures_total',
    'Total number of failed risk runs',
    ['tenant_id', 'error_type']
)

RISK_RUN_SUCCESS = Counter(
    'risk_run_success_total',
    'Total number of successful risk runs',
    ['tenant_id', 'engine_version']
)

RISK_RUN_ITERATIONS = Histogram(
    'risk_run_iterations',
    'Number of Monte Carlo iterations per run',
    ['tenant_id'],
    buckets=[1000, 5000, 10000, 50000, 100000, 500000]
)

# Risk assessment metrics
RISK_ASSESSMENT_CREATED = Counter(
    'risk_assessment_created_total',
    'Total number of risk assessments created',
    ['tenant_id']
)

RISK_ASSESSMENT_DUPLICATE = Counter(
    'risk_assessment_duplicate_total',
    'Total number of duplicate risk assessments (same input hash)',
    ['tenant_id']
)

# API metrics
API_REQUESTS = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status_code']
)

API_LATENCY = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

API_ERRORS = Counter(
    'api_errors_total',
    'Total API errors',
    ['method', 'endpoint', 'error_type']
)

# Database metrics
DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['table', 'operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
)

DB_CONNECTION_POOL_SIZE = Gauge(
    'db_connection_pool_size',
    'Database connection pool size',
    ['state']  # 'active', 'idle', 'overflow'
)

# Audit metrics
AUDIT_EVENTS = Counter(
    'audit_events_total',
    'Total audit events',
    ['tenant_id', 'action', 'resource_type']
)

AUDIT_EVENT_SIZE = Histogram(
    'audit_event_size_bytes',
    'Size of audit events in bytes',
    ['tenant_id', 'action'],
    buckets=[100, 500, 1000, 5000, 10000, 50000]
)

# Worker metrics
WORKER_JOBS_PROCESSED = Counter(
    'worker_jobs_processed_total',
    'Total jobs processed by workers',
    ['worker_id', 'status']
)

WORKER_JOBS_QUEUED = Gauge(
    'worker_jobs_queued',
    'Number of jobs in queue',
    ['status']  # 'QUEUED', 'LOCKED'
)

WORKER_JOB_DURATION = Histogram(
    'worker_job_duration_seconds',
    'Worker job processing duration',
    ['worker_id', 'status'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0]
)

# Authentication metrics
AUTH_LOGIN_ATTEMPTS = Counter(
    'auth_login_attempts_total',
    'Total login attempts',
    ['tenant_id', 'status']  # 'success', 'failure'
)

AUTH_SESSION_CREATED = Counter(
    'auth_session_created_total',
    'Total sessions created',
    ['tenant_id']
)

AUTH_SESSION_EXPIRED = Counter(
    'auth_session_expired_total',
    'Total sessions expired',
    ['tenant_id']
)

# Helper functions for metric recording
def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record API request metrics"""
    API_REQUESTS.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    API_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def record_api_error(method: str, endpoint: str, error_type: str):
    """Record API error"""
    API_ERRORS.labels(method=method, endpoint=endpoint, error_type=error_type).inc()


def record_risk_run(
    tenant_id: str,
    status: str,
    duration: float,
    engine_version: Optional[str] = None,
    iterations: Optional[int] = None,
    error_type: Optional[str] = None
):
    """Record risk run metrics"""
    if status == 'SUCCEEDED':
        RISK_RUN_SUCCESS.labels(tenant_id=tenant_id, engine_version=engine_version or 'unknown').inc()
    elif status == 'FAILED':
        RISK_RUN_FAILURES.labels(tenant_id=tenant_id, error_type=error_type or 'unknown').inc()
    
    RISK_RUN_LATENCY.labels(
        tenant_id=tenant_id,
        status=status,
        engine_version=engine_version or 'unknown'
    ).observe(duration)
    
    if iterations:
        RISK_RUN_ITERATIONS.labels(tenant_id=tenant_id).observe(iterations)


def record_risk_assessment(tenant_id: str, is_duplicate: bool = False):
    """Record risk assessment creation"""
    if is_duplicate:
        RISK_ASSESSMENT_DUPLICATE.labels(tenant_id=tenant_id).inc()
    else:
        RISK_ASSESSMENT_CREATED.labels(tenant_id=tenant_id).inc()


def record_audit_event(tenant_id: str, action: str, resource_type: str, event_size: int):
    """Record audit event metrics"""
    AUDIT_EVENTS.labels(tenant_id=tenant_id, action=action, resource_type=resource_type).inc()
    AUDIT_EVENT_SIZE.labels(tenant_id=tenant_id, action=action).observe(event_size)


def record_worker_job(worker_id: str, status: str, duration: float):
    """Record worker job metrics"""
    WORKER_JOBS_PROCESSED.labels(worker_id=worker_id, status=status).inc()
    WORKER_JOB_DURATION.labels(worker_id=worker_id, status=status).observe(duration)


def update_queue_depth(tenant_id: str, depth: int):
    """Update risk run queue depth"""
    RISK_RUN_QUEUE_DEPTH.labels(tenant_id=tenant_id).set(depth)


def update_worker_queue_depth(status: str, depth: int):
    """Update worker job queue depth"""
    WORKER_JOBS_QUEUED.labels(status=status).set(depth)
