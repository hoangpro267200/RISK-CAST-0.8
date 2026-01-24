"""
Alembic Environment Configuration
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import app models for autogenerate
from app.database import Base
from app.config import settings

# Import all models so Alembic can detect them
# This ensures Alembic can autogenerate migrations for all tables
from app.modules.tenancy.models import Tenant
from app.modules.identity_access.models import User, Session
from app.modules.rbac_policy.models import Role, Permission, UserRole
from app.modules.risk_assessments.models import RiskAssessment
from app.modules.risk_runs.models import RiskRun
from app.modules.risk_engine_v3.models import RiskModelVersion
from app.modules.audit_ledger.models import AuditLedger
from app.modules.evidence.models import Evidence
from app.modules.underwriting.models import UnderwritingDecision
from app.modules.claims.models import Claim
from app.modules.parametric.models import ParametricTrigger

# Import shared models if any
from app.shared.models import BaseMixin, TenantScopedMixin

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set SQLAlchemy URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
