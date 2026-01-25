"""
Authentication Observability

Structured logging, metrics, and security event tracking for the auth system.

SECURITY LOGGING PRINCIPLES:
1. Never log passwords, tokens, or secrets
2. Use partial masking for emails (show first 3 chars)
3. Log all security-relevant events
4. Include correlation IDs for request tracing
5. Separate security logs for SIEM integration
"""
import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from functools import wraps
import time


class SecurityEventType(Enum):
    """Types of security events to log."""
    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGIN_LOCKOUT = "auth.login.lockout"
    LOGOUT = "auth.logout"
    SESSION_CREATED = "auth.session.created"
    SESSION_REFRESHED = "auth.session.refreshed"
    SESSION_REVOKED = "auth.session.revoked"
    SESSION_EXPIRED = "auth.session.expired"
    
    # Password events
    PASSWORD_CHANGED = "auth.password.changed"
    PASSWORD_RESET_REQUESTED = "auth.password.reset_requested"
    PASSWORD_RESET_COMPLETED = "auth.password.reset_completed"
    PASSWORD_RESET_FAILED = "auth.password.reset_failed"
    
    # Account events
    ACCOUNT_CREATED = "auth.account.created"
    ACCOUNT_SUSPENDED = "auth.account.suspended"
    ACCOUNT_DELETED = "auth.account.deleted"
    ACCOUNT_UNLOCKED = "auth.account.unlocked"
    ACCOUNT_ROLE_CHANGED = "auth.account.role_changed"
    EMAIL_VERIFIED = "auth.email.verified"
    EMAIL_VERIFICATION_SENT = "auth.email.verification_sent"
    
    # API key events
    API_KEY_CREATED = "auth.apikey.created"
    API_KEY_REVOKED = "auth.apikey.revoked"
    API_KEY_USED = "auth.apikey.used"
    API_KEY_INVALID = "auth.apikey.invalid"
    
    # OAuth events
    OAUTH_LOGIN_STARTED = "auth.oauth.started"
    OAUTH_LOGIN_SUCCESS = "auth.oauth.success"
    OAUTH_LOGIN_FAILURE = "auth.oauth.failure"
    OAUTH_DISCONNECTED = "auth.oauth.disconnected"
    
    # Security alerts
    BRUTE_FORCE_DETECTED = "security.brute_force.detected"
    TOKEN_REUSE_DETECTED = "security.token_reuse.detected"
    SUSPICIOUS_IP = "security.suspicious_ip.detected"
    CSRF_VIOLATION = "security.csrf.violation"
    UNAUTHORIZED_ACCESS = "security.unauthorized.access"


class AuthLogger:
    """
    Structured logging for authentication events.
    
    Usage:
        auth_logger = AuthLogger()
        auth_logger.log_login_success(user_id=123, ip="1.2.3.4")
    """
    
    def __init__(self, logger_name: str = "auth.security"):
        self.logger = logging.getLogger(logger_name)
        self.security_logger = logging.getLogger(f"{logger_name}.security")
    
    def _mask_email(self, email: str) -> str:
        """Mask email for logging (show first 3 chars + domain)."""
        if not email or "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        if len(local) <= 3:
            return f"***@{domain}"
        return f"{local[:3]}***@{domain}"
    
    def _mask_ip(self, ip: str) -> str:
        """Mask last octet of IP for privacy."""
        if not ip:
            return "unknown"
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
        return ip  # IPv6 or unknown format
    
    def _create_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[int] = None,
        user_uuid: Optional[str] = None,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        session_id: Optional[int] = None,
        request_id: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a structured security event."""
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type.value,
            "level": "INFO" if "success" in event_type.value.lower() or "created" in event_type.value.lower() else "WARNING",
        }
        
        # Add identifiers (never include sensitive data)
        if user_id:
            event["user_id"] = user_id
        if user_uuid:
            event["user_uuid"] = user_uuid
        if email:
            event["email_masked"] = self._mask_email(email)
        if ip_address:
            event["ip_address"] = ip_address  # Full IP for security analysis
            event["ip_masked"] = self._mask_ip(ip_address)
        if session_id:
            event["session_id"] = session_id
        if request_id:
            event["request_id"] = request_id
        
        # Add extra fields
        if extra:
            for key, value in extra.items():
                # Ensure no sensitive data
                if key.lower() in ("password", "token", "secret", "key", "hash"):
                    continue
                event[key] = value
        
        return event
    
    def _log_event(
        self,
        event_type: SecurityEventType,
        level: int = logging.INFO,
        **kwargs
    ):
        """Log a security event."""
        event = self._create_event(event_type, **kwargs)
        
        # Determine log level based on event type
        if "failure" in event_type.value or "violation" in event_type.value:
            level = logging.WARNING
        elif "security" in event_type.value:
            level = logging.WARNING
        
        # Log to main logger
        self.logger.log(level, json.dumps(event))
        
        # Also log to security logger for SIEM
        self.security_logger.log(level, json.dumps(event))
    
    # Authentication events
    def log_login_success(
        self,
        user_id: int,
        email: str,
        ip_address: str,
        session_id: int,
        **extra
    ):
        """Log successful login."""
        self._log_event(
            SecurityEventType.LOGIN_SUCCESS,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            session_id=session_id,
            extra=extra
        )
    
    def log_login_failure(
        self,
        email: str,
        ip_address: str,
        reason: str = "invalid_credentials",
        **extra
    ):
        """Log failed login attempt."""
        self._log_event(
            SecurityEventType.LOGIN_FAILURE,
            email=email,
            ip_address=ip_address,
            extra={"reason": reason, **extra}
        )
    
    def log_login_lockout(
        self,
        email: str,
        ip_address: str,
        lockout_minutes: int,
        failed_attempts: int,
        **extra
    ):
        """Log account lockout due to failed attempts."""
        self._log_event(
            SecurityEventType.LOGIN_LOCKOUT,
            email=email,
            ip_address=ip_address,
            extra={
                "lockout_minutes": lockout_minutes,
                "failed_attempts": failed_attempts,
                **extra
            }
        )
    
    def log_logout(
        self,
        user_id: int,
        session_id: int,
        ip_address: Optional[str] = None,
        **extra
    ):
        """Log user logout."""
        self._log_event(
            SecurityEventType.LOGOUT,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            extra=extra
        )
    
    def log_session_created(
        self,
        user_id: int,
        session_id: int,
        ip_address: str,
        user_agent: Optional[str] = None,
        **extra
    ):
        """Log new session creation."""
        self._log_event(
            SecurityEventType.SESSION_CREATED,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            extra={"user_agent": user_agent[:100] if user_agent else None, **extra}
        )
    
    def log_session_refreshed(
        self,
        user_id: int,
        old_session_id: int,
        new_session_id: int,
        ip_address: str,
        **extra
    ):
        """Log session refresh/rotation."""
        self._log_event(
            SecurityEventType.SESSION_REFRESHED,
            user_id=user_id,
            session_id=new_session_id,
            ip_address=ip_address,
            extra={"old_session_id": old_session_id, **extra}
        )
    
    def log_session_revoked(
        self,
        session_id: int,
        user_id: int,
        reason: str,
        revoked_by: Optional[int] = None,
        **extra
    ):
        """Log session revocation."""
        self._log_event(
            SecurityEventType.SESSION_REVOKED,
            user_id=user_id,
            session_id=session_id,
            extra={"reason": reason, "revoked_by": revoked_by, **extra}
        )
    
    # Password events
    def log_password_changed(
        self,
        user_id: int,
        ip_address: str,
        **extra
    ):
        """Log password change."""
        self._log_event(
            SecurityEventType.PASSWORD_CHANGED,
            user_id=user_id,
            ip_address=ip_address,
            extra=extra
        )
    
    def log_password_reset_requested(
        self,
        email: str,
        ip_address: str,
        **extra
    ):
        """Log password reset request."""
        self._log_event(
            SecurityEventType.PASSWORD_RESET_REQUESTED,
            email=email,
            ip_address=ip_address,
            extra=extra
        )
    
    def log_password_reset_completed(
        self,
        user_id: int,
        ip_address: str,
        **extra
    ):
        """Log successful password reset."""
        self._log_event(
            SecurityEventType.PASSWORD_RESET_COMPLETED,
            user_id=user_id,
            ip_address=ip_address,
            extra=extra
        )
    
    # Account events
    def log_account_created(
        self,
        user_id: int,
        email: str,
        ip_address: str,
        **extra
    ):
        """Log new account creation."""
        self._log_event(
            SecurityEventType.ACCOUNT_CREATED,
            user_id=user_id,
            email=email,
            ip_address=ip_address,
            extra=extra
        )
    
    def log_account_role_changed(
        self,
        user_id: int,
        old_role: str,
        new_role: str,
        changed_by: int,
        **extra
    ):
        """Log role change."""
        self._log_event(
            SecurityEventType.ACCOUNT_ROLE_CHANGED,
            user_id=user_id,
            extra={
                "old_role": old_role,
                "new_role": new_role,
                "changed_by": changed_by,
                **extra
            }
        )
    
    # API key events
    def log_api_key_created(
        self,
        user_id: int,
        key_id: int,
        key_name: str,
        scope: str,
        **extra
    ):
        """Log API key creation."""
        self._log_event(
            SecurityEventType.API_KEY_CREATED,
            user_id=user_id,
            extra={
                "key_id": key_id,
                "key_name": key_name,
                "scope": scope,
                **extra
            }
        )
    
    def log_api_key_used(
        self,
        key_id: int,
        user_id: int,
        ip_address: str,
        endpoint: str,
        **extra
    ):
        """Log API key usage."""
        self._log_event(
            SecurityEventType.API_KEY_USED,
            user_id=user_id,
            ip_address=ip_address,
            extra={
                "key_id": key_id,
                "endpoint": endpoint,
                **extra
            }
        )
    
    def log_api_key_revoked(
        self,
        key_id: int,
        user_id: int,
        reason: str,
        **extra
    ):
        """Log API key revocation."""
        self._log_event(
            SecurityEventType.API_KEY_REVOKED,
            user_id=user_id,
            extra={
                "key_id": key_id,
                "reason": reason,
                **extra
            }
        )
    
    # Security alerts
    def log_brute_force_detected(
        self,
        ip_address: str,
        target_email: str,
        attempt_count: int,
        **extra
    ):
        """Log potential brute force attack."""
        self._log_event(
            SecurityEventType.BRUTE_FORCE_DETECTED,
            email=target_email,
            ip_address=ip_address,
            extra={
                "attempt_count": attempt_count,
                "severity": "HIGH",
                **extra
            }
        )
    
    def log_token_reuse_detected(
        self,
        user_id: int,
        session_id: int,
        ip_address: str,
        **extra
    ):
        """Log potential token reuse attack."""
        self._log_event(
            SecurityEventType.TOKEN_REUSE_DETECTED,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            extra={"severity": "HIGH", **extra}
        )
    
    def log_csrf_violation(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None,
        **extra
    ):
        """Log CSRF violation."""
        self._log_event(
            SecurityEventType.CSRF_VIOLATION,
            user_id=user_id,
            ip_address=ip_address,
            extra={
                "endpoint": endpoint,
                "severity": "MEDIUM",
                **extra
            }
        )
    
    def log_unauthorized_access(
        self,
        ip_address: str,
        endpoint: str,
        user_id: Optional[int] = None,
        reason: str = "insufficient_permissions",
        **extra
    ):
        """Log unauthorized access attempt."""
        self._log_event(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            user_id=user_id,
            ip_address=ip_address,
            extra={
                "endpoint": endpoint,
                "reason": reason,
                **extra
            }
        )


# Global auth logger instance
auth_logger = AuthLogger()


# Decorator for logging auth function execution
def log_auth_action(event_type: SecurityEventType):
    """
    Decorator to automatically log auth actions.
    
    Usage:
        @log_auth_action(SecurityEventType.PASSWORD_CHANGED)
        async def change_password(user_id: int, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            result = None
            error = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)
                extra = {"duration_ms": duration_ms}
                
                if error:
                    extra["error"] = str(error)
                    extra["success"] = False
                else:
                    extra["success"] = True
                
                # Extract common fields from kwargs
                user_id = kwargs.get("user_id") or kwargs.get("current_user", {}).get("id")
                ip_address = kwargs.get("ip_address") or kwargs.get("client_ip")
                
                auth_logger._log_event(
                    event_type,
                    user_id=user_id,
                    ip_address=ip_address,
                    extra=extra
                )
        
        return wrapper
    return decorator
