"""Create premium allocation tables.

Revision ID: 036_create_premium_allocations
Revises: 035_create_runbooks
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '036_create_premium_allocations'
down_revision = '035_create_runbooks'
branch_labels = None
depends_on = None


def upgrade():
    # Premium allocation rules
    op.create_table(
        'premium_allocation_rules',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        
        # Identification
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        # ACTIVE, INACTIVE
        
        # Scope
        sa.Column('scope_type', sa.String(length=50), nullable=True),  # CORRIDOR, PRODUCT, CARRIER, DEFAULT
        sa.Column('scope_id', sa.String(length=26), nullable=True),
        
        # Allocation parties
        sa.Column('allocations_json', sa.JSON(), nullable=False),
        # [
        #   {"party_type": "INSURER", "party_id": "...", "share_pct": 70, "commission_pct": 0},
        #   {"party_type": "REINSURER", "party_id": "...", "share_pct": 25, "commission_pct": 5},
        #   {"party_type": "BROKER", "party_id": "...", "share_pct": 0, "commission_pct": 5}
        # ]
        
        # Effective dates
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by_user_id', sa.String(length=26), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='SET NULL'),
    )
    
    # Premium allocations (actual splits per policy)
    op.create_table(
        'premium_allocations',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        
        # Policy reference
        sa.Column('policy_id', sa.String(length=26), nullable=False),
        sa.Column('rule_id', sa.String(length=26), nullable=True),
        
        # Total premium
        sa.Column('total_premium_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        
        # Allocations
        sa.Column('allocations_json', sa.JSON(), nullable=False),
        # [
        #   {
        #     "party_type": "INSURER",
        #     "party_id": "...",
        #     "party_name": "...",
        #     "premium_share_cents": 70000,
        #     "commission_cents": 0,
        #     "net_amount_cents": 70000
        #   }
        # ]
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ALLOCATED'),
        # ALLOCATED, SETTLED, RECONCILED
        
        # Settlement tracking
        sa.Column('settlements_json', sa.JSON(), nullable=True),
        # [
        #   {"party_id": "...", "amount_cents": 70000, "settled_at": "...", "reference": "..."}
        # ]
        
        # Timestamps
        sa.Column('allocated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('settled_at', sa.DateTime(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['rule_id'], ['premium_allocation_rules.id'], ondelete='SET NULL'),
    )
    
    # Indexes
    op.create_index('idx_alloc_rules_tenant', 'premium_allocation_rules', ['tenant_id'])
    op.create_index('idx_alloc_rules_scope', 'premium_allocation_rules', ['scope_type', 'scope_id'])
    op.create_index('idx_alloc_rules_status', 'premium_allocation_rules', ['status'])
    op.create_index('idx_alloc_rules_effective', 'premium_allocation_rules', ['effective_from', 'effective_to'])
    op.create_index('idx_allocations_policy', 'premium_allocations', ['policy_id'])
    op.create_index('idx_allocations_status', 'premium_allocations', ['status'])
    op.create_index('idx_allocations_tenant', 'premium_allocations', ['tenant_id'])


def downgrade():
    op.drop_index('idx_allocations_tenant', table_name='premium_allocations')
    op.drop_index('idx_allocations_status', table_name='premium_allocations')
    op.drop_index('idx_allocations_policy', table_name='premium_allocations')
    op.drop_index('idx_alloc_rules_effective', table_name='premium_allocation_rules')
    op.drop_index('idx_alloc_rules_status', table_name='premium_allocation_rules')
    op.drop_index('idx_alloc_rules_scope', table_name='premium_allocation_rules')
    op.drop_index('idx_alloc_rules_tenant', table_name='premium_allocation_rules')
    op.drop_table('premium_allocations')
    op.drop_table('premium_allocation_rules')
