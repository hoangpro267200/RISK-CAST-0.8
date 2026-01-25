"""
Example: How to integrate structured logging into your FastAPI application

This file demonstrates the complete integration of the structured logging system.
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import structured logging
from app.core.logging import setup_logging, get_logger, set_request_context
from app.middleware.request_logging import (
    RequestLoggingMiddleware,
    SlowRequestLoggingMiddleware
)


# =============================================================================
# Application Lifecycle with Logging
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with logging."""
    logger = get_logger("app.main")
    
    # Startup
    logger.info(
        "Application starting",
        event="app_startup",
        version="1.0.0",
        environment="production"
    )
    
    try:
        yield
    finally:
        # Shutdown
        logger.info(
            "Application shutting down",
            event="app_shutdown"
        )


# =============================================================================
# Create FastAPI App with Logging
# =============================================================================

def create_app() -> FastAPI:
    """Create and configure FastAPI application with structured logging."""
    
    # Initialize structured logging first
    logger = setup_logging(
        service_name="riskcast-api",
        environment="production",
        log_level="INFO",
        json_output=True
    )
    
    # Create FastAPI app
    app = FastAPI(
        title="RiskCast API",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add request logging middleware (order matters!)
    app.add_middleware(
        SlowRequestLoggingMiddleware,
        threshold_ms=1000  # Log requests > 1 second
    )
    
    app.add_middleware(
        RequestLoggingMiddleware,
        log_request_body=False,   # Set True for debugging
        log_response_body=False
    )
    
    logger.info("FastAPI application created with structured logging")
    
    return app


# =============================================================================
# Usage Examples in Route Handlers
# =============================================================================

logger = get_logger(__name__)

app = create_app()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Simple logs
    logger.debug("Health check called")
    return {"status": "healthy"}


@app.post("/api/v3/quotes")
async def create_quote(request: Request, quote_data: dict):
    """Create insurance quote with structured logging."""
    
    # Access request context that was set by middleware
    request_id = request.state.request_id
    
    logger.info(
        "Creating new quote",
        event="quote_creation_start",
        quote_type=quote_data.get("type"),
        customer_id=quote_data.get("customer_id")
    )
    
    try:
        # Business logic here
        quote_id = "QTE-123456"
        premium = 125000.00
        risk_score = 75.5
        
        # Log successful business event
        logger.business_event(
            "quote_created",
            quote_id=quote_id,
            customer_id=quote_data.get("customer_id"),
            premium=premium,
            risk_score=risk_score,
            currency="USD"
        )
        
        return {
            "quote_id": quote_id,
            "premium": premium,
            "risk_score": risk_score
        }
        
    except ValueError as e:
        # Log business error
        logger.warning(
            "Invalid quote data",
            event="quote_validation_failed",
            error=str(e),
            customer_id=quote_data.get("customer_id")
        )
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # Log system error
        logger.error(
            "Quote creation failed",
            event="quote_creation_error",
            error_type=type(e).__name__,
            customer_id=quote_data.get("customer_id")
        )
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/v3/risk-assessments")
async def create_risk_assessment(request: Request, assessment_data: dict):
    """Create risk assessment with audit logging."""
    
    user_id = getattr(request.state, 'user_id', None)
    tenant_id = getattr(request.state, 'tenant_id', None)
    
    logger.info(
        "Starting risk assessment",
        event="risk_assessment_start",
        shipment_id=assessment_data.get("shipment_id")
    )
    
    # Perform risk assessment
    assessment_id = "RISK-789"
    risk_level = "medium"
    
    # Log audit event for compliance
    logger.audit(
        action="risk_assessment_created",
        entity_type="risk_assessment",
        entity_id=assessment_id,
        user_id=user_id,
        tenant_id=tenant_id,
        risk_level=risk_level,
        shipment_id=assessment_data.get("shipment_id")
    )
    
    return {
        "assessment_id": assessment_id,
        "risk_level": risk_level
    }


@app.post("/api/v3/auth/login")
async def login(request: Request, credentials: dict):
    """User login with security event logging."""
    
    username = credentials.get("username")
    
    # Note: password will be automatically masked in logs
    logger.info(
        "Login attempt",
        event="login_attempt",
        username=username,
        ip_address=request.client.host if request.client else "unknown"
    )
    
    # Verify credentials
    if not verify_credentials(credentials):
        # Log security event
        logger.security_event(
            "failed_login_attempt",
            severity="medium",
            username=username,
            ip_address=request.client.host if request.client else "unknown",
            reason="invalid_credentials"
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Successful login
    user_id = "user-123"
    
    logger.security_event(
        "successful_login",
        severity="low",
        username=username,
        user_id=user_id,
        ip_address=request.client.host if request.client else "unknown"
    )
    
    return {
        "user_id": user_id,
        "token": "***MASKED***"  # This will be masked in logs
    }


def verify_credentials(credentials: dict) -> bool:
    """Mock credential verification."""
    return True


# =============================================================================
# Using Logging Decorator
# =============================================================================

from app.core.logging import log_function_call
import logging


@log_function_call(logger=logger, level=logging.DEBUG)
async def calculate_premium(policy_data: dict) -> float:
    """Calculate premium with automatic logging."""
    # This function's entry and exit will be logged automatically
    # Including timing information
    
    base_premium = 100000.00
    risk_factor = policy_data.get("risk_score", 50) / 100.0
    
    premium = base_premium * (1 + risk_factor)
    
    return premium


@log_function_call(logger=logger, level=logging.INFO)
async def send_notification(user_id: str, message: str):
    """Send notification with automatic logging."""
    # Entry and exit logged automatically
    # Errors are also logged automatically with traceback
    
    logger.debug(
        "Sending notification",
        user_id=user_id,
        message_preview=message[:50]
    )
    
    # Send notification logic here
    pass


# =============================================================================
# Error Handler with Logging
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler with structured logging."""
    
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Log the error with full context
    logger.error(
        "Unhandled exception",
        event="unhandled_exception",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "request_id": request_id
        }
    )


# =============================================================================
# Background Task with Logging
# =============================================================================

from fastapi import BackgroundTasks


async def process_risk_analysis(analysis_id: str, request_id: str):
    """Background task with logging context."""
    
    # Set logging context for background task
    set_request_context(request_id=request_id)
    
    logger.info(
        "Starting background risk analysis",
        event="background_task_start",
        task_type="risk_analysis",
        analysis_id=analysis_id
    )
    
    try:
        # Perform analysis
        # ... long-running task ...
        
        logger.info(
            "Background risk analysis completed",
            event="background_task_complete",
            analysis_id=analysis_id
        )
        
    except Exception as e:
        logger.error(
            "Background risk analysis failed",
            event="background_task_error",
            analysis_id=analysis_id,
            error_type=type(e).__name__
        )


@app.post("/api/v3/risk-analysis")
async def start_risk_analysis(
    request: Request,
    background_tasks: BackgroundTasks,
    analysis_data: dict
):
    """Start risk analysis with background task."""
    
    analysis_id = "ANALYSIS-456"
    request_id = request.state.request_id
    
    # Queue background task with logging context
    background_tasks.add_task(
        process_risk_analysis,
        analysis_id=analysis_id,
        request_id=request_id
    )
    
    logger.info(
        "Risk analysis queued",
        event="risk_analysis_queued",
        analysis_id=analysis_id
    )
    
    return {
        "analysis_id": analysis_id,
        "status": "queued"
    }


# =============================================================================
# Dependency Injection with Logging
# =============================================================================

async def get_current_user(request: Request) -> dict:
    """Dependency to get current user with logging."""
    
    # Extract token (will be masked in logs)
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        logger.security_event(
            "missing_auth_token",
            severity="low",
            path=request.url.path
        )
        raise HTTPException(status_code=401, detail="Missing authentication")
    
    # Verify token and get user
    user = {"user_id": "user-123", "tenant_id": "tenant-456"}
    
    # Set user context for all subsequent logs
    set_request_context(
        user_id=user["user_id"],
        tenant_id=user["tenant_id"]
    )
    
    return user


@app.get("/api/v3/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Protected endpoint with user context."""
    
    # All logs in this handler will include user_id and tenant_id
    logger.info(
        "Fetching user profile",
        event="profile_fetch"
    )
    
    return current_user


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Initialize logging
    logger = setup_logging(
        service_name="riskcast-api",
        environment="production"
    )
    
    logger.info("Starting RiskCast API server")
    
    # Run server
    uvicorn.run(
        "logging_integration_example:app",
        host="0.0.0.0",
        port=8000,
        log_config=None  # Disable uvicorn's logging config
    )
