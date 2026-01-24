"""Create evidence bundles tables

Revision ID: 021_evidence_bundles
Revises: 020_enhance_model_versioning_detailed
Create Date: 2025-01-23

Creates evidence bundles tables for grouping related evidence objects with manifest hash.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '021_evidence_bundles'
down_revision = '020_enhance_model_versioning_detailed'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Create evidence_bundles table
    table_exists = 'evidence_bundles' in inspector.get_table_names()
    
    if not table_exists:
        op.create_table(
            'evidence_bundles',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('tenant_id', sa.String(length=36), nullable=False),  # UUID
            
            # Bundle identification
            sa.Column('name', sa.String(length=255), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('bundle_type', sa.String(length=50), nullable=False),
            # UNDERWRITING, CLAIM, TRIGGER, ASSESSMENT, POLICY, EXPORT
            
            # Status
            sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
            # OPEN (can add items), SEALED (immutable), ARCHIVED
            
            # Manifest
            sa.Column('manifest_json', sa.JSON(), nullable=True, server_default='{}'),
            # {
            #   "items": [
            #     {"evidence_id": "...", "content_hash": "...", "added_at": "..."},
            #     ...
            #   ],
            #   "item_count": 5,
            #   "total_size_bytes": 12345
            # }
            sa.Column('manifest_hash', sa.String(length=64), nullable=True),  # SHA256 of manifest
            
            # Compliance
            sa.Column('retention_class', sa.String(length=50), nullable=False, server_default='STANDARD'),
            # STANDARD (7 years), REGULATORY (10 years), LEGAL_HOLD (indefinite)
            sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='0'),  # MySQL uses 0/1
            sa.Column('legal_hold_reason', sa.Text(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            
            # PII tracking
            sa.Column('contains_pii', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('pii_categories', sa.JSON(), nullable=True, server_default='[]'),
            # ["name", "address", "financial"]
            
            # Audit
            sa.Column('created_by_user_id', sa.String(length=36), nullable=True),  # UUID
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('sealed_at', sa.DateTime(), nullable=True),
            sa.Column('sealed_by_user_id', sa.String(length=36), nullable=True),  # UUID
            
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create evidence_bundle_items table
        op.create_table(
            'evidence_bundle_items',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('bundle_id', sa.String(length=36), nullable=False),  # UUID (FK)
            sa.Column('evidence_id', sa.String(length=36), nullable=False),  # UUID (FK)
            
            # Item metadata within bundle
            sa.Column('sequence', sa.Integer(), nullable=True),  # Order within bundle
            sa.Column('role', sa.String(length=50), nullable=True),  # PRIMARY, SUPPORTING, REFERENCE
            sa.Column('description', sa.Text(), nullable=True),
            
            # Hash at time of addition (for integrity)
            sa.Column('content_hash_at_addition', sa.String(length=64), nullable=False),
            
            sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('added_by_user_id', sa.String(length=36), nullable=True),  # UUID
            
            sa.ForeignKeyConstraint(['bundle_id'], ['evidence_bundles.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['evidence_id'], ['evidence_objects.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('bundle_id', 'evidence_id', name='uq_bundle_evidence')
        )
        
        # Create evidence_bundle_links table
        op.create_table(
            'evidence_bundle_links',
            sa.Column('id', sa.String(length=36), nullable=False),  # UUID
            sa.Column('bundle_id', sa.String(length=36), nullable=False),  # UUID (FK)
            
            # Polymorphic link
            sa.Column('entity_type', sa.String(length=100), nullable=False),
            # policy, claim, trigger_event, risk_run, underwriting_submission, quote
            sa.Column('entity_id', sa.String(length=36), nullable=False),  # UUID
            
            # Link type
            sa.Column('link_type', sa.String(length=50), nullable=False, server_default='PRIMARY'),
            # PRIMARY, SUPPLEMENTARY, REFERENCE
            
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            
            sa.ForeignKeyConstraint(['bundle_id'], ['evidence_bundles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('bundle_id', 'entity_type', 'entity_id', name='uq_bundle_entity')
        )
        
        # Create indexes for evidence_bundles
        op.create_index('idx_evidence_bundles_tenant', 'evidence_bundles', ['tenant_id'], unique=False)
        op.create_index('idx_evidence_bundles_type', 'evidence_bundles', ['bundle_type'], unique=False)
        op.create_index('idx_evidence_bundles_status', 'evidence_bundles', ['status'], unique=False)
        op.create_index('idx_evidence_bundles_created_by', 'evidence_bundles', ['created_by_user_id'], unique=False)
        
        # Create indexes for evidence_bundle_items
        op.create_index('idx_bundle_items_bundle', 'evidence_bundle_items', ['bundle_id'], unique=False)
        op.create_index('idx_bundle_items_evidence', 'evidence_bundle_items', ['evidence_id'], unique=False)
        
        # Create indexes for evidence_bundle_links
        op.create_index('idx_bundle_links_bundle', 'evidence_bundle_links', ['bundle_id'], unique=False)
        op.create_index('idx_bundle_links_entity', 'evidence_bundle_links', ['entity_type', 'entity_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Drop indexes for evidence_bundle_links
    if 'evidence_bundle_links' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_bundle_links')]
        if 'idx_bundle_links_entity' in existing_indexes:
            op.drop_index('idx_bundle_links_entity', table_name='evidence_bundle_links')
        if 'idx_bundle_links_bundle' in existing_indexes:
            op.drop_index('idx_bundle_links_bundle', table_name='evidence_bundle_links')
    
    # Drop indexes for evidence_bundle_items
    if 'evidence_bundle_items' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_bundle_items')]
        if 'idx_bundle_items_evidence' in existing_indexes:
            op.drop_index('idx_bundle_items_evidence', table_name='evidence_bundle_items')
        if 'idx_bundle_items_bundle' in existing_indexes:
            op.drop_index('idx_bundle_items_bundle', table_name='evidence_bundle_items')
    
    # Drop indexes for evidence_bundles
    if 'evidence_bundles' in inspector.get_table_names():
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('evidence_bundles')]
        if 'idx_evidence_bundles_created_by' in existing_indexes:
            op.drop_index('idx_evidence_bundles_created_by', table_name='evidence_bundles')
        if 'idx_evidence_bundles_status' in existing_indexes:
            op.drop_index('idx_evidence_bundles_status', table_name='evidence_bundles')
        if 'idx_evidence_bundles_type' in existing_indexes:
            op.drop_index('idx_evidence_bundles_type', table_name='evidence_bundles')
        if 'idx_evidence_bundles_tenant' in existing_indexes:
            op.drop_index('idx_evidence_bundles_tenant', table_name='evidence_bundles')
    
    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('evidence_bundle_links')
    op.drop_table('evidence_bundle_items')
    op.drop_table('evidence_bundles')
