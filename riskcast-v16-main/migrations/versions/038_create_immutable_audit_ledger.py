"""Create immutable audit ledger (hash-chained, HMAC-signed)

Revision ID: 038_immutable_audit
Revises: 037_enhance_calibration_detailed
Create Date: 2026-01-23

Creates audit_events_immutable and immutable_audit_chain_tip for
tamper-evident, insurance-grade audit trail.
"""
from alembic import op
import sqlalchemy as sa

revision = "038_immutable_audit"
down_revision = "037_enhance_calibration_detailed"
branch_labels = None
depends_on = None

GENESIS_HASH = "0" * 64


def upgrade():
    op.create_table(
        "immutable_audit_chain_tip",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("next_sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("latest_hash", sa.String(64), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.execute(
        sa.text(
            "INSERT INTO immutable_audit_chain_tip (id, next_sequence, latest_hash, updated_at) "
            "VALUES (1, 1, :h, CURRENT_TIMESTAMP)"
        ).bindparams(h=GENESIS_HASH)
    )

    op.create_table(
        "audit_events_immutable",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(200), nullable=False),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(200), nullable=True),
        sa.Column("tenant_id", sa.String(26), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(), nullable=False),
        sa.Column("server_timestamp", sa.DateTime(), nullable=False),
        sa.Column("prev_event_hash", sa.String(64), nullable=False),
        sa.Column("event_hash", sa.String(64), nullable=False),
        sa.Column("hmac_signature", sa.String(64), nullable=False),
        sa.Column("source_ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
    )
    op.create_index("idx_immutable_audit_type", "audit_events_immutable", ["event_type"])
    op.create_index(
        "idx_immutable_audit_entity",
        "audit_events_immutable",
        ["entity_type", "entity_id"],
    )
    op.create_index(
        "idx_immutable_audit_actor",
        "audit_events_immutable",
        ["actor_type", "actor_id"],
    )
    op.create_index(
        "idx_immutable_audit_timestamp",
        "audit_events_immutable",
        ["event_timestamp"],
    )
    op.create_index(
        "idx_immutable_audit_tenant",
        "audit_events_immutable",
        ["tenant_id"],
    )
    op.create_index(
        "idx_immutable_audit_sequence",
        "audit_events_immutable",
        ["sequence_number"],
        unique=True,
    )
    op.create_index(
        "idx_immutable_audit_hash",
        "audit_events_immutable",
        ["event_hash"],
    )


def downgrade():
    op.drop_index("idx_immutable_audit_hash", "audit_events_immutable")
    op.drop_index("idx_immutable_audit_sequence", "audit_events_immutable")
    op.drop_index("idx_immutable_audit_tenant", "audit_events_immutable")
    op.drop_index("idx_immutable_audit_timestamp", "audit_events_immutable")
    op.drop_index("idx_immutable_audit_actor", "audit_events_immutable")
    op.drop_index("idx_immutable_audit_entity", "audit_events_immutable")
    op.drop_index("idx_immutable_audit_type", "audit_events_immutable")
    op.drop_table("audit_events_immutable")
    op.drop_table("immutable_audit_chain_tip")
