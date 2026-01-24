"""
Identity & Access Router
FastAPI routes for authentication
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.shared.schemas import StandardResponse
from app.modules.identity_access.service import IdentityService
from app.modules.identity_access.schemas import UserCreate, LoginRequest, LoginResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Identity & Access"])


@router.post("/register", response_model=StandardResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    service = IdentityService(db)
    user = service.create_user(user_data)
    return StandardResponse(
        success=True,
        data=user.dict(),
        message="User registered successfully"
    )


@router.post("/login", response_model=StandardResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login user"""
    service = IdentityService(db)
    response = service.login(login_data)
    return StandardResponse(
        success=True,
        data=response.dict(),
        message="Login successful"
    )


@router.get("/me", response_model=StandardResponse)
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user = Depends(lambda: None)  # TODO: Implement get_current_user dependency
):
    """Get current user information"""
    # TODO: Implement
    return StandardResponse(
        success=True,
        message="User info retrieved"
    )
