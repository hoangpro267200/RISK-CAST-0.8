"""
RISKCAST Security - Audit Trail
Logs all security-relevant events for compliance and monitoring
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Setup logging
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

AUDIT_LOG_FILE = LOG_DIR / "audit.log"
SECURITY_LOG_FILE = LOG_DIR / "security.log"

# Configure audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
audit_handler = logging.FileHandler(AUDIT_LOG_FILE)
audit_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
audit_logger.addHandler(audit_handler)

# Configure security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.WARNING)
security_handler = logging.FileHandler(SECURITY_LOG_FILE)
security_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
))
security_logger.addHandler(security_handler)


def log_event(user_id: Optional[str], action: str, details: Dict[str, Any], severity: str = "INFO"):
    """
    Log a general audit event
    
    Args:
        user_id: User identifier (None if anonymous)
        action: Action name (e.g., "LOGIN", "API_CALL", "DATA_EXPORT")
        details: Additional details dictionary
        severity: Log severity (INFO, WARNING, ERROR)
    """
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "action": action,
        "details": details,
        "severity": severity
    }
    
    # Remove sensitive data from logs
    safe_details = {k: v for k, v in details.items() 
                    if k.lower() not in ['password', 'api_key', 'secret', 'token', 'authorization']}
    event["details"] = safe_details
    
    message = json.dumps(event, default=str)
    
    if severity == "ERROR":
        audit_logger.error(message)
        security_logger.error(message)
    elif severity == "WARNING":
        audit_logger.warning(message)
        security_logger.warning(message)
    else:
        audit_logger.info(message)


def log_api_call(ip: str, endpoint: str, method: str, payload_size: int = 0, 
                 status_code: int = 200, user_id: Optional[str] = None,
                 duration_ms: Optional[float] = None):
    """
    Log an API call
    
    Args:
        ip: Client IP address
        endpoint: API endpoint path
        method: HTTP method
        payload_size: Request payload size in bytes
        status_code: HTTP status code
        user_id: User identifier (None if anonymous)
        duration_ms: Request duration in milliseconds
    """
    details = {
        "ip": ip,
        "endpoint": endpoint,
        "method": method,
        "payload_size": payload_size,
        "status_code": status_code,
        "duration_ms": duration_ms
    }
    
    # Determine severity based on status code
    if status_code >= 500:
        severity = "ERROR"
    elif status_code >= 400:
        severity = "WARNING"
    else:
        severity = "INFO"
    
    log_event(user_id, "API_CALL", details, severity)


def log_admin_action(user_id: str, action: str, change: Dict[str, Any]):
    """
    Log an admin action
    
    Args:
        user_id: Admin user identifier
        action: Action name (e.g., "USER_CREATED", "SETTINGS_UPDATED")
        change: Change details dictionary
    """
    details = {
        "action": action,
        "changes": change
    }
    
    log_event(user_id, "ADMIN_ACTION", details, severity="WARNING")


def log_security_event(event_type: str, details: Dict[str, Any], ip: Optional[str] = None):
    """
    Log a security-related event
    
    Args:
        event_type: Event type (e.g., "RATE_LIMIT_EXCEEDED", "AUTH_FAILED", "SUSPICIOUS_ACTIVITY")
        details: Event details
        ip: Client IP address
    """
    details["event_type"] = event_type
    if ip:
        details["ip"] = ip
    
    security_logger.warning(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        **details
    }, default=str))
    
    # Also log to audit
    log_event(None, f"SECURITY_{event_type}", details, severity="WARNING")


def log_authentication_attempt(user_id: Optional[str], success: bool, ip: str, details: Dict[str, Any] = None):
    """
    Log authentication attempt
    
    Args:
        user_id: User identifier
        success: Whether authentication was successful
        ip: Client IP address
        details: Additional details
    """
    event_details = {
        "success": success,
        "ip": ip,
        **(details or {})
    }
    
    action = "AUTH_SUCCESS" if success else "AUTH_FAILED"
    severity = "INFO" if success else "WARNING"
    
    log_event(user_id, action, event_details, severity)
    
    if not success:
        log_security_event("AUTH_FAILED", {"user_id": user_id, "ip": ip})


def log_data_access(user_id: str, resource: str, action: str, success: bool = True):
    """
    Log data access
    
    Args:
        user_id: User identifier
        resource: Resource accessed
        action: Action performed (READ, WRITE, DELETE)
        success: Whether access was granted
    """
    details = {
        "resource": resource,
        "action": action,
        "success": success
    }
    
    severity = "WARNING" if not success else "INFO"
    log_event(user_id, "DATA_ACCESS", details, severity)


def rotate_logs(max_size_mb: int = 100, keep_files: int = 7):
    """
    Rotate log files when they get too large
    
    Args:
        max_size_mb: Maximum log file size in MB before rotation
        keep_files: Number of rotated log files to keep
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    
    for log_file in [AUDIT_LOG_FILE, SECURITY_LOG_FILE]:
        if log_file.exists() and log_file.stat().st_size > max_size_bytes:
            # Rotate file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            rotated_file = log_file.parent / f"{log_file.stem}_{timestamp}{log_file.suffix}"
            log_file.rename(rotated_file)
            pattern = f"{log_file.stem}_*.{log_file.suffix}"
            old_files = sorted(log_file.parent.glob(pattern), reverse=True)
            for old_file in old_files[keep_files:]:
                old_file.unlink()





















