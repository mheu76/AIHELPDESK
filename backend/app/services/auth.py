"""
Authentication service for user registration, login, and token management.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
import uuid

from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ConflictError, NotFoundError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Authentication service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, request: RegisterRequest) -> UserResponse:
        """
        Register a new user.

        Args:
            request: User registration data

        Returns:
            Created user

        Raises:
            ConflictError: If email or employee_id already exists
        """
        # Check if email already exists
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        if result.scalar_one_or_none():
            raise ConflictError(
                message="Email already registered",
                error_code="EMAIL_EXISTS"
            )

        # Check if employee_id already exists
        result = await self.db.execute(
            select(User).where(User.employee_id == request.employee_id)
        )
        if result.scalar_one_or_none():
            raise ConflictError(
                message="Employee ID already registered",
                error_code="EMPLOYEE_ID_EXISTS"
            )

        # Create new user
        hashed_password = get_password_hash(request.password)
        user = User(
            employee_id=request.employee_id,
            email=request.email,
            name=request.name,
            hashed_password=hashed_password,
            department=request.department,
            role=UserRole.EMPLOYEE  # Default role
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"User registered: {user.email}")
        return UserResponse.model_validate(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        """
        Authenticate user and return JWT tokens.

        Args:
            request: Login credentials

        Returns:
            JWT access and refresh tokens

        Raises:
            UnauthorizedError: If credentials are invalid
        """
        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == request.email)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.warning(f"Login attempt with non-existent email: {request.email}")
            raise UnauthorizedError(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )

        # Verify password
        if not verify_password(request.password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {user.email}")
            raise UnauthorizedError(
                message="Invalid email or password",
                error_code="INVALID_CREDENTIALS"
            )

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {user.email}")
            raise UnauthorizedError(
                message="Account is inactive",
                error_code="ACCOUNT_INACTIVE"
            )

        # Create tokens
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role.value
            }
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        logger.info(f"User logged in: {user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    async def get_current_user(self, token: str) -> User:
        """
        Get current user from JWT token.

        Args:
            token: JWT access token

        Returns:
            User object

        Raises:
            UnauthorizedError: If token is invalid or user not found
        """
        try:
            payload = decode_token(token)
        except Exception as e:
            logger.warning(f"Invalid token: {str(e)}")
            raise UnauthorizedError(
                message="Invalid token",
                error_code="INVALID_TOKEN"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(
                message="Invalid token payload",
                error_code="INVALID_TOKEN"
            )

        # Get user from database
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise UnauthorizedError(
                message="Invalid user ID in token",
                error_code="INVALID_TOKEN"
            )

        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(
                message="User not found",
                error_code="USER_NOT_FOUND"
            )

        if not user.is_active:
            raise UnauthorizedError(
                message="Account is inactive",
                error_code="ACCOUNT_INACTIVE"
            )

        return user

    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New access token

        Raises:
            UnauthorizedError: If refresh token is invalid
        """
        try:
            payload = decode_token(refresh_token)
        except Exception as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            raise UnauthorizedError(
                message="Invalid refresh token",
                error_code="INVALID_TOKEN"
            )

        # Verify token type
        if payload.get("type") != "refresh":
            raise UnauthorizedError(
                message="Invalid token type",
                error_code="INVALID_TOKEN_TYPE"
            )

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(
                message="Invalid token payload",
                error_code="INVALID_TOKEN"
            )

        # Verify user still exists and is active
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            raise UnauthorizedError(
                message="Invalid user ID in token",
                error_code="INVALID_TOKEN"
            )

        result = await self.db.execute(
            select(User).where(User.id == user_uuid)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError(
                message="User not found or inactive",
                error_code="INVALID_USER"
            )

        # Create new access token
        access_token = create_access_token(
            subject=str(user.id),
            additional_claims={
                "email": user.email,
                "role": user.role.value
            }
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Return same refresh token
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
