"""GraphQL resolvers."""

from app.graphql.resolvers.queries import Query
from app.graphql.resolvers.mutations import Mutation

__all__ = ["Query", "Mutation"]
