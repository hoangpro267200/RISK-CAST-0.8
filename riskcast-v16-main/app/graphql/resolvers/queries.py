"""
GraphQL Query Resolvers
"""

import asyncio
import strawberry
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_

from app.graphql.types.quote import Quote, QuoteConnection, QuoteEdge, QuoteFilterInput, QuoteSortInput
from app.graphql.types.policy import Policy, PolicyConnection, PolicyEdge, PolicyFilterInput
from app.graphql.types.claim import Claim, ClaimConnection, ClaimEdge, ClaimFilterInput
from app.graphql.types.base import PageInfo, PaginationInput
from app.graphql.dataloaders import (
    _quote_model_to_type,
    _policy_model_to_type,
    _claim_model_to_type,
)


def _run_sync(sync_fn, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, lambda: sync_fn(*args, **kwargs))


@strawberry.type
class Query:
    """Root query type."""

    @strawberry.field
    async def quote(self, info: strawberry.Info, id: strawberry.ID) -> Optional[Quote]:
        """Get a single quote by ID."""
        loaders = info.context["dataloaders"]
        return await loaders.quote_loader.load(str(id))

    @strawberry.field
    async def quote_by_number(
        self, info: strawberry.Info, quote_number: str
    ) -> Optional[Quote]:
        """Get a quote by quote number."""

        def _fetch(session: Session):
            from app.models.quote import Quote as QuoteModel
            from sqlalchemy.orm import selectinload

            r = session.execute(
                select(QuoteModel)
                .where(QuoteModel.quote_number == quote_number)
                .options(selectinload(QuoteModel.submission))
            )
            return r.scalar_one_or_none()

        session: Session = info.context["session"]
        model = await _run_sync(_fetch, session)
        return _quote_model_to_type(model)

    @strawberry.field
    async def quotes(
        self,
        info: strawberry.Info,
        filter: Optional[QuoteFilterInput] = None,
        sort: Optional[QuoteSortInput] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> QuoteConnection:
        """Get paginated quotes with filtering."""

        def _fetch(session: Session, tenant_id: Optional[str], f, s, p):
            from app.models.quote import Quote as QuoteModel

            q = select(QuoteModel)
            cq = select(func.count(QuoteModel.id))
            if tenant_id:
                q = q.where(QuoteModel.tenant_id == tenant_id)
                cq = cq.where(QuoteModel.tenant_id == tenant_id)
            if f and f.status:
                q = q.where(QuoteModel.status.in_([x.value for x in f.status]))
                cq = cq.where(QuoteModel.status.in_([x.value for x in f.status]))
            sort_field = (s.field if s else "created_at") or "created_at"
            sort_dir = (s.direction if s else "DESC") or "DESC"
            order_col = getattr(QuoteModel, sort_field, QuoteModel.created_at)
            q = q.order_by(order_col.desc() if sort_dir.upper() == "DESC" else order_col.asc())
            total = session.execute(cq).scalar() or 0
            offset = int(p.after) + 1 if (p and getattr(p, "after", None)) else 0
            limit = (getattr(p, "first", None) if p else None) or 20
            q = q.offset(offset).limit(limit + 1)
            rows = session.execute(q).scalars().all()
            return total, offset, limit, rows

        session: Session = info.context["session"]
        tenant_id = info.context.get("tenant_id")
        pagination = pagination or PaginationInput()
        total, offset, limit, models = await _run_sync(
            _fetch, session, tenant_id, filter, sort, pagination
        )
        has_next = len(models) > limit
        if has_next:
            models = models[:-1]
        edges = [
            QuoteEdge(node=_quote_model_to_type(m), cursor=str(offset + i))
            for i, m in enumerate(models)
        ]
        return QuoteConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=offset > 0,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                total_count=total,
            ),
        )

    @strawberry.field
    async def policy(self, info: strawberry.Info, id: strawberry.ID) -> Optional[Policy]:
        """Get a single policy by ID."""
        return await info.context["dataloaders"].policy_loader.load(str(id))

    @strawberry.field
    async def policy_by_number(
        self, info: strawberry.Info, policy_number: str
    ) -> Optional[Policy]:
        """Get a policy by policy number."""

        def _fetch(session: Session):
            from app.modules.underwriting.models import Policy as PolicyModel

            r = session.execute(
                select(PolicyModel).where(PolicyModel.policy_number == policy_number)
            )
            return r.scalar_one_or_none()

        model = await _run_sync(_fetch, info.context["session"])
        return _policy_model_to_type(model)

    @strawberry.field
    async def policies(
        self,
        info: strawberry.Info,
        filter: Optional[PolicyFilterInput] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> PolicyConnection:
        """Get paginated policies with filtering."""

        def _fetch(session: Session, tenant_id: str, f, p):
            from app.modules.underwriting.models import Policy as PolicyModel

            q = select(PolicyModel).where(PolicyModel.tenant_id == tenant_id)
            cq = select(func.count(PolicyModel.id)).where(
                PolicyModel.tenant_id == tenant_id
            )
            if f and f.status:
                q = q.where(PolicyModel.status.in_([s.value for s in f.status]))
                cq = cq.where(PolicyModel.status.in_([s.value for s in f.status]))
            if f and f.search:
                q = q.where(PolicyModel.policy_number.ilike(f"%{f.search}%"))
                cq = cq.where(PolicyModel.policy_number.ilike(f"%{f.search}%"))
            q = q.order_by(PolicyModel.created_at.desc())
            total = session.execute(cq).scalar() or 0
            offset = int(p.after) + 1 if (p and getattr(p, "after", None)) else 0
            limit = getattr(p, "first", None) or 20
            q = q.offset(offset).limit(limit + 1)
            rows = session.execute(q).scalars().all()
            return total, offset, limit, rows

        session = info.context["session"]
        tenant_id = info.context.get("tenant_id") or ""
        pagination = pagination or PaginationInput()
        total, offset, limit, models = await _run_sync(
            _fetch, session, tenant_id, filter, pagination
        )
        has_next = len(models) > limit
        if has_next:
            models = models[:-1]
        edges = [
            PolicyEdge(node=_policy_model_to_type(m), cursor=str(offset + i))
            for i, m in enumerate(models)
        ]
        return PolicyConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=offset > 0,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                total_count=total,
            ),
        )

    @strawberry.field
    async def claim(self, info: strawberry.Info, id: strawberry.ID) -> Optional[Claim]:
        """Get a single claim by ID."""
        return await info.context["dataloaders"].claim_loader.load(str(id))

    @strawberry.field
    async def claims(
        self,
        info: strawberry.Info,
        filter: Optional[ClaimFilterInput] = None,
        pagination: Optional[PaginationInput] = None,
    ) -> ClaimConnection:
        """Get paginated claims with filtering."""

        def _fetch(session: Session, tenant_id: str, f, p):
            from app.modules.claims.models import Claim as ClaimModel

            q = select(ClaimModel).where(ClaimModel.tenant_id == tenant_id)
            cq = select(func.count(ClaimModel.id)).where(
                ClaimModel.tenant_id == tenant_id
            )
            if f and f.status:
                q = q.where(ClaimModel.status.in_([s.value for s in f.status]))
                cq = cq.where(ClaimModel.status.in_([s.value for s in f.status]))
            q = q.order_by(ClaimModel.created_at.desc())
            total = session.execute(cq).scalar() or 0
            offset = int(p.after) + 1 if (p and getattr(p, "after", None)) else 0
            limit = getattr(p, "first", None) or 20
            q = q.offset(offset).limit(limit + 1)
            rows = session.execute(q).scalars().all()
            return total, offset, limit, rows

        session = info.context["session"]
        tenant_id = info.context.get("tenant_id") or ""
        pagination = pagination or PaginationInput()
        total, offset, limit, models = await _run_sync(
            _fetch, session, tenant_id, filter, pagination
        )
        has_next = len(models) > limit
        if has_next:
            models = models[:-1]
        edges = [
            ClaimEdge(node=_claim_model_to_type(m), cursor=str(offset + i))
            for i, m in enumerate(models)
        ]
        return ClaimConnection(
            edges=edges,
            page_info=PageInfo(
                has_next_page=has_next,
                has_previous_page=offset > 0,
                start_cursor=edges[0].cursor if edges else None,
                end_cursor=edges[-1].cursor if edges else None,
                total_count=total,
            ),
        )
