"""
Operational runbook models.

Models for runbooks and their executions.
"""

from datetime import datetime
from typing import Optional
import sqlalchemy as sa
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Runbook(Base):
    """
    Runbook model.
    
    Represents an operational runbook for incident response, maintenance, etc.
    """
    __tablename__ = 'runbooks'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Identification
    runbook_id = Column(String(length=50), nullable=False, unique=True, index=True)
    title = Column(String(length=255), nullable=False)
    description = Column(Text(), nullable=True)
    
    # Classification
    category = Column(String(length=100), nullable=False, index=True)
    # INCIDENT_RESPONSE, DISASTER_RECOVERY, MAINTENANCE, DEPLOYMENT, SECURITY
    severity_level = Column(String(length=20), nullable=True)  # P1, P2, P3, P4
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='DRAFT', index=True)
    # DRAFT, PUBLISHED, DEPRECATED
    version = Column(Integer(), nullable=False, server_default='1')
    
    # Content
    trigger_conditions = Column(Text(), nullable=True)
    prerequisites_json = Column(sa.JSON(), nullable=True)
    steps_json = Column(sa.JSON(), nullable=False)
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
    
    rollback_steps_json = Column(sa.JSON(), nullable=True)
    escalation_path_json = Column(sa.JSON(), nullable=True)
    # {
    #   "level_1": {"role": "SRE", "response_time_minutes": 15},
    #   "level_2": {"role": "SRE_MANAGER", "response_time_minutes": 30},
    #   "level_3": {"role": "VP_ENGINEERING", "response_time_minutes": 60}
    # }
    
    # Metadata
    estimated_duration_minutes = Column(Integer(), nullable=True)
    last_tested_at = Column(DateTime(), nullable=True)
    test_results_json = Column(sa.JSON(), nullable=True)
    
    # Ownership
    owner_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    reviewer_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    published_at = Column(DateTime(), nullable=True)
    
    # Relationships
    executions = relationship('RunbookExecution', back_populates='runbook', lazy='select', order_by='desc(RunbookExecution.started_at)')
    
    def __repr__(self):
        return f"<Runbook(id={self.id}, runbook_id={self.runbook_id}, status={self.status})>"


class RunbookExecution(Base):
    """
    Runbook execution model.
    
    Tracks execution of a runbook step by step.
    """
    __tablename__ = 'runbook_executions'
    
    # Primary key
    id = Column(String(length=26), primary_key=True)
    
    # Foreign key
    runbook_id = Column(String(length=26), ForeignKey('runbooks.id'), nullable=False, index=True)
    
    # Execution details
    execution_type = Column(String(length=50), nullable=True, index=True)  # INCIDENT, TEST, MAINTENANCE
    incident_reference = Column(String(length=100), nullable=True)
    
    # Status
    status = Column(String(length=20), nullable=False, server_default='IN_PROGRESS', index=True)
    # IN_PROGRESS, COMPLETED, FAILED, ABORTED
    
    # Executor
    executed_by_user_id = Column(String(length=26), ForeignKey('users.id'), nullable=False)
    
    # Progress
    current_step = Column(Integer(), nullable=False, server_default='1')
    step_results_json = Column(sa.JSON(), nullable=True)
    # [
    #   {"step": 1, "status": "COMPLETED", "started_at": "...", "completed_at": "...", "notes": "..."}
    # ]
    
    # Outcome
    outcome_json = Column(sa.JSON(), nullable=True)
    # {
    #   "success": true,
    #   "duration_minutes": 45,
    #   "deviations": [...],
    #   "lessons_learned": "..."
    # }
    
    # Timestamps
    started_at = Column(DateTime(), nullable=False, index=True)
    completed_at = Column(DateTime(), nullable=True)
    
    # Relationships
    runbook = relationship('Runbook', foreign_keys=[runbook_id], back_populates='executions', lazy='select')
    
    def __repr__(self):
        return f"<RunbookExecution(id={self.id}, runbook_id={self.runbook_id}, status={self.status}, current_step={self.current_step})>"
