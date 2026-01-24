"""Create loss experience tables.

Revision ID: 030_create_loss_experience
Revises: 029_enhance_trigger_events
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '030_create_loss_experience'
down_revision = '029_enhance_trigger_events'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'loss_experience_records',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=False),
        
        # Source references
        sa.Column('policy_id', sa.String(length=26), nullable=False),
        sa.Column('claim_id', sa.String(length=26), nullable=True),
        sa.Column('payout_id', sa.String(length=26), nullable=True),
        
        # Dimensions for analysis
        sa.Column('corridor_id', sa.String(length=26), nullable=True),
        sa.Column('carrier_id', sa.String(length=26), nullable=True),
        sa.Column('cargo_type', sa.String(length=100), nullable=True),
        sa.Column('coverage_type', sa.String(length=50), nullable=True),
        sa.Column('loss_type', sa.String(length=50), nullable=True),  # DAMAGE, LOSS, DELAY, etc.
        
        # Exposure
        sa.Column('exposure_cents', sa.BigInteger(), nullable=False),
        sa.Column('premium_cents', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='USD'),
        
        # Expected loss (from underwriting)
        sa.Column('expected_loss_cents', sa.BigInteger(), nullable=True),
        sa.Column('expected_loss_rate', sa.Float(), nullable=True),  # expected_loss / exposure
        sa.Column('risk_score_at_bind', sa.Float(), nullable=True),
        sa.Column('model_version_id', sa.String(length=26), nullable=True),
        
        # Actual loss
        sa.Column('actual_loss_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('actual_loss_rate', sa.Float(), nullable=True),  # actual_loss / exposure
        sa.Column('paid_loss_cents', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('reserved_loss_cents', sa.BigInteger(), nullable=False, server_default='0'),
        
        # Timing
        sa.Column('policy_effective_date', sa.Date(), nullable=False),
        sa.Column('loss_date', sa.Date(), nullable=True),
        sa.Column('reported_date', sa.Date(), nullable=True),
        sa.Column('settled_date', sa.Date(), nullable=True),
        
        # Status
        sa.Column('record_status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        # ACTIVE, SETTLED, CANCELLED
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        # Foreign keys (only add if tables exist)
        # Note: Some foreign key tables may not exist, so we'll make them optional
        # In production, you may want to check table existence before adding FKs
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_loss_exp_tenant'),
        sa.ForeignKeyConstraint(['policy_id'], ['policies.id'], name='fk_loss_exp_policy'),
        sa.ForeignKeyConstraint(['claim_id'], ['claims.id'], name='fk_loss_exp_claim', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['payout_id'], ['payouts.id'], name='fk_loss_exp_payout', ondelete='SET NULL'),
        # Optional foreign keys - only add if tables exist
        # sa.ForeignKeyConstraint(['corridor_id'], ['corridors.id'], name='fk_loss_exp_corridor', ondelete='SET NULL'),
        # sa.ForeignKeyConstraint(['carrier_id'], ['carriers.id'], name='fk_loss_exp_carrier', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['model_version_id'], ['risk_model_versions.id'], name='fk_loss_exp_model', ondelete='SET NULL'),
    )
    
    # Indexes for common queries
    op.create_index('idx_loss_exp_tenant', 'loss_experience_records', ['tenant_id'])
    op.create_index('idx_loss_exp_policy', 'loss_experience_records', ['policy_id'])
    op.create_index('idx_loss_exp_corridor', 'loss_experience_records', ['corridor_id'])
    op.create_index('idx_loss_exp_carrier', 'loss_experience_records', ['carrier_id'])
    op.create_index('idx_loss_exp_cargo', 'loss_experience_records', ['cargo_type'])
    op.create_index('idx_loss_exp_date', 'loss_experience_records', ['policy_effective_date'])
    op.create_index('idx_loss_exp_model', 'loss_experience_records', ['model_version_id'])
    op.create_index('idx_loss_exp_status', 'loss_experience_records', ['record_status'])


def downgrade():
    op.drop_table('loss_experience_records')
