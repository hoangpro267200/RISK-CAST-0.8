"""
Parametric Router
FastAPI routes for parametric insurance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.shared.dependencies import require_user, require_tenant
from app.modules.parametric.service import ParametricService
from app.modules.parametric.schemas import ParametricTriggerCreate, ParametricTriggerResponse
from app.services.parametric_monitoring import get_parametric_monitor
from app.core.parametric.oracle_gateway import OracleQuery, OracleNotConfiguredError
from app.core.parametric.exceptions import OracleFetchError

router = APIRouter(prefix="/parametric", tags=["Parametric Insurance"])


@router.post("/triggers", response_model=StandardResponse)
async def create_trigger(
    trigger_data: ParametricTriggerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """Create parametric trigger"""
    service = ParametricService(db)
    trigger = service.create_trigger(trigger_data, tenant_id)
    return StandardResponse(
        success=True,
        data=trigger.dict(),
        message="Parametric trigger created"
    )


@router.get("/triggers", response_model=StandardResponse)
async def list_triggers(
    db: Session = Depends(get_db),
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """List active parametric triggers"""
    service = ParametricService(db)
    triggers = service.list_active_triggers(tenant_id)
    return StandardResponse(
        success=True,
        data={"triggers": [t.dict() for t in triggers]},
        message="Triggers retrieved"
    )


@router.get("/status", response_model=Dict[str, bool])
async def get_parametric_status(
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """
    Get parametric oracle configuration status.
    
    Returns:
        Dictionary mapping oracle source names to configuration status
    """
    monitor = get_parametric_monitor()
    
    return {
        "weather_oracle": monitor.is_oracle_configured("weather"),
        "port_oracle": monitor.is_oracle_configured("port"),
        "natcat_oracle": monitor.is_oracle_configured("natcat"),
        "ais_oracle": monitor.is_oracle_configured("ais"),
    }


@router.get("/weather/{location}", response_model=Dict[str, Any])
async def get_weather(
    location: str,
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """
    Get weather data for a location.
    
    Returns:
        Weather data dictionary
        
    Raises:
        503 Service Unavailable: If weather oracle is not configured
        500 Internal Server Error: If fetch operation fails
    """
    monitor = get_parametric_monitor()
    
    try:
        query = OracleQuery(
            location=location,
            timestamp=None,  # Current time
            parameters={"trigger_type": "weather"}
        )
        
        payload = await monitor.oracle_gateway.fetch("weather", query)
        return payload.payload
        
    except OracleNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except OracleFetchError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/port/{port_code}", response_model=Dict[str, Any])
async def get_port_congestion(
    port_code: str,
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """
    Get port congestion data for a port.
    
    Returns:
        Port congestion data dictionary
        
    Raises:
        503 Service Unavailable: If port oracle is not configured
        500 Internal Server Error: If fetch operation fails
    """
    monitor = get_parametric_monitor()
    
    try:
        query = OracleQuery(
            location=port_code,
            timestamp=None,  # Current time
            parameters={"trigger_type": "port_congestion"}
        )
        
        payload = await monitor.oracle_gateway.fetch("port", query)
        return payload.payload
        
    except OracleNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except OracleFetchError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/natcat/{location}", response_model=Dict[str, Any])
async def get_catastrophe_data(
    location: str,
    current_user = Depends(require_user),
    tenant_id: str = Depends(require_tenant)
):
    """
    Get catastrophe data for a location.
    
    Returns:
        Catastrophe data dictionary
        
    Raises:
        503 Service Unavailable: If natcat oracle is not configured
        500 Internal Server Error: If fetch operation fails
    """
    monitor = get_parametric_monitor()
    
    try:
        query = OracleQuery(
            location=location,
            timestamp=None,  # Current time
            parameters={"trigger_type": "natcat"}
        )
        
        payload = await monitor.oracle_gateway.fetch("natcat", query)
        return payload.payload
        
    except OracleNotConfiguredError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except OracleFetchError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
