"""Seed roles and permissions

Revision ID: 006_seed_roles_permissions
Revises: 005_risk_runs
Create Date: 2024-12-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_seed_roles_permissions'
down_revision = '005_risk_runs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Seed initial roles and permissions.
    
    This migration creates:
    - All permissions from app.modules.rbac_policy.constants.Permissions
    - All roles from DEFAULT_ROLE_PERMISSIONS
    - Role-permission associations based on DEFAULT_ROLE_PERMISSIONS
    """
    # Import here to avoid circular dependencies
    from migrations.seed_data import seed_roles_and_permissions
    from app.database import SessionLocal
    
    # Get database connection from Alembic
    bind = op.get_bind()
    
    # Create session using the connection
    session = SessionLocal(bind=bind)
    
    try:
        seed_roles_and_permissions(session)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def downgrade() -> None:
    """
    Remove seeded roles and permissions.
    
    Note: This will delete ALL roles and permissions, not just seeded ones.
    Use with caution in production.
    """
    # Import here to avoid circular dependencies
    from migrations.seed_data import clear_roles_and_permissions
    from sqlalchemy.orm import sessionmaker
    
    # Get database connection from Alembic
    bind = op.get_bind()
    
    # Create session using the connection
    Session = sessionmaker(bind=bind)
    session = Session()
    
    try:
        clear_roles_and_permissions(session)
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
