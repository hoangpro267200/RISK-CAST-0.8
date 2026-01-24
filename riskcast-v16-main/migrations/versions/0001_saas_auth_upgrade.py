"""saas auth upgrade

Revision ID: 0001_saas_auth_upgrade
Revises:
Create Date: 2026-01-21 00:00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_saas_auth_upgrade"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(conn, name):
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def column_exists(conn, table, column):
    insp = sa.inspect(conn)
    return any(col["name"] == column for col in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()

    # user_preferences
    if not table_exists(conn, "user_preferences"):
        op.create_table(
            "user_preferences",
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            sa.Column("timezone", sa.String(length=64), nullable=True),
            sa.Column("currency", sa.String(length=8), nullable=True),
            sa.Column("units", sa.String(length=16), nullable=True),
            sa.Column("theme", sa.String(length=16), nullable=True),
            sa.Column("personalization_opt_in", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("preferences_json", sa.JSON(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    # oauth_identities
    if not table_exists(conn, "oauth_identities"):
        op.create_table(
            "oauth_identities",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("provider", sa.String(length=32), nullable=False),
            sa.Column("provider_user_id", sa.String(length=128), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("connected_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("disconnected_at", sa.DateTime(), nullable=True),
            sa.UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
        )

    # audit_log
    if not table_exists(conn, "audit_log"):
        op.create_table(
            "audit_log",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("action_type", sa.String(length=64), nullable=False),
            sa.Column("metadata_json", sa.JSON(), nullable=True),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        )
        op.create_index("ix_audit_log_user_created", "audit_log", ["user_id", "created_at"])

    # events
    if not table_exists(conn, "events"):
        op.create_table(
            "events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("event_name", sa.String(length=128), nullable=False),
            sa.Column("payload_json", sa.JSON(), nullable=True),
            sa.Column("ip", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        )
        op.create_index("ix_events_user_created", "events", ["user_id", "created_at"])

    # sessions columns
    session_cols = {
        "absolute_expires_at": sa.Column("absolute_expires_at", sa.DateTime(), nullable=True),
        "revoke_reason": sa.Column("revoke_reason", sa.String(length=128), nullable=True),
        "rotated_from_session_id": sa.Column("rotated_from_session_id", sa.Integer(), nullable=True),
        "csrf_token_hash": sa.Column("csrf_token_hash", sa.String(length=64), nullable=True),
        "last_seen_at": sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        "user_agent_hash": sa.Column("user_agent_hash", sa.String(length=64), nullable=True),
        "ip_prefix": sa.Column("ip_prefix", sa.String(length=64), nullable=True),
    }
    for col_name, col_def in session_cols.items():
        if not column_exists(conn, "sessions", col_name):
            op.add_column("sessions", col_def)

    # users columns (email_verified already exists; add tenant_id/role/status if missing)
    if not column_exists(conn, "users", "tenant_id"):
        op.add_column("users", sa.Column("tenant_id", sa.String(length=64), nullable=True))
    if not column_exists(conn, "users", "role"):
        op.add_column("users", sa.Column("role", sa.String(length=32), nullable=True))
    if not column_exists(conn, "users", "status"):
        op.add_column("users", sa.Column("status", sa.String(length=32), nullable=True, server_default="active"))


def downgrade() -> None:
    conn = op.get_bind()

    # Drop added columns
    for col in ["absolute_expires_at", "revoke_reason", "rotated_from_session_id", "csrf_token_hash", "last_seen_at", "user_agent_hash", "ip_prefix"]:
        if column_exists(conn, "sessions", col):
            op.drop_column("sessions", col)

    for col in ["tenant_id", "role", "status"]:
        if column_exists(conn, "users", col):
            op.drop_column("users", col)

    for tbl in ["events", "audit_log", "oauth_identities", "user_preferences"]:
        if table_exists(conn, tbl):
            op.drop_table(tbl)
