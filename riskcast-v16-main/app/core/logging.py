"""
Structured Logging Configuration

Features:
1. JSON structured logging
2. Correlation IDs
3. Request context
4. Log levels by environment
5. Sensitive data masking
"""

import logging
import sys
import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from functools import wraps
import os

# Context variables for request tracking
request_id_ctx: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
trace_id_ctx: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)
user_id_ctx: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
tenant_id_ctx: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)


# =============================================================================
# Sensitive Data Masking
# =============================================================================

SENSITIVE_FIELDS = {
    'password', 'secret', 'token', 'api_key', 'apikey', 'api-key',
    'authorization', 'auth', 'credential', 'private_key', 'secret_key',
    'access_token', 'refresh_token', 'ssn', 'social_security',
    'credit_card', 'card_number', 'cvv', 'pin'
}

SENSITIVE_PATTERNS = [
    r'bearer\s+[a-zA-Z0-9\-_.]+',  # Bearer tokens
    r'basic\s+[a-zA-Z0-9=]+',       # Basic auth
    r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit cards
]


def mask_sensitive_data(data: Any, depth: int = 0) -> Any:
    """
    Recursively mask sensitive data in dictionaries and strings.
    """
    if depth > 10:  # Prevent infinite recursion
        return data
    
    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELDS):
                masked[key] = "***MASKED***"
            else:
                masked[key] = mask_sensitive_data(value, depth + 1)
        return masked
    
    elif isinstance(data, list):
        return [mask_sensitive_data(item, depth + 1) for item in data]
    
    elif isinstance(data, str):
        import re
        result = data
        for pattern in SENSITIVE_PATTERNS:
            result = re.sub(pattern, '***MASKED***', result, flags=re.IGNORECASE)
        return result
    
    return data


# =============================================================================
# JSON Formatter
# =============================================================================

class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging.
    """
    
    def __init__(
        self,
        service_name: str = "riskcast-api",
        environment: str = "production",
        include_traceback: bool = True
    ):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_traceback = include_traceback
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            # Timestamp
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "unix_timestamp": datetime.utcnow().timestamp(),
            
            # Log level
            "level": record.levelname,
            "level_num": record.levelno,
            
            # Service info
            "service": self.service_name,
            "environment": self.environment,
            
            # Source location
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "file": record.pathname,
            
            # Message
            "message": record.getMessage(),
            
            # Context from contextvars
            "request_id": request_id_ctx.get(),
            "trace_id": trace_id_ctx.get(),
            "user_id": user_id_ctx.get(),
            "tenant_id": tenant_id_ctx.get(),
            
            # Process info
            "process_id": record.process,
            "thread_id": record.thread,
            "thread_name": record.threadName,
        }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            extra = mask_sensitive_data(record.extra_data)
            log_data["extra"] = extra
        
        # Add exception info
        if record.exc_info and self.include_traceback:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        # Remove None values for cleaner output
        log_data = {k: v for k, v in log_data.items() if v is not None}
        
        return json.dumps(log_data, default=str, ensure_ascii=False)


# =============================================================================
# Custom Logger
# =============================================================================

class StructuredLogger(logging.Logger):
    """
    Custom logger that supports structured extra data.
    """
    
    def _log_with_extra(
        self,
        level: int,
        msg: str,
        args: tuple,
        exc_info=None,
        extra: Optional[Dict] = None,
        **kwargs
    ):
        """Log with extra structured data."""
        if extra is None:
            extra = {}
        
        # Merge kwargs into extra
        extra_data = {**extra, **kwargs}
        
        # Create record with extra_data attribute
        record_extra = {'extra_data': extra_data} if extra_data else {}
        
        super()._log(level, msg, args, exc_info=exc_info, extra=record_extra)
    
    def debug(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.DEBUG, msg, args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.INFO, msg, args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self._log_with_extra(logging.WARNING, msg, args, **kwargs)
    
    def error(self, msg: str, *args, exc_info=True, **kwargs):
        self._log_with_extra(logging.ERROR, msg, args, exc_info=exc_info, **kwargs)
    
    def critical(self, msg: str, *args, exc_info=True, **kwargs):
        self._log_with_extra(logging.CRITICAL, msg, args, exc_info=exc_info, **kwargs)
    
    # Business event logging helpers
    def audit(self, action: str, entity_type: str, entity_id: str, **kwargs):
        """Log audit event."""
        self.info(
            f"AUDIT: {action}",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            event_type="audit",
            **kwargs
        )
    
    def business_event(self, event_name: str, **kwargs):
        """Log business event."""
        self.info(
            f"BUSINESS_EVENT: {event_name}",
            event_name=event_name,
            event_type="business",
            **kwargs
        )
    
    def security_event(self, event_name: str, severity: str = "medium", **kwargs):
        """Log security event."""
        log_method = self.warning if severity in ["low", "medium"] else self.error
        log_method(
            f"SECURITY: {event_name}",
            event_name=event_name,
            event_type="security",
            severity=severity,
            **kwargs
        )


# =============================================================================
# Logger Setup
# =============================================================================

def setup_logging(
    service_name: str = "riskcast-api",
    environment: str = None,
    log_level: str = None,
    json_output: bool = None
) -> StructuredLogger:
    """
    Configure logging for the application.
    
    Args:
        service_name: Name of the service
        environment: Deployment environment
        log_level: Logging level
        json_output: Whether to output JSON
    
    Returns:
        Configured logger instance
    """
    # Get config from environment
    environment = environment or os.getenv("ENVIRONMENT", "production")
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    json_output = json_output if json_output is not None else (environment != "development")
    
    # Set custom logger class
    logging.setLoggerClass(StructuredLogger)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set formatter
    if json_output:
        formatter = JSONFormatter(
            service_name=service_name,
            environment=environment,
            include_traceback=True
        )
    else:
        # Human-readable format for development
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | '
            '%(message)s | request_id=%(request_id)s',
            defaults={'request_id': 'N/A'}
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger(service_name)


def get_logger(name: str = None) -> StructuredLogger:
    """Get a logger instance."""
    return logging.getLogger(name or "riskcast-api")


# =============================================================================
# Context Management
# =============================================================================

def set_request_context(
    request_id: str = None,
    trace_id: str = None,
    user_id: str = None,
    tenant_id: str = None
):
    """Set logging context for current request."""
    if request_id:
        request_id_ctx.set(request_id)
    if trace_id:
        trace_id_ctx.set(trace_id)
    if user_id:
        user_id_ctx.set(user_id)
    if tenant_id:
        tenant_id_ctx.set(tenant_id)


def clear_request_context():
    """Clear logging context."""
    request_id_ctx.set(None)
    trace_id_ctx.set(None)
    user_id_ctx.set(None)
    tenant_id_ctx.set(None)


# =============================================================================
# Logging Decorator
# =============================================================================

def log_function_call(logger: logging.Logger = None, level: int = logging.DEBUG):
    """Decorator to log function calls."""
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.log(level, f"Calling {func_name}", args_count=len(args), kwargs_keys=list(kwargs.keys()))
            
            try:
                result = await func(*args, **kwargs)
                logger.log(level, f"Completed {func_name}")
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {e}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            logger.log(level, f"Calling {func_name}", args_count=len(args), kwargs_keys=list(kwargs.keys()))
            
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"Completed {func_name}")
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {e}")
                raise
        
        import asyncio
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator
