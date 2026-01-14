"""
RISKCAST API v2 Router

This module combines all v2 API routes into a single router
for easy mounting in the main application.

Routes included:
- /api/v2/api-keys - API Key management
- /api/v2/enterprise - Enterprise features
- /api/v2/market - Market data
"""

from fastapi import APIRouter

# Create main v2 router
router = APIRouter(prefix="/api/v2", tags=["API v2"])

# Import and include sub-routers
try:
    from app.api.v2.api_keys import router as api_keys_router
    # Include without prefix since api_keys already has /api/v2 prefix
    # We'll adjust the import in main.py instead
except ImportError as e:
    print(f"[API v2] Warning: Could not import api_keys router: {e}")
    api_keys_router = None

try:
    from app.api.v2.enterprise_routes import router as enterprise_router
except ImportError as e:
    print(f"[API v2] Warning: Could not import enterprise router: {e}")
    enterprise_router = None

try:
    from app.api.v2.market_routes import router as market_router
except ImportError as e:
    print(f"[API v2] Warning: Could not import market router: {e}")
    market_router = None


def get_v2_router() -> APIRouter:
    """
    Get the combined v2 router.
    
    Usage in main.py:
        from app.api.v2 import get_v2_router
        app.include_router(get_v2_router())
    """
    combined = APIRouter(tags=["API v2"])
    
    if api_keys_router:
        combined.include_router(api_keys_router)
    
    if enterprise_router:
        combined.include_router(enterprise_router)
    
    if market_router:
        combined.include_router(market_router)
    
    return combined


# Export routers
__all__ = ['router', 'get_v2_router', 'api_keys_router', 'enterprise_router', 'market_router']
