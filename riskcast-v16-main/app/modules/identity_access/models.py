"""
Identity & Access Models
SQLAlchemy models for authentication (sessions and API keys)
RISKCAST V3 - Modular Monolith
"""
from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Enum as SQLEnum,
    Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base
from app.shared.models import BaseMixin


class ActorType(str, enum.Enum):
    """Actor type for authentication"""
    USER = "USER"
    API_KEY = "API_KEY"
    SYSTEM = "SYSTEM"


class Session(Base, BaseMixin):
    """
    Session Model
    
    Web session for user authentication.
    Stores session token hash and metadata.
    """
    __tablename__ = "sessions"
    
    user_id = Column(String(26), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_sessions_user_expires", "user_id", "expires_at"),
    )
    
    def __repr__(self):
        return f"<Session(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at


class ApiKeyStatus(str, enum.Enum):
    """API Key status"""
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class ApiKey(Base, BaseMixin):
    """
    API Key Model
    
    API key for programmatic access.
    Keys are hashed before storage, raw key shown only once.
    """
    __tablename__ = "api_keys"
    
    tenant_id = Column(String(26), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # For display, e.g., "sk_live_..."
    scopes_json = Column(JSON, nullable=True, default=list)  # List of permission keys
    status = Column(
        SQLEnum(ApiKeyStatus, native_enum=False),
        default=ApiKeyStatus.ACTIVE,
        nullable=False,
        index=True
    )
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    created_by_user_id = Column(String(26), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    # Indexes
    __table_args__ = (
        Index("idx_api_keys_tenant_status", "tenant_id", "status"),
        {'extend_existing': True}
    )
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name}, tenant_id={self.tenant_id}, status={self.status.value})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if API key is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if API key is valid (active and not expired)"""
        return self.status == ApiKeyStatus.ACTIVE and not self.is_expired
