"""
RISKCAST - Enhanced Logging System
Structured logging with JSON format and better organization
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import traceback


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info else None
            }
        
        return json.dumps(log_entry, default=str)


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    use_json: bool = True,
    console: bool = True
) -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Log file path (optional)
        level: Logging level
        use_json: Use JSON format (True) or text format (False)
        console: Also log to console
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs
    
    # Remove existing handlers
    logger.handlers = []
    
    # Formatter
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


# Setup default loggers
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Application logger
app_logger = setup_logger(
    "riskcast.app",
    log_file=LOG_DIR / "app.log",
    level=logging.INFO,
    use_json=True
)

# Error logger
error_logger = setup_logger(
    "riskcast.error",
    log_file=LOG_DIR / "errors.log",
    level=logging.ERROR,
    use_json=True
)

# API logger
api_logger = setup_logger(
    "riskcast.api",
    log_file=LOG_DIR / "api.log",
    level=logging.INFO,
    use_json=True
)

# Security logger
security_logger = setup_logger(
    "riskcast.security",
    log_file=LOG_DIR / "security.log",
    level=logging.WARNING,
    use_json=True
)


def log_api_call(
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """
    Log API call with structured data
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        user_id: User ID (optional)
        request_id: Request ID for tracing (optional, will be extracted from context if available)
        **kwargs: Additional fields
    """
    api_logger.info(
        "API call",
        extra={
            "extra_fields": {
                "event_type": "api_call",
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "user_id": user_id,
                "request_id": request_id,  # CRITICAL: Include request_id for tracing
                **kwargs
            }
        }
    )


def log_security_event(
    event_type: str,
    message: str,
    severity: str = "INFO",
    user_id: Optional[str] = None,
    ip: Optional[str] = None,
    **kwargs
):
    """
    Log security event
    
    Args:
        event_type: Event type (e.g., "unauthorized_access", "suspicious_activity")
        message: Event message
        severity: Severity level (INFO, WARNING, ERROR)
        user_id: User ID (optional)
        ip: IP address (optional)
        **kwargs: Additional fields
    """
    log_level = getattr(logging, severity.upper(), logging.INFO)
    
    security_logger.log(
        log_level,
        message,
        extra={
            "extra_fields": {
                "event_type": event_type,
                "severity": severity,
                "user_id": user_id,
                "ip": ip,
                **kwargs
            }
        }
    )


def log_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    **kwargs
):
    """
    Log error with structured data
    
    Args:
        error: Exception object
        context: Additional context (optional)
        request_id: Request ID for tracing (optional)
        **kwargs: Additional fields
    """
    error_logger.error(
        f"Error: {str(error)}",
        exc_info=error,
        extra={
            "extra_fields": {
                "event_type": "error",
                "error_type": type(error).__name__,
                "error_message": str(error),
                "request_id": request_id,  # CRITICAL: Include request_id for tracing
                "context": context or {},
                **kwargs
            }
        }
    )

