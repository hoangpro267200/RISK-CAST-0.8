# app/routes/update_shipment_route_v33.py
"""
RISKCAST Update Shipment Route v33
PATCH endpoint for updating shipment data
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.memory import memory_system
from typing import Dict, Any
import json

router = APIRouter()

@router.patch("/api/update_shipment")
async def update_shipment(shipment: Dict[str, Any]):
    """
    Update shipment data
    
    Args:
        shipment: Complete shipment state object
    
    Returns:
        JSONResponse with success status
    """
    try:
        # Validate shipment structure
        required_keys = ['transport', 'cargo', 'parties', 'risk', 'segments']
        for key in required_keys:
            if key not in shipment:
                raise HTTPException(status_code=400, detail=f"Missing required key: {key}")
        
        # Store in memory system
        memory_system.set("latest_shipment", shipment)
        
        # Also store as separate fields for compatibility
        if shipment.get('transport'):
            memory_system.set("transport_mode", shipment['transport'].get('mode', 'ocean'))
        if shipment.get('cargo'):
            memory_system.set("cargo_type", shipment['cargo'].get('commodity', ''))
        if shipment.get('risk'):
            memory_system.set("risk_score", shipment['risk'].get('score', 7.2))
        
        return JSONResponse({
            "status": "success",
            "message": "Shipment updated successfully",
            "shipment": shipment
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update shipment: {str(e)}")

