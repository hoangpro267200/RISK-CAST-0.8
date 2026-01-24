"""Create security control tables.

Revision ID: 034_create_security_controls
Revises: 033_create_sla_monitoring
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '034_create_security_controls'
down_revision = '033_create_sla_monitoring'
branch_labels = None
depends_on = None


def upgrade():
    # Security controls
    op.create_table(
        'security_controls',
        sa.Column('id', sa.String(length=26), primary_key=True),
        
        # Identification
        sa.Column('control_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Classification
        sa.Column('framework', sa.String(length=50), nullable=False, index=True),
        # SOC2, ISO27001, GDPR, PCI_DSS, NIST
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('subcategory', sa.String(length=100), nullable=True),
        
        # Control details
        sa.Column('control_type', sa.String(length=50), nullable=True),  # PREVENTIVE, DETECTIVE, CORRECTIVE
        sa.Column('implementation_type', sa.String(length=50), nullable=True),  # TECHNICAL, ADMINISTRATIVE, PHYSICAL
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='NOT_IMPLEMENTED', index=True),
        # NOT_IMPLEMENTED, IMPLEMENTED, PARTIALLY_IMPLEMENTED, NOT_APPLICABLE
        
        # Evidence requirements
        sa.Column('evidence_requirements_json', sa.JSON(), nullable=True),
        # {
        #   "required_evidence": ["policy_document", "audit_logs", "config_screenshots"],
        #   "review_frequency": "QUARTERLY"
        # }
        
        # Owner
        sa.Column('owner_user_id', sa.String(length=26), nullable=True),
        sa.Column('owner_role', sa.String(length=100), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], name='fk_control_owner', ondelete='SET NULL')
    )
    
    # Control assessments
    op.create_table(
        'control_assessments',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('control_id', sa.String(length=26), nullable=False),
        
        # Assessment details
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('assessor_user_id', sa.String(length=26), nullable=True),
        sa.Column('assessment_type', sa.String(length=50), nullable=True),  # INTERNAL, EXTERNAL, SELF
        
        # Results
        sa.Column('effectiveness', sa.String(length=20), nullable=False),
        # EFFECTIVE, PARTIALLY_EFFECTIVE, INEFFECTIVE
        sa.Column('maturity_level', sa.Integer(), nullable=True),  # 1-5
        sa.Column('risk_rating', sa.String(length=20), nullable=True),  # LOW, MEDIUM, HIGH, CRITICAL
        
        # Findings
        sa.Column('findings_json', sa.JSON(), nullable=True),
        # {
        #   "gaps": [...],
        #   "recommendations": [...],
        #   "compensating_controls": [...]
        # }
        
        # Evidence
        sa.Column('evidence_bundle_id', sa.String(length=26), nullable=True),
        sa.Column('evidence_summary', sa.Text(), nullable=True),
        
        # Next assessment
        sa.Column('next_assessment_date', sa.Date(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['control_id'], ['security_controls.id'], name='fk_assessment_control', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessor_user_id'], ['users.id'], name='fk_assessment_assessor', ondelete='SET NULL')
    )
    
    # Control remediation plans
    op.create_table(
        'control_remediation_plans',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('control_id', sa.String(length=26), nullable=False),
        sa.Column('assessment_id', sa.String(length=26), nullable=True),
        
        # Plan details
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),  # LOW, MEDIUM, HIGH, CRITICAL
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PLANNED', index=True),
        # PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
        
        # Timeline
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('completion_date', sa.Date(), nullable=True),
        
        # Owner
        sa.Column('owner_user_id', sa.String(length=26), nullable=True),
        
        # Actions
        sa.Column('actions_json', sa.JSON(), nullable=True),
        # [
        #   {"action": "...", "owner": "...", "status": "...", "due_date": "..."}
        # ]
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['control_id'], ['security_controls.id'], name='fk_remediation_control', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assessment_id'], ['control_assessments.id'], name='fk_remediation_assessment', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], name='fk_remediation_owner', ondelete='SET NULL')
    )
    
    # Indexes
    op.create_index('idx_controls_framework', 'security_controls', ['framework'])
    op.create_index('idx_controls_status', 'security_controls', ['status'])
    op.create_index('idx_controls_category', 'security_controls', ['category'])
    op.create_index('idx_assessments_control', 'control_assessments', ['control_id'])
    op.create_index('idx_assessments_date', 'control_assessments', ['assessment_date'])
    op.create_index('idx_assessments_effectiveness', 'control_assessments', ['effectiveness'])
    op.create_index('idx_assessments_next_date', 'control_assessments', ['next_assessment_date'])
    op.create_index('idx_remediation_control', 'control_remediation_plans', ['control_id'])
    op.create_index('idx_remediation_status', 'control_remediation_plans', ['status'])
    op.create_index('idx_remediation_priority', 'control_remediation_plans', ['priority'])
    op.create_index('idx_remediation_target_date', 'control_remediation_plans', ['target_date'])


def downgrade():
    op.drop_table('control_remediation_plans')
    op.drop_table('control_assessments')
    op.drop_table('security_controls')
