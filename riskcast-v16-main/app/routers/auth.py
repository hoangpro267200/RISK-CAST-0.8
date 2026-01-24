"""
Authentication Router

RISKCAST Auth System - Phase 1
API endpoints for user authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
import os
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Tuple
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
from app.models.auth import User, Session as SessionModel, PasswordResetToken
from app.models.account import AuditLog, UserPreference, OAuthIdentity, EventLog
from app.utils.password import hash_password, verify_password, validate_password_strength
from app.config.auth import AUTH_CONFIG, is_auth_enabled
from app.dependencies.auth import get_current_user, require_auth
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

FAILED_LOGIN_WINDOW_MINUTES = 15
FAILED_LOGIN_MAX_ATTEMPTS = 5
FAILED_LOGIN_LOCKOUT_MINUTES = 15

# failed login tracker: {(email, ip): (fail_count, first_failure_ts, locked_until_ts)}
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
    id: int
    email: str
    name: Optional[str]
    is_active: bool
    email_verified: bool
    created_at: str
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    id: int
    user_id: int
    expires_at: str
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: str
    is_valid: bool
    
    class Config:
        from_attributes = True


class PreferenceResponse(BaseModel):
    timezone: Optional[str] = None
    currency: Optional[str] = None
    units: Optional[str] = None
    theme: Optional[str] = None
    personalization_opt_in: bool = False
    preferences_json: Optional[dict] = None


class AccountResponse(UserResponse):
    preferences: PreferenceResponse


@router.post("/login", response_model=UserResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and create session.
    
    Sets session cookie on success.
    """
    if not is_auth_enabled():
        return fail("AUTH_DISABLED", "Authentication is not enabled", status_code=503, request=request)
    
    client_ip = get_client_ip(request)
    ensure_not_locked(login_data.email, client_ip)
    
    # Find user
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    
    # Generic error to prevent email enumeration
    if not user or not verify_password(login_data.password, user.password_hash):
        register_login_failure(login_data.email, client_ip)
        return fail("INVALID_CREDENTIALS", "Invalid email or password", status_code=401, request=request)
    
    clear_login_failures(login_data.email, client_ip)
    
    if not user.is_active:
        return fail("ACCOUNT_DISABLED", "Account is disabled", status_code=403, request=request)
    
    csrf_token = generate_csrf_token()
    session, token = create_session(db, user, request, csrf_token=csrf_token)
    
    set_session_cookie(response, token)
    set_csrf_cookie(response, csrf_token)
    
    logger.info(f"User logged in: {user.email} (ID: {user.id})")

    record_audit(
        db=db,
        user_id=user.id,
        action="login",
        request=request,
        metadata={"session_id": session.id},
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
        return fail("GOOGLE_OAUTH_NOT_CONFIGURED", "Google OAuth is not configured. Please set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REDIRECT_URI in your environment.", status_code=503, request=request)
    
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
        
        # Create user
        user = User(
            email=signup_data.email.lower(),
            password_hash=hash_password(signup_data.password),
            name=name_value,
            is_active=True,
            email_verified=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        csrf_token = generate_csrf_token()
        # Create session
        session, token = create_session(db, user, request, csrf_token=csrf_token)
        
        # Set cookie
        set_session_cookie(response, token)
        set_csrf_cookie(response, csrf_token)
        
        logger.info(f"User signed up: {user.email} (ID: {user.id})")

        record_audit(
            db=db,
            user_id=user.id,
            action="signup",
            request=request,
            metadata={"email": user.email},
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
    return ok(
        data=UserResponse(
            id=current_user.id,
            email=current_user.email,
            name=current_user.name,
            is_active=current_user.is_active,
            email_verified=current_user.email_verified,
            created_at=current_user.created_at.isoformat()
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
