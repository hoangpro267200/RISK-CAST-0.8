"""Create system_configs table

Revision ID: 041_system_configs
Revises: 040_gdpr_requests
Create Date: 2026-01-23

System-wide key-value config (e.g. active_model_version_id).
"""
from alembic import op
import sqlalchemy as sa

revision = "041_system_configs"
down_revision = "040_gdpr_requests"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "system_configs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("key", sa.String(100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_system_configs_key", "system_configs", ["key"], unique=True)


def downgrade():
    op.drop_index("ix_system_configs_key", "system_configs")
    op.drop_table("system_configs")
