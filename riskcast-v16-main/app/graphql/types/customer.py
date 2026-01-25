"""
Customer GraphQL Types
"""

import strawberry
from datetime import datetime
from typing import Optional

from app.graphql.types.base import Node, Timestamped


@strawberry.type
class Customer(Node, Timestamped):
    """Customer type."""

    id: strawberry.ID
    customer_number: str
    name: str
    email: str
    company_name: str
    tier: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
