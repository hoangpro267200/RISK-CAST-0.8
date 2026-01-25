"""
GraphQL Router for FastAPI
"""

from fastapi import Request, Depends

from strawberry.fastapi import GraphQLRouter

from app.graphql.schema import schema
from app.graphql.context import get_context
from app.database import get_db
from sqlalchemy.orm import Session


def graphql_context_getter(
    request: Request,
    session: Session = Depends(get_db),
) -> dict:
    """Build GraphQL context. Session is injected via FastAPI Depends(get_db)."""
    return get_context(request, session)


graphql_app = GraphQLRouter(
    schema,
    path="/",
    context_getter=graphql_context_getter,
    graphql_ide="graphiql",
)
