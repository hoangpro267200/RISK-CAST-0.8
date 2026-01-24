"""
Premium allocation service.

Manages multi-party premium splits.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
import logging

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.premium_allocation import PremiumAllocationRule, PremiumAllocation
from app.core.audit_ledger.ledger import AuditLedger
from app.shared.utils import generate_ulid

logger = logging.getLogger(__name__)


class PremiumAllocationService:
    """Service for premium allocation."""
    
    def __init__(self, db: Session, audit: Optional[AuditLedger] = None):
        """
        Initialize premium allocation service.
        
        Args:
            db: Database session
            audit: Optional audit ledger
        """
        self.db = db
        self.audit = audit or AuditLedger(db)
    
    def create_allocation_rule(
        self,
        tenant_id: str,
        name: str,
        allocations: List[Dict[str, Any]],
        effective_from: date,
        created_by: str,
        scope_type: Optional[str] = None,
        scope_id: Optional[str] = None,
        effective_to: Optional[date] = None,
        description: Optional[str] = None
    ) -> PremiumAllocationRule:
        """
        Create a premium allocation rule.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            name: Rule name
            allocations: List of allocation dictionaries with party_type, party_id, share_pct, commission_pct
            effective_from: Effective start date
            created_by: User ID who created the rule
            scope_type: Scope type (CORRIDOR, PRODUCT, CARRIER, DEFAULT)
            scope_id: Scope ID (corridor_id, product_id, etc.)
            effective_to: Optional effective end date
            description: Optional description
            
        Returns:
            Created PremiumAllocationRule instance
            
        Raises:
            InvalidAllocationError: If allocations don't sum to 100%
        """
        # Validate allocations sum to 100%
        total_share = sum(a.get('share_pct', 0) for a in allocations)
        if abs(total_share - 100.0) > 0.01:
            raise InvalidAllocationError(f"Shares must sum to 100%, got {total_share}")
        
        rule = PremiumAllocationRule(
            id=generate_ulid(),
            tenant_id=tenant_id,
            name=name,
            description=description,
            status='ACTIVE',
            scope_type=scope_type,
            scope_id=scope_id,
            allocations_json=allocations,
            effective_from=effective_from,
            effective_to=effective_to,
            created_at=datetime.utcnow(),
            created_by_user_id=created_by
        )
        
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        
        # Audit
        self.audit.append_event(
            tenant_id=tenant_id,
            event_type="PREMIUM_ALLOCATION",
            action="RULE_CREATED",
            entity_type="premium_allocation_rule",
            entity_id=rule.id,
            actor_type="USER",
            actor_id=created_by,
            payload={
                "name": name,
                "scope_type": scope_type,
                "parties": [a.get('party_type') for a in allocations]
            }
        )
        
        logger.info(f"Created premium allocation rule {rule.id} for tenant {tenant_id}")
        return rule
    
    def allocate_premium(
        self,
        policy_id: str,
        allocated_by: Optional[str] = None
    ) -> PremiumAllocation:
        """
        Allocate premium for a policy.
        
        Finds applicable rule and creates allocation record.
        
        Args:
            policy_id: Policy ID (ULID string)
            allocated_by: Optional user ID who triggered allocation
            
        Returns:
            Created PremiumAllocation instance
            
        Raises:
            PolicyNotFoundError: If policy not found
            NoAllocationRuleError: If no applicable rule found
        """
        try:
            from app.modules.underwriting.models import Policy
        except ImportError:
            raise PolicyNotFoundError("Policy model not available")
        
        policy = self.db.query(Policy).filter(Policy.id == policy_id).first()
        if not policy:
            raise PolicyNotFoundError(f"Policy {policy_id} not found")
        
        # Find applicable rule
        # Convert effective_from to date if it's a datetime
        if hasattr(policy.effective_from, 'date'):
            as_of_date = policy.effective_from.date()
        elif isinstance(policy.effective_from, date):
            as_of_date = policy.effective_from
        else:
            # Try to parse if it's a string
            from datetime import datetime as dt
            if isinstance(policy.effective_from, str):
                as_of_date = dt.fromisoformat(policy.effective_from.replace('Z', '+00:00')).date()
            else:
                as_of_date = date.today()
        
        rule = self._find_applicable_rule(
            tenant_id=policy.tenant_id,
            corridor_id=getattr(policy, 'corridor_id', None),
            as_of_date=as_of_date
        )
        
        if not rule:
            raise NoAllocationRuleError("No allocation rule found for this policy")
        
        # Calculate allocations
        premium_json = getattr(policy, 'premium_json', None) or {}
        total_premium = premium_json.get('total_premium_cents', 0)
        if total_premium == 0:
            # Try alternative field names
            total_premium = premium_json.get('total_premium', 0)
            if isinstance(total_premium, float):
                total_premium = int(total_premium * 100)  # Convert to cents
        
        currency = premium_json.get('currency', 'USD')
        
        allocations = []
        for party in rule.allocations_json:
            share_pct = party.get('share_pct', 0)
            commission_pct = party.get('commission_pct', 0)
            
            premium_share = int(total_premium * share_pct / 100)
            commission = int(total_premium * commission_pct / 100)
            net_amount = premium_share - commission
            
            allocations.append({
                "party_type": party.get('party_type'),
                "party_id": party.get('party_id'),
                "party_name": party.get('party_name', ''),
                "share_pct": share_pct,
                "commission_pct": commission_pct,
                "premium_share_cents": premium_share,
                "commission_cents": commission,
                "net_amount_cents": net_amount
            })
        
        # Create allocation record
        allocation = PremiumAllocation(
            id=generate_ulid(),
            tenant_id=policy.tenant_id,
            policy_id=policy_id,
            rule_id=rule.id,
            total_premium_cents=total_premium,
            currency=currency,
            allocations_json=allocations,
            status='ALLOCATED',
            allocated_at=datetime.utcnow()
        )
        
        self.db.add(allocation)
        self.db.commit()
        self.db.refresh(allocation)
        
        # Audit
        self.audit.append_event(
            tenant_id=policy.tenant_id,
            event_type="PREMIUM_ALLOCATION",
            action="ALLOCATED",
            entity_type="premium_allocation",
            entity_id=allocation.id,
            actor_type="USER" if allocated_by else "SYSTEM",
            actor_id=allocated_by,
            payload={
                "policy_id": policy_id,
                "rule_id": rule.id,
                "total_premium_cents": total_premium,
                "parties_count": len(allocations)
            }
        )
        
        logger.info(f"Allocated premium for policy {policy_id}, total: {total_premium} cents")
        return allocation
    
    def record_settlement(
        self,
        allocation_id: str,
        party_id: str,
        amount_cents: int,
        reference: str,
        settled_by: str
    ) -> PremiumAllocation:
        """
        Record a settlement payment for an allocation.
        
        Args:
            allocation_id: Allocation ID (ULID string)
            party_id: Party ID receiving payment
            amount_cents: Amount in cents
            reference: Settlement reference (invoice, payment ID, etc.)
            settled_by: User ID recording settlement
            
        Returns:
            Updated PremiumAllocation instance
            
        Raises:
            AllocationNotFoundError: If allocation not found
        """
        allocation = self._get_allocation(allocation_id)
        
        settlements = allocation.settlements_json or []
        settlements.append({
            "party_id": party_id,
            "amount_cents": amount_cents,
            "reference": reference,
            "settled_at": datetime.utcnow().isoformat(),
            "settled_by": settled_by
        })
        
        allocation.settlements_json = settlements
        
        # Check if fully settled
        expected = {
            a['party_id']: a['net_amount_cents']
            for a in allocation.allocations_json
            if a.get('party_id')
        }
        settled = {}
        for s in settlements:
            party = s['party_id']
            settled[party] = settled.get(party, 0) + s['amount_cents']
        
        # Check if all parties are fully settled
        if all(settled.get(p, 0) >= amt for p, amt in expected.items()):
            allocation.status = 'SETTLED'
            allocation.settled_at = datetime.utcnow()
            
            # Audit settlement completion
            self.audit.append_event(
                tenant_id=allocation.tenant_id,
                event_type="PREMIUM_ALLOCATION",
                action="SETTLED",
                entity_type="premium_allocation",
                entity_id=allocation.id,
                actor_type="USER",
                actor_id=settled_by,
                payload={
                    "policy_id": allocation.policy_id,
                    "total_settled_cents": sum(settled.values())
                }
            )
        
        self.db.commit()
        self.db.refresh(allocation)
        
        logger.info(f"Recorded settlement for allocation {allocation_id}, party {party_id}, amount {amount_cents} cents")
        return allocation
    
    def get_party_statement(
        self,
        tenant_id: str,
        party_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """
        Generate statement for a party showing their allocations.
        
        Args:
            tenant_id: Tenant ID (ULID string)
            party_id: Party ID to generate statement for
            start_date: Statement start date
            end_date: Statement end date
            
        Returns:
            Dictionary with party statement
        """
        allocations = self.db.query(PremiumAllocation).filter(
            PremiumAllocation.tenant_id == tenant_id,
            PremiumAllocation.allocated_at >= datetime.combine(start_date, datetime.min.time()),
            PremiumAllocation.allocated_at <= datetime.combine(end_date, datetime.max.time())
        ).all()
        
        party_allocations = []
        total_share = 0
        total_commission = 0
        total_net = 0
        total_settled = 0
        
        for alloc in allocations:
            for party_alloc in alloc.allocations_json:
                if party_alloc.get('party_id') == party_id:
                    premium_share = party_alloc.get('premium_share_cents', 0)
                    commission = party_alloc.get('commission_cents', 0)
                    net_amount = party_alloc.get('net_amount_cents', 0)
                    
                    # Calculate settled amount for this party
                    settled_amount = 0
                    if alloc.settlements_json:
                        for s in alloc.settlements_json:
                            if s.get('party_id') == party_id:
                                settled_amount += s.get('amount_cents', 0)
                    
                    party_allocations.append({
                        "policy_id": alloc.policy_id,
                        "allocation_id": alloc.id,
                        "allocated_at": alloc.allocated_at.isoformat(),
                        "total_premium_cents": alloc.total_premium_cents,
                        "premium_share_cents": premium_share,
                        "commission_cents": commission,
                        "net_amount_cents": net_amount,
                        "settled_amount_cents": settled_amount,
                        "outstanding_cents": net_amount - settled_amount,
                        "status": alloc.status
                    })
                    total_share += premium_share
                    total_commission += commission
                    total_net += net_amount
                    total_settled += settled_amount
        
        return {
            "party_id": party_id,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "allocation_count": len(party_allocations),
                "total_premium_share_cents": total_share,
                "total_commission_cents": total_commission,
                "total_net_amount_cents": total_net,
                "total_settled_cents": total_settled,
                "total_outstanding_cents": total_net - total_settled
            },
            "allocations": party_allocations,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _find_applicable_rule(
        self,
        tenant_id: str,
        corridor_id: Optional[str],
        as_of_date: date
    ) -> Optional[PremiumAllocationRule]:
        """
        Find applicable allocation rule by priority.
        
        Priority: CORRIDOR > DEFAULT
        
        Args:
            tenant_id: Tenant ID (ULID string)
            corridor_id: Optional corridor ID
            as_of_date: Date to check rule effectiveness
            
        Returns:
            Applicable PremiumAllocationRule or None
        """
        # Try corridor-specific
        if corridor_id:
            rule = self.db.query(PremiumAllocationRule).filter(
                PremiumAllocationRule.tenant_id == tenant_id,
                PremiumAllocationRule.scope_type == 'CORRIDOR',
                PremiumAllocationRule.scope_id == corridor_id,
                PremiumAllocationRule.status == 'ACTIVE',
                PremiumAllocationRule.effective_from <= as_of_date,
                or_(
                    PremiumAllocationRule.effective_to.is_(None),
                    PremiumAllocationRule.effective_to >= as_of_date
                )
            ).first()
            
            if rule:
                return rule
        
        # Fall back to default
        return self.db.query(PremiumAllocationRule).filter(
            PremiumAllocationRule.tenant_id == tenant_id,
            PremiumAllocationRule.scope_type == 'DEFAULT',
            PremiumAllocationRule.status == 'ACTIVE',
            PremiumAllocationRule.effective_from <= as_of_date,
            or_(
                PremiumAllocationRule.effective_to.is_(None),
                PremiumAllocationRule.effective_to >= as_of_date
            )
        ).first()
    
    def _get_allocation(self, allocation_id: str) -> PremiumAllocation:
        """
        Get allocation by ID.
        
        Args:
            allocation_id: Allocation ID (ULID string)
            
        Returns:
            PremiumAllocation instance
            
        Raises:
            AllocationNotFoundError: If allocation not found
        """
        allocation = self.db.query(PremiumAllocation).filter(
            PremiumAllocation.id == allocation_id
        ).first()
        if not allocation:
            raise AllocationNotFoundError(f"Allocation {allocation_id} not found")
        return allocation


class PolicyNotFoundError(Exception):
    """Policy not found."""
    pass


class NoAllocationRuleError(Exception):
    """No allocation rule found."""
    pass


class InvalidAllocationError(Exception):
    """Invalid allocation configuration."""
    pass


class AllocationNotFoundError(Exception):
    """Allocation not found."""
    pass
