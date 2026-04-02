"""
Tests for admin dashboard and user management services
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.settings import SettingsService
from app.services.user import UserService
from app.models.user import User, UserRole
from app.schemas.admin import SystemSettingsUpdateRequest, UserUpdateRequest
from app.core.exceptions import ForbiddenError, BadRequestError


class TestSettingsService:
    """Test system settings service"""

    @pytest.fixture
    def admin_user(self):
        """Create admin user"""
        return User(
            id=uuid4(),
            employee_id="ADMIN001",
            email="admin@company.com",
            full_name="Admin User",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def employee_user(self):
        """Create employee user"""
        return User(
            id=uuid4(),
            employee_id="EMP001",
            email="user@company.com",
            full_name="Test User",
            hashed_password="hashed",
            role=UserRole.EMPLOYEE,
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_get_settings_as_admin(self, test_db: AsyncSession, admin_user):
        """Test admin can get settings"""
        service = SettingsService(test_db)
        result = await service.get_settings(admin_user)

        assert result.llm_provider in ["claude", "openai"]
        assert result.rag_enabled is not None
        assert result.llm_temperature > 0

    @pytest.mark.asyncio
    async def test_get_settings_as_employee_denied(self, test_db: AsyncSession, employee_user):
        """Test employee cannot get settings"""
        service = SettingsService(test_db)

        with pytest.raises(ForbiddenError):
            await service.get_settings(employee_user)

    @pytest.mark.asyncio
    async def test_update_llm_provider(self, test_db: AsyncSession, admin_user):
        """Test admin can update LLM provider"""
        service = SettingsService(test_db)

        # Save original
        original = await service.get_settings(admin_user)

        # Update to openai
        update_data = SystemSettingsUpdateRequest(llm_provider="openai")
        result = await service.update_settings(admin_user, update_data)

        assert result.llm_provider == "openai"

        # Reset to original
        reset_data = SystemSettingsUpdateRequest(llm_provider=original.llm_provider)
        await service.update_settings(admin_user, reset_data)

    @pytest.mark.asyncio
    async def test_update_temperature(self, test_db: AsyncSession, admin_user):
        """Test admin can update temperature"""
        service = SettingsService(test_db)

        update_data = SystemSettingsUpdateRequest(llm_temperature=0.5)
        result = await service.update_settings(admin_user, update_data)

        assert result.llm_temperature == 0.5

        # Reset
        reset_data = SystemSettingsUpdateRequest(llm_temperature=0.7)
        await service.update_settings(admin_user, reset_data)

    @pytest.mark.asyncio
    async def test_employee_cannot_update_settings(self, test_db: AsyncSession, employee_user):
        """Test employee cannot update settings"""
        service = SettingsService(test_db)
        update_data = SystemSettingsUpdateRequest(llm_provider="openai")

        with pytest.raises(ForbiddenError):
            await service.update_settings(employee_user, update_data)


class TestUserService:
    """Test user management service"""

    @pytest.fixture
    def admin_user(self):
        """Create admin user"""
        return User(
            id=uuid4(),
            employee_id="ADMIN001",
            email="admin@company.com",
            full_name="Admin User",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def second_admin(self):
        """Create second admin user"""
        return User(
            id=uuid4(),
            employee_id="ADMIN002",
            email="admin2@company.com",
            full_name="Second Admin",
            hashed_password="hashed",
            role=UserRole.ADMIN,
            is_active=True
        )

    @pytest.fixture
    def target_user(self):
        """Create target user for updates"""
        return User(
            id=uuid4(),
            employee_id="USER001",
            email="user@company.com",
            full_name="Test User",
            hashed_password="hashed",
            role=UserRole.EMPLOYEE,
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_cannot_remove_last_admin(self, admin_user):
        """Test that the last active admin cannot be deactivated"""
        mock_db = AsyncMock()

        # Mock query to return the admin user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin_user

        # Mock count query to return 0 (no other admins)
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0

        async def execute_side_effect(query):
            # First call returns the user, second call returns count
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1

            if execute_side_effect.call_count == 1:
                return mock_result
            else:
                return mock_count_result

        mock_db.execute.side_effect = execute_side_effect

        service = UserService(mock_db)
        update_data = UserUpdateRequest(is_active=False)

        with pytest.raises(BadRequestError, match="Cannot remove the last active admin"):
            await service.update_user(admin_user, str(admin_user.id), update_data)

    @pytest.mark.asyncio
    async def test_cannot_demote_last_admin(self, admin_user):
        """Test that the last active admin cannot be demoted"""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin_user

        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 0

        async def execute_side_effect(query):
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1

            if execute_side_effect.call_count == 1:
                return mock_result
            else:
                return mock_count_result

        mock_db.execute.side_effect = execute_side_effect

        service = UserService(mock_db)
        update_data = UserUpdateRequest(role=UserRole.IT_STAFF)

        with pytest.raises(BadRequestError, match="Cannot remove the last active admin"):
            await service.update_user(admin_user, str(admin_user.id), update_data)

    @pytest.mark.asyncio
    async def test_can_update_admin_when_others_exist(self, admin_user, second_admin):
        """Test that an admin can be updated when other admins exist"""
        mock_db = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin_user

        # Mock count query to return 1 (one other admin exists)
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        # Mock get_user to return updated user detail
        mock_detail_result = MagicMock()

        async def execute_side_effect(query):
            if not hasattr(execute_side_effect, 'call_count'):
                execute_side_effect.call_count = 0
            execute_side_effect.call_count += 1

            if execute_side_effect.call_count == 1:
                return mock_result
            elif execute_side_effect.call_count == 2:
                return mock_count_result
            else:
                return mock_detail_result

        mock_db.execute.side_effect = execute_side_effect
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        service = UserService(mock_db)
        service.get_user = AsyncMock()  # Mock the get_user method

        update_data = UserUpdateRequest(is_active=False)

        # Should not raise an error
        await service.update_user(admin_user, str(admin_user.id), update_data)

        # Verify commit was called
        mock_db.commit.assert_called_once()
