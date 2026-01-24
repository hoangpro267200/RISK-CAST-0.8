"""Add deprecation fields to risk_model_versions

Revision ID: 042_deprecation_fields
Revises: 041_system_configs
Create Date: 2026-01-23
"""
from alembic import op
import sqlalchemy as sa

revision = "042_deprecation_fields"
down_revision = "041_system_configs"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("risk_model_versions", sa.Column("deprecated_at", sa.DateTime(), nullable=True))
    op.add_column("risk_model_versions", sa.Column("deprecated_reason", sa.String(2000), nullable=True))
    op.add_column("risk_model_versions", sa.Column("replacement_version_id", sa.String(26), nullable=True))
    op.create_index("ix_risk_model_versions_deprecated_at", "risk_model_versions", ["deprecated_at"])
    op.create_foreign_key(
        "fk_risk_model_versions_replacement",
        "risk_model_versions",
        "risk_model_versions",
        ["replacement_version_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade():
    op.drop_constraint("fk_risk_model_versions_replacement", "risk_model_versions", type_="foreignkey")
    op.drop_index("ix_risk_model_versions_deprecated_at", "risk_model_versions")
    op.drop_column("risk_model_versions", "replacement_version_id")
    op.drop_column("risk_model_versions", "deprecated_reason")
    op.drop_column("risk_model_versions", "deprecated_at")
