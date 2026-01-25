"""
GraphQL Context
"""

from dataclasses import dataclass
from typing import Optional, Any

from sqlalchemy.orm import Session

from app.graphql.dataloaders import DataLoaders


@dataclass
class GraphQLContext:
    """Context available in all resolvers."""

    session: Session
    dataloaders: DataLoaders
    user: Optional[Any]
    tenant_id: Optional[str]
    request: Any
    risk_engine: Any = None
    quote_service: Any = None


def get_context(request: Any, session: Session) -> dict:
    """Build GraphQL context from request. Used as context_getter."""
    user = getattr(request.state, "user", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    loaders = DataLoaders(session)
    return {
        "session": session,
        "dataloaders": loaders,
        "user": user,
        "tenant_id": tenant_id,
        "request": request,
    }
