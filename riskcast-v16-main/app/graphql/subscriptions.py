"""
GraphQL Subscriptions for Real-time Updates
"""

import strawberry
from typing import AsyncGenerator, Optional
import asyncio

from app.graphql.types.quote import Quote
from app.graphql.types.policy import Policy
from app.graphql.types.claim import Claim


@strawberry.type
class RiskAlert:
    """Risk alert payload."""

    alert_id: str
    tenant_id: str
    severity: str
    message: str
    payload: str  # JSON string


@strawberry.type
class Subscription:
    """Root subscription type."""

    @strawberry.subscription
    async def quote_updates(
        self, info: strawberry.Info, quote_id: strawberry.ID
    ) -> AsyncGenerator[Optional[Quote], None]:
        """Subscribe to updates for a specific quote."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        queue: asyncio.Queue = asyncio.Queue()
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield msg.get("quote")
                except asyncio.TimeoutError:
                    continue
        finally:
            pass

    @strawberry.subscription
    async def policy_updates(self, info: strawberry.Info) -> AsyncGenerator[Optional[Policy], None]:
        """Subscribe to all policy updates for the current tenant."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        tenant_id = info.context.get("tenant_id")
        queue: asyncio.Queue = asyncio.Queue()
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if msg.get("tenant_id") == tenant_id:
                        yield msg.get("policy")
                except asyncio.TimeoutError:
                    continue
        finally:
            pass

    @strawberry.subscription
    async def claim_updates(
        self,
        info: strawberry.Info,
        claim_id: Optional[strawberry.ID] = None,
    ) -> AsyncGenerator[Optional[Claim], None]:
        """Subscribe to claim updates."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        tenant_id = info.context.get("tenant_id")
        queue: asyncio.Queue = asyncio.Queue()
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if claim_id and msg.get("claim_id") != str(claim_id):
                        continue
                    if msg.get("tenant_id") != tenant_id:
                        continue
                    yield msg.get("claim")
                except asyncio.TimeoutError:
                    continue
        finally:
            pass

    @strawberry.subscription
    async def risk_alerts(self, info: strawberry.Info) -> AsyncGenerator[Optional[RiskAlert], None]:
        """Subscribe to real-time risk alerts."""
        user = info.context.get("user")
        if not user:
            raise Exception("Authentication required")
        tenant_id = info.context.get("tenant_id")
        queue: asyncio.Queue = asyncio.Queue()
        try:
            while True:
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=30.0)
                    if alert.get("tenant_id") != tenant_id:
                        continue
                    import json
                    yield RiskAlert(
                        alert_id=alert.get("alert_id", ""),
                        tenant_id=alert.get("tenant_id", ""),
                        severity=alert.get("severity", "INFO"),
                        message=alert.get("message", ""),
                        payload=json.dumps(alert.get("payload", {})),
                    )
                except asyncio.TimeoutError:
                    continue
        finally:
            pass
