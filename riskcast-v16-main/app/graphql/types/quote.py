"""
Quote GraphQL Types
"""

import strawberry
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Annotated

from app.graphql.types.base import (
    Node,
    Auditable,
    QuoteStatus,
    RiskGrade,
    Connection,
    Edge,
    PageInfo,
    ValidationError,
    AuthenticationError,
    NotFoundError,
)

# Use lazy refs to avoid circular imports
PolicyRef = Annotated["Policy", strawberry.lazy("app.graphql.types.policy")]
CustomerRef = Annotated["Customer", strawberry.lazy("app.graphql.types.customer")]


@strawberry.type
class RiskBreakdown:
    """Risk score breakdown by category."""

    weather_risk: float
    port_risk: float
    cargo_risk: float
    route_risk: float
    carrier_risk: float
    overall_score: float
    risk_grade: RiskGrade


@strawberry.type
class PremiumBreakdown:
    """Premium calculation breakdown."""

    base_premium: Decimal
    risk_loading: Decimal
    war_risk_premium: Optional[Decimal]
    strikes_premium: Optional[Decimal]
    extensions_premium: Decimal
    discounts: Decimal
    taxes: Decimal
    total_premium: Decimal
    rate_per_mille: float


@strawberry.type
class CoverageDetails:
    """Coverage details for a quote."""

    coverage_type: str
    coverage_limit: Decimal
    deductible_amount: Decimal
    deductible_percentage: float
    extensions: List[str]
    exclusions: List[str]


@strawberry.type
class Quote(Node, Auditable):
    """Quote type."""

    id: strawberry.ID
    quote_number: str
    status: QuoteStatus

    # Cargo details
    cargo_type: str
    cargo_description: Optional[str]
    cargo_value_usd: Decimal
    container_count: int

    # Route details
    origin_port: str
    origin_port_name: Optional[str]
    destination_port: str
    destination_port_name: Optional[str]

    # Dates
    departure_date: Optional[datetime]
    arrival_date: Optional[datetime]
    valid_until: Optional[datetime]

    # Risk and pricing
    risk_breakdown: Optional[RiskBreakdown]
    premium_breakdown: Optional[PremiumBreakdown]
    coverage_details: Optional[CoverageDetails]

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    # Private: for dataloader resolution
    customer_id: strawberry.Private[str]

    @strawberry.field
    async def customer(self, info: strawberry.Info) -> Optional[CustomerRef]:
        """Get the customer who requested this quote."""
        loader = info.context["dataloaders"].customer_loader
        return await loader.load(self.customer_id)

    @strawberry.field
    async def policy(self, info: strawberry.Info) -> Optional[PolicyRef]:
        """Get the policy created from this quote (if accepted)."""
        if self.status != QuoteStatus.ACCEPTED:
            return None
        loader = info.context["dataloaders"].policy_by_quote_loader
        return await loader.load(str(self.id))


@strawberry.type
class QuoteEdge:
    """Quote edge for pagination."""

    node: Quote
    cursor: str


@strawberry.type
class QuoteConnection:
    """Paginated quotes."""

    edges: List[QuoteEdge]
    page_info: PageInfo


# =============================================================================
# Input Types
# =============================================================================

@strawberry.input
class QuoteRequestInput:
    """Input for requesting a new quote."""

    cargo_type: str
    cargo_description: Optional[str] = None
    cargo_value_usd: Decimal
    container_count: int = 1
    origin_port: str
    destination_port: str
    departure_date: Optional[datetime] = None
    coverage_type: str = "ALL_RISKS"
    coverage_extensions: Optional[List[str]] = None
    deductible_percentage: Optional[float] = None


@strawberry.input
class QuoteFilterInput:
    """Filter input for quotes."""

    status: Optional[List[QuoteStatus]] = None
    cargo_type: Optional[str] = None
    origin_port: Optional[str] = None
    destination_port: Optional[str] = None
    min_value: Optional[Decimal] = None
    max_value: Optional[Decimal] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


@strawberry.input
class QuoteSortInput:
    """Sort input for quotes."""

    field: str = "created_at"
    direction: str = "DESC"


# =============================================================================
# Mutation Results
# =============================================================================

@strawberry.type
class QuoteRequestSuccess:
    """Successful quote request result."""

    quote: Quote
    message: str


@strawberry.type
class QuoteAcceptSuccess:
    """Successful quote acceptance result."""

    quote: Quote
    policy: PolicyRef
    message: str


QuoteRequestResult = strawberry.union(
    "QuoteRequestResult",
    [QuoteRequestSuccess, ValidationError, AuthenticationError],
)

QuoteAcceptResult = strawberry.union(
    "QuoteAcceptResult",
    [QuoteAcceptSuccess, NotFoundError, ValidationError],
)
