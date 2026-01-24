"""Add UNIQUE(tenant_id, input_hash) and schema_version to risk_assessments

Revision ID: 012_risk_assessments
Revises: 011_parametric
Create Date: 2024-12-19

- Adds schema_version VARCHAR(20) NOT NULL (backfilled from input_schema_version).
- Replaces ix_risk_assessments_tenant_hash with UNIQUE(tenant_id, input_hash).
- Keeps existing columns; no drop of risk_assessments or risk_runs.
"""
from alembic import op
import sqlalchemy as sa

revision = "012_risk_assessments"
down_revision = "011_parametric"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add schema_version; backfill from input_schema_version, then set NOT NULL.
    op.add_column(
        "risk_assessments",
        sa.Column("schema_version", sa.String(length=20), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE risk_assessments SET schema_version = SUBSTR(input_schema_version, 1, 20) WHERE schema_version IS NULL"
        )
    )
    op.alter_column(
        "risk_assessments",
        "schema_version",
        existing_type=sa.String(20),
        existing_nullable=True,
        nullable=False,
    )

    # Replace non-unique (tenant_id, input_hash) index with UNIQUE constraint.
    op.drop_index("ix_risk_assessments_tenant_hash", table_name="risk_assessments")
    op.create_unique_constraint(
        "uq_risk_assessments_tenant_input_hash",
        "risk_assessments",
        ["tenant_id", "input_hash"],
    )

    # User spec: idx_risk_assessments_tenant, idx_risk_assessments_input_hash.
    # 004 already has ix_* on same columns; add these named indexes.
    op.create_index(
        "idx_risk_assessments_tenant",
        "risk_assessments",
        ["tenant_id"],
        unique=False,
    )
    op.create_index(
        "idx_risk_assessments_input_hash",
        "risk_assessments",
        ["input_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_risk_assessments_input_hash", table_name="risk_assessments")
    op.drop_index("idx_risk_assessments_tenant", table_name="risk_assessments")
    op.drop_constraint(
        "uq_risk_assessments_tenant_input_hash",
        "risk_assessments",
        type_="unique",
    )
    op.create_index(
        "ix_risk_assessments_tenant_hash",
        "risk_assessments",
        ["tenant_id", "input_hash"],
        unique=False,
    )
    op.drop_column("risk_assessments", "schema_version")
