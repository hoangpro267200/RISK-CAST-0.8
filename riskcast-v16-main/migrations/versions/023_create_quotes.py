"""Create quotes table with versioning support

Revision ID: 023_create_quotes
Revises: 022_enhance_underwriting_submissions
Create Date: 2025-01-23

Creates quotes table with versioning support for immutable quote snapshots.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '023_create_quotes'
down_revision = '022_enhance_underwriting_submissions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if table exists
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    table_exists = 'quotes' in inspector.get_table_names()
    
    if not table_exists:
        op.create_table(
            'quotes',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('tenant_id', sa.String(length=26), nullable=False),  # ULID
            
            # Reference
            sa.Column('quote_number', sa.String(length=50), nullable=False),
            sa.Column('submission_id', sa.String(length=26), nullable=False),  # ULID
            
            # Versioning
            sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='0'),  # MySQL boolean
            sa.Column('replaces_quote_id', sa.String(length=36), nullable=True),  # UUID
            
            # Status
            sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
            # DRAFT, ISSUED, ACCEPTED, DECLINED, EXPIRED, REPLACED
            
            # Pinned references (immutable after ISSUED)
            sa.Column('model_version_id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('risk_run_id', sa.String(length=26), nullable=False),  # ULID
            sa.Column('evidence_bundle_id', sa.String(length=36), nullable=True),  # UUID
            
            # Pricing snapshot (immutable)
            sa.Column('pricing_snapshot_json', sa.JSON(), nullable=False),
            
            # Coverage terms (immutable)
            sa.Column('coverage_terms_json', sa.JSON(), nullable=False),
            
            # Risk summary (immutable)
            sa.Column('risk_summary_json', sa.JSON(), nullable=True),
            
            # Quote hash (for integrity verification)
            sa.Column('quote_hash', sa.String(length=64), nullable=False, server_default='', index=True),
            
            # Validity
            sa.Column('valid_from', sa.DateTime(), nullable=False),
            sa.Column('valid_until', sa.DateTime(), nullable=False),
            
            # Timestamps
            sa.Column('issued_at', sa.DateTime(), nullable=True),
            sa.Column('issued_by_user_id', sa.String(length=26), nullable=True),  # ULID
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            
            sa.ForeignKeyConstraint(['submission_id'], ['underwriting_submissions.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['replaces_quote_id'], ['quotes.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['model_version_id'], ['risk_model_versions.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['risk_run_id'], ['risk_runs.id'], ondelete='RESTRICT'),
            sa.ForeignKeyConstraint(['evidence_bundle_id'], ['evidence_bundles.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['issued_by_user_id'], ['users.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Unique constraints
        op.create_unique_constraint('uq_quote_version', 'quotes', ['tenant_id', 'quote_number', 'version'])
        
        # Indexes
        op.create_index('idx_quotes_tenant', 'quotes', ['tenant_id'], unique=False)
        op.create_index('idx_quotes_submission', 'quotes', ['submission_id'], unique=False)
        op.create_index('idx_quotes_status', 'quotes', ['status'], unique=False)
        op.create_index('idx_quotes_latest', 'quotes', ['submission_id', 'is_latest'], unique=False)
        op.create_index('idx_quotes_hash', 'quotes', ['quote_hash'], unique=False)
        op.create_index('idx_quotes_valid_until', 'quotes', ['valid_until'], unique=False)
        op.create_index('idx_quotes_quote_number', 'quotes', ['quote_number'], unique=False)


def downgrade() -> None:
    # Drop indexes
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'quotes' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('quotes')]
        
        if 'idx_quotes_quote_number' in existing_indexes:
            op.drop_index('idx_quotes_quote_number', table_name='quotes')
        if 'idx_quotes_valid_until' in existing_indexes:
            op.drop_index('idx_quotes_valid_until', table_name='quotes')
        if 'idx_quotes_hash' in existing_indexes:
            op.drop_index('idx_quotes_hash', table_name='quotes')
        if 'idx_quotes_latest' in existing_indexes:
            op.drop_index('idx_quotes_latest', table_name='quotes')
        if 'idx_quotes_status' in existing_indexes:
            op.drop_index('idx_quotes_status', table_name='quotes')
        if 'idx_quotes_submission' in existing_indexes:
            op.drop_index('idx_quotes_submission', table_name='quotes')
        if 'idx_quotes_tenant' in existing_indexes:
            op.drop_index('idx_quotes_tenant', table_name='quotes')
        
        # Drop unique constraint
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('quotes')]
        if 'uq_quote_version' in existing_constraints:
            op.drop_constraint('uq_quote_version', 'quotes', type_='unique')
        
        op.drop_table('quotes')
