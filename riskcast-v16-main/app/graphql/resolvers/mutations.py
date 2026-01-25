"""
GraphQL Mutation Resolvers
"""

import strawberry
from typing import Union
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from app.graphql.types.quote import (
    Quote,
    QuoteRequestInput,
    QuoteRequestResult,
    QuoteRequestSuccess,
    QuoteAcceptResult,
    QuoteAcceptSuccess,
)
from app.graphql.types.policy import Policy
from app.graphql.types.claim import Claim, ClaimFileInput, ClaimFileSuccess
from app.graphql.types.base import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    FieldError,
)
from app.graphql.dataloaders import (
    _quote_model_to_type,
    _policy_model_to_type,
    _claim_model_to_type,
)


@strawberry.type
class Mutation:
    """Root mutation type."""

    @strawberry.mutation
    async def request_quote(
        self, info: strawberry.Info, input: QuoteRequestInput
    ) -> QuoteRequestResult:
        """Request a new insurance quote."""
        user = info.context.get("user")
        if not user:
            return AuthenticationError(message="Authentication required")

        errors = []
        if input.cargo_value_usd <= 0:
            errors.append(
                FieldError(
                    field="cargo_value_usd",
                    message="Cargo value must be positive",
                    code="INVALID_VALUE",
                )
            )
        if not input.origin_port or len(input.origin_port) != 5:
            errors.append(
                FieldError(
                    field="origin_port",
                    message="Invalid port code (must be 5 characters)",
                    code="INVALID_PORT",
                )
            )
        if not input.destination_port or len(input.destination_port) != 5:
            errors.append(
                FieldError(
                    field="destination_port",
                    message="Invalid port code (must be 5 characters)",
                    code="INVALID_PORT",
                )
            )
        if errors:
            return ValidationError(message="Validation failed", errors=errors)

        session = info.context["session"]
        tenant_id = info.context.get("tenant_id") or "default"
        customer_id = getattr(user, "customer_id", None) or getattr(user, "id", str(uuid.uuid4()))

        def _create(sess):
            from app.models.quote import Quote as QuoteModel

            quote_number = f"Q{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            # Build pricing/coverage JSON from input
            pricing = {
                "total_premium_usd": float(input.cargo_value_usd * Decimal("0.0012")),
                "sum_insured_usd": float(input.cargo_value_usd),
                "rate_per_mille": 1.2,
            }
            coverage = {
                "coverage_type": input.coverage_type,
                "cargo_type": input.cargo_type,
                "cargo_value_usd": float(input.cargo_value_usd),
                "origin_port": input.origin_port,
                "destination_port": input.destination_port,
                "container_count": input.container_count,
            }
            # We need submission_id and model_version_id, risk_run_id. Use placeholder flow.
            from app.modules.underwriting.models import UnderwritingSubmission
            from app.modules.risk_assessments.models import RiskAssessment
            from app.modules.risk_runs.models import RiskRun
            from app.modules.model_versioning.models import RiskModelVersion
            from sqlalchemy import select as sa_select

            sub = sess.execute(sa_select(UnderwritingSubmission).limit(1)).scalars().first()
            ra = sess.execute(sa_select(RiskAssessment).limit(1)).scalars().first()
            rrun = sess.execute(sa_select(RiskRun).limit(1)).scalars().first()
            rmv = sess.execute(sa_select(RiskModelVersion).limit(1)).scalars().first()
            if not all([sub, ra, rrun, rmv]):
                raise ValueError(
                    "Missing underwriting/risk setup. Create submission, risk assessment, risk run, model version first."
                )
            quote = QuoteModel(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                submission_id=sub.id,
                model_version_id=rmv.id,
                risk_run_id=rrun.id,
                quote_number=quote_number,
                status="ISSUED",
                pricing_snapshot_json=pricing,
                coverage_terms_json=coverage,
                risk_summary_json={"overall_score": 0.35, "risk_grade": "B"},
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=7),
                created_at=datetime.utcnow(),
            )
            sess.add(quote)
            sess.commit()
            sess.refresh(quote)
            return quote

        try:
            import asyncio

            quote = await asyncio.get_running_loop().run_in_executor(
                None, _create, session
            )
            return QuoteRequestSuccess(
                quote=_quote_model_to_type(quote),
                message=f"Quote {quote.quote_number} created successfully",
            )
        except Exception as e:
            return ValidationError(
                message="Failed to create quote",
                errors=[FieldError(field="", message=str(e), code="SYSTEM_ERROR")],
            )

    @strawberry.mutation
    async def accept_quote(
        self, info: strawberry.Info, quote_id: strawberry.ID
    ) -> QuoteAcceptResult:
        """Accept a quote and create a policy."""
        user = info.context.get("user")
        if not user:
            return AuthenticationError(message="Authentication required")

        session = info.context["session"]

        def _accept(sess):
            from sqlalchemy import select
            from app.models.quote import Quote as QuoteModel
            from app.modules.underwriting.models import Policy as PolicyModel

            r = sess.execute(
                select(QuoteModel).where(QuoteModel.id == str(quote_id))
            )
            quote = r.scalar_one_or_none()
            if not quote:
                return None, "NOT_FOUND"
            if quote.status not in ("ISSUED", "PENDING"):
                return None, "INVALID_STATUS"
            if quote.valid_until and datetime.utcnow() > quote.valid_until:
                return None, "EXPIRED"
            policy_number = f"P{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            cov = quote.coverage_terms_json or {}
            prem = quote.pricing_snapshot_json or {}
            terms = {
                "coverage_type": cov.get("coverage_type", "ALL_RISKS"),
                "coverage_limit_usd": cov.get("cargo_value_usd", 0),
                "cargo_type": cov.get("cargo_type", "GENERAL"),
                "origin_port": cov.get("origin_port", ""),
                "destination_port": cov.get("destination_port", ""),
                "cargo_value_usd": cov.get("cargo_value_usd", 0),
            }
            from app.shared.utils import generate_ulid
            from app.modules.underwriting.models import PolicyStatus as PStatus

            policy = PolicyModel(
                id=generate_ulid(),
                tenant_id=quote.tenant_id,
                policy_number=policy_number,
                status=PStatus.ACTIVE,
                quote_id=quote.id,
                submission_id=quote.submission_id,
                model_version_id=quote.model_version_id,
                risk_run_id=quote.risk_run_id,
                effective_from=datetime.utcnow(),
                effective_to=datetime.utcnow() + timedelta(days=90),
                bound_at=datetime.utcnow(),
                terms_json=terms,
                premium_json={
                    "total_premium_usd": prem.get("total_premium_usd", 0),
                    "paid_premium_usd": 0,
                    "payment_status": "PENDING",
                },
                policyholder_json={"customer_id": quote.submission_id},
                policy_hash=uuid.uuid4().hex,
            )
            sess.add(policy)
            quote.status = "ACCEPTED"
            sess.commit()
            sess.refresh(quote)
            sess.refresh(policy)
            return (quote, policy), "OK"

        try:
            import asyncio

            out, status = await asyncio.get_running_loop().run_in_executor(
                None, _accept, session
            )
            if status == "NOT_FOUND":
                return NotFoundError(
                    message="Quote not found",
                    resource_type="Quote",
                    resource_id=str(quote_id),
                )
            if status == "INVALID_STATUS":
                return ValidationError(
                    message="Quote cannot be accepted in current status",
                    errors=[
                        FieldError(
                            field="status",
                            message="Quote must be ISSUED or PENDING",
                            code="INVALID_STATUS",
                        )
                    ],
                )
            if status == "EXPIRED":
                return ValidationError(
                    message="Quote has expired",
                    errors=[
                        FieldError(
                            field="valid_until",
                            message="Quote has expired",
                            code="QUOTE_EXPIRED",
                        )
                    ],
                )
            quote, policy = out
            return QuoteAcceptSuccess(
                quote=_quote_model_to_type(quote),
                policy=_policy_model_to_type(policy),
                message=f"Policy {policy.policy_number} created successfully",
            )
        except Exception as e:
            return ValidationError(
                message="Failed to accept quote",
                errors=[FieldError(field="", message=str(e), code="SYSTEM_ERROR")],
            )

    @strawberry.mutation
    async def file_claim(
        self, info: strawberry.Info, input: ClaimFileInput
    ) -> Union[ClaimFileSuccess, ValidationError, NotFoundError, AuthenticationError]:
        """File a new claim."""
        user = info.context.get("user")
        if not user:
            return AuthenticationError(message="Authentication required")

        session = info.context["session"]

        def _file(sess):
            from sqlalchemy import select
            from app.modules.underwriting.models import Policy as PolicyModel
            from app.modules.claims.models import Claim as ClaimModel
            from app.modules.claims.models import ClaimStatus as CS

            r = sess.execute(
                select(PolicyModel).where(PolicyModel.id == str(input.policy_id))
            )
            policy = r.scalar_one_or_none()
            if not policy:
                return None, "NOT_FOUND"
            if policy.status.value != "ACTIVE":
                return None, "INACTIVE"
            claim_number = f"CLM{datetime.utcnow().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
            fnol = {
                "loss_date": input.loss_date.isoformat(),
                "loss_type": input.loss_type,
                "loss_location": input.loss_location,
                "loss_description": input.loss_description,
                "claimed_amount_usd": float(input.claimed_amount),
            }
            from app.shared.utils import generate_ulid

            claim = ClaimModel(
                id=generate_ulid(),
                tenant_id=policy.tenant_id,
                policy_id=policy.id,
                claim_number=claim_number,
                status=CS.FNOL_RECEIVED,
                fnol_json=fnol,
                approved_amount_cents=None,
                created_by_user_id=getattr(user, "id", None),
            )
            sess.add(claim)
            sess.commit()
            sess.refresh(claim)
            return claim, "OK"

        try:
            import asyncio

            out = await asyncio.get_running_loop().run_in_executor(None, _file, session)
            if out[1] == "NOT_FOUND":
                return NotFoundError(
                    message="Policy not found",
                    resource_type="Policy",
                    resource_id=str(input.policy_id),
                )
            if out[1] == "INACTIVE":
                return ValidationError(
                    message="Can only file claims against active policies",
                    errors=[
                        FieldError(
                            field="policy_id",
                            message="Policy is not active",
                            code="INACTIVE_POLICY",
                        )
                    ],
                )
            claim, _ = out
            return ClaimFileSuccess(
                claim=_claim_model_to_type(claim),
                message=f"Claim {claim.claim_number} filed successfully",
            )
        except Exception as e:
            return ValidationError(
                message="Failed to file claim",
                errors=[FieldError(field="", message=str(e), code="SYSTEM_ERROR")],
            )
