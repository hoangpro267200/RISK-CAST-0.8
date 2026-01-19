"""
RISKCAST API v1 - General Routes
Core API endpoints
"""

from fastapi import APIRouter
from .analyze import router as analyze_router

router = APIRouter()

# Include analyze router
router.include_router(analyze_router)


