"""
Policy GraphQL Types
"""

import strawberry
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Annotated

from app.graphql.types.base import Node, Auditable, PolicyStatus, Connection, Edge, PageInfo

QuoteRef = Annotated["Quote", strawberry.lazy("app.graphql.types.quote")]
ClaimRef = Annotated["Claim", strawberry.lazy("app.graphql.types.claim")]
CustomerRef = Annotated["Customer", strawberry.lazy("app.graphql.types.customer")]


@strawberry.type
class PolicyCoverage:
    """Policy coverage details."""

    coverage_type: str
    coverage_limit: Decimal
    deductible: Decimal
    extensions: List[str]
    territories: List[str]
    conveyances: List[str]


@strawberry.type
class PolicyPremium:
    """Policy premium details."""

    total_premium: Decimal
    paid_premium: Decimal
    outstanding_premium: Decimal
    payment_status: str
    next_payment_date: Optional[date]


@strawberry.type
class Policy(Node, Auditable):
    """Policy type."""

    id: strawberry.ID
    policy_number: str
    status: PolicyStatus

    # Dates
    effective_from: date
    effective_to: date
    issue_date: date

    # Coverage
    coverage: PolicyCoverage

    # Premium
    premium: PolicyPremium

    # Shipment details
    cargo_type: str
    cargo_description: Optional[str]
    cargo_value_usd: Decimal
    origin_port: str
    destination_port: str

    # Carrier
    carrier_name: Optional[str]
    vessel_name: Optional[str]
    voyage_number: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    # Internal IDs for relationships
    customer_id: strawberry.Private[str]
    quote_id: strawberry.Private[Optional[str]]

    @strawberry.field
    async def customer(self, info: strawberry.Info) -> Optional[CustomerRef]:
        """Get the policy holder."""
        loader = info.context["dataloaders"].customer_loader
        return await loader.load(self.customer_id)

    @strawberry.field
    async def quote(self, info: strawberry.Info) -> Optional[QuoteRef]:
        """Get the originating quote."""
        if not self.quote_id:
            return None
        loader = info.context["dataloaders"].quote_loader
        return await loader.load(self.quote_id)

    @strawberry.field
    async def claims(self, info: strawberry.Info) -> List[ClaimRef]:
        """Get claims filed against this policy."""
        loader = info.context["dataloaders"].claims_by_policy_loader
        return await loader.load(str(self.id))

    @strawberry.field
    def days_remaining(self) -> int:
        """Days remaining until policy expiry."""
        today = date.today()
        if isinstance(self.effective_to, datetime):
            eff_to = self.effective_to.date()
        else:
            eff_to = self.effective_to
        if today > eff_to:
            return 0
        return (eff_to - today).days

    @strawberry.field
    def is_active(self) -> bool:
        """Check if policy is currently active."""
        today = date.today()
        if isinstance(self.effective_from, datetime):
            eff_from = self.effective_from.date()
        else:
            eff_from = self.effective_from
        if isinstance(self.effective_to, datetime):
            eff_to = self.effective_to.date()
        else:
            eff_to = self.effective_to
        return (
            self.status == PolicyStatus.ACTIVE
            and eff_from <= today <= eff_to
        )


@strawberry.type
class PolicyEdge:
    """Policy edge for pagination."""

    node: "Policy"  # self-reference, no cycle
    cursor: str


@strawberry.type
class PolicyConnection:
    """Paginated policies."""

    edges: List[PolicyEdge]
    page_info: PageInfo


# =============================================================================
# Input Types
# =============================================================================

@strawberry.input
class PolicyFilterInput:
    """Filter input for policies."""

    status: Optional[List[PolicyStatus]] = None
    cargo_type: Optional[str] = None
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    min_coverage: Optional[Decimal] = None
    max_coverage: Optional[Decimal] = None
    search: Optional[str] = None


@strawberry.input
class PolicyEndorsementInput:
    """Input for policy endorsement."""

    policy_id: strawberry.ID
    endorsement_type: str
    effective_date: date
    changes: str
    reason: str


# =============================================================================
# Mutation Results
# =============================================================================

@strawberry.type
class PolicyCancelSuccess:
    """Successful policy cancellation."""

    policy: Policy
    refund_amount: Decimal
    message: str


@strawberry.type
class PolicyEndorsementSuccess:
    """Successful policy endorsement."""

    policy: Policy
    endorsement_number: str
    premium_adjustment: Decimal
    message: str
