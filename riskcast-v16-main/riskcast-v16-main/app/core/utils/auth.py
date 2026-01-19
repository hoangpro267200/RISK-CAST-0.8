"""
RISKCAST Security - JWT Authentication
Handles JWT token creation, verification, and refresh
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from fastapi import HTTPException, status
from functools import wraps
from fastapi import Request

# Get secret key from environment (must be set in production)
SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))


def create_jwt(payload: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token
    
    Args:
        payload: Dictionary containing token data (user_id, email, etc.)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    if not SECRET_KEY or SECRET_KEY == "dev-secret-key-change-in-production":
        raise ValueError("SECRET_KEY must be set in environment variables")
    
    to_encode = payload.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_jwt(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid, expired, or tampered
    """
    if not SECRET_KEY or SECRET_KEY == "dev-secret-key-change-in-production":
        raise ValueError("SECRET_KEY must be set in environment variables")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def refresh_jwt(old_token: str) -> str:
    """
    Refresh an access token
    
    Args:
        old_token: Existing JWT token
        
    Returns:
        New JWT token with extended expiration
    """
    payload = verify_jwt(old_token)
    
    # Remove expiration and issued at from payload
    payload.pop("exp", None)
    payload.pop("iat", None)
    payload.pop("type", None)
    
    # Create new token
    return create_jwt(payload)


def get_token_from_header(request: Request) -> Optional[str]:
    """
    Extract JWT token from Authorization header
    
    Args:
        request: FastAPI request object
        
    Returns:
        Token string or None
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None


def require_auth(f):
    """
    Decorator to require JWT authentication on routes
    
    Usage:
        @require_auth
        async def my_endpoint(request: Request):
            user_id = request.state.user_id
            ...
    """
    @wraps(f)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if not request:
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break
        
        if not request:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Request object not found"
            )
        
        token = get_token_from_header(request)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            payload = verify_jwt(token)
            request.state.user_id = payload.get("user_id")
            request.state.user_email = payload.get("email")
            request.state.jwt_payload = payload
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return await f(*args, **kwargs)
    
    return wrapper


def optional_auth(f):
    """
    Decorator for optional authentication (sets user info if token present)
    """
    @wraps(f)
    async def wrapper(*args, **kwargs):
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break
        
        if request:
            token = get_token_from_header(request)
            if token:
                try:
                    payload = verify_jwt(token)
                    request.state.user_id = payload.get("user_id")
                    request.state.user_email = payload.get("email")
                    request.state.jwt_payload = payload
                except:
                    pass  # Ignore invalid tokens for optional auth
        
        return await f(*args, **kwargs)
    
    return wrapper





















