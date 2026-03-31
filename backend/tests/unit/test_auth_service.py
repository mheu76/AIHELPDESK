"""
Tests for authentication service
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth import AuthService
from app.models.user import User, UserRole
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.schemas.auth import RegisterRequest


class TestAuthService:
    """Test authentication service"""

    @pytest.mark.asyncio
    async def test_register_user_success(self, test_db: AsyncSession):
        """Test successful user registration"""
        auth_service = AuthService(test_db)

        request = RegisterRequest(
            employee_id="NEW001",
            email="new@company.com",
            password="NewPass123!",
            full_name="New User"
        )

        user = await auth_service.register_user(request)

        assert user.employee_id == "NEW001"
        assert user.email == "new@company.com"
        assert user.full_name == "New User"
        assert user.role == UserRole.EMPLOYEE
        assert user.hashed_password != "NewPass123!"  # Should be hashed

    @pytest.mark.asyncio
    async def test_register_duplicate_employee_id_fails(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Test that duplicate employee_id raises error"""
        auth_service = AuthService(test_db)

        request = RegisterRequest(
            employee_id=test_user.employee_id,  # Duplicate
            email="different@company.com",
            password="Pass123!",
            full_name="Different User"
        )

        with pytest.raises(BadRequestError, match="already exists"):
            await auth_service.register_user(request)

    @pytest.mark.asyncio
    async def test_register_duplicate_email_fails(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Test that duplicate email raises error"""
        auth_service = AuthService(test_db)

        request = RegisterRequest(
            employee_id="NEW002",
            email=test_user.email,  # Duplicate
            password="Pass123!",
            full_name="Different User"
        )

        with pytest.raises(BadRequestError, match="already exists"):
            await auth_service.register_user(request)

    @pytest.mark.asyncio
    async def test_login_success(self, test_db: AsyncSession, test_user: User):
        """Test successful login"""
        auth_service = AuthService(test_db)

        response = await auth_service.login(
            employee_id=test_user.employee_id,
            password="Test123!@#"
        )

        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.token_type == "bearer"
        assert response.user.employee_id == test_user.employee_id

    @pytest.mark.asyncio
    async def test_login_wrong_password_fails(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Test login with wrong password"""
        auth_service = AuthService(test_db)

        with pytest.raises(UnauthorizedError, match="Invalid credentials"):
            await auth_service.login(
                employee_id=test_user.employee_id,
                password="WrongPassword"
            )

    @pytest.mark.asyncio
    async def test_login_nonexistent_user_fails(self, test_db: AsyncSession):
        """Test login with non-existent user"""
        auth_service = AuthService(test_db)

        with pytest.raises(UnauthorizedError, match="Invalid credentials"):
            await auth_service.login(
                employee_id="NONEXISTENT",
                password="SomePassword"
            )

    @pytest.mark.asyncio
    async def test_get_current_user_success(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Test getting current user from token"""
        auth_service = AuthService(test_db)

        # Login to get token
        login_response = await auth_service.login(
            employee_id=test_user.employee_id,
            password="Test123!@#"
        )

        # Get user from token
        user = await auth_service.get_current_user(login_response.access_token)

        assert user.id == test_user.id
        assert user.employee_id == test_user.employee_id

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_fails(self, test_db: AsyncSession):
        """Test getting user with invalid token"""
        auth_service = AuthService(test_db)

        with pytest.raises(UnauthorizedError):
            await auth_service.get_current_user("invalid.token.here")

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Test token refresh"""
        auth_service = AuthService(test_db)

        # Login to get refresh token
        login_response = await auth_service.login(
            employee_id=test_user.employee_id,
            password="Test123!@#"
        )

        # Refresh token
        new_token = await auth_service.refresh_access_token(
            login_response.refresh_token
        )

        assert new_token.access_token is not None
        assert new_token.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(
        self,
        test_db: AsyncSession,
        test_user: User
    ):
        """Test that access token cannot be used for refresh"""
        auth_service = AuthService(test_db)

        # Login
        login_response = await auth_service.login(
            employee_id=test_user.employee_id,
            password="Test123!@#"
        )

        # Try to refresh with access token (should fail)
        with pytest.raises(UnauthorizedError, match="Invalid refresh token"):
            await auth_service.refresh_access_token(
                login_response.access_token  # Wrong token type
            )
