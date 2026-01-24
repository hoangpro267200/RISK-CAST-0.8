"""Create runbook tables.

Revision ID: 035_create_runbooks
Revises: 034_create_security_controls
Create Date: 2026-01-23

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '035_create_runbooks'
down_revision = '034_create_security_controls'
branch_labels = None
depends_on = None


def upgrade():
    # Runbooks
    op.create_table(
        'runbooks',
        sa.Column('id', sa.String(length=26), primary_key=True),
        
        # Identification
        sa.Column('runbook_id', sa.String(length=50), nullable=False, unique=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Classification
        sa.Column('category', sa.String(length=100), nullable=False, index=True),
        # INCIDENT_RESPONSE, DISASTER_RECOVERY, MAINTENANCE, DEPLOYMENT, SECURITY
        sa.Column('severity_level', sa.String(length=20), nullable=True),  # P1, P2, P3, P4
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT', index=True),
        # DRAFT, PUBLISHED, DEPRECATED
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        
        # Content
        sa.Column('trigger_conditions', sa.Text(), nullable=True),
        sa.Column('prerequisites_json', sa.JSON(), nullable=True),
        sa.Column('steps_json', sa.JSON(), nullable=False),
        # [
        #   {
        #     "step_number": 1,
        #     "title": "Identify issue",
        #     "description": "...",
        #     "responsible_role": "SRE",
        #     "estimated_duration_minutes": 5,
        #     "automation_available": false,
        #     "commands": ["..."],
        #     "verification": "..."
        #   }
        # ]
        
        sa.Column('rollback_steps_json', sa.JSON(), nullable=True),
        sa.Column('escalation_path_json', sa.JSON(), nullable=True),
        # {
        #   "level_1": {"role": "SRE", "response_time_minutes": 15},
        #   "level_2": {"role": "SRE_MANAGER", "response_time_minutes": 30},
        #   "level_3": {"role": "VP_ENGINEERING", "response_time_minutes": 60}
        # }
        
        # Metadata
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('test_results_json', sa.JSON(), nullable=True),
        
        # Ownership
        sa.Column('owner_user_id', sa.String(length=26), nullable=True),
        sa.Column('reviewer_user_id', sa.String(length=26), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['owner_user_id'], ['users.id'], name='fk_runbook_owner', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewer_user_id'], ['users.id'], name='fk_runbook_reviewer', ondelete='SET NULL')
    )
    
    # Runbook executions
    op.create_table(
        'runbook_executions',
        sa.Column('id', sa.String(length=26), primary_key=True),
        sa.Column('runbook_id', sa.String(length=26), nullable=False),
        
        # Execution details
        sa.Column('execution_type', sa.String(length=50), nullable=True),  # INCIDENT, TEST, MAINTENANCE
        sa.Column('incident_reference', sa.String(length=100), nullable=True),
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='IN_PROGRESS', index=True),
        # IN_PROGRESS, COMPLETED, FAILED, ABORTED
        
        # Executor
        sa.Column('executed_by_user_id', sa.String(length=26), nullable=False),
        
        # Progress
        sa.Column('current_step', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('step_results_json', sa.JSON(), nullable=True),
        # [
        #   {"step": 1, "status": "COMPLETED", "started_at": "...", "completed_at": "...", "notes": "..."}
        # ]
        
        # Outcome
        sa.Column('outcome_json', sa.JSON(), nullable=True),
        # {
        #   "success": true,
        #   "duration_minutes": 45,
        #   "deviations": [...],
        #   "lessons_learned": "..."
        # }
        
        # Timestamps
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['runbook_id'], ['runbooks.id'], name='fk_execution_runbook', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['executed_by_user_id'], ['users.id'], name='fk_execution_executor', ondelete='RESTRICT')
    )
    
    # Indexes
    op.create_index('idx_runbooks_category', 'runbooks', ['category'])
    op.create_index('idx_runbooks_status', 'runbooks', ['status'])
    op.create_index('idx_runbooks_runbook_id', 'runbooks', ['runbook_id'])
    op.create_index('idx_executions_runbook', 'runbook_executions', ['runbook_id'])
    op.create_index('idx_executions_status', 'runbook_executions', ['status'])
    op.create_index('idx_executions_type', 'runbook_executions', ['execution_type'])
    op.create_index('idx_executions_started', 'runbook_executions', ['started_at'])


def downgrade():
    op.drop_table('runbook_executions')
    op.drop_table('runbooks')
