"""
Account models: preferences, oauth identities, audit log, events.
Designed to be append-only/minimally mutating for compliance and SaaS readiness.

IMPORTANT: These models use AuthBase to stay isolated from other modules
that have conflicting class names (User, Tenant, Role, etc.)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator
import json

# Use AuthBase to avoid SQLAlchemy mapper conflicts
from app.models.auth import AuthBase as Base


class JSONType(TypeDecorator):
    """Platform-independent JSON type that works with SQLite, MySQL, PostgreSQL"""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


def json_column():
    """Return a JSON-compatible column type"""
    return JSONType


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), primary_key=True)
    timezone = Column(String(64), nullable=True)
    currency = Column(String(8), nullable=True)
    units = Column(String(16), nullable=True)  # e.g., metric/imperial
    theme = Column(String(16), nullable=True)  # e.g., light/dark/system
    personalization_opt_in = Column(Boolean, default=False, nullable=False)
    preferences_json = Column(json_column(), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class OAuthIdentity(Base):
    __tablename__ = "oauth_identities"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_provider_user"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(32), nullable=False)  # e.g., google
    provider_user_id = Column(String(128), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    disconnected_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action_type = Column(String(64), nullable=False)
    metadata_json = Column(json_column(), nullable=True)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class EventLog(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("auth_users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_name = Column(String(128), nullable=False)
    payload_json = Column(json_column(), nullable=True)
    ip = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
