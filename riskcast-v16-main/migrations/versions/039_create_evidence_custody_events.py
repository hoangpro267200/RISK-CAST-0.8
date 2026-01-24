"""Create evidence custody events table

Revision ID: 039_evidence_custody
Revises: 038_immutable_audit
Create Date: 2026-01-23

Creates evidence_custody_events table for hash-chained chain of custody tracking.
"""
from alembic import op
import sqlalchemy as sa

revision = "039_evidence_custody"
down_revision = "038_immutable_audit"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "evidence_custody_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bundle_id", sa.String(36), nullable=True),
        sa.Column("item_id", sa.String(36), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("prev_event_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.ForeignKeyConstraint(
            ["bundle_id"],
            ["evidence_bundles.id"],
            name="fk_custody_event_bundle",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["item_id"],
            ["evidence_objects.id"],
            name="fk_custody_event_item",
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_custody_event_bundle", "evidence_custody_events", ["bundle_id"])
    op.create_index("idx_custody_event_item", "evidence_custody_events", ["item_id"])
    op.create_index(
        "idx_custody_event_sequence",
        "evidence_custody_events",
        ["bundle_id", "sequence_number"],
    )


def downgrade():
    op.drop_index("idx_custody_event_sequence", "evidence_custody_events")
    op.drop_index("idx_custody_event_item", "evidence_custody_events")
    op.drop_index("idx_custody_event_bundle", "evidence_custody_events")
    op.drop_table("evidence_custody_events")
