"""
Claim GraphQL Types
"""

import strawberry
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Annotated

from app.graphql.types.base import Node, Auditable, ClaimStatus, Connection, Edge, PageInfo

PolicyRef = Annotated["Policy", strawberry.lazy("app.graphql.types.policy")]


@strawberry.type
class ClaimDocument:
    """Document attached to a claim."""

    id: strawberry.ID
    document_type: str
    filename: str
    file_size: int
    uploaded_at: datetime
    uploaded_by: str
    url: str


@strawberry.type
class ClaimAssessment:
    """Claim assessment details."""

    assessed_by: str
    assessed_at: datetime
    assessed_amount: Decimal
    assessment_notes: str
    recommendation: str


@strawberry.type
class ClaimPayment:
    """Claim payment details."""

    payment_id: str
    amount: Decimal
    paid_at: datetime
    payment_method: str
    reference: str


@strawberry.type
class ClaimTimeline:
    """Timeline event for a claim."""

    event_type: str
    description: str
    timestamp: datetime
    actor: Optional[str]


@strawberry.type
class Claim(Node, Auditable):
    """Claim type."""

    id: strawberry.ID
    claim_number: str
    status: ClaimStatus

    # Loss details
    loss_date: date
    loss_type: str
    loss_location: Optional[str]
    loss_description: str

    # Amounts
    claimed_amount: Decimal
    assessed_amount: Optional[Decimal]
    approved_amount: Optional[Decimal]
    paid_amount: Optional[Decimal]

    # Assessment
    assessment: Optional[ClaimAssessment]

    # Denial
    denial_reason: Optional[str]

    # Documents
    documents: List[ClaimDocument]

    # Timeline
    timeline: List[ClaimTimeline]

    # Timestamps
    filed_at: datetime
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    updated_by: Optional[str]

    # Private fields for relationships
    policy_id: strawberry.Private[str]

    @strawberry.field
    async def policy(self, info: strawberry.Info) -> Optional[PolicyRef]:
        """Get the policy this claim is filed against."""
        loader = info.context["dataloaders"].policy_loader
        return await loader.load(self.policy_id)

    @strawberry.field
    def days_since_filed(self) -> int:
        """Days since claim was filed."""
        return (datetime.utcnow() - self.filed_at).days

    @strawberry.field
    def is_open(self) -> bool:
        """Check if claim is still open."""
        return self.status in [ClaimStatus.FILED, ClaimStatus.IN_REVIEW]


@strawberry.type
class ClaimEdge:
    """Claim edge for pagination."""

    node: Claim
    cursor: str


@strawberry.type
class ClaimConnection:
    """Paginated claims."""

    edges: List[ClaimEdge]
    page_info: PageInfo


# =============================================================================
# Input Types
# =============================================================================

@strawberry.input
class ClaimFileInput:
    """Input for filing a new claim."""

    policy_id: strawberry.ID
    loss_date: date
    loss_type: str
    loss_location: Optional[str] = None
    loss_description: str
    claimed_amount: Decimal
    supporting_documents: Optional[List[str]] = None


@strawberry.input
class ClaimFilterInput:
    """Filter input for claims."""

    status: Optional[List[ClaimStatus]] = None
    loss_type: Optional[str] = None
    filed_after: Optional[datetime] = None
    filed_before: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


@strawberry.input
class ClaimAssessmentInput:
    """Input for claim assessment."""

    claim_id: strawberry.ID
    assessed_amount: Decimal
    assessment_notes: str
    recommendation: str


# =============================================================================
# Mutation Results
# =============================================================================

@strawberry.type
class ClaimFileSuccess:
    """Successful claim filing."""

    claim: Claim
    message: str


@strawberry.type
class ClaimApproveSuccess:
    """Successful claim approval."""

    claim: Claim
    approved_amount: Decimal
    message: str
