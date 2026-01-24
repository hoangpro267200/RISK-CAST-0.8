"""Enhance trigger definitions table with additional fields

Revision ID: 028_enhance_trigger_definitions
Revises: 027_create_oracle_events
Create Date: 2025-01-23

Adds name, description, trigger_type, replaces_definition_id, scope_constraints_json,
corroboration_json, payout_structure_json, and published_by_user_id fields.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '028_enhance_trigger_definitions'
down_revision = '027_create_oracle_events'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables exist
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Enhance trigger_definitions table
    if 'trigger_definitions' in inspector.get_table_names():
        existing_columns = [col['name'] for col in inspector.get_columns('trigger_definitions')]
        
        # Add name
        if 'name' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('name', sa.String(length=100), nullable=True))
        
        # Add description
        if 'description' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('description', sa.Text(), nullable=True))
        
        # Add trigger_type (if different from type)
        if 'trigger_type' not in existing_columns:
            # Check if 'type' exists - if so, copy data
            if 'type' in existing_columns:
                op.add_column('trigger_definitions', sa.Column('trigger_type', sa.String(length=50), nullable=True))
                # Copy data from type to trigger_type
                op.execute("UPDATE trigger_definitions SET trigger_type = type WHERE trigger_type IS NULL")
            else:
                op.add_column('trigger_definitions', sa.Column('trigger_type', sa.String(length=50), nullable=True))
        
        # Add replaces_definition_id
        if 'replaces_definition_id' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('replaces_definition_id', sa.String(length=26), nullable=True))
        
        # Add scope_constraints_json
        if 'scope_constraints_json' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('scope_constraints_json', sa.JSON(), nullable=True))
        
        # Add corroboration_json
        if 'corroboration_json' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('corroboration_json', sa.JSON(), nullable=True))
        
        # Add payout_structure_json
        if 'payout_structure_json' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('payout_structure_json', sa.JSON(), nullable=True))
        
        # Add published_by_user_id
        if 'published_by_user_id' not in existing_columns:
            op.add_column('trigger_definitions', sa.Column('published_by_user_id', sa.String(length=26), nullable=True))
        
        # Create foreign key for replaces_definition_id
        existing_constraints = [c['name'] for c in inspector.get_foreign_keys('trigger_definitions')]
        if 'fk_trigger_def_replaces' not in existing_constraints:
            try:
                op.create_foreign_key(
                    'fk_trigger_def_replaces',
                    'trigger_definitions',
                    'trigger_definitions',
                    ['replaces_definition_id'],
                    ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                pass
        
        # Create foreign key for published_by_user_id
        if 'fk_trigger_def_published_by' not in existing_constraints:
            try:
                op.create_foreign_key(
                    'fk_trigger_def_published_by',
                    'trigger_definitions',
                    'users',
                    ['published_by_user_id'],
                    ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                pass
        
        # Create unique constraint for name+version per tenant
        existing_constraints = [c['name'] for c in inspector.get_unique_constraints('trigger_definitions')]
        if 'uq_trigger_def_version' not in existing_constraints:
            try:
                op.create_unique_constraint('uq_trigger_def_version', 'trigger_definitions', ['tenant_id', 'name', 'version'])
            except Exception:
                pass
        
        # Create indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('trigger_definitions')]
        
        if 'idx_trigger_defs_name' not in existing_indexes:
            op.create_index('idx_trigger_defs_name', 'trigger_definitions', ['name'], unique=False)
        if 'idx_trigger_defs_trigger_type' not in existing_indexes:
            op.create_index('idx_trigger_defs_trigger_type', 'trigger_definitions', ['trigger_type'], unique=False)
        if 'idx_trigger_defs_replaces' not in existing_indexes:
            op.create_index('idx_trigger_defs_replaces', 'trigger_definitions', ['replaces_definition_id'], unique=False)


def downgrade() -> None:
    # Note: We don't drop columns in downgrade to preserve data
    # If full rollback is needed, manually drop columns
    pass
