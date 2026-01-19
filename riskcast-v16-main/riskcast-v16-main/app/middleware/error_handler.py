"""
RISKCAST Security - Error Handler Middleware
Sanitizes errors to prevent information leakage
"""

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
import traceback
import logging
import os
from pathlib import Path

# Setup error logging
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
ERROR_LOG_FILE = LOG_DIR / "errors.log"

error_logger = logging.getLogger("error")
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(ERROR_LOG_FILE)
error_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(message)s\n%(pathname)s:%(lineno)d\n'
))
error_logger.addHandler(error_handler)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to sanitize errors and prevent information leakage"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HTTPException as http_exc:
            # HTTPException is expected, just re-raise
            raise http_exc
        except Exception as exc:
            # Log full error details internally
            error_id = id(exc)
            error_traceback = traceback.format_exc()
            
            # Log to file
            error_logger.error(
                f"Error ID: {error_id}\n"
                f"Path: {request.url.path}\n"
                f"Method: {request.method}\n"
                f"IP: {request.client.host if request.client else 'unknown'}\n"
                f"Error: {str(exc)}\n"
                f"Traceback:\n{error_traceback}"
            )
            
            # Check if this is a production environment
            is_production = os.getenv("ENVIRONMENT") == "production"
            
            # Return sanitized error response
            if is_production:
                # In production, hide all error details
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "error_id": str(error_id),
                        "message": "An unexpected error occurred. Please contact support if this persists."
                    }
                )
            else:
                # In development, show more details (but still sanitized)
                # Remove any sensitive paths or keys
                safe_message = str(exc)
                
                # Remove API keys from error messages
                import re
                safe_message = re.sub(r'api[_-]?key["\']?\s*[:=]\s*["\']?[^\s"\']+', 
                                     'api_key=***HIDDEN***', safe_message, flags=re.IGNORECASE)
                safe_message = re.sub(r'secret["\']?\s*[:=]\s*["\']?[^\s"\']+', 
                                     'secret=***HIDDEN***', safe_message, flags=re.IGNORECASE)
                
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "Internal server error",
                        "error_id": str(error_id),
                        "message": safe_message,
                        "traceback": error_traceback if os.getenv("DEBUG") == "true" else None
                    }
                )


