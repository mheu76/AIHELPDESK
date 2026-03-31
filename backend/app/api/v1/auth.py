"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, security
from app.services.auth import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    - **employee_id**: Unique employee ID
    - **email**: Valid email address
    - **name**: Full name
    - **password**: Password (minimum 8 characters)
    - **department**: Optional department
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(request)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access token"
)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    - **email**: User email address
    - **password**: User password

    Returns access token and refresh token.
    """
    auth_service = AuthService(db)
    return await auth_service.login(request)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token"
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a new access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access token with same refresh token.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(request.refresh_token)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Returns:
        Current user object

    Raises:
        UnauthorizedError: If token is invalid or user not found
    """
    auth_service = AuthService(db)
    return await auth_service.get_current_user(credentials.credentials)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.

    Requires valid JWT access token in Authorization header.
    """
    return UserResponse.model_validate(current_user)
