"""
Authentication Configuration

RISKCAST Auth System - Production Grade

Feature flags and configuration for the authentication system.

SECURITY CONSIDERATIONS:
- In production, AUTH_ENABLED should be True
- In production, COOKIE_SECURE must be True (HTTPS required)
- SECRET_KEY must be changed from default in production
- SESSION_SECRET should be at least 32 characters of random data

ENVIRONMENT VARIABLES:
- AUTH_ENABLED: Master switch for authentication (default: false in dev)
- SESSION_SECRET: Secret key for session signing
- SESSION_EXPIRE_HOURS: Idle timeout in hours (default: 48)
- SESSION_ABSOLUTE_HOURS: Absolute session lifetime (default: 720 = 30 days)
- COOKIE_SECURE: Use HTTPS-only cookies (default: true in production)
- COOKIE_SAMESITE: Cookie SameSite policy (strict, lax, none)
- PROTECT_INPUT: Require auth for input pages
- PROTECT_RESULTS: Require auth for results pages
"""
import os
import secrets
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass


def _get_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable."""
    value = os.getenv(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    if value in ("false", "0", "no", "off"):
        return False
    return default


def _get_int(key: str, default: int) -> int:
    """Get integer from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def _get_list(key: str, default: Optional[List[str]] = None) -> List[str]:
    """Get list from comma-separated environment variable."""
    value = os.getenv(key, "")
    if not value:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def _detect_environment() -> str:
    """Detect the runtime environment."""
    env = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).lower()
    if env in ("prod", "production"):
        return "production"
    if env in ("staging", "stage"):
        return "staging"
    return "development"


def _generate_dev_secret() -> str:
    """Generate a random secret for development only."""
    return secrets.token_urlsafe(32)


def _validate_production_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration for production environment.
    Returns list of warnings/errors.
    """
    issues = []
    
    if not config.get("AUTH_ENABLED"):
        issues.append("WARNING: AUTH_ENABLED is False in production!")
    
    if not config.get("SESSION_SECRET"):
        issues.append("CRITICAL: SESSION_SECRET is not set!")
    elif len(config.get("SESSION_SECRET", "")) < 32:
        issues.append("WARNING: SESSION_SECRET should be at least 32 characters")
    
    if not config.get("COOKIE_SECURE"):
        issues.append("CRITICAL: COOKIE_SECURE should be True in production!")
    
    if config.get("COOKIE_SAMESITE", "").lower() == "none":
        issues.append("WARNING: COOKIE_SAMESITE='none' reduces CSRF protection")
    
    if not config.get("ALLOWED_ORIGINS"):
        issues.append("WARNING: ALLOWED_ORIGINS is empty - CORS may not work correctly")
    
    return issues


def get_auth_config() -> Dict[str, Any]:
    """
    Get authentication configuration from environment variables.
    
    Returns:
        Dictionary with auth configuration
    """
    environment = _detect_environment()
    is_production = environment == "production"
    
    # Determine defaults based on environment
    default_auth_enabled = is_production  # Enable auth by default in production
    default_cookie_secure = is_production  # HTTPS only in production
    default_samesite = "strict" if is_production else "lax"
    
    # Build configuration
    config = {
        # Environment
        "ENVIRONMENT": environment,
        "IS_PRODUCTION": is_production,
        
        # Master switch - disable auth entirely
        "AUTH_ENABLED": _get_bool("AUTH_ENABLED", default_auth_enabled),
        
        # Route protection flags (granular control)
        "PROTECT_INPUT": _get_bool("PROTECT_INPUT", False),
        "PROTECT_RESULTS": _get_bool("PROTECT_RESULTS", False),
        
        # Invite-only mode
        "INVITE_ONLY": _get_bool("INVITE_ONLY", False),
        
        # Session configuration
        "SESSION_SECRET": os.getenv("SESSION_SECRET") or os.getenv("SESSION_SECRET_KEY") or "",
        "SESSION_EXPIRE_HOURS": _get_int("SESSION_EXPIRE_HOURS", 48),  # Idle timeout (48h)
        "SESSION_ABSOLUTE_HOURS": _get_int("SESSION_ABSOLUTE_HOURS", 720),  # Absolute (30 days)
        
        # Cookie security
        "COOKIE_SECURE": _get_bool("COOKIE_SECURE", default_cookie_secure),
        "COOKIE_SAMESITE": os.getenv("COOKIE_SAMESITE", default_samesite).lower(),
        "COOKIE_PREFIX_HOST": _get_bool("COOKIE_PREFIX_HOST", is_production),
        "COOKIE_DOMAIN": os.getenv("COOKIE_DOMAIN", ""),  # Empty = current domain only
        
        # Password policy
        "PASSWORD_MIN_LENGTH": _get_int("PASSWORD_MIN_LENGTH", 8),
        "PASSWORD_REQUIRE_UPPERCASE": _get_bool("PASSWORD_REQUIRE_UPPERCASE", True),
        "PASSWORD_REQUIRE_LOWERCASE": _get_bool("PASSWORD_REQUIRE_LOWERCASE", True),
        "PASSWORD_REQUIRE_NUMBER": _get_bool("PASSWORD_REQUIRE_NUMBER", True),
        "PASSWORD_REQUIRE_SPECIAL": _get_bool("PASSWORD_REQUIRE_SPECIAL", True),
        
        # Account security
        "MAX_LOGIN_ATTEMPTS": _get_int("MAX_LOGIN_ATTEMPTS", 5),
        "LOGIN_LOCKOUT_MINUTES": _get_int("LOGIN_LOCKOUT_MINUTES", 15),
        "PASSWORD_RESET_EXPIRY_HOURS": _get_int("PASSWORD_RESET_EXPIRY_HOURS", 1),
        "EMAIL_VERIFICATION_EXPIRY_HOURS": _get_int("EMAIL_VERIFICATION_EXPIRY_HOURS", 24),
        
        # Email configuration
        "EMAIL_ENABLED": _get_bool("EMAIL_ENABLED", False),
        "SMTP_HOST": os.getenv("SMTP_HOST", ""),
        "SMTP_PORT": _get_int("SMTP_PORT", 587),
        "SMTP_USER": os.getenv("SMTP_USER", ""),
        "SMTP_PASS": os.getenv("SMTP_PASS", ""),
        "SMTP_USE_TLS": _get_bool("SMTP_USE_TLS", True),
        "EMAIL_FROM": os.getenv("EMAIL_FROM", "noreply@riskcast.com"),
        "EMAIL_FROM_NAME": os.getenv("EMAIL_FROM_NAME", "RISKCAST"),
        
        # OAuth providers
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID", ""),
        "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI", ""),
        
        # CORS / Origin allowlist
        "ALLOWED_ORIGINS": _get_list("ALLOWED_ORIGINS", [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]),
        
        # Rate limiting
        "RATE_LIMIT_ENABLED": _get_bool("RATE_LIMIT_ENABLED", True),
        "RATE_LIMIT_PER_MINUTE": _get_int("RATE_LIMIT_PER_MINUTE", 60),
        "RATE_LIMIT_LOGIN_PER_MINUTE": _get_int("RATE_LIMIT_LOGIN_PER_MINUTE", 5),
        "REDIS_URL": os.getenv("REDIS_URL", ""),  # Required for distributed rate limiting
        
        # API keys
        "API_KEY_ENABLED": _get_bool("API_KEY_ENABLED", True),
        "API_KEY_MAX_PER_USER": _get_int("API_KEY_MAX_PER_USER", 10),
        
        # Audit logging
        "AUDIT_LOG_ENABLED": _get_bool("AUDIT_LOG_ENABLED", True),
        "AUDIT_LOG_SENSITIVE": _get_bool("AUDIT_LOG_SENSITIVE", False),  # Log sensitive operations
        
        # Security headers
        "ENABLE_SECURITY_HEADERS": _get_bool("ENABLE_SECURITY_HEADERS", True),
    }
    
    # Generate development secret if not provided
    if not config["SESSION_SECRET"]:
        if is_production:
            logger.critical(
                "SESSION_SECRET is not set! This is a critical security issue. "
                "Set SESSION_SECRET environment variable with at least 32 random characters."
            )
            # In production, we should fail fast
            raise ValueError(
                "SESSION_SECRET must be set in production. "
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        else:
            # Development only - generate a temporary secret
            config["SESSION_SECRET"] = _generate_dev_secret()
            logger.warning(
                "SESSION_SECRET not set - using generated secret for development. "
                "This will invalidate sessions on restart."
            )
    
    # Validate production configuration
    if is_production:
        issues = _validate_production_config(config)
        for issue in issues:
            if issue.startswith("CRITICAL"):
                logger.critical(issue)
            else:
                logger.warning(issue)
    
    return config


# Global config instance
AUTH_CONFIG = get_auth_config()


def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return AUTH_CONFIG["AUTH_ENABLED"]


def is_production() -> bool:
    """Check if running in production environment."""
    return AUTH_CONFIG["IS_PRODUCTION"]


def should_protect_route(route_path: str) -> bool:
    """
    Check if a route should be protected based on configuration.
    
    Args:
        route_path: Route path (e.g., "/input_react", "/results")
        
    Returns:
        True if route should be protected
    """
    if not is_auth_enabled():
        return False
    
    # Check specific route flags
    if route_path in ["/input", "/input_react", "/input_v20"] and AUTH_CONFIG["PROTECT_INPUT"]:
        return True
    if route_path in ["/results", "/summary"] and AUTH_CONFIG["PROTECT_RESULTS"]:
        return True
    
    return False


def get_session_config() -> Dict[str, Any]:
    """Get session-specific configuration."""
    return {
        "secret": AUTH_CONFIG["SESSION_SECRET"],
        "expire_hours": AUTH_CONFIG["SESSION_EXPIRE_HOURS"],
        "absolute_hours": AUTH_CONFIG["SESSION_ABSOLUTE_HOURS"],
        "cookie_secure": AUTH_CONFIG["COOKIE_SECURE"],
        "cookie_samesite": AUTH_CONFIG["COOKIE_SAMESITE"],
        "cookie_prefix_host": AUTH_CONFIG["COOKIE_PREFIX_HOST"],
        "cookie_domain": AUTH_CONFIG["COOKIE_DOMAIN"],
    }


def get_password_policy() -> Dict[str, Any]:
    """Get password policy configuration."""
    return {
        "min_length": AUTH_CONFIG["PASSWORD_MIN_LENGTH"],
        "require_uppercase": AUTH_CONFIG["PASSWORD_REQUIRE_UPPERCASE"],
        "require_lowercase": AUTH_CONFIG["PASSWORD_REQUIRE_LOWERCASE"],
        "require_number": AUTH_CONFIG["PASSWORD_REQUIRE_NUMBER"],
        "require_special": AUTH_CONFIG["PASSWORD_REQUIRE_SPECIAL"],
    }


def get_rate_limit_config() -> Dict[str, Any]:
    """Get rate limiting configuration."""
    return {
        "enabled": AUTH_CONFIG["RATE_LIMIT_ENABLED"],
        "per_minute": AUTH_CONFIG["RATE_LIMIT_PER_MINUTE"],
        "login_per_minute": AUTH_CONFIG["RATE_LIMIT_LOGIN_PER_MINUTE"],
        "redis_url": AUTH_CONFIG["REDIS_URL"],
    }


def get_oauth_config(provider: str) -> Optional[Dict[str, str]]:
    """
    Get OAuth configuration for a provider.
    
    Args:
        provider: OAuth provider name (e.g., "google")
        
    Returns:
        Configuration dict or None if not configured
    """
    if provider.lower() == "google":
        client_id = AUTH_CONFIG.get("GOOGLE_CLIENT_ID")
        client_secret = AUTH_CONFIG.get("GOOGLE_CLIENT_SECRET")
        redirect_uri = AUTH_CONFIG.get("GOOGLE_REDIRECT_URI")
        
        if client_id and client_secret and redirect_uri:
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
            }
    
    return None


def is_oauth_configured(provider: str) -> bool:
    """Check if OAuth provider is configured."""
    return get_oauth_config(provider) is not None


# Log configuration on import (only in development)
if not AUTH_CONFIG["IS_PRODUCTION"]:
    logger.info(f"Auth config loaded: AUTH_ENABLED={AUTH_CONFIG['AUTH_ENABLED']}, "
                f"ENV={AUTH_CONFIG['ENVIRONMENT']}")
