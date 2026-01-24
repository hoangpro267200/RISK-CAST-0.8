"""Create SLA monitoring tables.

Revision ID: 033_create_sla_monitoring
Revises: 032_create_corridor_intelligence
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '033_create_sla_monitoring'
down_revision = '032_create_corridor_intelligence'
branch_labels = None
depends_on = None


def upgrade():
    # SLA definitions
    op.create_table(
        'sla_definitions',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),  # NULL for system-wide SLAs
        
        # Identification
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False),
        # AVAILABILITY, RESPONSE_TIME, PROCESSING_TIME, DATA_QUALITY
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        
        # Metrics
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_unit', sa.String(length=50), nullable=True),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('warning_threshold', sa.Float(), nullable=True),
        sa.Column('critical_threshold', sa.Float(), nullable=True),
        sa.Column('comparison', sa.String(length=10), nullable=False),  # >=, <=, ==
        
        # Measurement
        sa.Column('measurement_window', sa.String(length=20), nullable=True),  # HOURLY, DAILY, WEEKLY, MONTHLY
        sa.Column('measurement_config_json', sa.JSON(), nullable=True),
        
        # Contractual
        sa.Column('contract_reference', sa.String(length=255), nullable=True),
        sa.Column('penalty_config_json', sa.JSON(), nullable=True),
        # {
        #   "penalty_type": "CREDIT",
        #   "penalty_per_violation_pct": 5,
        #   "max_monthly_penalty_pct": 25
        # }
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_sla_def_tenant', ondelete='CASCADE')
    )
    
    # SLA measurements
    op.create_table(
        'sla_measurements',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('sla_definition_id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        
        # Measurement period
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        
        # Results
        sa.Column('measured_value', sa.Float(), nullable=False),
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        # MET, WARNING, BREACHED
        
        # Details
        sa.Column('sample_count', sa.Integer(), nullable=True),
        sa.Column('details_json', sa.JSON(), nullable=True),
        # {
        #   "breakdown": [...],
        #   "outliers": [...],
        #   "notes": "..."
        # }
        
        # Timestamps
        sa.Column('measured_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['sla_definition_id'], ['sla_definitions.id'], name='fk_measurement_sla_def', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_measurement_tenant', ondelete='SET NULL')
    )
    
    # SLA breaches
    op.create_table(
        'sla_breaches',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('sla_definition_id', sa.String(length=26), nullable=False),
        sa.Column('measurement_id', sa.String(length=26), nullable=False),
        sa.Column('tenant_id', sa.String(length=26), nullable=True),
        
        # Breach details
        sa.Column('severity', sa.String(length=20), nullable=False),  # WARNING, CRITICAL
        sa.Column('target_value', sa.Float(), nullable=False),
        sa.Column('actual_value', sa.Float(), nullable=False),
        sa.Column('variance', sa.Float(), nullable=False),
        
        # Resolution
        sa.Column('status', sa.String(length=20), nullable=False, server_default='OPEN'),
        # OPEN, ACKNOWLEDGED, RESOLVED, CREDITED
        sa.Column('root_cause', sa.Text(), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        
        # Penalty
        sa.Column('penalty_applied', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('penalty_amount_cents', sa.Integer(), nullable=True),
        sa.Column('penalty_currency', sa.String(length=3), nullable=True),
        
        # Timestamps
        sa.Column('occurred_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('acknowledged_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by_user_id', sa.String(length=26), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['sla_definition_id'], ['sla_definitions.id'], name='fk_breach_sla_def', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['measurement_id'], ['sla_measurements.id'], name='fk_breach_measurement', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], name='fk_breach_tenant', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['acknowledged_by_user_id'], ['users.id'], name='fk_breach_acknowledged_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolved_by_user_id'], ['users.id'], name='fk_breach_resolved_by', ondelete='SET NULL')
    )
    
    # Indexes
    op.create_index('idx_sla_defs_tenant', 'sla_definitions', ['tenant_id'])
    op.create_index('idx_sla_defs_category', 'sla_definitions', ['category'])
    op.create_index('idx_sla_defs_status', 'sla_definitions', ['status'])
    op.create_index('idx_sla_measurements_def', 'sla_measurements', ['sla_definition_id'])
    op.create_index('idx_sla_measurements_period', 'sla_measurements', ['period_start', 'period_end'])
    op.create_index('idx_sla_measurements_status', 'sla_measurements', ['status'])
    op.create_index('idx_sla_breaches_def', 'sla_breaches', ['sla_definition_id'])
    op.create_index('idx_sla_breaches_status', 'sla_breaches', ['status'])
    op.create_index('idx_sla_breaches_severity', 'sla_breaches', ['severity'])
    op.create_index('idx_sla_breaches_occurred', 'sla_breaches', ['occurred_at'])


def downgrade():
    op.drop_table('sla_breaches')
    op.drop_table('sla_measurements')
    op.drop_table('sla_definitions')
