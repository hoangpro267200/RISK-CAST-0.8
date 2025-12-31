"""
RISKCAST Cache Headers Middleware
Sets appropriate caching headers for production assets
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from pathlib import Path

class CacheHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to set cache headers for static assets"""
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Set cache headers for dist assets (production bundles)
        if request.url.path.startswith("/dist/"):
            # Long-term caching for hashed assets (365 days)
            if any(ext in request.url.path for ext in ['.js', '.css', '.png', '.jpg', '.woff2', '.woff']):
                response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
                response.headers["X-Content-Type-Options"] = "nosniff"
        
        # No cache for HTML templates
        elif request.url.path.endswith(".html") or "/" in request.url.path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response


