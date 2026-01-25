"""Production-grade auth system migration

Revision ID: auth_prod_001
Revises: 
Create Date: 2024-01-25

This migration adds:
- UUID field to auth_users
- Role and status fields
- Security tracking fields (last_login, failed_attempts, etc.)
- Email verification tokens table
- API keys table
- Refresh tokens table (for JWT mobile support)
- Enhanced session tracking
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'auth_prod_001'
down_revision = None  # Update this to your latest revision
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database dialect
    conn = op.get_bind()
    dialect = conn.dialect.name
    
    # Helper for UUID column
    uuid_type = sa.String(36)
    
    # Helper for JSON column (different for SQLite vs others)
    if dialect == 'sqlite':
        json_type = sa.Text()
    else:
        json_type = sa.JSON()
    
    # ========================================
    # Upgrade auth_users table
    # ========================================
    
    # Add new columns to auth_users (if they don't exist)
    try:
        op.add_column('auth_users', sa.Column('uuid', uuid_type, nullable=True, unique=True))
    except Exception:
        pass  # Column might already exist
    
    try:
        op.add_column('auth_users', sa.Column('status', sa.String(20), nullable=True, default='active'))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('role', sa.String(20), nullable=True, default='user'))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('last_login_at', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('last_login_ip', sa.String(45), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('failed_login_count', sa.Integer(), nullable=True, default=0))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('last_failed_login_at', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('locked_until', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('password_changed_at', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('tenant_id', uuid_type, nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_users', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    except Exception:
        pass
    
    # Create indexes
    try:
        op.create_index('idx_auth_user_uuid', 'auth_users', ['uuid'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_auth_user_status_role', 'auth_users', ['status', 'role'])
    except Exception:
        pass
    
    try:
        op.create_index('idx_auth_user_tenant', 'auth_users', ['tenant_id', 'status'])
    except Exception:
        pass
    
    # ========================================
    # Upgrade auth_sessions table
    # ========================================
    
    try:
        op.add_column('auth_sessions', sa.Column('rotated_to_session_id', sa.Integer(), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('auth_sessions', sa.Column('request_count', sa.Integer(), nullable=True, default=0))
    except Exception:
        pass
    
    try:
        op.add_column('auth_sessions', sa.Column('country_code', sa.String(2), nullable=True))
    except Exception:
        pass
    
    # Create indexes for sessions
    try:
        op.create_index('idx_session_valid', 'auth_sessions', ['token_hash', 'revoked_at', 'expires_at'])
    except Exception:
        pass
    
    # ========================================
    # Create email_verification_tokens table
    # ========================================
    
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    )
    
    # ========================================
    # Create api_keys table
    # ========================================
    
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('key_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('key_prefix', sa.String(8), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('tenant_id', uuid_type, nullable=True, index=True),
        sa.Column('scope', sa.String(20), nullable=False, default='read'),
        sa.Column('permissions', sa.Text(), nullable=True),  # JSON array
        sa.Column('allowed_ips', sa.Text(), nullable=True),  # JSON array
        sa.Column('allowed_origins', sa.Text(), nullable=True),  # JSON array
        sa.Column('expires_at', sa.DateTime(), nullable=True, index=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoke_reason', sa.String(255), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_ip', sa.String(45), nullable=True),
        sa.Column('use_count', sa.Integer(), nullable=False, default=0),
        sa.Column('rate_limit_per_minute', sa.Integer(), nullable=True),
        sa.Column('rate_limit_per_day', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    )
    
    op.create_index('idx_api_key_user_scope', 'api_keys', ['user_id', 'scope'])
    
    # ========================================
    # Create refresh_tokens table
    # ========================================
    
    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('token_hash', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('auth_users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('family_id', uuid_type, nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('revoke_reason', sa.String(128), nullable=True),
        sa.Column('rotated_from_id', sa.Integer(), nullable=True),
        sa.Column('device_id', sa.String(64), nullable=True, index=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
    )
    
    # ========================================
    # Update password_reset_tokens table
    # ========================================
    
    try:
        op.add_column('password_reset_tokens', sa.Column('requested_ip', sa.String(45), nullable=True))
    except Exception:
        pass
    
    try:
        op.add_column('password_reset_tokens', sa.Column('used_ip', sa.String(45), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    # Drop new tables
    op.drop_table('refresh_tokens')
    op.drop_table('api_keys')
    op.drop_table('email_verification_tokens')
    
    # Remove added columns from auth_users
    try:
        op.drop_column('auth_users', 'uuid')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'status')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'role')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'last_login_at')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'last_login_ip')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'failed_login_count')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'last_failed_login_at')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'locked_until')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'password_changed_at')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'tenant_id')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_users', 'deleted_at')
    except Exception:
        pass
    
    # Remove session columns
    try:
        op.drop_column('auth_sessions', 'rotated_to_session_id')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_sessions', 'request_count')
    except Exception:
        pass
    
    try:
        op.drop_column('auth_sessions', 'country_code')
    except Exception:
        pass
    
    # Remove password reset columns
    try:
        op.drop_column('password_reset_tokens', 'requested_ip')
    except Exception:
        pass
    
    try:
        op.drop_column('password_reset_tokens', 'used_ip')
    except Exception:
        pass
