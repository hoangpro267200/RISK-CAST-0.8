"""
RISKCAST - Standard Response Format
Standardized error and success responses for consistency

Target Envelope Format:
{
  "success": bool,
  "data": ...,
  "error": { "code": str, "message": str, "details": any } | null,
  "meta": { "request_id": str, "ts": iso, "version": "v16" }
}
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from datetime import datetime
import os


class StandardResponse:
    """Standard response format for API"""
    
    @staticmethod
    def _get_request_id(request: Optional[Request] = None) -> Optional[str]:
        """Extract request_id from request state or return None"""
        if request and hasattr(request.state, 'request_id'):
            return request.state.request_id
        return None
    
    @staticmethod
    def _build_meta(request_id: Optional[str] = None, additional_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build meta object with request_id, timestamp, and version"""
        meta = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "version": "v16"
        }
        if request_id:
            meta["request_id"] = request_id
        if additional_meta:
            meta.update(additional_meta)
        return meta
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        request: Optional[Request] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> JSONResponse:
        """
        Standard success response with envelope format
        
        Args:
            data: Response data
            message: Success message (optional, for backward compat)
            status_code: HTTP status code
            request: FastAPI Request object (for request_id extraction)
            meta: Additional metadata (merged into meta object)
            
        Returns:
            JSONResponse with standard envelope format
        """
        request_id = StandardResponse._get_request_id(request)
        meta_obj = StandardResponse._build_meta(request_id, meta)
        
        response_data = {
            "success": True,
            "data": data,
            "error": None,
            "meta": meta_obj
        }
        
        # Include message for backward compatibility (optional)
        if message and message != "Success":
            response_data["message"] = message
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def error(
        message: str,
        error_code: str = "GENERIC_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """
        Standard error response with envelope format
        
        Args:
            message: Error message (user-friendly)
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
            error_type: Error type (validation, server, client, etc.)
            request: FastAPI Request object (for request_id extraction)
            
        Returns:
            JSONResponse with standard envelope format
        """
        request_id = StandardResponse._get_request_id(request)
        meta_obj = StandardResponse._build_meta(request_id)
        
        error_obj = {
            "code": error_code,
            "message": message
        }
        
        if details:
            error_obj["details"] = details
        if error_type:
            error_obj["type"] = error_type
        
        response_data = {
            "success": False,
            "data": None,
            "error": error_obj,
            "meta": meta_obj
        }
        
        # Include error_code at root for backward compatibility (temporary)
        response_data["error_code"] = error_code
        response_data["status_code"] = status_code
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def validation_error(
        message: str = "Validation error",
        errors: Optional[Dict[str, list]] = None,
        status_code: int = 422,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """
        Validation error response with envelope format
        
        Args:
            message: Error message
            errors: Field-specific errors {field: [error1, error2]}
            status_code: HTTP status code (default: 422)
            request: FastAPI Request object (for request_id extraction)
            
        Returns:
            JSONResponse with validation error format
        """
        request_id = StandardResponse._get_request_id(request)
        meta_obj = StandardResponse._build_meta(request_id)
        
        error_obj = {
            "code": "VALIDATION_ERROR",
            "message": message,
            "type": "validation"
        }
        
        if errors:
            error_obj["details"] = {"field_errors": errors}
        
        response_data = {
            "success": False,
            "data": None,
            "error": error_obj,
            "meta": meta_obj
        }
        
        # Include errors at root for backward compatibility (temporary)
        if errors:
            response_data["errors"] = errors
        response_data["error_code"] = "VALIDATION_ERROR"
        response_data["status_code"] = status_code
            
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @staticmethod
    def not_found(
        resource: str = "Resource",
        message: Optional[str] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """
        Not found error response
        
        Args:
            resource: Resource name (e.g., "Shipment", "User")
            message: Custom message (optional)
            request: FastAPI Request object (for request_id extraction)
            
        Returns:
            JSONResponse with 404 error
        """
        if not message:
            message = f"{resource} not found"
            
        return StandardResponse.error(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            error_type="client",
            request=request
        )
    
    @staticmethod
    def server_error(
        message: str = "Internal server error",
        error_id: Optional[str] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """
        Server error response (500) with envelope format
        
        Args:
            message: Error message (generic, don't leak details)
            error_id: Error ID for tracking (optional)
            request: FastAPI Request object (for request_id extraction)
            
        Returns:
            JSONResponse with 500 error
        """
        request_id = StandardResponse._get_request_id(request)
        meta_obj = StandardResponse._build_meta(request_id)
        
        error_obj = {
            "code": "INTERNAL_SERVER_ERROR",
            "message": message,
            "type": "server"
        }
        
        if error_id:
            error_obj["details"] = {"error_id": error_id}
        
        response_data = {
            "success": False,
            "data": None,
            "error": error_obj,
            "meta": meta_obj
        }
        
        # Include error_id at root for backward compatibility (temporary)
        if error_id:
            response_data["error_id"] = error_id
        response_data["error_code"] = "INTERNAL_SERVER_ERROR"
        response_data["status_code"] = 500
            
        return JSONResponse(
            status_code=500,
            content=response_data
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Unauthorized",
        details: Optional[str] = None,
        request: Optional[Request] = None
    ) -> JSONResponse:
        """
        Unauthorized error response (401) with envelope format
        
        Args:
            message: Error message
            details: Additional details (optional)
            request: FastAPI Request object (for request_id extraction)
            
        Returns:
            JSONResponse with 401 error
        """
        error_details = None
        if details:
            error_details = {"reason": details}
        
        return StandardResponse.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
            details=error_details,
            error_type="authentication",
            request=request
        )


# Convenience helper functions
def ok(data: Any = None, request: Optional[Request] = None, **kwargs) -> JSONResponse:
    """
    Success response helper
    
    Args:
        data: Response data
        request: FastAPI Request object (for request_id)
        **kwargs: Additional metadata to include in meta
        
    Returns:
        JSONResponse with success envelope
    """
    return StandardResponse.success(data=data, request=request, meta=kwargs if kwargs else None)


def fail(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 400,
    request: Optional[Request] = None
) -> JSONResponse:
    """
    Error response helper
    
    Args:
        code: Error code
        message: Error message
        details: Error details
        status_code: HTTP status code
        request: FastAPI Request object (for request_id)
        
    Returns:
        JSONResponse with error envelope
    """
    return StandardResponse.error(
        message=message,
        error_code=code,
        status_code=status_code,
        details=details,
        request=request
    )

