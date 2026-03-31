"""
Tests for authentication API endpoints
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class TestAuthAPI:
    """Test authentication endpoints"""

    @pytest.mark.asyncio
    async def test_register_success(self, test_client: AsyncClient):
        """Test successful user registration"""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "employee_id": "EMP999",
                "email": "emp999@company.com",
                "password": "SecurePass123!",
                "full_name": "Test Employee"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["employee_id"] == "EMP999"
        assert data["email"] == "emp999@company.com"
        assert data["full_name"] == "Test Employee"
        assert data["role"] == "employee"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_register_duplicate_employee_id(
        self,
        test_client: AsyncClient,
        test_user: User
    ):
        """Test registration with duplicate employee_id"""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "employee_id": test_user.employee_id,
                "email": "different@company.com",
                "password": "Pass123!",
                "full_name": "Different"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self, test_client: AsyncClient):
        """Test registration with weak password"""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "employee_id": "EMP888",
                "email": "emp888@company.com",
                "password": "weak",  # Too weak
                "full_name": "Test"
            }
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_success(self, test_client: AsyncClient, test_user: User):
        """Test successful login"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "employee_id": test_user.employee_id,
                "password": "Test123!@#"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["employee_id"] == test_user.employee_id

    @pytest.mark.asyncio
    async def test_login_wrong_password(
        self,
        test_client: AsyncClient,
        test_user: User
    ):
        """Test login with wrong password"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "employee_id": test_user.employee_id,
                "password": "WrongPassword"
            }
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, test_client: AsyncClient):
        """Test login with non-existent user"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "employee_id": "NONEXISTENT",
                "password": "SomePassword"
            }
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authenticated(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict
    ):
        """Test getting current user info"""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["employee_id"] == test_user.employee_id
        assert data["email"] == test_user.email

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, test_client: AsyncClient):
        """Test getting user info without authentication"""
        response = await test_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, test_client: AsyncClient):
        """Test getting user info with invalid token"""
        response = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_success(
        self,
        test_client: AsyncClient,
        test_user: User
    ):
        """Test token refresh"""
        # First login to get refresh token
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "employee_id": test_user.employee_id,
                "password": "Test123!@#"
            }
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh token
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(
        self,
        test_client: AsyncClient,
        test_user: User
    ):
        """Test that access token cannot be used for refresh"""
        # Login to get access token
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "employee_id": test_user.employee_id,
                "password": "Test123!@#"
            }
        )
        access_token = login_response.json()["access_token"]

        # Try to refresh with access token
        response = await test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token}  # Wrong token type
        )

        assert response.status_code == 401
