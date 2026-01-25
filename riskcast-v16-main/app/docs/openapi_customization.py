"""
OpenAPI Customization

Customize OpenAPI schema for better documentation.
"""

import logging
from typing import Dict, Any
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)


def customize_openapi(app: FastAPI) -> Dict[str, Any]:
    """
    Generate customized OpenAPI schema.
    Falls back to default if customization fails.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    try:
        openapi_schema = get_openapi(
            title="RISKCAST API",
            version="3.0.0",
            description="""
# RISKCAST Marine Cargo Insurance API

Real-time risk assessment and insurance platform for marine cargo.

## Overview

RISKCAST provides a comprehensive API for:
- **Risk Assessment**: Real-time risk scoring using ML models
- **Quote Management**: Request, modify, and manage insurance quotes
- **Policy Management**: Bind quotes and manage policies
- **Claims Processing**: File and track claims
- **Analytics**: Access risk and business analytics

## Authentication

All API requests require authentication using an API key:
```
X-API-Key: your_api_key_here
```

Or using Bearer token:
```
Authorization: Bearer your_jwt_token
```

## Rate Limiting

API requests are rate-limited based on your subscription tier:

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Starter | 100 | 10,000 |
| Professional | 500 | 100,000 |
| Enterprise | 2,000 | 1,000,000 |

## Errors

All errors follow this format:

```json
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "details": {}
    }
}
```

## Support

- Documentation: https://docs.riskcast.io
- Support: support@riskcast.io
        """,
            routes=app.routes,
        )
        
        # Add servers
        openapi_schema["servers"] = [
            {"url": "https://api.riskcast.io", "description": "Production"},
            {"url": "https://sandbox.api.riskcast.io", "description": "Sandbox"},
            {"url": "http://localhost:8000", "description": "Local Development"}
        ]
        
        # Add security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}
        
        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}
        
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for authentication"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for user authentication"
            }
        }
        
        # Add global security
        openapi_schema["security"] = [
            {"ApiKeyAuth": []},
            {"BearerAuth": []}
        ]
        
        # Add tags with descriptions
        openapi_schema["tags"] = [
            {"name": "Risk Assessment", "description": "Risk scoring and assessment endpoints"},
            {"name": "Quotes", "description": "Quote management - request, view, accept/decline"},
            {"name": "Policies", "description": "Policy management - bind, view, renew"},
            {"name": "Claims", "description": "Claims filing and management"},
            {"name": "Health", "description": "System health and status"},
            {"name": "Usage", "description": "API usage statistics and quotas"}
        ]
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
        
    except Exception as e:
        # Fall back to default FastAPI OpenAPI if customization fails
        logger.warning(f"Failed to generate custom OpenAPI schema: {e}. Using default.")
        
        # Use default FastAPI OpenAPI generation
        try:
            default_schema = get_openapi(
                title=app.title or "RISKCAST API",
                version=app.version or "3.0.0",
                description=app.description or "RISKCAST Marine Cargo Insurance API",
                routes=app.routes,
            )
            app.openapi_schema = default_schema
            return app.openapi_schema
        except Exception as e2:
            logger.error(f"Failed to generate default OpenAPI schema: {e2}")
            # Return minimal schema
            app.openapi_schema = {
                "openapi": "3.1.0",
                "info": {"title": "RISKCAST API", "version": "3.0.0"},
                "paths": {}
            }
            return app.openapi_schema


def setup_docs(app: FastAPI):
    """Set up documentation endpoints."""
    
    # Override OpenAPI generation with error handling
    app.openapi = lambda: customize_openapi(app)
    
    # Add additional documentation endpoints
    try:
        from fastapi import APIRouter
        docs_router = APIRouter(prefix="/api/v3/docs", tags=["Documentation"])
        
        @docs_router.get("/getting-started")
        async def getting_started():
            """Quick start guide."""
            return {
                "title": "Getting Started with RISKCAST API",
                "steps": [
                    {
                        "step": 1,
                        "title": "Get API Key",
                        "description": "Sign up at https://riskcast.io and create an API key"
                    },
                    {
                        "step": 2,
                        "title": "Make First Request",
                        "description": "Test your API key with a health check",
                        "example": "curl -H 'X-API-Key: YOUR_KEY' http://localhost:8000/health"
                    }
                ]
            }
        
        # Include docs router in app
        app.include_router(docs_router)
    except Exception as e:
        logger.warning(f"Failed to setup documentation routes: {e}")
