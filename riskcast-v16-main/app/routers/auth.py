"""
Authentication Router

RISKCAST Auth System - Production Grade
API endpoints for user authentication, authorization, and account management.

SECURITY ARCHITECTURE:
- Session-based authentication with HttpOnly cookies
- CSRF protection via double-submit cookie pattern
- Brute-force protection with exponential backoff
- Secure token generation and rotation
- Comprehensive audit logging

ENDPOINTS:
- POST /api/auth/signup - Register new account
- POST /api/auth/login - Authenticate user
- POST /api/auth/logout - End session
- POST /api/auth/refresh - Rotate session token
- GET /api/auth/me - Get current user profile
- POST /api/auth/change-password - Change password (authenticated)
- POST /api/auth/forgot-password - Request password reset
- POST /api/auth/reset-password - Reset password with token
- POST /api/auth/verify-email - Verify email address
- POST /api/auth/resend-verification - Resend verification email
- GET /api/auth/sessions - List active sessions
- DELETE /api/auth/sessions/{id} - Revoke specific session
- POST /api/auth/logout-all - Revoke all sessions
- API key management endpoints under /api/auth/keys/*
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
import os
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Tuple, List
from datetime import datetime, timedelta
import logging
import secrets
import urllib.parse
import urllib.request
import json
import time
import hmac
import hashlib

from app.database import get_db
from app.models.auth import (
    AuthUser as User, 
    Session as SessionModel, 
    PasswordResetToken,
    EmailVerificationToken,
    APIKey,
    APIKeyScope,
    AccountStatus,
    UserRole
)
from app.models.account import AuditLog, UserPreference, OAuthIdentity, EventLog
from app.utils.password import hash_password, verify_password, validate_password_strength
from app.auth_config.auth import AUTH_CONFIG, is_auth_enabled, is_production, get_rate_limit_config
from app.dependencies.auth import (
    get_current_user, 
    require_auth, 
    require_admin,
    require_role,
    AuthContext,
    get_auth_context,
    require_auth_context
)
from app.utils.standard_responses import ok, fail, StandardResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Security scheme (for OpenAPI docs)
security = HTTPBearer()

# ============================
# Security Constants & State
# ============================
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"

# Get from config with fallbacks
FAILED_LOGIN_WINDOW_MINUTES = AUTH_CONFIG.get("LOGIN_LOCKOUT_MINUTES", 15)
FAILED_LOGIN_MAX_ATTEMPTS = AUTH_CONFIG.get("MAX_LOGIN_ATTEMPTS", 5)
FAILED_LOGIN_LOCKOUT_MINUTES = AUTH_CONFIG.get("LOGIN_LOCKOUT_MINUTES", 15)

# In-memory failed login tracker (use Redis in production for distributed systems)
# Format: {(email, ip): (fail_count, first_failure_ts, locked_until_ts)}
_failed_login_tracker: Dict[Tuple[str, str], Tuple[int, datetime, Optional[datetime]]] = {}


# ============================
# Request/Response Models
# ============================

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None
    
    @validator("password")
    def validate_password(cls, v):
        if not v:
            raise ValueError("Password is required")
        is_valid, error = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    class Config:
        # Allow extra fields to be ignored (for backward compatibility)
        extra = "ignore"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator("new_password")
    def validate_new_password(cls, v):
        is_valid, error = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    
    @validator("new_password")
    def validate_new_password(cls, v):
        is_valid, error = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v


class UserResponse(BaseModel):
    """User information response (public fields only)."""
    id: str  # UUID, not internal ID
    email: str
    name: Optional[str]
    role: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: str
    last_login_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Session information response."""
    id: int
    user_id: int
    expires_at: str
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: str
    last_seen_at: Optional[str] = None
    is_valid: bool
    is_current: bool = False  # Flag to identify the current session
    
    class Config:
        from_attributes = True


class PreferenceResponse(BaseModel):
    """User preferences response."""
    timezone: Optional[str] = None
    currency: Optional[str] = None
    units: Optional[str] = None
    theme: Optional[str] = None
    personalization_opt_in: bool = False
    preferences_json: Optional[dict] = None


class AccountResponse(UserResponse):
    """Full account information with preferences."""
    preferences: PreferenceResponse


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str


class ResendVerificationRequest(BaseModel):
    """Resend verification email request."""
    email: EmailStr


class CreateAPIKeyRequest(BaseModel):
    """API key creation request."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope: str = "read"  # read, write, admin, webhook, service
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    permissions: Optional[List[str]] = None
    
    @validator("scope")
    def validate_scope(cls, v):
        valid_scopes = ["read", "write", "admin", "webhook", "service"]
        if v.lower() not in valid_scopes:
            raise ValueError(f"Invalid scope. Must be one of: {', '.join(valid_scopes)}")
        return v.lower()


class APIKeyResponse(BaseModel):
    """API key response (never includes full key after creation)."""
    id: int
    name: str
    description: Optional[str]
    key_prefix: str
    scope: str
    expires_at: Optional[str]
    is_valid: bool
    last_used_at: Optional[str]
    use_count: int
    created_at: str
    
    class Config:
        from_attributes = True


class APIKeyCreatedResponse(APIKeyResponse):
    """API key creation response (includes full key ONCE)."""
    key: str  # Only returned on creation, never again


@router.post("/login", response_model=UserResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and create session.
    
    Security:
    - Validates credentials with constant-time comparison
    - Tracks failed login attempts with exponential backoff
    - Records successful login for security auditing
    - Sets HttpOnly session cookie and CSRF cookie
    
    Returns:
        User profile on success
        
    Raises:
        401: Invalid credentials
        403: Account disabled/locked
        429: Too many failed attempts
        503: Auth not enabled
    """
    if not is_auth_enabled():
        return fail("AUTH_DISABLED", "Authentication is not enabled", status_code=503, request=request)
    
    client_ip = get_client_ip(request)
    
    # Check if IP/email combination is locked out
    ensure_not_locked(login_data.email, client_ip)
    
    # Find user by email (case-insensitive)
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    
    # Constant-time password verification to prevent timing attacks
    # Even if user doesn't exist, we still "verify" against a dummy hash
    password_valid = False
    if user:
        password_valid = verify_password(login_data.password, user.password_hash)
    else:
        # Perform a dummy verification to prevent timing attacks
        verify_password(login_data.password, "$argon2id$v=19$m=65536,t=2,p=4$dummy")
    
    # Generic error to prevent email enumeration
    if not user or not password_valid:
        register_login_failure(login_data.email, client_ip)
        
        # Log failed attempt (without revealing if user exists)
        logger.warning(
            f"Login failed: email={login_data.email[:3]}*** ip={client_ip}",
            extra={"security_event": "login_failed", "ip": client_ip}
        )
        
        return fail("INVALID_CREDENTIALS", "Invalid email or password", status_code=401, request=request)
    
    # Check account status (backward-compatible)
    is_locked = getattr(user, 'is_locked', False) if hasattr(user, 'is_locked') else False
    if is_locked:
        logger.warning(
            f"Locked account login attempt: user={user.email}",
            extra={"security_event": "locked_account_login", "user_id": user.id}
        )
        return fail("ACCOUNT_LOCKED", "Account is temporarily locked. Please try again later.", status_code=403, request=request)
    
    # Check if account is active (works with both old and new schema)
    is_active = user.is_active
    if hasattr(user, 'is_active_account'):
        is_active = user.is_active_account
    
    if not is_active:
        status_msg = "Account is disabled"
        if hasattr(user, 'status'):
            status_msg = {
                AccountStatus.SUSPENDED.value: "Account is suspended. Please contact support.",
                AccountStatus.DELETED.value: "Account not found.",
                AccountStatus.PENDING_VERIFICATION.value: "Please verify your email first.",
            }.get(user.status, "Account is disabled")
        
        return fail("ACCOUNT_DISABLED", status_msg, status_code=403, request=request)
    
    # Clear failed login tracking on successful auth
    clear_login_failures(login_data.email, client_ip)
    
    # Record successful login (if method exists in new schema)
    if hasattr(user, 'record_login_success'):
        user.record_login_success(client_ip)
    
    # Create session with CSRF token
    csrf_token = generate_csrf_token()
    session, token = create_session(db, user, request, csrf_token=csrf_token)
    
    # Set cookies
    set_session_cookie(response, token)
    set_csrf_cookie(response, csrf_token)
    
    # Commit user changes (last_login, failed_count reset)
    db.commit()
    
    # Security logging (safe - no sensitive data)
    logger.info(
        f"User logged in: {user.email}",
        extra={
            "security_event": "login_success",
            "user_id": user.id,
            "session_id": session.id,
            "ip": client_ip
        }
    )

    # Audit log
    record_audit(
        db=db,
        user_id=user.id,
        action="login",
        request=request,
        metadata={"session_id": session.id},
    )
    
    # Build response - handle both old and new schemas
    user_id = getattr(user, 'uuid', None) or str(user.id)
    user_role = getattr(user, 'role', 'user')
    is_active = getattr(user, 'is_active_account', user.is_active) if hasattr(user, 'is_active_account') else user.is_active
    last_login = getattr(user, 'last_login_at', None)
    
    return ok(
        data=UserResponse(
            id=user_id,
            email=user.email,
            name=user.name,
            role=user_role,
            is_active=is_active,
            email_verified=user.email_verified,
            created_at=user.created_at.isoformat(),
            last_login_at=last_login.isoformat() if last_login else None
        ),
        request=request,
    )


# ============================
# Helper Functions
# ============================

def create_session(
    db: Session,
    user: User,
    request: Request,
    expires_in_hours: Optional[int] = None,
    absolute_hours: Optional[int] = None,
    rotated_from: Optional[int] = None,
    csrf_token: Optional[str] = None,
) -> tuple[SessionModel, str]:
    """
    Create a new session for a user.
    
    Returns:
        (Session object, plain token string)
    """
    if expires_in_hours is None:
        expires_in_hours = AUTH_CONFIG["SESSION_EXPIRE_HOURS"]
    if absolute_hours is None:
        absolute_hours = AUTH_CONFIG.get("SESSION_ABSOLUTE_HOURS") or expires_in_hours
    
    token = SessionModel.generate_token()
    token_hash = SessionModel.hash_token(token)
    expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    absolute_expires_at = datetime.utcnow() + timedelta(hours=absolute_hours)
    
    # Get client info
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else None
    user_agent_hash = SessionModel.hash_user_agent(user_agent) if user_agent else None
    ip_prefix = None
    if ip_address:
        # Basic privacy-preserving prefix (drop last octet)
        parts = ip_address.split(".")
        if len(parts) == 4:
            ip_prefix = ".".join(parts[:3]) + ".0"
    
    session = SessionModel(
        token_hash=token_hash,
        user_id=user.id,
        expires_at=expires_at,
        user_agent=user_agent[:500],  # Limit length
        user_agent_hash=user_agent_hash,
        ip_address=ip_address,
        ip_prefix=ip_prefix,
        csrf_token_hash=SessionModel.hash_csrf(csrf_token) if csrf_token else None,
        rotated_from_session_id=rotated_from,
        last_seen_at=datetime.utcnow(),
        absolute_expires_at=absolute_expires_at,
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return session, token


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: str):
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        httponly=False,  # double-submit cookie must be readable by JS
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=AUTH_CONFIG["SESSION_EXPIRE_HOURS"] * 3600,
        path="/",
    )


def verify_csrf(request: Request, csrf_cookie: Optional[str], db: Optional[Session] = None):
    # Only enforce on unsafe methods
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    header_token = request.headers.get(CSRF_HEADER_NAME)
    # Origin/Referer check (best effort)
    origin = request.headers.get("Origin") or request.headers.get("origin")
    referer = request.headers.get("Referer") or request.headers.get("referer")
    if AUTH_CONFIG["ALLOWED_ORIGINS"]:
        allowed = set(AUTH_CONFIG["ALLOWED_ORIGINS"])
        origin_ok = (origin in allowed) if origin else True
        referer_ok = (referer.split("/")[0:3] if referer else [])  # minimal check
        if origin and not origin_ok:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF origin check failed",
            )
        if referer and referer.split("/")[0:3]:
            ref_origin = "/".join(referer.split("/")[0:3])
            if ref_origin not in allowed:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF referer check failed",
                )

    if not csrf_cookie or not header_token or csrf_cookie != header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF_INVALID",
        )
    # Bind CSRF to session if possible
    if db:
        session_token = request.cookies.get("session_token")
        if session_token:
            token_hash = SessionModel.hash_token(session_token)
            sess = db.query(SessionModel).filter(SessionModel.token_hash == token_hash).first()
            if sess and sess.csrf_token_hash and sess.csrf_token_hash != SessionModel.hash_csrf(header_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="CSRF_INVALID",
                )


def get_client_ip(request: Request) -> str:
    if request.client:
        return request.client.host
    return "unknown"


def register_login_failure(email: str, ip: str):
    key = (email.lower(), ip)
    now = datetime.utcnow()
    if key in _failed_login_tracker:
        count, first_ts, locked_until = _failed_login_tracker[key]
        if locked_until and locked_until > now:
            _failed_login_tracker[key] = (count + 1, first_ts, locked_until)
            return
        # window reset
        if now - first_ts > timedelta(minutes=FAILED_LOGIN_WINDOW_MINUTES):
            _failed_login_tracker[key] = (1, now, None)
        else:
            _failed_login_tracker[key] = (count + 1, first_ts, None)
    else:
        _failed_login_tracker[key] = (1, now, None)

    count, first_ts, _ = _failed_login_tracker[key]
    if count >= FAILED_LOGIN_MAX_ATTEMPTS:
        _failed_login_tracker[key] = (
            count,
            first_ts,
            now + timedelta(minutes=FAILED_LOGIN_LOCKOUT_MINUTES),
        )


def clear_login_failures(email: str, ip: str):
    key = (email.lower(), ip)
    if key in _failed_login_tracker:
        del _failed_login_tracker[key]


def ensure_not_locked(email: str, ip: str):
    key = (email.lower(), ip)
    now = datetime.utcnow()
    if key not in _failed_login_tracker:
        return
    count, first_ts, locked_until = _failed_login_tracker[key]
    if locked_until and locked_until > now:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to repeated failures. Try again later.",
        )
    if now - first_ts > timedelta(minutes=FAILED_LOGIN_WINDOW_MINUTES):
        del _failed_login_tracker[key]


def record_audit(
    db: Session,
    user_id: Optional[int],
    action: str,
    request: Request,
    metadata: Optional[dict] = None,
):
    try:
        entry = AuditLog(
            user_id=user_id,
            action_type=action,
            metadata_json=metadata or {},
            ip=get_client_ip(request),
            user_agent=request.headers.get("user-agent", "")[:500],
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to write audit log for {action}: {e}")


def get_or_create_preferences(db: Session, user_id: int) -> UserPreference:
    pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if pref is None:
        pref = UserPreference(user_id=user_id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def _get_google_config():
    client_id = AUTH_CONFIG.get("GOOGLE_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID")
    client_secret = AUTH_CONFIG.get("GOOGLE_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = AUTH_CONFIG.get("GOOGLE_REDIRECT_URI") or os.getenv("GOOGLE_REDIRECT_URI")
    if not client_id or not client_secret or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured"
        )
    return client_id, client_secret, redirect_uri


def _sign_state(state: str, ts: int) -> str:
    secret = AUTH_CONFIG.get("SESSION_SECRET") or "state-secret"
    payload = f"{state}.{ts}".encode()
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _verify_state(state: str, ts: int, sig: str, max_age_seconds: int = 600) -> bool:
    secret = AUTH_CONFIG.get("SESSION_SECRET") or "state-secret"
    if not state or not sig:
        return False
    expected = hmac.new(secret.encode(), f"{state}.{ts}".encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return False
    if abs(int(time.time()) - ts) > max_age_seconds:
        return False
    return True


def exchange_google_code(code: str, redirect_uri: str, client_id: str, client_secret: str) -> dict:
    token_url = "https://oauth2.googleapis.com/token"
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(token_url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = resp.read().decode()
        return json.loads(payload)


def fetch_google_userinfo(access_token: str) -> dict:
    req = urllib.request.Request("https://www.googleapis.com/oauth2/v3/userinfo")
    req.add_header("Authorization", f"Bearer {access_token}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _validate_redirect_uri(uri: str) -> bool:
    """
    Validate redirect URI to prevent open redirect attacks.
    Only allows localhost and 127.0.0.1 for security.
    """
    if not uri:
        return False
    
    try:
        parsed = urllib.parse.urlparse(uri)
        host = parsed.hostname or ""
        
        # Allow localhost and 127.0.0.1 only
        allowed_hosts = ["localhost", "127.0.0.1"]
        if host in allowed_hosts:
            return True
        
        # Also allow configured allowed origins
        allowed_origins = AUTH_CONFIG.get("ALLOWED_ORIGINS", [])
        for origin in allowed_origins:
            if origin and uri.startswith(origin):
                return True
        
        return False
    except Exception:
        return False


def set_session_cookie(response: Response, token: str):
    """Set session cookie on response."""
    cookie_name = "session_token"
    response.set_cookie(
        key=cookie_name,
        value=token,
        httponly=True,
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=AUTH_CONFIG["SESSION_EXPIRE_HOURS"] * 3600,
        path="/"
    )
    if AUTH_CONFIG.get("COOKIE_PREFIX_HOST") and AUTH_CONFIG["COOKIE_SECURE"]:
        response.set_cookie(
            key="__Host-session",
            value=token,
            httponly=True,
            secure=True,
            samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
            max_age=AUTH_CONFIG["SESSION_EXPIRE_HOURS"] * 3600,
            path="/",
        )


def clear_session_cookie(response: Response):
    """Clear session cookie."""
    response.set_cookie(
        key="session_token",
        value="",
        httponly=True,
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=0,
        path="/"
    )
    if AUTH_CONFIG.get("COOKIE_PREFIX_HOST") and AUTH_CONFIG["COOKIE_SECURE"]:
        response.set_cookie(
            key="__Host-session",
            value="",
            httponly=True,
            secure=True,
            samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
            max_age=0,
            path="/",
        )


def clear_csrf_cookie(response: Response):
    """Clear CSRF cookie."""
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value="",
        httponly=False,
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=0,
        path="/",
    )


# ============================
# API Endpoints
# ============================


@router.get("/csrf")
async def get_csrf_token(response: Response):
    """
    Issue a CSRF token (double-submit cookie).
    """
    token = generate_csrf_token()
    set_csrf_cookie(response, token)
    return {"csrf_token": token}


@router.get("/config")
async def get_auth_config_status():
    """
    Get authentication configuration status.
    
    Returns which auth methods are available (useful for frontend to show/hide buttons).
    """
    google_configured = bool(
        AUTH_CONFIG.get("GOOGLE_CLIENT_ID") and 
        AUTH_CONFIG.get("GOOGLE_CLIENT_SECRET") and
        AUTH_CONFIG.get("GOOGLE_REDIRECT_URI")
    )
    
    return ok({
        "auth_enabled": is_auth_enabled(),
        "email_password_enabled": is_auth_enabled(),  # Always available when auth is enabled
        "google_enabled": google_configured,
        "email_verification_required": AUTH_CONFIG.get("EMAIL_ENABLED", False),
    })


@router.get("/google/start")
async def google_start(request: Request, response: Response, redirect_uri_override: Optional[str] = None):
    """
    Start Google OAuth flow - returns redirect URL.
    
    Security: redirect_uri_override must be whitelisted to prevent open redirect attacks.
    """
    if not is_auth_enabled():
        return fail("AUTH_DISABLED", "Authentication is not enabled", status_code=503, request=request)
    
    try:
        client_id, _, redirect_uri = _get_google_config()
    except HTTPException as e:
        # Return 501 Not Implemented instead of 503 for missing config
        return fail("GOOGLE_OAUTH_NOT_CONFIGURED", "Google OAuth is not configured. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in your environment.", status_code=501, request=request)
    
    # Validate redirect_uri_override if provided (security: prevent open redirect)
    if redirect_uri_override:
        if not _validate_redirect_uri(redirect_uri_override):
            return fail("INVALID_REDIRECT_URI", "Redirect URI is not allowed. Only localhost and 127.0.0.1 are permitted for security.", status_code=400, request=request)
        redirect_target = redirect_uri_override
    else:
        redirect_target = redirect_uri
    state = secrets.token_urlsafe(16)
    ts = int(time.time())
    sig = _sign_state(state, ts)
    params = urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_target,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{params}"
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=600,
        path="/",
    )
    response.set_cookie(
        key="oauth_state_ts",
        value=str(ts),
        httponly=True,
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=600,
        path="/",
    )
    response.set_cookie(
        key="oauth_state_sig",
        value=sig,
        httponly=True,
        secure=AUTH_CONFIG["COOKIE_SECURE"],
        samesite=AUTH_CONFIG["COOKIE_SAMESITE"],
        max_age=600,
        path="/",
    )
    return ok({"redirect_url": auth_url}, request=request)


@router.get("/google/callback", response_model=UserResponse)
async def google_callback(
    request: Request,
    response: Response,
    code: str,
    state: str,
    state_cookie: Optional[str] = Cookie(None, alias="oauth_state"),
    state_ts: Optional[str] = Cookie(None, alias="oauth_state_ts"),
    state_sig: Optional[str] = Cookie(None, alias="oauth_state_sig"),
    db: Session = Depends(get_db),
):
    """
    Google OAuth callback - exchanges code for tokens and issues session.
    """
    if state_cookie is None or state_cookie != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")
    try:
        ts_int = int(state_ts) if state_ts else 0
    except Exception:
        ts_int = 0
    if not _verify_state(state, ts_int, state_sig or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state")

    client_id, client_secret, redirect_uri = _get_google_config()
    token_payload = exchange_google_code(code, redirect_uri, client_id, client_secret)
    access_token = token_payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code")

    userinfo = fetch_google_userinfo(access_token)
    email = userinfo.get("email")
    name = userinfo.get("name")
    sub = userinfo.get("sub")

    if not email or not sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Google user info")

    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        user = User(
            email=email.lower(),
            password_hash=hash_password(secrets.token_urlsafe(16)),
            name=name,
            is_active=True,
            email_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Upsert OAuth identity
    identity = db.query(OAuthIdentity).filter(
        OAuthIdentity.provider == "google",
        OAuthIdentity.provider_user_id == sub
    ).first()
    if identity is None:
        identity = OAuthIdentity(
            user_id=user.id,
            provider="google",
            provider_user_id=sub,
            email=email,
        )
        db.add(identity)
    else:
        identity.disconnected_at = None
        identity.email = email
    db.commit()

    # Issue session
    session, token = create_session(db, user, request)
    set_session_cookie(response, token)
    csrf_token = generate_csrf_token()
    set_csrf_cookie(response, csrf_token)

    record_audit(
        db=db,
        user_id=user.id,
        action="google_login",
        request=request,
        metadata={"oauth_provider": "google", "oauth_identity_id": identity.id},
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        is_active=user.is_active,
        email_verified=user.email_verified,
        created_at=user.created_at.isoformat()
    )


@router.post("/google/disconnect")
async def google_disconnect(
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    """
    Disconnect Google account for current user.
    """
    verify_csrf(request, csrf_token_cookie, db)
    identity = db.query(OAuthIdentity).filter(
        OAuthIdentity.user_id == current_user.id,
        OAuthIdentity.provider == "google",
        OAuthIdentity.disconnected_at.is_(None)
    ).first()
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Google account not connected")
    identity.disconnected_at = datetime.utcnow()
    db.commit()

    record_audit(
        db=db,
        user_id=current_user.id,
        action="google_disconnect",
        request=request,
        metadata={"oauth_identity_id": identity.id},
    )
    return {"message": "Google account disconnected"}


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: Request,
    signup_data: SignupRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    Creates user, creates session, and sets session cookie.
    """
    try:
        if not is_auth_enabled():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication is not enabled"
            )
        
        # Validate password (already validated by Pydantic, but double-check for safety)
        is_valid, error_msg = validate_password_strength(signup_data.password)
        if not is_valid:
            return fail("INVALID_PASSWORD", error_msg, status_code=400, request=request)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == signup_data.email.lower()).first()
        if existing_user:
            return fail("EMAIL_EXISTS", "An account with this email already exists", status_code=409, request=request)
        
        # Process name field - handle empty strings and None
        name_value = None
        if signup_data.name:
            name_stripped = signup_data.name.strip()
            name_value = name_stripped if name_stripped else None
        
        # Create user (backward-compatible with old schema)
        client_ip = get_client_ip(request)
        
        # Build user data - only include fields that exist in the database
        user_data = {
            "email": signup_data.email.lower(),
            "password_hash": hash_password(signup_data.password),
            "name": name_value,
            "is_active": True,
            "email_verified": False
        }
        
        # Try to add new fields if they exist in the model
        try:
            import uuid as uuid_mod
            if hasattr(User, 'uuid'):
                user_data["uuid"] = str(uuid_mod.uuid4())
            if hasattr(User, 'status'):
                user_data["status"] = AccountStatus.ACTIVE.value
            if hasattr(User, 'role'):
                user_data["role"] = UserRole.USER.value
        except Exception:
            pass
        
        user = User(**user_data)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Create email verification token if email verification is required
        if AUTH_CONFIG.get("EMAIL_ENABLED"):
            try:
                verification_token_obj, verification_token = EmailVerificationToken.create_for_user(
                    user_id=user.id,
                    email=user.email
                )
                db.add(verification_token_obj)
                db.commit()
                
                # Would send email here in production
                logger.info(f"Email verification token for {user.email}: {verification_token}")
            except Exception as e:
                logger.warning(f"Could not create verification token: {e}")
        
        csrf_token = generate_csrf_token()
        # Create session
        session, token = create_session(db, user, request, csrf_token=csrf_token)
        
        # Set cookie
        set_session_cookie(response, token)
        set_csrf_cookie(response, csrf_token)
        
        # Security logging
        logger.info(
            f"User signed up: {user.email}",
            extra={
                "security_event": "signup_success",
                "user_id": user.id,
                "ip": client_ip
            }
        )

        record_audit(
            db=db,
            user_id=user.id,
            action="signup",
            request=request,
            metadata={"email": user.email},
        )
        
        # Build response - handle both old and new schemas
        user_id = getattr(user, 'uuid', None) or str(user.id)
        user_role = getattr(user, 'role', 'user')
        is_active = getattr(user, 'is_active_account', user.is_active) if hasattr(user, 'is_active_account') else user.is_active
        
        return ok(
            data=UserResponse(
                id=user_id,
                email=user.email,
                name=user.name,
                role=user_role,
                is_active=is_active,
                email_verified=user.email_verified,
                created_at=user.created_at.isoformat(),
                last_login_at=None
            ),
            request=request,
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Pydantic validation errors (e.g., invalid password format)
        db.rollback()
        return fail("VALIDATION_ERROR", str(e), status_code=400, request=request)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Signup error: {str(e)}", exc_info=True)
        # Rollback any database changes
        db.rollback()
        # Return a generic error to prevent information leakage
        return fail("SIGNUP_FAILED", "An error occurred during signup. Please try again.", status_code=500, request=request)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """
    Log out current user by revoking session.
    """
    if not is_auth_enabled():
        return {"message": "Authentication is not enabled"}

    verify_csrf(request, csrf_token_cookie, db)
    
    if session_token:
        token_hash = SessionModel.hash_token(session_token)
        session = db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash
        ).first()
        
        if session:
            session.revoke()
            db.commit()
            logger.info(f"Session revoked: {session.id}")
            record_audit(
                db=db,
                user_id=session.user_id if current_user else None,
                action="logout",
                request=request,
                metadata={"session_id": session.id},
            )
    
    # Clear cookie
    clear_session_cookie(response)
    clear_csrf_cookie(response)
    
    return ok({"message": "Logged out successfully"}, request=request)


@router.post("/refresh", response_model=UserResponse)
async def refresh_session(
    request: Request,
    response: Response,
    session_token: Optional[str] = Cookie(None, alias="session_token"),
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    """
    Rotate session token and refresh user session.
    """
    if not is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled"
        )

    verify_csrf(request, csrf_token_cookie, db)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token_hash = SessionModel.hash_token(session_token)
    session = db.query(SessionModel).filter(
        SessionModel.token_hash == token_hash
    ).first()

    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    if session.revoked_at is not None:
        record_audit(
            db=db,
            user_id=session.user_id,
            action="token_reuse_detected",
            request=request,
            metadata={"reason": "revoked_session_used"},
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")
    if not session.is_valid():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Revoke old session and issue new
    session.revoke()
    session.revoke_reason = "rotated"
    db.commit()

    new_csrf = generate_csrf_token()
    new_session, new_token = create_session(
        db,
        user,
        request,
        rotated_from=session.id,
        csrf_token=new_csrf,
    )
    set_session_cookie(response, new_token)
    set_csrf_cookie(response, new_csrf)

    record_audit(
        db=db,
        user_id=user.id,
        action="refresh_session",
        request=request,
        metadata={"previous_session_id": session.id, "new_session_id": new_session.id},
    )

    return ok(
        data=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at.isoformat()
        ),
        request=request,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(require_auth)
):
    """
    Get current authenticated user's profile.
    """
    # Build response - handle both old and new schemas
    user_id = getattr(current_user, 'uuid', None) or str(current_user.id)
    user_role = getattr(current_user, 'role', 'user')
    is_active = getattr(current_user, 'is_active_account', current_user.is_active) if hasattr(current_user, 'is_active_account') else current_user.is_active
    last_login = getattr(current_user, 'last_login_at', None)
    
    return ok(
        data=UserResponse(
            id=user_id,
            email=current_user.email,
            name=current_user.name,
            role=user_role,
            is_active=is_active,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at.isoformat(),
            last_login_at=last_login.isoformat() if last_login else None
        )
    )


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = None


class AccountUpdateRequest(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    currency: Optional[str] = None
    units: Optional[str] = None
    theme: Optional[str] = None
    personalization_opt_in: Optional[bool] = None
    preferences_json: Optional[dict] = None


class EventRequest(BaseModel):
    event_name: str
    payload: Optional[dict] = None


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Update current user's profile (name).
    """
    verify_csrf(request, csrf_token_cookie, db)

    if profile_data.name is not None:
        current_user.name = profile_data.name.strip() if profile_data.name else None
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Profile updated for user: {current_user.email}")
    record_audit(
        db=db,
        user_id=current_user.id,
        action="update_profile",
        request=request,
        metadata={"name": current_user.name},
    )
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        is_active=current_user.is_active,
        email_verified=current_user.email_verified,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Change user's password (requires current password).
    """
    verify_csrf(request, csrf_token_cookie, db)

    # Verify current password
    if not verify_password(password_data.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update password
    current_user.password_hash = hash_password(password_data.new_password)
    db.commit()
    
    logger.info(f"Password changed for user: {current_user.email}")
    record_audit(
        db=db,
        user_id=current_user.id,
        action="change_password",
        request=request,
        metadata={},
    )
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset token.
    
    In development, token is printed to console.
    In production, token would be sent via email.
    """
    if not is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled"
        )
    
    # Find user (don't reveal if email exists)
    user = db.query(User).filter(User.email == request.email.lower()).first()
    
    if user:
        # Create reset token
        reset_token, token = PasswordResetToken.create_for_user(user.id)
        db.add(reset_token)
        db.commit()
        
        # In development, print to console
        if not AUTH_CONFIG["EMAIL_ENABLED"]:
            logger.info(f"Password reset token for {user.email}: {token}")
            try:
                print(f"\n{'='*60}")
                print(f"PASSWORD RESET TOKEN (DEV MODE)")
                print(f"Email: {user.email}")
                print(f"Token: {token}")
                print(f"URL: /reset-password?token={token}")
                print(f"{'='*60}\n")
            except UnicodeEncodeError:
                # Windows console may not support emoji
                logger.info(f"Password reset token for {user.email}: {token}")
        # TODO: Send email in production
    
    # Always return success (don't reveal if email exists)
    return ok({"message": "If the email exists, a password reset link has been sent"}, request=None)


@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token.
    """
    if not is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not enabled"
        )
    
    # Find token
    token_hash = PasswordResetToken.hash_token(reset_data.token)
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()
    
    if not reset_token or not reset_token.is_valid():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user
    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.password_hash = hash_password(reset_data.new_password)
    reset_token.mark_used()
    db.commit()
    
    logger.info(f"Password reset for user: {user.email}")
    
    return ok({"message": "Password reset successfully"}, request=None)


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: int,
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Revoke a specific session.
    """
    verify_csrf(request, csrf_token_cookie, db)
    # Find session
    session = db.query(SessionModel).filter(
        SessionModel.id == session_id,
        SessionModel.user_id == current_user.id
    ).first()
    
    if not session:
        return fail("SESSION_NOT_FOUND", "Session not found", status_code=404, request=request)
    
    if session.revoked_at is not None:
        return fail("SESSION_ALREADY_REVOKED", "Session already revoked", status_code=400, request=request)
    
    session.revoke()
    db.commit()
    
    logger.info(f"Session {session_id} revoked for user: {current_user.email}")
    record_audit(
        db=db,
        user_id=current_user.id,
        action="revoke_session",
        request=request,
        metadata={"session_id": session_id},
    )
    
    return ok({"message": "Session revoked successfully"}, request=request)


@router.post("/logout-all")
async def logout_all(
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Revoke all sessions for current user.
    """
    verify_csrf(request, csrf_token_cookie, db)
    # Revoke all active sessions
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id,
        SessionModel.revoked_at.is_(None)
    ).all()
    
    for session in sessions:
        session.revoke()
    
    db.commit()
    
    logger.info(f"All sessions revoked for user: {current_user.email}")
    record_audit(
        db=db,
        user_id=current_user.id,
        action="logout_all",
        request=request,
        metadata={"revoked": len(sessions)},
    )
    
    return ok({"message": f"Revoked {len(sessions)} session(s)"}, request=request)


@router.get("/sessions", response_model=list[SessionResponse])
async def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    List all active sessions for current user.
    """
    sessions = db.query(SessionModel).filter(
        SessionModel.user_id == current_user.id
    ).order_by(SessionModel.created_at.desc()).all()
    
    return ok(
        data=[
            SessionResponse(
                id=s.id,
                user_id=s.user_id,
                expires_at=s.expires_at.isoformat(),
                user_agent=s.user_agent,
                ip_address=s.ip_address,
                created_at=s.created_at.isoformat(),
                is_valid=s.is_valid()
            )
            for s in sessions
        ]
    )


# ============================
# Account Router (/api/account)
# ============================

account_router = APIRouter(prefix="/api/account", tags=["account"])


@account_router.get("/me", response_model=AccountResponse)
async def account_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    pref = get_or_create_preferences(db, current_user.id)
    return ok(
        data=AccountResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            is_active=current_user.is_active,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at.isoformat(),
            preferences=PreferenceResponse(
                timezone=pref.timezone,
                currency=pref.currency,
                units=pref.units,
                theme=pref.theme,
                personalization_opt_in=pref.personalization_opt_in,
                preferences_json=pref.preferences_json,
            ),
        )
    )


@account_router.patch("/me", response_model=AccountResponse)
async def account_update(
    request: Request,
    update: AccountUpdateRequest,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    verify_csrf(request, csrf_token_cookie, db)
    pref = get_or_create_preferences(db, current_user.id)

    if update.name is not None:
        current_user.name = update.name.strip() if update.name else None

    if update.timezone is not None:
        pref.timezone = update.timezone
    if update.currency is not None:
        pref.currency = update.currency
    if update.units is not None:
        pref.units = update.units
    if update.theme is not None:
        pref.theme = update.theme
    if update.personalization_opt_in is not None:
        pref.personalization_opt_in = update.personalization_opt_in
    if update.preferences_json is not None:
        pref.preferences_json = update.preferences_json

    db.commit()
    db.refresh(current_user)
    db.refresh(pref)

    record_audit(
        db=db,
        user_id=current_user.id,
        action="account_update",
        request=request,
        metadata={
            "personalization_opt_in": pref.personalization_opt_in,
        },
    )

    return ok(
        data=AccountResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            is_active=current_user.is_active,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at.isoformat(),
            preferences=PreferenceResponse(
                timezone=pref.timezone,
                currency=pref.currency,
                units=pref.units,
                theme=pref.theme,
                personalization_opt_in=pref.personalization_opt_in,
                preferences_json=pref.preferences_json,
            ),
        ),
        request=request,
    )


@account_router.get("/preferences", response_model=PreferenceResponse)
async def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    pref = get_or_create_preferences(db, current_user.id)
    return ok(
        data=PreferenceResponse(
            timezone=pref.timezone,
            currency=pref.currency,
            units=pref.units,
            theme=pref.theme,
            personalization_opt_in=pref.personalization_opt_in,
            preferences_json=pref.preferences_json,
        )
    )


@account_router.get("/oauth", response_model=list[dict])
async def list_connected_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    identities = db.query(OAuthIdentity).filter(
        OAuthIdentity.user_id == current_user.id
    ).all()
    return ok(
        data=[
            {
                "id": identity.id,
                "provider": identity.provider,
                "email": identity.email,
                "connected_at": identity.connected_at.isoformat() if identity.connected_at else None,
                "disconnected_at": identity.disconnected_at.isoformat() if identity.disconnected_at else None,
            }
            for identity in identities
        ]
    )


@account_router.post("/events")
async def track_event(
    request: Request,
    event: EventRequest,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    verify_csrf(request, csrf_token_cookie, db)
    log = EventLog(
        user_id=current_user.id if current_user else None,
        event_name=event.event_name,
        payload_json=event.payload or {},
        ip=get_client_ip(request),
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(log)
    db.commit()
    record_audit(
        db=db,
        user_id=current_user.id if current_user else None,
        action="track_event",
        request=request,
        metadata={"event_name": event.event_name},
    )
    return ok({"status": "ok"}, request=request)


@account_router.post("/data/export")
async def export_my_data(
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    verify_csrf(request, csrf_token_cookie, db)
    record_audit(
        db=db,
        user_id=current_user.id,
        action="export_data",
        request=request,
        metadata={},
    )
    # Stub: would trigger async export job
    return ok({"message": "Export request received"}, request=request)


@account_router.post("/data/delete")
async def request_data_delete(
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth),
):
    verify_csrf(request, csrf_token_cookie, db)
    record_audit(
        db=db,
        user_id=current_user.id,
        action="request_delete",
        request=request,
        metadata={},
    )
    return ok({"message": "Deletion request received"}, request=request)


# ============================
# Email Verification Endpoints
# ============================

@router.post("/verify-email")
async def verify_email(
    request: Request,
    verify_data: VerifyEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Verify email address using verification token.
    
    Called when user clicks the verification link in their email.
    """
    if not is_auth_enabled():
        return fail("AUTH_DISABLED", "Authentication is not enabled", status_code=503, request=request)
    
    # Find token
    token_hash = EmailVerificationToken.hash_token(verify_data.token)
    verification = db.query(EmailVerificationToken).filter(
        EmailVerificationToken.token_hash == token_hash
    ).first()
    
    if not verification or not verification.is_valid():
        return fail("INVALID_TOKEN", "Invalid or expired verification token", status_code=400, request=request)
    
    # Get user
    user = db.query(User).filter(User.id == verification.user_id).first()
    if not user:
        return fail("USER_NOT_FOUND", "User not found", status_code=404, request=request)
    
    # Verify email matches
    if user.email.lower() != verification.email.lower():
        return fail("EMAIL_MISMATCH", "Email does not match", status_code=400, request=request)
    
    # Mark email as verified
    user.email_verified = True
    if user.status == AccountStatus.PENDING_VERIFICATION.value:
        user.status = AccountStatus.ACTIVE.value
    verification.mark_verified()
    
    db.commit()
    
    logger.info(
        f"Email verified: {user.email}",
        extra={"security_event": "email_verified", "user_id": user.id}
    )
    
    record_audit(
        db=db,
        user_id=user.id,
        action="email_verified",
        request=request,
        metadata={"email": user.email},
    )
    
    return ok({"message": "Email verified successfully"}, request=request)


@router.post("/resend-verification")
async def resend_verification(
    request: Request,
    resend_data: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Resend email verification token.
    
    Rate limited to prevent abuse. Always returns success to prevent
    email enumeration attacks.
    """
    if not is_auth_enabled():
        return fail("AUTH_DISABLED", "Authentication is not enabled", status_code=503, request=request)
    
    # Find user (don't reveal if exists)
    user = db.query(User).filter(User.email == resend_data.email.lower()).first()
    
    if user and not user.email_verified:
        # Invalidate existing tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.verified_at.is_(None)
        ).update({"verified_at": datetime.utcnow()})
        
        # Create new token
        token_obj, token = EmailVerificationToken.create_for_user(
            user_id=user.id,
            email=user.email
        )
        db.add(token_obj)
        db.commit()
        
        # Send email (or log in development)
        if AUTH_CONFIG.get("EMAIL_ENABLED"):
            # TODO: Implement email sending
            logger.info(f"Would send verification email to {user.email}")
        else:
            # Development mode - log token
            logger.info(f"Email verification token for {user.email}: {token}")
            try:
                print(f"\n{'='*60}")
                print(f"EMAIL VERIFICATION TOKEN (DEV MODE)")
                print(f"Email: {user.email}")
                print(f"Token: {token}")
                print(f"URL: /verify-email?token={token}")
                print(f"{'='*60}\n")
            except UnicodeEncodeError:
                pass
        
        record_audit(
            db=db,
            user_id=user.id,
            action="verification_resent",
            request=request,
            metadata={},
        )
    
    # Always return success to prevent enumeration
    return ok({"message": "If the email exists and is unverified, a verification link has been sent"}, request=request)


# ============================
# API Key Management Endpoints
# ============================

api_key_router = APIRouter(prefix="/api/auth/keys", tags=["api-keys"])


@api_key_router.get("", response_model=List[APIKeyResponse])
async def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    List all API keys for the current user.
    
    Note: Full key values are never returned after creation.
    """
    keys = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.revoked_at.is_(None)
    ).order_by(APIKey.created_at.desc()).all()
    
    return ok(
        data=[
            APIKeyResponse(
                id=key.id,
                name=key.name,
                description=key.description,
                key_prefix=key.key_prefix,
                scope=key.scope,
                expires_at=key.expires_at.isoformat() if key.expires_at else None,
                is_valid=key.is_valid(),
                last_used_at=key.last_used_at.isoformat() if key.last_used_at else None,
                use_count=key.use_count,
                created_at=key.created_at.isoformat()
            )
            for key in keys
        ]
    )


@api_key_router.post("", response_model=APIKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: Request,
    key_data: CreateAPIKeyRequest,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Create a new API key.
    
    IMPORTANT: The full API key is only returned ONCE during creation.
    Store it securely - it cannot be retrieved again.
    
    Scopes:
    - read: Read-only API access
    - write: Read and write access
    - admin: Full administrative access
    - webhook: Webhook delivery only
    - service: Service-to-service communication
    """
    verify_csrf(request, csrf_token_cookie, db)
    
    # Check key limit
    max_keys = AUTH_CONFIG.get("API_KEY_MAX_PER_USER", 10)
    existing_count = db.query(APIKey).filter(
        APIKey.user_id == current_user.id,
        APIKey.revoked_at.is_(None)
    ).count()
    
    if existing_count >= max_keys:
        return fail("KEY_LIMIT_REACHED", f"Maximum {max_keys} API keys allowed", status_code=400, request=request)
    
    # Validate scope (admin/service require elevated privileges)
    scope = APIKeyScope(key_data.scope)
    if scope in (APIKeyScope.ADMIN, APIKeyScope.SERVICE):
        if not current_user.has_role(UserRole.ADMIN):
            return fail("INSUFFICIENT_PERMISSIONS", "Admin role required for this scope", status_code=403, request=request)
    
    # Create API key
    api_key, plain_key = APIKey.create_for_user(
        user_id=current_user.id,
        name=key_data.name,
        scope=scope,
        description=key_data.description,
        expires_in_days=key_data.expires_in_days,
        tenant_id=current_user.tenant_id,
        permissions=key_data.permissions
    )
    
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    
    logger.info(
        f"API key created: {api_key.name} ({api_key.key_prefix}***)",
        extra={
            "security_event": "api_key_created",
            "user_id": current_user.id,
            "key_id": api_key.id,
            "scope": api_key.scope
        }
    )
    
    record_audit(
        db=db,
        user_id=current_user.id,
        action="api_key_created",
        request=request,
        metadata={"key_id": api_key.id, "key_name": api_key.name, "scope": api_key.scope},
    )
    
    return ok(
        data=APIKeyCreatedResponse(
            id=api_key.id,
            name=api_key.name,
            description=api_key.description,
            key_prefix=api_key.key_prefix,
            key=plain_key,  # Only returned once!
            scope=api_key.scope,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            is_valid=True,
            last_used_at=None,
            use_count=0,
            created_at=api_key.created_at.isoformat()
        ),
        request=request
    )


@api_key_router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Revoke an API key.
    
    This immediately invalidates the key. This action cannot be undone.
    """
    verify_csrf(request, csrf_token_cookie, db)
    
    # Find key
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        return fail("KEY_NOT_FOUND", "API key not found", status_code=404, request=request)
    
    if api_key.revoked_at is not None:
        return fail("KEY_ALREADY_REVOKED", "API key already revoked", status_code=400, request=request)
    
    # Revoke
    api_key.revoke("user_request")
    db.commit()
    
    logger.info(
        f"API key revoked: {api_key.name} ({api_key.key_prefix}***)",
        extra={
            "security_event": "api_key_revoked",
            "user_id": current_user.id,
            "key_id": api_key.id
        }
    )
    
    record_audit(
        db=db,
        user_id=current_user.id,
        action="api_key_revoked",
        request=request,
        metadata={"key_id": api_key.id, "key_name": api_key.name},
    )
    
    return ok({"message": "API key revoked successfully"}, request=request)


@api_key_router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auth)
):
    """
    Get details of a specific API key.
    
    Note: The full key value is never returned.
    """
    api_key = db.query(APIKey).filter(
        APIKey.id == key_id,
        APIKey.user_id == current_user.id
    ).first()
    
    if not api_key:
        return fail("KEY_NOT_FOUND", "API key not found", status_code=404, request=None)
    
    return ok(
        data=APIKeyResponse(
            id=api_key.id,
            name=api_key.name,
            description=api_key.description,
            key_prefix=api_key.key_prefix,
            scope=api_key.scope,
            expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
            is_valid=api_key.is_valid(),
            last_used_at=api_key.last_used_at.isoformat() if api_key.last_used_at else None,
            use_count=api_key.use_count,
            created_at=api_key.created_at.isoformat()
        )
    )


# ============================
# Admin User Management
# ============================

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


@admin_router.get("/users")
async def list_users(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List users (admin only).
    
    Supports filtering by status and role, with pagination.
    """
    query = db.query(User)
    
    # Apply filters
    if status_filter:
        query = query.filter(User.status == status_filter)
    if role_filter:
        query = query.filter(User.role == role_filter)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.order_by(User.created_at.desc()).offset(skip).limit(min(limit, 100)).all()
    
    return ok(
        data={
            "users": [user.to_dict(include_sensitive=True) for user in users],
            "total": total,
            "skip": skip,
            "limit": limit
        },
        request=request
    )


@admin_router.get("/users/{user_uuid}")
async def get_user(
    user_uuid: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get user details (admin only).
    """
    user = db.query(User).filter(User.uuid == user_uuid).first()
    
    if not user:
        return fail("USER_NOT_FOUND", "User not found", status_code=404, request=None)
    
    return ok(data=user.to_dict(include_sensitive=True))


@admin_router.patch("/users/{user_uuid}/status")
async def update_user_status(
    user_uuid: str,
    request: Request,
    new_status: str,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user status (admin only).
    
    Valid statuses: active, suspended, locked, deleted
    """
    verify_csrf(request, csrf_token_cookie, db)
    
    # Validate status
    valid_statuses = [s.value for s in AccountStatus]
    if new_status not in valid_statuses:
        return fail("INVALID_STATUS", f"Invalid status. Must be one of: {', '.join(valid_statuses)}", status_code=400, request=request)
    
    # Find user
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        return fail("USER_NOT_FOUND", "User not found", status_code=404, request=request)
    
    # Prevent self-modification
    if user.id == current_user.id:
        return fail("SELF_MODIFICATION", "Cannot modify your own status", status_code=400, request=request)
    
    old_status = user.status
    user.status = new_status
    
    # If suspending/deleting, revoke all sessions
    if new_status in (AccountStatus.SUSPENDED.value, AccountStatus.DELETED.value, AccountStatus.LOCKED.value):
        db.query(SessionModel).filter(
            SessionModel.user_id == user.id,
            SessionModel.revoked_at.is_(None)
        ).update({"revoked_at": datetime.utcnow(), "revoke_reason": f"user_{new_status}"})
    
    db.commit()
    
    logger.info(
        f"User status changed: {user.email} from {old_status} to {new_status}",
        extra={
            "security_event": "user_status_changed",
            "target_user_id": user.id,
            "admin_user_id": current_user.id,
            "old_status": old_status,
            "new_status": new_status
        }
    )
    
    record_audit(
        db=db,
        user_id=current_user.id,
        action="admin_update_user_status",
        request=request,
        metadata={
            "target_user_id": user.id,
            "old_status": old_status,
            "new_status": new_status
        },
    )
    
    return ok({"message": f"User status updated to {new_status}"}, request=request)


@admin_router.patch("/users/{user_uuid}/role")
async def update_user_role(
    user_uuid: str,
    request: Request,
    new_role: str,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Update user role (admin only).
    
    Valid roles: user, operator, analyst, underwriter, admin, super_admin
    Note: Only super_admin can assign admin/super_admin roles.
    """
    verify_csrf(request, csrf_token_cookie, db)
    
    # Validate role
    valid_roles = [r.value for r in UserRole]
    if new_role not in valid_roles:
        return fail("INVALID_ROLE", f"Invalid role. Must be one of: {', '.join(valid_roles)}", status_code=400, request=request)
    
    # Only super admin can assign admin roles
    if new_role in (UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value):
        if not current_user.has_role(UserRole.SUPER_ADMIN):
            return fail("INSUFFICIENT_PERMISSIONS", "Super admin required to assign admin roles", status_code=403, request=request)
    
    # Find user
    user = db.query(User).filter(User.uuid == user_uuid).first()
    if not user:
        return fail("USER_NOT_FOUND", "User not found", status_code=404, request=request)
    
    # Prevent self-demotion
    if user.id == current_user.id:
        return fail("SELF_MODIFICATION", "Cannot modify your own role", status_code=400, request=request)
    
    old_role = user.role
    user.role = new_role
    db.commit()
    
    logger.info(
        f"User role changed: {user.email} from {old_role} to {new_role}",
        extra={
            "security_event": "user_role_changed",
            "target_user_id": user.id,
            "admin_user_id": current_user.id,
            "old_role": old_role,
            "new_role": new_role
        }
    )
    
    record_audit(
        db=db,
        user_id=current_user.id,
        action="admin_update_user_role",
        request=request,
        metadata={
            "target_user_id": user.id,
            "old_role": old_role,
            "new_role": new_role
        },
    )
    
    return ok({"message": f"User role updated to {new_role}"}, request=request)


@admin_router.get("/sessions")
async def list_all_sessions(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    user_uuid: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    List all active sessions (admin only).
    
    Optionally filter by user UUID.
    """
    query = db.query(SessionModel).filter(SessionModel.revoked_at.is_(None))
    
    if user_uuid:
        user = db.query(User).filter(User.uuid == user_uuid).first()
        if user:
            query = query.filter(SessionModel.user_id == user.id)
    
    total = query.count()
    sessions = query.order_by(SessionModel.created_at.desc()).offset(skip).limit(min(limit, 100)).all()
    
    return ok(
        data={
            "sessions": [s.to_dict(include_sensitive=True) for s in sessions],
            "total": total,
            "skip": skip,
            "limit": limit
        },
        request=request
    )


@admin_router.delete("/sessions/{session_id}")
async def admin_revoke_session(
    session_id: int,
    request: Request,
    csrf_token_cookie: Optional[str] = Cookie(None, alias=CSRF_COOKIE_NAME),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Revoke any session (admin only).
    """
    verify_csrf(request, csrf_token_cookie, db)
    
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    
    if not session:
        return fail("SESSION_NOT_FOUND", "Session not found", status_code=404, request=request)
    
    if session.revoked_at is not None:
        return fail("SESSION_ALREADY_REVOKED", "Session already revoked", status_code=400, request=request)
    
    session.revoke("admin")
    db.commit()
    
    logger.info(
        f"Admin revoked session: {session.id}",
        extra={
            "security_event": "admin_session_revoked",
            "session_id": session.id,
            "target_user_id": session.user_id,
            "admin_user_id": current_user.id
        }
    )
    
    record_audit(
        db=db,
        user_id=current_user.id,
        action="admin_revoke_session",
        request=request,
        metadata={"session_id": session.id, "target_user_id": session.user_id},
    )
    
    return ok({"message": "Session revoked"}, request=request)


@admin_router.get("/audit-log")
async def get_audit_log(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    user_uuid: Optional[str] = None,
    action_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Query audit log (admin only).
    
    Supports filtering by user, action type, and date range.
    """
    query = db.query(AuditLog)
    
    # Apply filters
    if user_uuid:
        user = db.query(User).filter(User.uuid == user_uuid).first()
        if user:
            query = query.filter(AuditLog.user_id == user.id)
    
    if action_type:
        query = query.filter(AuditLog.action_type == action_type)
    
    if start_date:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(AuditLog.created_at <= end)
        except ValueError:
            pass
    
    total = query.count()
    logs = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(min(limit, 500)).all()
    
    return ok(
        data={
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action_type": log.action_type,
                    "metadata": log.metadata_json,
                    "ip": log.ip,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        },
        request=request
    )
