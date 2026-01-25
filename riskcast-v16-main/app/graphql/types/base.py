"""
Base GraphQL Types and Interfaces

Features:
1. Common interfaces
2. Scalar types
3. Pagination types
4. Error types
"""

import strawberry
from datetime import datetime, date
from decimal import Decimal
from typing import Generic, TypeVar, List, Optional
from enum import Enum


# =============================================================================
# Custom Scalars
# =============================================================================

@strawberry.scalar(description="Decimal number for precise currency values")
class DecimalScalar:
    @staticmethod
    def serialize(value: Decimal) -> str:
        return str(value)

    @staticmethod
    def parse_value(value: str) -> Decimal:
        return Decimal(value)


@strawberry.scalar(description="JSON object")
class JSONScalar:
    @staticmethod
    def serialize(value: dict) -> dict:
        return value

    @staticmethod
    def parse_value(value: dict) -> dict:
        return value


# =============================================================================
# Common Interfaces
# =============================================================================

@strawberry.interface
class Node:
    """Interface for objects with global IDs."""

    id: strawberry.ID


@strawberry.interface
class Timestamped:
    """Interface for objects with timestamps."""

    created_at: datetime
    updated_at: Optional[datetime]


@strawberry.interface
class Auditable(Timestamped):
    """Interface for auditable objects."""

    created_by: Optional[str]
    updated_by: Optional[str]


# =============================================================================
# Pagination Types
# =============================================================================

T = TypeVar("T")


@strawberry.type
class PageInfo:
    """Pagination info following Relay spec."""

    has_next_page: bool
    has_previous_page: bool
    start_cursor: Optional[str]
    end_cursor: Optional[str]
    total_count: int


@strawberry.type
class Edge(Generic[T]):
    """Edge in a connection."""

    node: T
    cursor: str


@strawberry.type
class Connection(Generic[T]):
    """Connection following Relay spec."""

    edges: List[Edge]
    page_info: PageInfo


# =============================================================================
# Error Types
# =============================================================================

@strawberry.type
class FieldError:
    """Error for a specific field."""

    field: str
    message: str
    code: str


@strawberry.type
class ValidationError:
    """Validation error response."""

    message: str
    errors: List[FieldError]


@strawberry.type
class NotFoundError:
    """Resource not found error."""

    message: str
    resource_type: str
    resource_id: str


@strawberry.type
class AuthenticationError:
    """Authentication error."""

    message: str


@strawberry.type
class AuthorizationError:
    """Authorization error."""

    message: str
    required_permission: Optional[str]


# Union for mutation results
MutationError = strawberry.union(
    "MutationError",
    [ValidationError, NotFoundError, AuthenticationError, AuthorizationError],
)


# =============================================================================
# Common Enums
# =============================================================================

@strawberry.enum
class SortDirection(Enum):
    ASC = "ASC"
    DESC = "DESC"


@strawberry.enum
class QuoteStatus(Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"


@strawberry.enum
class PolicyStatus(Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


@strawberry.enum
class ClaimStatus(Enum):
    FILED = "FILED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    PAID = "PAID"


@strawberry.enum
class RiskGrade(Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


# =============================================================================
# Input Types
# =============================================================================

@strawberry.input
class PaginationInput:
    """Pagination input."""

    first: Optional[int] = 20
    after: Optional[str] = None
    last: Optional[int] = None
    before: Optional[str] = None


@strawberry.input
class DateRangeInput:
    """Date range filter."""

    start: Optional[date] = None
    end: Optional[date] = None


@strawberry.input
class MoneyRangeInput:
    """Money range filter."""

    min: Optional[Decimal] = None
    max: Optional[Decimal] = None
