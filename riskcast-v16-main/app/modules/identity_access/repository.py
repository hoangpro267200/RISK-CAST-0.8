"""
Identity & Access Repository
Data access layer for authentication and user management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import secrets

from app.modules.identity_access.models import User, Session as SessionModel
from app.shared.exceptions import NotFoundError, ConflictError
from app.config import settings


class IdentityRepository:
    """Repository for identity and access data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # User methods
    def create_user(self, user_data: dict) -> User:
        """Create a new user"""
        # Check if email exists
        existing = self.db.query(User).filter(
            User.email == user_data["email"],
            User.deleted_at.is_(None)
        ).first()
        if existing:
            raise ConflictError(
                f"User with email '{user_data['email']}' already exists",
                resource="user"
            )
        
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(
            User.id == user_id,
            User.deleted_at.is_(None)
        ).first()
    
    def get_user_by_email(self, email: str, tenant_id: Optional[str] = None) -> Optional[User]:
        """Get user by email"""
        query = self.db.query(User).filter(
            User.email == email,
            User.deleted_at.is_(None)
        )
        if tenant_id:
            query = query.filter(User.tenant_id == tenant_id)
        return query.first()
    
    def update_user(self, user_id: str, update_data: dict) -> User:
        """Update user"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        
        for key, value in update_data.items():
            setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    # Session methods
    def create_session(self, user_id: str, token: str, expires_at: datetime, 
                      ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> SessionModel:
        """Create a new session"""
        token_hash = self._hash_token(token)
        
        session = SessionModel(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_session_by_token(self, token: str) -> Optional[SessionModel]:
        """Get session by token"""
        token_hash = self._hash_token(token)
        return self.db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash,
            SessionModel.expires_at > datetime.utcnow(),
            SessionModel.revoked_at.is_(None)
        ).first()
    
    def revoke_session(self, token: str) -> bool:
        """Revoke a session"""
        session = self.get_session_by_token(token)
        if not session:
            return False
        
        session.revoked_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a user"""
        count = self.db.query(SessionModel).filter(
            SessionModel.user_id == user_id,
            SessionModel.revoked_at.is_(None)
        ).update({"revoked_at": datetime.utcnow()})
        self.db.commit()
        return count
    
    @staticmethod
    def _hash_token(token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
