"""
Premium allocation API endpoints.

Manages multi-party premium splits.
"""

from typing import Optional, List, Dict, Any
from datetime import date
from fastapi import APIRouter, Depends, Query, Body, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.dependencies import TenantContext, resolve_tenant_context
from app.api.deps.rbac import PermissionChecker
from app.services.premium_allocation_service import (
    PremiumAllocationService,
    PolicyNotFoundError,
    NoAllocationRuleError,
    InvalidAllocationError,
    AllocationNotFoundError
)
from app.core.audit_ledger.ledger import AuditLedger

router = APIRouter(prefix="/premium-allocations", tags=["Premium Allocations"])


def get_premium_allocation_service(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(resolve_tenant_context)
) -> PremiumAllocationService:
    """Dependency to get PremiumAllocationService."""
    audit = AuditLedger(db)
    return PremiumAllocationService(db, audit)


@router.post("/rules")
async def create_allocation_rule(
    name: str = Body(..., description="Rule name"),
    allocations: List[Dict[str, Any]] = Body(..., description="List of party allocations"),
    effective_from: date = Body(..., description="Effective start date"),
    scope_type: Optional[str] = Body(None, description="Scope type: CORRIDOR, PRODUCT, CARRIER, DEFAULT"),
    scope_id: Optional[str] = Body(None, description="Scope ID (corridor_id, product_id, etc.)"),
    effective_to: Optional[date] = Body(None, description="Optional effective end date"),
    description: Optional[str] = Body(None, description="Optional description"),
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:write"))
) -> dict:
    """
    Create a premium allocation rule.
    
    Defines how premiums should be split among parties.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    if not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
    
    try:
        rule = service.create_allocation_rule(
            tenant_id=tenant_id,
            name=name,
            allocations=allocations,
            effective_from=effective_from,
            created_by=context.user_id,
            scope_type=scope_type,
            scope_id=scope_id,
            effective_to=effective_to,
            description=description
        )
        
        return {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "status": rule.status,
            "scope_type": rule.scope_type,
            "scope_id": rule.scope_id,
            "allocations": rule.allocations_json,
            "effective_from": rule.effective_from.isoformat(),
            "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
            "created_at": rule.created_at.isoformat()
        }
    except InvalidAllocationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/rules")
async def list_allocation_rules(
    scope_type: Optional[str] = Query(None, description="Filter by scope type"),
    scope_id: Optional[str] = Query(None, description="Filter by scope ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:read"))
) -> List[dict]:
    """
    List premium allocation rules.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    from app.models.premium_allocation import PremiumAllocationRule
    from sqlalchemy import and_
    
    query = service.db.query(PremiumAllocationRule).filter(
        PremiumAllocationRule.tenant_id == tenant_id
    )
    
    if scope_type:
        query = query.filter(PremiumAllocationRule.scope_type == scope_type)
    if scope_id:
        query = query.filter(PremiumAllocationRule.scope_id == scope_id)
    if status_filter:
        query = query.filter(PremiumAllocationRule.status == status_filter)
    
    rules = query.order_by(PremiumAllocationRule.created_at.desc()).all()
    
    return [
        {
            "id": rule.id,
            "name": rule.name,
            "description": rule.description,
            "status": rule.status,
            "scope_type": rule.scope_type,
            "scope_id": rule.scope_id,
            "allocations": rule.allocations_json,
            "effective_from": rule.effective_from.isoformat(),
            "effective_to": rule.effective_to.isoformat() if rule.effective_to else None,
            "created_at": rule.created_at.isoformat()
        }
        for rule in rules
    ]


@router.post("/allocate/{policy_id}")
async def allocate_policy_premium(
    policy_id: str,
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:write"))
) -> dict:
    """
    Allocate premium for a policy.
    
    Finds applicable rule and creates allocation record.
    """
    if not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
    
    try:
        allocation = service.allocate_premium(
            policy_id=policy_id,
            allocated_by=context.user_id
        )
        
        return {
            "id": allocation.id,
            "policy_id": allocation.policy_id,
            "rule_id": allocation.rule_id,
            "total_premium_cents": allocation.total_premium_cents,
            "currency": allocation.currency,
            "allocations": allocation.allocations_json,
            "status": allocation.status,
            "allocated_at": allocation.allocated_at.isoformat()
        }
    except PolicyNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except NoAllocationRuleError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/allocations")
async def list_allocations(
    policy_id: Optional[str] = Query(None, description="Filter by policy ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:read"))
) -> List[dict]:
    """
    List premium allocations.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    from app.models.premium_allocation import PremiumAllocation
    
    query = service.db.query(PremiumAllocation).filter(
        PremiumAllocation.tenant_id == tenant_id
    )
    
    if policy_id:
        query = query.filter(PremiumAllocation.policy_id == policy_id)
    if status_filter:
        query = query.filter(PremiumAllocation.status == status_filter)
    
    allocations = query.order_by(PremiumAllocation.allocated_at.desc()).all()
    
    return [
        {
            "id": alloc.id,
            "policy_id": alloc.policy_id,
            "rule_id": alloc.rule_id,
            "total_premium_cents": alloc.total_premium_cents,
            "currency": alloc.currency,
            "allocations": alloc.allocations_json,
            "status": alloc.status,
            "settlements": alloc.settlements_json or [],
            "allocated_at": alloc.allocated_at.isoformat(),
            "settled_at": alloc.settled_at.isoformat() if alloc.settled_at else None
        }
        for alloc in allocations
    ]


@router.get("/allocations/{allocation_id}")
async def get_allocation(
    allocation_id: str,
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:read"))
) -> dict:
    """
    Get premium allocation details.
    """
    try:
        allocation = service._get_allocation(allocation_id)
        
        # Check tenant access
        tenant_id = context.tenant_id or context.user_id
        if allocation.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "id": allocation.id,
            "policy_id": allocation.policy_id,
            "rule_id": allocation.rule_id,
            "total_premium_cents": allocation.total_premium_cents,
            "currency": allocation.currency,
            "allocations": allocation.allocations_json,
            "status": allocation.status,
            "settlements": allocation.settlements_json or [],
            "allocated_at": allocation.allocated_at.isoformat(),
            "settled_at": allocation.settled_at.isoformat() if allocation.settled_at else None
        }
    except AllocationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/allocations/{allocation_id}/settlements")
async def record_settlement(
    allocation_id: str,
    party_id: str = Body(..., description="Party ID receiving payment"),
    amount_cents: int = Body(..., description="Amount in cents"),
    reference: str = Body(..., description="Settlement reference"),
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:write"))
) -> dict:
    """
    Record a settlement payment for an allocation.
    """
    if not context.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User authentication required"
        )
    
    try:
        allocation = service.record_settlement(
            allocation_id=allocation_id,
            party_id=party_id,
            amount_cents=amount_cents,
            reference=reference,
            settled_by=context.user_id
        )
        
        return {
            "id": allocation.id,
            "status": allocation.status,
            "settlements": allocation.settlements_json or [],
            "settled_at": allocation.settled_at.isoformat() if allocation.settled_at else None
        }
    except AllocationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/statements/{party_id}")
async def get_party_statement(
    party_id: str,
    start_date: date = Query(..., description="Statement start date"),
    end_date: date = Query(..., description="Statement end date"),
    service: PremiumAllocationService = Depends(get_premium_allocation_service),
    context: TenantContext = Depends(resolve_tenant_context),
    _: None = Depends(PermissionChecker("premium:read"))
) -> dict:
    """
    Generate statement for a party showing their allocations.
    """
    tenant_id = context.tenant_id or context.user_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required"
        )
    
    return service.get_party_statement(
        tenant_id=tenant_id,
        party_id=party_id,
        start_date=start_date,
        end_date=end_date
    )
