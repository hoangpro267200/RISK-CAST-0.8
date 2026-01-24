"""Create GDPR requests table

Revision ID: 040_gdpr_requests
Revises: 039_evidence_custody
Create Date: 2026-01-23

Creates gdpr_requests table for tracking GDPR data subject requests.
"""
from alembic import op
import sqlalchemy as sa

revision = "040_gdpr_requests"
down_revision = "039_evidence_custody"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gdpr_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("request_type", sa.String(50), nullable=False),
        sa.Column("user_id", sa.String(26), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("response_deadline", sa.DateTime(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("result_location", sa.String(500), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("tenant_id", sa.String(26), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_gdpr_request_user",
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_gdpr_requests_user", "gdpr_requests", ["user_id"])
    op.create_index("idx_gdpr_requests_status", "gdpr_requests", ["status"])
    op.create_index("idx_gdpr_requests_type", "gdpr_requests", ["request_type"])
    op.create_index("idx_gdpr_requests_tenant", "gdpr_requests", ["tenant_id"])


def downgrade():
    op.drop_index("idx_gdpr_requests_tenant", "gdpr_requests")
    op.drop_index("idx_gdpr_requests_type", "gdpr_requests")
    op.drop_index("idx_gdpr_requests_status", "gdpr_requests")
    op.drop_index("idx_gdpr_requests_user", "gdpr_requests")
    op.drop_table("gdpr_requests")
