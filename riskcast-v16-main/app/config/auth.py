"""
Authentication Configuration

RISKCAST Auth System - Phase 1
Feature flags and configuration for auth system.
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).resolve().parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)


def get_auth_config() -> Dict[str, Any]:
    """
    Get authentication configuration from environment variables.
    
    Returns:
        Dictionary with auth configuration
    """
    return {
        # Master switch - disable auth entirely
        "AUTH_ENABLED": os.getenv("AUTH_ENABLED", "false").lower() == "true",
        
        # Route protection flags (granular control)
        "PROTECT_INPUT": os.getenv("PROTECT_INPUT", "false").lower() == "true",
        "PROTECT_RESULTS": os.getenv("PROTECT_RESULTS", "false").lower() == "true",
        
        # Invite-only mode (future feature)
        "INVITE_ONLY": os.getenv("INVITE_ONLY", "false").lower() == "true",
        
        # Session configuration
        "SESSION_SECRET": os.getenv("SESSION_SECRET", os.getenv("SESSION_SECRET_KEY", "")),
        # Idle timeout (sliding)
        "SESSION_EXPIRE_HOURS": int(os.getenv("SESSION_EXPIRE_HOURS", "48")),  # default 48h idle
        # Absolute lifetime cap
        "SESSION_ABSOLUTE_HOURS": int(os.getenv("SESSION_ABSOLUTE_HOURS", "720")),  # 30 days default
        "COOKIE_SECURE": os.getenv("COOKIE_SECURE", "false").lower() == "true",  # HTTPS only in prod
        "COOKIE_SAMESITE": os.getenv("COOKIE_SAMESITE", "lax").lower(),  # lax, strict, none
        "COOKIE_PREFIX_HOST": os.getenv("COOKIE_PREFIX_HOST", "false").lower() == "true",
        
        # Email configuration (optional)
        "EMAIL_ENABLED": os.getenv("EMAIL_ENABLED", "false").lower() == "true",
        "SMTP_HOST": os.getenv("SMTP_HOST", ""),
        "SMTP_PORT": int(os.getenv("SMTP_PORT", "587")),
        "SMTP_USER": os.getenv("SMTP_USER", ""),
        "SMTP_PASS": os.getenv("SMTP_PASS", ""),
        "EMAIL_FROM": os.getenv("EMAIL_FROM", "noreply@riskcast.com"),
        # OAuth
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID", ""),
        "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET", ""),
        "GOOGLE_REDIRECT_URI": os.getenv("GOOGLE_REDIRECT_URI", ""),
        # CSRF / Origin allowlist (comma-separated origins)
        "ALLOWED_ORIGINS": [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()],
        # Rate limit backend (redis recommended)
        "REDIS_URL": os.getenv("REDIS_URL", ""),
    }


# Global config instance
AUTH_CONFIG = get_auth_config()


def is_auth_enabled() -> bool:
    """Check if authentication is enabled."""
    return AUTH_CONFIG["AUTH_ENABLED"]


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
    if route_path in ["/input", "/input_react"] and AUTH_CONFIG["PROTECT_INPUT"]:
        return True
    if route_path == "/results" and AUTH_CONFIG["PROTECT_RESULTS"]:
        return True
    
    return False
