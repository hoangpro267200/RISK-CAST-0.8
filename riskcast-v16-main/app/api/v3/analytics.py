"""
Analytics API endpoints.

Loss ratio reports, model performance, and aggregations.
"""

from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.loss_analytics_service import LossAnalyticsService
from app.services.roi_reporting_service import ROIReportingService
from app.services.network_benchmarking_service import NetworkBenchmarkingService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_loss_analytics_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> LossAnalyticsService:
    """Dependency to get LossAnalyticsService."""
    return LossAnalyticsService(db)


def get_roi_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> ROIReportingService:
    """Dependency to get ROIReportingService."""
    loss_analytics = LossAnalyticsService(db)
    return ROIReportingService(db, loss_analytics)


def get_network_benchmarking_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> NetworkBenchmarkingService:
    """Dependency to get NetworkBenchmarkingService."""
    return NetworkBenchmarkingService(db)


@router.get("/loss-ratio")
async def get_loss_ratio(
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    corridor_id: Optional[str] = Query(None, description="Filter by corridor ID"),
    carrier_id: Optional[str] = Query(None, description="Filter by carrier ID"),
    cargo_type: Optional[str] = Query(None, description="Filter by cargo type"),
    model_version_id: Optional[str] = Query(None, description="Filter by model version ID"),
    service: LossAnalyticsService = Depends(get_loss_analytics_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Get loss ratio metrics.
    
    Returns loss ratio, expected loss ratio, and related metrics
    for the specified period and filters.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_loss_ratio(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        corridor_id=corridor_id,
        carrier_id=carrier_id,
        cargo_type=cargo_type,
        model_version_id=model_version_id
    )


@router.get("/loss-ratio/report")
async def get_loss_ratio_report(
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    dimensions: List[str] = Query(
        default=['corridor', 'cargo_type'],
        description="Dimensions to include in breakdown"
    ),
    service: LossAnalyticsService = Depends(get_loss_analytics_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Get comprehensive loss ratio report.
    
    Returns overall metrics plus breakdowns by specified dimensions.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_loss_ratio_report(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        include_dimensions=dimensions
    )


@router.get("/model-performance/{model_version_id}")
async def get_model_performance(
    model_version_id: str,
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: LossAnalyticsService = Depends(get_loss_analytics_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Get model performance metrics.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_model_performance(
        tenant_id=tenant_id,
        model_version_id=model_version_id,
        start_date=start_date,
        end_date=end_date
    )


# ==================== ROI Reporting ====================

@router.get("/roi/portfolio")
async def get_portfolio_roi(
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: ROIReportingService = Depends(get_roi_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Generate portfolio-level ROI report.
    
    Shows overall financial performance including profitability and model accuracy.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_portfolio_roi_report(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/roi/corridor/{corridor_id}")
async def get_corridor_roi(
    corridor_id: str,
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: ROIReportingService = Depends(get_roi_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Generate ROI report for a specific corridor.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_corridor_roi_report(
        tenant_id=tenant_id,
        corridor_id=corridor_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/roi/model/{model_version_id}")
async def get_model_roi(
    model_version_id: str,
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: ROIReportingService = Depends(get_roi_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Generate ROI report for a specific model version.
    
    Shows value added vs naive baseline model.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_model_roi_report(
        tenant_id=tenant_id,
        model_version_id=model_version_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/roi/trend")
async def get_roi_trend(
    months: int = Query(12, ge=1, le=36, description="Number of months to analyze"),
    service: ROIReportingService = Depends(get_roi_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Generate trend report over time.
    
    Shows monthly trends in loss ratio and profitability.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_trend_report(
        tenant_id=tenant_id,
        months=months
    )


@router.get("/roi/comparative")
async def get_comparative_roi(
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    dimensions: List[str] = Query(
        default=['corridor', 'cargo_type'],
        description="Dimensions to compare: corridor, cargo_type, model_version"
    ),
    service: ROIReportingService = Depends(get_roi_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Generate comparative ROI report across dimensions.
    
    Compares performance across corridors, cargo types, or model versions.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_comparative_roi_report(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        compare_dimensions=dimensions
    )


# ==================== Network Benchmarking ====================

@router.get("/benchmark/network")
async def get_network_benchmark(
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: NetworkBenchmarkingService = Depends(get_network_benchmarking_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Generate network benchmark report comparing tenant to network.
    
    Provides anonymized comparison with percentile rankings.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.generate_tenant_benchmark_report(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/benchmark/corridor/{corridor_id}")
async def get_corridor_benchmark(
    corridor_id: str,
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: NetworkBenchmarkingService = Depends(get_network_benchmarking_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Compare tenant performance on a specific corridor to benchmark.
    
    Uses corridor benchmarks for comparison.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_corridor_comparison(
        tenant_id=tenant_id,
        corridor_id=corridor_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/benchmark/network-summary")
async def get_network_summary(
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: NetworkBenchmarkingService = Depends(get_network_benchmarking_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Get anonymized network summary statistics.
    
    Provides aggregate insights without exposing individual tenant data.
    """
    return service.get_network_summary(
        start_date=start_date,
        end_date=end_date
    )
    """
    Get model performance report.
    
    Returns model calibration metrics, accuracy analysis, and recommendations
    for the specified model version and period.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_model_performance_report(
        tenant_id=tenant_id,
        model_version_id=model_version_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/loss-ratio/by-dimension")
async def get_loss_ratio_by_dimension(
    dimension: str = Query(..., description="Dimension to group by (corridor, carrier, cargo_type, coverage_type, model_version)"),
    start_date: date = Query(..., description="Start date for period"),
    end_date: date = Query(..., description="End date for period"),
    service: LossAnalyticsService = Depends(get_loss_analytics_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> List[dict]:
    """
    Get loss ratios broken down by a specific dimension.
    
    Returns list of metrics grouped by dimension value.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_loss_ratio_by_dimension(
        tenant_id=tenant_id,
        start_date=start_date,
        end_date=end_date,
        dimension=dimension
    )


@router.get("/loss-development/{policy_id}")
async def get_loss_development(
    policy_id: str,
    service: LossAnalyticsService = Depends(get_loss_analytics_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("analytics:read"))
) -> dict:
    """
    Get loss development for a specific policy.
    
    Shows how loss estimate evolved over time.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_loss_development(
        tenant_id=tenant_id,
        policy_id=policy_id
    )
