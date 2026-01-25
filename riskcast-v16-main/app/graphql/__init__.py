"""
GraphQL API Layer (Strawberry)

Provides GraphQL API alongside REST for Quote, Policy, Claim, and Customer.
"""

from app.graphql.schema import schema

__all__ = ["schema"]
