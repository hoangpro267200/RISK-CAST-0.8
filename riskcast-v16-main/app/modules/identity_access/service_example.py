"""
Example Usage of Identity & Access Service

This file demonstrates how to use the authentication service.
"""
from sqlalchemy.orm import Session
from app.modules.identity_access.service import AuthService
from app.modules.identity_access.schemas import LoginRequest, ApiKeyCreate
import asyncio


async def example_login(db: Session):
    """Example: User login"""
    service = AuthService(db)
    
    response = await service.login(
        email="admin@acme.com",
        password="password123",
        tenant_id="tenant_123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )
    
    print(f"Login successful: {response.session_id}")
    print(f"Token: {response.token[:50]}...")
    return response


async def example_validate_session(db: Session, token: str):
    """Example: Validate session token"""
    service = AuthService(db)
    
    user = await service.validate_session(token)
    print(f"User authenticated: {user.email}")
    return user


async def example_create_api_key(db: Session, tenant_id: str, creator_id: str):
    """Example: Create API key"""
    service = AuthService(db)
    
    api_key_data = ApiKeyCreate(
        name="Production API Key",
        scopes=["risk:read", "risk:write"],
        expires_at=None  # No expiration
    )
    
    api_key, raw_key = await service.create_api_key(tenant_id, api_key_data, creator_id)
    
    print(f"Created API key: {api_key.id}")
    print(f"Raw key (store securely): {raw_key}")
    print(f"Key prefix: {api_key.key_prefix}")
    
    return api_key, raw_key


async def example_validate_api_key(db: Session, raw_key: str):
    """Example: Validate API key"""
    service = AuthService(db)
    
    api_key, tenant = await service.validate_api_key(raw_key)
    
    print(f"API key valid: {api_key.name}")
    print(f"Tenant: {tenant.name}")
    print(f"Scopes: {api_key.scopes_json}")
    
    return api_key, tenant


async def example_logout(db: Session, session_id: str):
    """Example: Logout"""
    service = AuthService(db)
    
    await service.logout(session_id)
    print(f"Session {session_id} invalidated")


if __name__ == "__main__":
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Example usage
        # response = asyncio.run(example_login(db))
        pass
    finally:
        db.close()
