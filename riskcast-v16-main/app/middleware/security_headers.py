"""
RISKCAST Security - Security Headers Middleware
Adds security headers to all responses
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

# CSP Policy - Content Security Policy configuration
# Phase 6 - Day 17: CSP Hardening
# 
# SECURITY: Remove unsafe-inline and unsafe-eval where possible.
# Use nonces for inline scripts/styles in production.
# 
# Note: Some libraries (CesiumJS, Vite HMR) may require unsafe-inline in development.
# In production, use nonces or hashes for inline content.

def generate_csp_nonce() -> str:
    """Generate CSP nonce for inline scripts/styles"""
    import secrets
    return secrets.token_urlsafe(16)

# Get nonce from environment or generate
CSP_NONCE = os.getenv("CSP_NONCE", generate_csp_nonce())

# Production CSP (strict, with nonces)
CSP_POLICY_PRODUCTION = (
    f"default-src 'self'; "
    f"script-src 'self' 'nonce-{CSP_NONCE}' blob: https://unpkg.com https://cdn.jsdelivr.net https://cesium.com; "
    f"style-src 'self' 'nonce-{CSP_NONCE}' https://fonts.googleapis.com https://unpkg.com https://cesium.com; "
    f"img-src 'self' data: blob: https://*; "
    f"connect-src 'self' https://*; "
    f"font-src 'self' data: https://fonts.gstatic.com https://fonts.googleapis.com; "
    f"media-src 'self' https://cdn.coverr.co https://*.coverr.co; "
    f"worker-src 'self' blob: data:; "
    f"child-src 'self' blob: data:; "
    f"frame-src 'self';"
)

# Development CSP (permissive for Vite HMR and CesiumJS)
CSP_POLICY_DEVELOPMENT = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://unpkg.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://cesium.com https://threejs.org; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cesium.com; "
    "img-src 'self' data: blob: https://*; "
    "connect-src 'self' https://* ws://localhost:* wss://localhost:*; "
    "font-src 'self' data: https://fonts.gstatic.com https://fonts.googleapis.com; "
    "media-src 'self' https://cdn.coverr.co https://*.coverr.co; "
    "worker-src 'self' blob: data:; "
    "child-src 'self' blob: data:; "
    "frame-src 'self';"
)

# Select CSP based on environment
is_production = os.getenv("ENVIRONMENT", "development") == "production"
CSP_POLICY = os.getenv(
    "CSP_POLICY",
    CSP_POLICY_PRODUCTION if is_production else CSP_POLICY_DEVELOPMENT
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = CSP_POLICY
        
        # HSTS (only for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Permissions Policy (formerly Feature Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        return response


