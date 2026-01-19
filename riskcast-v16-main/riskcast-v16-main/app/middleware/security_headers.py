"""
RISKCAST Security - Security Headers Middleware
Adds security headers to all responses
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

# CSP Policy - Content Security Policy configuration
# FULL ALLOW Cesium CSP - Allows CesiumJS, Web Workers, imagery providers, and all tiles
# This CSP is permissive to ensure CesiumJS works correctly with all its features:
# - Web Workers (blob: workers)
# - Imagery tiles (ArcGIS, Carto, OpenStreetMap, Cesium Ion)
# - Terrain data
# - All Cesium services

# Build comprehensive CSP that allows CesiumJS to function fully with local files
# Note: CSP doesn't accept absolute paths like /static/cesium/ - use 'self' which covers same-origin
CSP_POLICY = os.getenv(
    "CSP_POLICY",
    (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' blob: https://unpkg.com https://cdn.jsdelivr.net https://cdn.tailwindcss.com https://cesium.com https://threejs.org; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://unpkg.com https://cesium.com; "
        "img-src 'self' data: blob: https://*; "
        "connect-src 'self' https://*; "
        "font-src 'self' data: https://fonts.gstatic.com https://fonts.googleapis.com; "
        "media-src 'self' https://cdn.coverr.co https://*.coverr.co; "
        "worker-src 'self' blob: data:; "
        "child-src 'self' blob: data:; "
        "frame-src 'self';"
    )
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


