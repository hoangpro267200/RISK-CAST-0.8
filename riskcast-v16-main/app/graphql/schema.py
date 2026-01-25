"""
GraphQL Schema Definition
"""

import strawberry
from decimal import Decimal

from app.graphql.resolvers.queries import Query
from app.graphql.resolvers.mutations import Mutation
from app.graphql.subscriptions import Subscription
from app.graphql.types.base import DecimalScalar

try:
    from strawberry.extensions import QueryDepthLimiter
    _extensions = [QueryDepthLimiter(max_depth=10)]
except Exception:
    _extensions = []

try:
    from strawberry.schema.config import StrawberryConfig
    _config = StrawberryConfig(auto_camel_case=True)
except Exception:
    _config = None

_schema_kw = dict(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
    extensions=_extensions,
    scalar_overrides={Decimal: DecimalScalar},
)
if _config is not None:
    _schema_kw["config"] = _config

schema = strawberry.Schema(**_schema_kw)
