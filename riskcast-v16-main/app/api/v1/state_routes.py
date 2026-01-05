"""
RISKCAST API v1 - State Routes

Backend state synchronization endpoints for shipment state.
Enables backend-first state management with localStorage as cache.

ARCHITECTURE:
- GET /api/v1/state/{shipment_id} - Get state from backend
- PUT /api/v1/state/{shipment_id} - Save state to backend
- GET /api/v1/state - List recent shipments
"""
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from app.core.state_storage import (
    save_state,
    load_state,
    list_shipments,
    generate_shipment_id
)
from app.utils.standard_responses import ok, fail

router = APIRouter()


class StateRequest(BaseModel):
    """Request model for saving state"""
    state: Dict[str, Any]
    shipment_id: Optional[str] = None  # If not provided, will be generated


@router.get("/state/{shipment_id}")
async def get_state(shipment_id: str, request: Request):
    """
    Get shipment state from backend
    
    Args:
        shipment_id: Shipment identifier
        
    Returns:
        State object with metadata (updated_at, created_at)
    """
    try:
        state_data = load_state(shipment_id)
        
        if state_data is None:
            return fail(
                code="STATE_NOT_FOUND",
                message=f"State not found for shipment_id: {shipment_id}",
                status_code=404,
                request=request
            )
        
        return ok(data=state_data, request=request)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading state for {shipment_id}: {e}", exc_info=True)
        return fail(
            code="STATE_LOAD_ERROR",
            message="Failed to load state",
            details={"error": str(e)} if os.getenv("DEBUG") == "true" else None,
            status_code=500,
            request=request
        )


@router.put("/state/{shipment_id}")
async def save_state_endpoint(shipment_id: str, state_request: StateRequest, request: Request):
    """
    Save shipment state to backend
    
    Conflict resolution: last-write-wins (based on updated_at)
    
    Args:
        shipment_id: Shipment identifier
        state_request: State request with state data
        
    Returns:
        Success response with updated state metadata
    """
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Check for conflict if existing state
        existing = load_state(shipment_id)
        if existing:
            # Check if client has stale data (optional - can be enhanced)
            client_updated_at = state_request.state.get("_updated_at")
            if client_updated_at and existing.get("updated_at"):
                if client_updated_at < existing.get("updated_at"):
                    logger.warning(
                        f"[State Sync] Potential conflict for {shipment_id}: "
                        f"client={client_updated_at}, server={existing.get('updated_at')}"
                    )
                    # Still allow save (last-write-wins), but log conflict
        
        # Save state
        success = save_state(shipment_id, state_request.state)
        
        if not success:
            return fail(
                code="STATE_SAVE_ERROR",
                message="Failed to save state",
                status_code=500,
                request=request
            )
        
        # Return updated state with metadata
        updated_state = load_state(shipment_id)
        
        return ok(
            data=updated_state,
            request=request,
            message="State saved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error saving state for {shipment_id}: {e}", exc_info=True)
        return fail(
            code="STATE_SAVE_ERROR",
            message="Failed to save state",
            details={"error": str(e)} if os.getenv("DEBUG") == "true" else None,
            status_code=500,
            request=request
        )


@router.post("/state")
async def create_state(state_request: StateRequest, request: Request):
    """
    Create new shipment state (generates shipment_id if not provided)
    
    Args:
        state_request: State request (shipment_id optional)
        
    Returns:
        Created state with shipment_id
    """
    import os
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Generate shipment_id if not provided
        shipment_id = state_request.shipment_id
        if not shipment_id:
            shipment_id = generate_shipment_id(state_request.state)
        
        # Check if already exists
        existing = load_state(shipment_id)
        if existing:
            return fail(
                code="STATE_ALREADY_EXISTS",
                message=f"State already exists for shipment_id: {shipment_id}. Use PUT to update.",
                status_code=409,
                request=request
            )
        
        # Save state
        success = save_state(shipment_id, state_request.state)
        
        if not success:
            return fail(
                code="STATE_SAVE_ERROR",
                message="Failed to create state",
                status_code=500,
                request=request
            )
        
        # Return created state
        created_state = load_state(shipment_id)
        
        return ok(
            data=created_state,
            request=request,
            message="State created successfully"
        )
        
    except Exception as e:
        logger.error(f"Error creating state: {e}", exc_info=True)
        return fail(
            code="STATE_CREATE_ERROR",
            message="Failed to create state",
            details={"error": str(e)} if os.getenv("DEBUG") == "true" else None,
            status_code=500,
            request=request
        )


@router.get("/state")
async def list_shipments_endpoint(request: Request, limit: int = 100):
    """
    List recent shipments
    
    Args:
        limit: Maximum number of shipments to return (default: 100)
        
    Returns:
        List of shipment metadata
    """
    try:
        shipments = list_shipments(limit=limit)
        
        return ok(
            data={"shipments": shipments, "count": len(shipments)},
            request=request
        )
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing shipments: {e}", exc_info=True)
        return fail(
            code="STATE_LIST_ERROR",
            message="Failed to list shipments",
            status_code=500,
            request=request
        )

