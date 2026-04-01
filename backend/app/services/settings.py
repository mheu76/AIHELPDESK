"""
System settings service for runtime configuration management
"""
from typing import Dict, Any, Optional
from datetime import datetime

from app.models.user import User, UserRole
from app.schemas.admin import SystemSettingsResponse, SystemSettingsUpdateRequest
from app.core.config import settings
from app.core.exceptions import ForbiddenError
from app.core.logging import get_logger

logger = get_logger(__name__)


# Runtime settings override storage (in-memory)
# In production, this should be persisted to database
_settings_override: Dict[str, Any] = {}


class SettingsService:
    """Service for system settings management"""

    def get_settings(self, current_user: User) -> SystemSettingsResponse:
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

        return SystemSettingsResponse(
            llm_provider=_settings_override.get("llm_provider", settings.LLM_PROVIDER),
            llm_model=_settings_override.get("llm_model", settings.LLM_MODEL),
            llm_temperature=_settings_override.get("llm_temperature", settings.LLM_TEMPERATURE),
            max_tokens=_settings_override.get("max_tokens", settings.LLM_MAX_TOKENS),
            rag_enabled=_settings_override.get("rag_enabled", True),
            rag_top_k=_settings_override.get("rag_top_k", settings.RAG_TOP_K)
        )

    def update_settings(
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

        # Update override storage
        update_dict = update_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            _settings_override[key] = value
            logger.info(
                f"Admin {current_user.employee_id} updated setting {key} to {value}"
            )

        # Special handling for LLM provider change
        if "llm_provider" in update_dict:
            provider = update_dict["llm_provider"]
            logger.warning(
                f"LLM provider changed to {provider} by {current_user.employee_id}"
            )

        return self.get_settings(current_user)

    @staticmethod
    def get_current_llm_provider() -> str:
        """
        Get current LLM provider.

        Returns:
            Current provider name
        """
        return _settings_override.get("llm_provider", settings.LLM_PROVIDER)

    @staticmethod
    def get_current_llm_model() -> str:
        """
        Get current LLM model.

        Returns:
            Current model name
        """
        return _settings_override.get("llm_model", settings.LLM_MODEL)

    @staticmethod
    def get_current_llm_temperature() -> float:
        """
        Get current LLM temperature.

        Returns:
            Current temperature
        """
        return _settings_override.get("llm_temperature", settings.LLM_TEMPERATURE)

    @staticmethod
    def get_current_max_tokens() -> int:
        """
        Get current max tokens.

        Returns:
            Current max tokens
        """
        return _settings_override.get("max_tokens", settings.LLM_MAX_TOKENS)

    @staticmethod
    def get_current_rag_enabled() -> bool:
        """
        Get RAG enabled status.

        Returns:
            True if RAG is enabled
        """
        return _settings_override.get("rag_enabled", True)

    @staticmethod
    def get_current_rag_top_k() -> int:
        """
        Get RAG top K.

        Returns:
            Current top K value
        """
        return _settings_override.get("rag_top_k", settings.RAG_TOP_K)
