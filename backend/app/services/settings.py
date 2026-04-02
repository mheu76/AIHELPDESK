"""
System settings service for runtime configuration management
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import SystemSettings
from app.models.user import User, UserRole
from app.schemas.admin import SystemSettingsResponse, SystemSettingsUpdateRequest
from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.core.logging import get_logger

logger = get_logger(__name__)


class SettingsService:
    """Service for system settings management"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_settings(self, current_user: User) -> SystemSettingsResponse:
        """
        Get current system settings.

        Args:
            current_user: Current authenticated user

        Returns:
            Current settings

        Raises:
            ForbiddenError: If user is not admin
        """
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only admins can view settings")

        return await self.get_runtime_settings()

    async def update_settings(
        self,
        current_user: User,
        update_data: SystemSettingsUpdateRequest
    ) -> SystemSettingsResponse:
        """
        Update system settings.

        Args:
            current_user: Current authenticated user
            update_data: Settings to update

        Returns:
            Updated settings

        Raises:
            ForbiddenError: If user is not admin
        """
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only admins can update settings")

        settings_row = await self._get_or_create_settings()
        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(settings_row, key, value)
            logger.info(
                f"Admin {current_user.employee_id} updated setting {key} to {value}"
            )

        # Special handling for LLM provider change
        if "llm_provider" in update_dict:
            provider = update_dict["llm_provider"]
            logger.warning(
                f"LLM provider changed to {provider} by {current_user.employee_id}"
            )

        await self.db.commit()
        await self.db.refresh(settings_row)
        return await self.get_settings(current_user)

    async def get_runtime_settings(self) -> SystemSettingsResponse:
        """Get current runtime settings without authorization checks."""
        settings_row = await self._get_or_create_settings()
        return SystemSettingsResponse(
            llm_provider=settings_row.llm_provider,
            llm_model=settings_row.llm_model,
            llm_temperature=settings_row.llm_temperature,
            max_tokens=settings_row.max_tokens,
            rag_enabled=settings_row.rag_enabled,
            rag_top_k=settings_row.rag_top_k,
        )

    async def _get_or_create_settings(self) -> SystemSettings:
        """Load the singleton settings row, creating it if necessary."""
        result = await self.db.execute(
            select(SystemSettings).where(SystemSettings.id == 1)
        )
        settings_row = result.scalar_one_or_none()
        if settings_row:
            return settings_row

        settings_row = SystemSettings(
            id=1,
            llm_provider=settings.LLM_PROVIDER,
            llm_model=settings.LLM_MODEL,
            llm_temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            rag_enabled=True,
            rag_top_k=settings.RAG_TOP_K,
        )
        self.db.add(settings_row)
        await self.db.flush()
        return settings_row
