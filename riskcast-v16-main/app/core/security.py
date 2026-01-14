"""
Security utilities for API key authentication and request signing.

RISKCAST v17 - Production Security
"""

from fastapi import Header, HTTPException, Depends, Request
from typing import Optional, Callable
from datetime import datetime
import hmac
import hashlib
import json
import os


# ============================================================
# API KEY VERIFICATION
# ============================================================

async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    request: Request = None
):
    """
    Verify API key from request header.
    
    Usage:
        @router.get("/protected")
        async def protected_endpoint(api_key = Depends(verify_api_key)):
            # api_key is validated APIKey object
            return {"user_id": api_key.user_id}
    
    Returns:
        APIKey object if valid
    
    Raises:
        HTTPException 401 if key is missing or invalid
        HTTPException 403 if key is expired or revoked
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail={
                'error': 'API key required',
                'message': 'Include X-API-Key header with your API key'
            }
        )
    
    # Validate key format
    if not x_api_key.startswith('rsk_'):
        raise HTTPException(
            status_code=401,
            detail={
                'error': 'Invalid API key format',
                'message': 'API key should start with "rsk_"'
            }
        )
    
    try:
        # Import here to avoid circular imports
        from app.models.api_key import APIKey
        
        # Try to get database session
        try:
            from app.database import get_db
            db = next(get_db())
        except Exception:
            # If database not available, use simple validation
            # In production, this should always use the database
            print("[Security] Warning: Database not available for API key validation")
            # Return a mock object for development
            class MockAPIKey:
                user_id = "dev_user"
                organization_id = "dev_org"
                def has_scope(self, scope): return True
                def record_usage(self): pass
                def is_valid(self): return True
            return MockAPIKey()
        
        # Hash the provided key
        key_hash = APIKey.hash_key(x_api_key)
        
        # Look up in database
        api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail={'error': 'Invalid API key'}
            )
        
        if not api_key.is_valid():
            if api_key.revoked:
                raise HTTPException(
                    status_code=403,
                    detail={
                        'error': 'API key revoked',
                        'revoked_at': api_key.revoked_at.isoformat() if api_key.revoked_at else None,
                        'reason': api_key.revoked_reason
                    }
                )
            else:
                raise HTTPException(
                    status_code=403,
                    detail={
                        'error': 'API key expired',
                        'expired_at': api_key.expires_at.isoformat() if api_key.expires_at else None
                    }
                )
        
        # Update usage stats
        api_key.record_usage()
        db.commit()
        
        return api_key
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Security] Error validating API key: {e}")
        raise HTTPException(
            status_code=500,
            detail={'error': 'Error validating API key'}
        )


def require_scope(required_scope: str) -> Callable:
    """
    Dependency to check if API key has required scope.
    
    Usage:
        @router.post("/risk/analyze")
        async def analyze(
            api_key = Depends(verify_api_key),
            _ = Depends(require_scope("risk:analyze"))
        ):
            # Only keys with "risk:analyze" scope can access
    """
    async def scope_checker(api_key = Depends(verify_api_key)):
        if not api_key.has_scope(required_scope):
            raise HTTPException(
                status_code=403,
                detail={
                    'error': 'Insufficient permissions',
                    'required_scope': required_scope,
                    'message': f'API key missing required scope: {required_scope}'
                }
            )
        return api_key
    
    return scope_checker


def optional_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    """
    Optional API key verification - doesn't fail if missing.
    
    Usage:
        @router.get("/public")
        async def public_endpoint(api_key = Depends(optional_api_key)):
            if api_key:
                # Authenticated request
                return {"user": api_key.user_id}
            else:
                # Anonymous request
                return {"user": "anonymous"}
    """
    if not x_api_key:
        return None
    
    try:
        # Reuse verify_api_key logic
        return verify_api_key(x_api_key)
    except HTTPException:
        return None


# ============================================================
# REQUEST SIGNING
# ============================================================

def sign_payload(payload: dict, secret: str) -> str:
    """
    Generate HMAC-SHA256 signature for payload.
    
    Args:
        payload: Dictionary to sign
        secret: Secret key for signing
    
    Returns:
        Hex-encoded signature
    """
    # Serialize payload deterministically (sorted keys)
    payload_bytes = json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()
    
    # Generate HMAC signature
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signature(payload: dict, signature: str, secret: str) -> bool:
    """
    Verify payload signature.
    
    Returns:
        True if signature is valid, False otherwise
    """
    expected_signature = sign_payload(payload, secret)
    
    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


async def verify_request_signature(
    request: Request,
    x_signature: str = Header(..., alias="X-Signature")
):
    """
    FastAPI dependency to verify request signature.
    
    Usage:
        @router.post("/sensitive")
        async def sensitive_op(
            data: dict,
            _ = Depends(verify_request_signature)
        ):
            # Request signature verified
    
    Headers required:
        X-Signature: HMAC-SHA256 signature of request body
    """
    # Get secret from environment
    secret = os.getenv('REQUEST_SIGNING_SECRET')
    
    if not secret:
        raise HTTPException(
            status_code=500,
            detail={
                'error': 'Request signing not configured',
                'message': 'Set REQUEST_SIGNING_SECRET environment variable'
            }
        )
    
    # Get request body
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail={'error': 'Invalid JSON body'}
        )
    
    # Verify signature
    if not verify_signature(body, x_signature, secret):
        raise HTTPException(
            status_code=401,
            detail={
                'error': 'Invalid request signature',
                'message': 'Request body signature verification failed'
            }
        )
    
    return body


def generate_client_signature(payload: dict) -> str:
    """
    Generate signature for client-side use.
    
    This is a helper for testing - in production, clients
    should generate signatures themselves.
    """
    secret = os.getenv('REQUEST_SIGNING_SECRET', 'development-secret')
    return sign_payload(payload, secret)


# ============================================================
# SECURITY HEADERS
# ============================================================

def get_security_headers() -> dict:
    """Get recommended security headers."""
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
    }


# ============================================================
# PASSWORD UTILITIES
# ============================================================

def hash_password(password: str) -> str:
    """Hash password using bcrypt (if available) or SHA-256."""
    try:
        import bcrypt
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    except ImportError:
        # Fallback to SHA-256 with salt (less secure)
        import secrets
        salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}${hashed}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    try:
        import bcrypt
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ImportError:
        # Fallback to SHA-256
        if '$' in hashed:
            salt, stored_hash = hashed.split('$', 1)
            computed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
            return hmac.compare_digest(computed, stored_hash)
        return False
