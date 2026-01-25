"""
Prometheus Metrics Configuration

Exposes application metrics for monitoring.
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST,
    CollectorRegistry, multiprocess, REGISTRY
)
from functools import wraps
import time
import os


# =============================================================================
# Custom Registry for multiprocess mode
# =============================================================================

def get_registry():
    """Get appropriate registry for single/multiprocess mode."""
    if 'prometheus_multiproc_dir' in os.environ:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return registry
    return REGISTRY


# =============================================================================
# Application Metrics
# =============================================================================

# Request metrics
REQUEST_COUNT = Counter(
    'riskcast_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_LATENCY = Histogram(
    'riskcast_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[.005, .01, .025, .05, .075, .1, .25, .5, .75, 1.0, 2.5, 5.0, 7.5, 10.0]
)

REQUEST_IN_PROGRESS = Gauge(
    'riskcast_http_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint']
)

# Risk assessment metrics
RISK_ASSESSMENT_COUNT = Counter(
    'riskcast_risk_assessments_total',
    'Total risk assessments performed',
    ['cargo_type', 'risk_grade']
)

RISK_ASSESSMENT_DURATION = Histogram(
    'riskcast_risk_assessment_duration_seconds',
    'Risk assessment computation time',
    ['model_version'],
    buckets=[.05, .1, .25, .5, .75, 1.0, 2.5, 5.0]
)

RISK_SCORE_DISTRIBUTION = Histogram(
    'riskcast_risk_score_distribution',
    'Distribution of risk scores',
    buckets=[.1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0]
)

# Quote metrics
QUOTE_COUNT = Counter(
    'riskcast_quotes_total',
    'Total quotes generated',
    ['status', 'coverage_type']
)

QUOTE_PREMIUM = Histogram(
    'riskcast_quote_premium_usd',
    'Quote premium amounts',
    buckets=[100, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
)

QUOTE_CONVERSION_RATE = Gauge(
    'riskcast_quote_conversion_rate',
    'Quote to policy conversion rate',
    ['period']
)

# Policy metrics
ACTIVE_POLICIES = Gauge(
    'riskcast_active_policies_total',
    'Number of active policies',
    ['coverage_type']
)

TOTAL_COVERAGE = Gauge(
    'riskcast_total_coverage_usd',
    'Total coverage amount in USD'
)

# Claims metrics
CLAIMS_COUNT = Counter(
    'riskcast_claims_total',
    'Total claims filed',
    ['loss_type', 'status']
)

CLAIMS_AMOUNT = Histogram(
    'riskcast_claim_amount_usd',
    'Claim amounts',
    buckets=[1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000]
)

CLAIMS_PROCESSING_TIME = Histogram(
    'riskcast_claim_processing_days',
    'Claim processing time in days',
    buckets=[1, 3, 5, 7, 14, 21, 30, 45, 60]
)

# External service metrics
EXTERNAL_REQUEST_COUNT = Counter(
    'riskcast_external_requests_total',
    'External API requests',
    ['service', 'status']
)

EXTERNAL_REQUEST_LATENCY = Histogram(
    'riskcast_external_request_duration_seconds',
    'External API latency',
    ['service'],
    buckets=[.1, .25, .5, 1.0, 2.5, 5.0, 10.0]
)

# Database metrics
DB_QUERY_COUNT = Counter(
    'riskcast_db_queries_total',
    'Database queries',
    ['operation', 'table']
)

DB_QUERY_DURATION = Histogram(
    'riskcast_db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[.001, .005, .01, .025, .05, .1, .25, .5, 1.0]
)

DB_CONNECTION_POOL = Gauge(
    'riskcast_db_connections',
    'Database connection pool status',
    ['state']  # active, idle, total
)

# Cache metrics
CACHE_HITS = Counter(
    'riskcast_cache_hits_total',
    'Cache hits',
    ['cache_type']
)

CACHE_MISSES = Counter(
    'riskcast_cache_misses_total',
    'Cache misses',
    ['cache_type']
)

# Background job metrics
JOB_COUNT = Counter(
    'riskcast_jobs_total',
    'Background jobs processed',
    ['job_type', 'status']
)

JOB_DURATION = Histogram(
    'riskcast_job_duration_seconds',
    'Background job duration',
    ['job_type'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600]
)

JOB_QUEUE_SIZE = Gauge(
    'riskcast_job_queue_size',
    'Number of jobs in queue',
    ['queue']
)

# System info
APP_INFO = Info(
    'riskcast_app',
    'Application information'
)


# =============================================================================
# Metric Decorators
# =============================================================================

def track_request_metrics(endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('request', args[0] if args else None)
            method_name = getattr(method, 'method', 'UNKNOWN') if method else 'UNKNOWN'
            
            REQUEST_IN_PROGRESS.labels(method=method_name, endpoint=endpoint).inc()
            
            start_time = time.time()
            status_code = 500
            
            try:
                response = await func(*args, **kwargs)
                status_code = getattr(response, 'status_code', 200)
                return response
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                
                REQUEST_COUNT.labels(
                    method=method_name,
                    endpoint=endpoint,
                    status_code=status_code
                ).inc()
                
                REQUEST_LATENCY.labels(
                    method=method_name,
                    endpoint=endpoint
                ).observe(duration)
                
                REQUEST_IN_PROGRESS.labels(method=method_name, endpoint=endpoint).dec()
        
        return wrapper
    return decorator


def track_risk_assessment(func):
    """Decorator to track risk assessment metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # Record metrics
            duration = time.time() - start_time
            
            cargo_type = kwargs.get('cargo_type', 'UNKNOWN')
            risk_grade = getattr(result, 'risk_grade', 'UNKNOWN')
            model_version = getattr(result, 'model_version_id', 'UNKNOWN')
            risk_score = getattr(result, 'overall_risk_score', 0)
            
            RISK_ASSESSMENT_COUNT.labels(
                cargo_type=cargo_type,
                risk_grade=risk_grade
            ).inc()
            
            RISK_ASSESSMENT_DURATION.labels(
                model_version=model_version
            ).observe(duration)
            
            RISK_SCORE_DISTRIBUTION.observe(risk_score)
            
            return result
        except Exception:
            raise
    
    return wrapper


def track_external_request(service: str):
    """Decorator to track external API requests."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                EXTERNAL_REQUEST_COUNT.labels(service=service, status=status).inc()
                EXTERNAL_REQUEST_LATENCY.labels(service=service).observe(duration)
        
        return wrapper
    return decorator


# =============================================================================
# Metrics Endpoint
# =============================================================================

async def metrics_endpoint():
    """Generate metrics for Prometheus scraping."""
    registry = get_registry()
    return generate_latest(registry), CONTENT_TYPE_LATEST


def setup_app_info(version: str, environment: str):
    """Set application info metric."""
    APP_INFO.info({
        'version': version,
        'environment': environment,
        'python_version': '3.11'
    })
