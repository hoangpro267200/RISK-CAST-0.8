"""
Authentication System Tests

RISKCAST Auth System - Phase 1
Comprehensive tests for auth endpoints and functionality.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

# Set AUTH_ENABLED=true for tests
os.environ["AUTH_ENABLED"] = "true"
os.environ["SESSION_SECRET"] = "test-secret-key-for-testing-only-32-chars-min"
os.environ["COOKIE_SECURE"] = "false"

from app.main import app
from app.database import get_db, Base, engine, SessionLocal
from app.models.auth import User, Session as SessionModel, PasswordResetToken
from app.utils.password import hash_password, verify_password, validate_password_strength


@pytest.fixture(scope="function")
def db():
    """Create a test database session."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        password_hash=hash_password("Test123!@#"),
        name="Test User",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestPasswordUtilities:
    """Test password hashing and validation utilities."""
    
    def test_hash_password(self):
        """Test password hashing."""
        password = "Test123!@#"
        hashed = hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$")  # Should have algorithm prefix
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "Test123!@#"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "Test123!@#"
        hashed = hash_password(password)
        assert verify_password("WrongPassword123!", hashed) is False
    
    def test_validate_password_strength_valid(self):
        """Test password strength validation with valid password."""
        password = "Test123!@#"
        is_valid, error = validate_password_strength(password)
        assert is_valid is True
        assert error is None
    
    def test_validate_password_strength_too_short(self):
        """Test password strength validation with too short password."""
        password = "Test1!"
        is_valid, error = validate_password_strength(password)
        assert is_valid is False
        assert "8 characters" in error
    
    def test_validate_password_strength_no_uppercase(self):
        """Test password strength validation without uppercase."""
        password = "test123!@#"
        is_valid, error = validate_password_strength(password)
        assert is_valid is False
        assert "uppercase" in error
    
    def test_validate_password_strength_no_lowercase(self):
        """Test password strength validation without lowercase."""
        password = "TEST123!@#"
        is_valid, error = validate_password_strength(password)
        assert is_valid is False
        assert "lowercase" in error
    
    def test_validate_password_strength_no_number(self):
        """Test password strength validation without number."""
        password = "TestPass!@#"
        is_valid, error = validate_password_strength(password)
        assert is_valid is False
        assert "number" in error
    
    def test_validate_password_strength_no_special(self):
        """Test password strength validation without special character."""
        password = "TestPass123"
        is_valid, error = validate_password_strength(password)
        assert is_valid is False
        assert "special character" in error


class TestSignup:
    """Test user signup endpoint."""
    
    def test_signup_success(self, client: TestClient, db: Session):
        """Test successful user signup."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "newuser@example.com",
                "password": "NewUser123!@#",
                "name": "New User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "password" not in data  # Should not return password
        
        # Check cookie is set
        assert "session_token" in response.cookies
        
        # Verify user exists in database
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.name == "New User"
    
    def test_signup_duplicate_email(self, client: TestClient, test_user: User):
        """Test signup with duplicate email."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "test@example.com",
                "password": "Test123!@#",
                "name": "Another User"
            }
        )
        assert response.status_code == 400
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_signup_weak_password(self, client: TestClient):
        """Test signup with weak password."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "weak@example.com",
                "password": "weak",
                "name": "Weak User"
            }
        )
        assert response.status_code == 422  # Validation error
    
    def test_signup_invalid_email(self, client: TestClient):
        """Test signup with invalid email."""
        response = client.post(
            "/api/auth/signup",
            json={
                "email": "not-an-email",
                "password": "Test123!@#",
                "name": "Test User"
            }
        )
        assert response.status_code == 422  # Validation error


class TestLogin:
    """Test user login endpoint."""
    
    def test_login_success(self, client: TestClient, test_user: User):
        """Test successful login."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        
        # Check cookie is set
        assert "session_token" in response.cookies
    
    def test_login_wrong_password(self, client: TestClient, test_user: User):
        """Test login with wrong password."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "WrongPassword123!"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_nonexistent_email(self, client: TestClient):
        """Test login with non-existent email."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Test123!@#"
            }
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    def test_login_inactive_user(self, client: TestClient, db: Session):
        """Test login with inactive user."""
        user = User(
            email="inactive@example.com",
            password_hash=hash_password("Test123!@#"),
            is_active=False
        )
        db.add(user)
        db.commit()
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "Test123!@#"
            }
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


class TestMe:
    """Test /api/auth/me endpoint."""
    
    def test_me_requires_auth(self, client: TestClient):
        """Test that /me requires authentication."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401
    
    def test_me_returns_user(self, client: TestClient, test_user: User, db: Session):
        """Test that /me returns current user info."""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        assert login_response.status_code == 200
        
        # Get user info
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["id"] == test_user.id


class TestLogout:
    """Test logout endpoint."""
    
    def test_logout_success(self, client: TestClient, test_user: User, db: Session):
        """Test successful logout."""
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        session_token = login_response.cookies.get("session_token")
        assert session_token is not None
        
        # Logout
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        
        # Check cookie is cleared (set-cookie header should clear it)
        # FastAPI clears cookies by setting them with empty value and max-age=0
        # The cookie may or may not appear in response.cookies, so we verify by checking database
        
        # Verify session is revoked in database
        token_hash = SessionModel.hash_token(session_token)
        session = db.query(SessionModel).filter(
            SessionModel.token_hash == token_hash
        ).first()
        assert session is not None
        assert session.revoked_at is not None
    
    def test_logout_invalidates_session(self, client: TestClient, test_user: User):
        """Test that logout invalidates session for subsequent requests."""
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        
        # Verify can access /me
        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 200
        
        # Logout
        client.post("/api/auth/logout")
        
        # Verify cannot access /me anymore
        me_response = client.get("/api/auth/me")
        assert me_response.status_code == 401


class TestChangePassword:
    """Test change password endpoint."""
    
    def test_change_password_success(self, client: TestClient, test_user: User, db: Session):
        """Test successful password change."""
        # Login
        client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        
        # Change password
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "Test123!@#",
                "new_password": "NewPass123!@#"
            }
        )
        assert response.status_code == 200
        
        # Verify new password works
        db.refresh(test_user)
        assert verify_password("NewPass123!@#", test_user.password_hash) is True
    
    def test_change_password_wrong_current(self, client: TestClient, test_user: User):
        """Test password change with wrong current password."""
        # Login
        client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        
        # Try to change with wrong current password
        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "WrongPassword123!",
                "new_password": "NewPass123!@#"
            }
        )
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()


class TestPasswordReset:
    """Test password reset flow."""
    
    def test_forgot_password_creates_token(self, client: TestClient, test_user: User, db: Session):
        """Test that forgot password creates a reset token."""
        response = client.post(
            "/api/auth/forgot-password",
            json={
                "email": "test@example.com"
            }
        )
        assert response.status_code == 200
        
        # Verify token exists in database
        tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == test_user.id
        ).all()
        assert len(tokens) > 0
        assert tokens[0].is_valid() is True
    
    def test_reset_password_success(self, client: TestClient, test_user: User, db: Session):
        """Test successful password reset."""
        # Create reset token
        reset_token, token = PasswordResetToken.create_for_user(test_user.id)
        db.add(reset_token)
        db.commit()
        
        # Reset password
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": token,
                "new_password": "ResetPass123!@#"
            }
        )
        assert response.status_code == 200
        
        # Verify password changed
        db.refresh(test_user)
        assert verify_password("ResetPass123!@#", test_user.password_hash) is True
        
        # Verify token is marked as used
        db.refresh(reset_token)
        assert reset_token.used_at is not None
    
    def test_reset_password_invalid_token(self, client: TestClient):
        """Test password reset with invalid token."""
        response = client.post(
            "/api/auth/reset-password",
            json={
                "token": "invalid-token-12345",
                "new_password": "NewPass123!@#"
            }
        )
        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]


class TestSessionManagement:
    """Test session management endpoints."""
    
    def test_logout_all_revokes_sessions(self, client: TestClient, test_user: User, db: Session):
        """Test that logout-all revokes all sessions."""
        # Create multiple sessions
        session1, token1 = SessionModel.generate_token(), SessionModel.generate_token()
        session2, token2 = SessionModel.generate_token(), SessionModel.generate_token()
        
        s1 = SessionModel(
            token_hash=SessionModel.hash_token(token1),
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        s2 = SessionModel(
            token_hash=SessionModel.hash_token(token2),
            user_id=test_user.id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.add_all([s1, s2])
        db.commit()
        
        # Login to get authenticated session
        client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        
        # Logout all
        response = client.post("/api/auth/logout-all")
        assert response.status_code == 200
        
        # Verify all sessions are revoked
        db.refresh(s1)
        db.refresh(s2)
        assert s1.revoked_at is not None
        assert s2.revoked_at is not None
    
    def test_get_sessions(self, client: TestClient, test_user: User, db: Session):
        """Test getting list of sessions."""
        # Login
        client.post(
            "/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "Test123!@#"
            }
        )
        
        # Get sessions
        response = client.get("/api/auth/sessions")
        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)
        assert len(sessions) > 0
