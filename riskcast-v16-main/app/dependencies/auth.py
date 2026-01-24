"""
Authentication Dependencies

RISKCAST Auth System - Phase 1
FastAPI dependencies for authentication.
"""
from fastapi import Depends, HTTPException, status, Request, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import os

from app.database import get_db
from app.models.auth import User, Session as SessionModel
from app.config.auth import is_auth_enabled
from datetime import datetime, timedelta


async def get_current_user(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from session cookie.
    
    This is an optional dependency - returns None if auth is disabled or no session.
    Use require_auth() for routes that MUST have authentication.
    
    Args:
        request: FastAPI request
        session_token: Session token from cookie
        db: Database session
        
    Returns:
        User object if authenticated, None otherwise
    """
    # If auth is disabled, return None (no user required)
    if not is_auth_enabled():
        return None
    
    # If no session token, return None
    if not session_token:
        return None
    
    # Look up session in database
    token_hash = SessionModel.hash_token(session_token)
    session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash
    ).first()
    
    if not session or not session.is_valid():
        return None
    
    # Idle timeout refresh (throttled to every 5 minutes)
    idle_hours = SessionModel
    try:
        idle_expiry_hours = int(os.getenv("SESSION_EXPIRE_HOURS", "48"))
    except Exception:
        idle_expiry_hours = 48
    now = datetime.utcnow()
    if session.last_seen_at is None or (now - session.last_seen_at) > timedelta(minutes=5):
        session.last_seen_at = now
        session.expires_at = now + timedelta(hours=idle_expiry_hours)
        db.add(session)
        db.commit()
    
    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()
    
    if not user or not user.is_active:
        return None
    
    return user


async def require_auth(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require authentication - raises 401 if not authenticated.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: User = Depends(require_auth)):
            return {"user_id": user.id}
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if not authenticated
    """
    if not is_auth_enabled():
        # If auth is disabled, we can't require it
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled"
        )
    
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Cookie"},
        )
    
    return current_user
