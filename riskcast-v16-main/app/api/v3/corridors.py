"""
Corridor intelligence API endpoints.

Corridors, benchmarks, ports, and carriers.
"""

from typing import Optional, List, Dict, Any
from datetime import date, datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Body, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.corridor_service import (
    CorridorService,
    CorridorNotFoundError,
    CorridorExistsError,
    BenchmarkNotFoundError
)
from app.services.corridor_intelligence_service import (
    CorridorIntelligenceService,
    CorridorNotFoundError as IntelligenceCorridorNotFoundError,
    CorridorExistsError as IntelligenceCorridorExistsError,
    BenchmarkNotFoundError as IntelligenceBenchmarkNotFoundError,
    NoBenchmarkError,
    PortNotFoundError,
    CarrierNotFoundError
)
from app.services.data_feed_service import DataFeedService
from app.core.audit_ledger.ledger import AuditLedger
from app.schemas.corridor import (
    CorridorResponse,
    CorridorDetailResponse,
    CorridorCreateRequest,
    BenchmarkResponse,
    BenchmarkPublishRequest,
    BenchmarkComparisonResponse,
    PortIntelligenceResponse,
    CarrierProfileResponse,
    CorridorRiskInputResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/corridors", tags=["Corridor Intelligence"])


def get_corridor_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> CorridorService:
    """Dependency to get CorridorService."""
    audit = AuditLedger(db)
    return CorridorService(db, audit)


def get_corridor_intelligence_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> CorridorIntelligenceService:
    """Dependency to get CorridorIntelligenceService."""
    audit = AuditLedger(db)
    return CorridorIntelligenceService(db, audit)


def get_data_feed_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> DataFeedService:
    """Dependency to get DataFeedService."""
    from app.services.oracle_event_service import OracleEventService
    
    audit = AuditLedger(db)
    corridor_service = CorridorIntelligenceService(db, audit)
    oracle_service = OracleEventService(db, audit)
    return DataFeedService(db, corridor_service, oracle_service, audit)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_corridor(
    request: CorridorCreateRequest,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:write"))
) -> CorridorResponse:
    """
    Create a new corridor.
    """
    created_by = context.user_id or context.actor_id
    
    if not created_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        corridor = service.create_corridor(
            corridor_code=request.corridor_code,
            name=request.name,
            origin_port_code=request.origin_port_code,
            destination_port_code=request.destination_port_code,
            created_by=created_by,
            description=request.description,
            origin_port_name=request.origin_port_name,
            origin_country=request.origin_country,
            origin_coordinates=request.origin_coordinates,
            destination_port_name=request.destination_port_name,
            destination_country=request.destination_country,
            destination_coordinates=request.destination_coordinates,
            distance_nm=request.distance_nm,
            typical_transit_days=request.typical_transit_days,
            route_type=request.route_type,
            transshipment_ports=request.transshipment_ports,
            trade_lane=request.trade_lane,
            region=request.region,
            cargo_types=request.cargo_types
        )
        return CorridorResponse.model_validate(corridor)
    except IntelligenceCorridorExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))




@router.get("")
async def list_corridors(
    trade_lane: Optional[str] = Query(None),
    origin_country: Optional[str] = Query(None),
    destination_country: Optional[str] = Query(None),
    status: str = Query("ACTIVE", description="Filter by status"),
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> List[CorridorResponse]:
    """
    List corridors with optional filters.
    """
    corridors = service.list_corridors(
        trade_lane=trade_lane,
        origin_country=origin_country,
        destination_country=destination_country,
        status=status
    )
    return [CorridorResponse.model_validate(c) for c in corridors]


@router.get("/search")
async def search_corridor(
    origin_port: str = Query(..., description="Origin port code"),
    destination_port: str = Query(..., description="Destination port code"),
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> Optional[CorridorResponse]:
    """
    Search for corridor by origin/destination ports.
    """
    corridor = service.find_corridor(origin_port, destination_port)
    return CorridorResponse.model_validate(corridor) if corridor else None


@router.get("/{corridor_id}")
async def get_corridor(
    corridor_id: str,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> CorridorDetailResponse:
    """
    Get corridor details including current benchmark.
    """
    try:
        corridor = service.get_corridor(corridor_id)
        benchmark = service.get_current_benchmark(corridor_id)
        return CorridorDetailResponse(
            corridor=CorridorResponse.model_validate(corridor),
            current_benchmark=BenchmarkResponse.model_validate(benchmark) if benchmark else None
        )
    except IntelligenceCorridorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))




@router.get("/ports/{port_code}")
async def get_port_intelligence(
    port_code: str,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> PortIntelligenceResponse:
    """
    Get port intelligence.
    """
    try:
        port = service.get_port_intelligence(port_code)
        # Map JSON fields to response
        port_dict = {
            "id": port.id,
            "port_code": port.port_code,
            "port_name": port.port_name,
            "country": port.country,
            "region": port.region,
            "coordinates": port.coordinates,
            "port_type": port.port_type,
            "size_class": port.size_class,
            "annual_teu_capacity": port.annual_teu_capacity,
            "current_conditions": port.current_conditions_json,
            "risk_factors": port.risk_factors_json,
            "created_at": port.created_at,
            "updated_at": port.updated_at
        }
        return PortIntelligenceResponse(**port_dict)
    except PortNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/carriers/{carrier_code}")
async def get_carrier_profile(
    carrier_code: str,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> CarrierProfileResponse:
    """
    Get carrier profile.
    """
    try:
        carrier = service.get_carrier_profile(carrier_code)
        carrier_dict = {
            "id": carrier.id,
            "carrier_code": carrier.carrier_code,
            "carrier_name": carrier.carrier_name,
            "carrier_type": carrier.carrier_type,
            "global_metrics": carrier.global_metrics_json,
            "service_quality": carrier.service_quality_json,
            "created_at": carrier.created_at,
            "updated_at": carrier.updated_at
        }
        return CarrierProfileResponse(**carrier_dict)
    except CarrierNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/carriers/{carrier_code}/corridors/{corridor_id}/performance")
async def get_carrier_corridor_performance(
    carrier_code: str,
    corridor_id: str,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> Optional[dict]:
    """
    Get carrier performance on specific corridor.
    """
    performance = service.get_carrier_corridor_performance(carrier_code, corridor_id)
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No performance data for carrier {carrier_code} on corridor {corridor_id}"
        )
    return {"carrier_code": carrier_code, "corridor_id": corridor_id, "performance": performance}


# ==================== Intelligence Service Endpoints ====================

@router.post("/{corridor_id}/benchmarks", status_code=status.HTTP_201_CREATED)
async def publish_benchmark(
    corridor_id: str,
    request: BenchmarkPublishRequest,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:benchmark"))
) -> BenchmarkResponse:
    """
    Publish a new benchmark version for a corridor.
    """
    published_by = context.user_id or context.actor_id
    
    if not published_by:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User context required"
        )
    
    try:
        benchmark = service.publish_benchmark(
            corridor_id=corridor_id,
            delay_metrics=request.delay_metrics.model_dump(exclude_none=True),
            risk_metrics=request.risk_metrics.model_dump(exclude_none=True),
            effective_from=request.effective_from,
            published_by=published_by,
            carrier_performance=request.carrier_performance,
            seasonal_factors=request.seasonal_factors,
            cost_benchmarks=request.cost_benchmarks.model_dump(exclude_none=True) if request.cost_benchmarks else None,
            data_source=request.data_source,
            data_period_start=request.data_period_start,
            data_period_end=request.data_period_end,
            sample_size=request.sample_size
        )
        return BenchmarkResponse.model_validate(benchmark)
    except IntelligenceCorridorNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{corridor_id}/benchmarks/current")
async def get_current_benchmark(
    corridor_id: str,
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> BenchmarkResponse:
    """
    Get the current active benchmark for a corridor.
    """
    benchmark = service.get_current_benchmark(corridor_id)
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No benchmark available"
        )
    return BenchmarkResponse.model_validate(benchmark)


@router.get("/{corridor_id}/benchmarks/as-of")
async def get_benchmark_as_of(
    corridor_id: str,
    as_of_date: date = Query(..., description="Date to get benchmark for"),
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> BenchmarkResponse:
    """
    Get benchmark that was effective on a given date.
    """
    benchmark = service.get_benchmark_as_of(corridor_id, as_of_date)
    if not benchmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No benchmark available for date {as_of_date}"
        )
    return BenchmarkResponse.model_validate(benchmark)


@router.get("/{corridor_id}/benchmarks/history")
async def get_benchmark_history(
    corridor_id: str,
    limit: int = Query(10, ge=1, le=50, description="Maximum number of versions to return"),
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> List[BenchmarkResponse]:
    """
    Get benchmark version history for a corridor.
    """
    benchmarks = service.get_benchmark_history(corridor_id, limit)
    return [BenchmarkResponse.model_validate(b) for b in benchmarks]


@router.get("/benchmarks/compare")
async def compare_benchmarks(
    benchmark_id_1: str = Query(..., description="First benchmark ID"),
    benchmark_id_2: str = Query(..., description="Second benchmark ID"),
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> BenchmarkComparisonResponse:
    """
    Compare two benchmark versions.
    """
    try:
        comparison = service.compare_benchmarks(benchmark_id_1, benchmark_id_2)
        return BenchmarkComparisonResponse(**comparison)
    except IntelligenceBenchmarkNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{corridor_id}/risk-inputs")
async def get_corridor_risk_inputs(
    corridor_id: str,
    carrier_code: Optional[str] = Query(None, description="Optional carrier code for carrier-specific performance"),
    as_of_date: Optional[date] = Query(None, description="Optional date to get historical benchmark"),
    service: CorridorIntelligenceService = Depends(get_corridor_intelligence_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:read"))
) -> CorridorRiskInputResponse:
    """
    Get corridor data formatted for risk engine.
    
    This is the primary integration point for risk assessment.
    """
    try:
        inputs = service.get_corridor_risk_inputs(
            corridor_id=corridor_id,
            carrier_code=carrier_code,
            as_of_date=as_of_date
        )
        return CorridorRiskInputResponse(**inputs)
    except (IntelligenceCorridorNotFoundError, NoBenchmarkError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==================== Data Feed Endpoints ====================

@router.post("/data-feeds/ingest", status_code=status.HTTP_200_OK)
async def trigger_data_feed_ingestion(
    feed_type: Optional[str] = Query(None, description="Type: port_congestion, carrier_reliability, corridor_delays, or all"),
    port_codes: Optional[List[str]] = Query(None, description="Specific port codes (optional)"),
    carrier_codes: Optional[List[str]] = Query(None, description="Specific carrier codes (optional)"),
    service: DataFeedService = Depends(get_data_feed_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("corridor:write"))
) -> dict:
    """
    Trigger data feed ingestion manually.
    
    Can ingest specific feed types or all feeds.
    """
    from app.services.data_feed_service import (
        MarineTrafficProvider,
        Project44Provider
    )
    from app.config import settings
    
    # Register providers
    marine_traffic_key = (
        getattr(settings, 'MARINE_TRAFFIC_API_KEY', None) or
        getattr(settings, 'MARINETRAFFIC_API_KEY', None)
    )
    
    if marine_traffic_key:
        service.register_provider(MarineTrafficProvider(marine_traffic_key))
    
    if hasattr(settings, 'PROJECT44_API_KEY') and settings.PROJECT44_API_KEY:
        service.register_provider(Project44Provider(settings.PROJECT44_API_KEY))
    
    if not service.providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data feed providers configured"
        )
    
    results = {
        "started_at": datetime.utcnow().isoformat()
    }
    
    try:
        if feed_type is None or feed_type == "all":
            # Run all ingestion
            results = service.run_scheduled_ingestion()
        elif feed_type == "port_congestion":
            results["port_congestion"] = service.ingest_port_congestion(port_codes=port_codes)
        elif feed_type == "carrier_reliability":
            results["carrier_reliability"] = service.ingest_carrier_reliability(carrier_codes=carrier_codes)
        elif feed_type == "corridor_delays":
            results["corridor_delays"] = service.ingest_corridor_delays()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feed_type: {feed_type}. Must be: port_congestion, carrier_reliability, corridor_delays, or all"
            )
        
        results["completed_at"] = datetime.utcnow().isoformat()
        return results
        
    except Exception as e:
        logger.error(f"Data feed ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Data feed ingestion failed: {str(e)}"
        )
