"""
RISKCAST Security - Enhanced Error Handler Middleware
Improved error handling with standardized responses and better logging
"""
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import traceback
import logging
import os
from pathlib import Path
from typing import Optional
import uuid

from app.utils.standard_responses import StandardResponse
from app.utils.custom_exceptions import RISKCASTException, ValidationError

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
    """
    Enhanced middleware to handle errors with standardized responses
    
    Features:
    - Standardized error response format
    - Error tracking with unique IDs
    - Detailed logging (internal) vs sanitized responses (external)
    - Different handling for different exception types
    """
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            # For static file requests (/assets, /static, /dist), don't modify response
            # Let Starlette handle 404s naturally
            if request.url.path.startswith(("/assets/", "/static/", "/dist/")):
                return response
            return response
            
        except HTTPException as http_exc:
            # For static file requests, let Starlette handle 404s naturally
            # Don't convert to JSON response for static files
            if request.url.path.startswith(("/assets/", "/static/", "/dist/")):
                # Re-raise to let Starlette handle it
                raise http_exc
            
            # HTTPException is expected, return standard format for API routes
            return StandardResponse.error(
                message=http_exc.detail,
                error_code=f"HTTP_{http_exc.status_code}",
                status_code=http_exc.status_code,
                error_type="client" if http_exc.status_code < 500 else "server",
                request=request
            )
            
        except ValidationError as val_exc:
            # Custom validation error
            return StandardResponse.validation_error(
                message=val_exc.message,
                errors=val_exc.field_errors,
                request=request
            )
            
        except RISKCASTException as rc_exc:
            # Custom RISKCAST exceptions
            error_id = str(uuid.uuid4())[:8]
            
            # Get request_id from request state if available
            request_id = getattr(request.state, 'request_id', None) if hasattr(request, 'state') else None
            
            # Log internally (include request_id if available)
            log_msg = f"Error ID: {error_id}\n"
            if request_id:
                log_msg += f"Request ID: {request_id}\n"
            log_msg += (
                f"Path: {request.url.path}\n"
                f"Method: {request.method}\n"
                f"Error Code: {rc_exc.error_code}\n"
                f"Message: {rc_exc.message}\n"
                f"Details: {rc_exc.details}"
            )
            error_logger.error(log_msg)
            
            # Return sanitized response
            return StandardResponse.error(
                message=rc_exc.message,
                error_code=rc_exc.error_code,
                status_code=400,
                details={"error_id": error_id} if os.getenv("DEBUG") == "true" else None,
                request=request
            )
            
        except Exception as exc:
            # Unexpected exceptions
            error_id = str(uuid.uuid4())[:8]
            error_traceback = traceback.format_exc()
            
            # Get request info
            client_ip = request.client.host if request.client else "unknown"
            request_path = request.url.path
            request_method = request.method
            
            # Get request_id from request state if available
            request_id = getattr(request.state, 'request_id', None) if hasattr(request, 'state') else None
            
            # Log full error details internally (include request_id if available)
            log_msg = f"Error ID: {error_id}\n"
            if request_id:
                log_msg += f"Request ID: {request_id}\n"
            log_msg += (
                f"Path: {request_path}\n"
                f"Method: {request_method}\n"
                f"IP: {client_ip}\n"
                f"Error Type: {type(exc).__name__}\n"
                f"Error: {str(exc)}\n"
                f"Traceback:\n{error_traceback}"
            )
            error_logger.error(log_msg)
            
            # Check if this is a production environment
            is_production = os.getenv("ENVIRONMENT") == "production"
            is_debug = os.getenv("DEBUG") == "true"
            
            # Return sanitized error response
            if is_production or not is_debug:
                # Production: Generic error message, no details
                return StandardResponse.server_error(
                    message="An error occurred. Please try again later.",
                    error_id=error_id,
                    request=request
                )
            else:
                # Development: More details
                return StandardResponse.server_error(
                    message=f"Internal server error: {str(exc)}",
                    error_id=error_id,
                    request=request
                )

