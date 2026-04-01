"""
Tests for admin dashboard and user management services
"""
import pytest
from uuid import uuid4

from app.services.settings import SettingsService
from app.models.user import User, UserRole
from app.schemas.admin import SystemSettingsUpdateRequest
from app.core.exceptions import ForbiddenError


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

    def test_get_settings_as_admin(self, admin_user):
        """Test admin can get settings"""
        service = SettingsService()
        result = service.get_settings(admin_user)

        assert result.llm_provider in ["claude", "openai"]
        assert result.rag_enabled is not None
        assert result.llm_temperature > 0

    def test_get_settings_as_employee_denied(self, employee_user):
        """Test employee cannot get settings"""
        service = SettingsService()

        with pytest.raises(ForbiddenError):
            service.get_settings(employee_user)

    def test_update_llm_provider(self, admin_user):
        """Test admin can update LLM provider"""
        service = SettingsService()

        # Save original
        original = service.get_settings(admin_user)

        # Update to openai
        update_data = SystemSettingsUpdateRequest(llm_provider="openai")
        result = service.update_settings(admin_user, update_data)

        assert result.llm_provider == "openai"
        assert SettingsService.get_current_llm_provider() == "openai"

        # Reset to original
        reset_data = SystemSettingsUpdateRequest(llm_provider=original.llm_provider)
        service.update_settings(admin_user, reset_data)

    def test_update_temperature(self, admin_user):
        """Test admin can update temperature"""
        service = SettingsService()

        update_data = SystemSettingsUpdateRequest(llm_temperature=0.5)
        result = service.update_settings(admin_user, update_data)

        assert result.llm_temperature == 0.5
        assert SettingsService.get_current_llm_temperature() == 0.5

        # Reset
        reset_data = SystemSettingsUpdateRequest(llm_temperature=0.7)
        service.update_settings(admin_user, reset_data)

    def test_employee_cannot_update_settings(self, employee_user):
        """Test employee cannot update settings"""
        service = SettingsService()
        update_data = SystemSettingsUpdateRequest(llm_provider="openai")

        with pytest.raises(ForbiddenError):
            service.update_settings(employee_user, update_data)
