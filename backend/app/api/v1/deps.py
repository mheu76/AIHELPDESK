"""
FastAPI dependencies for request handling.
Provides database sessions, current user, LLM instances, etc.
"""
from typing import Optional, Dict, Any, List, AsyncIterator
from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.llm import LLMFactory, LLMBase
from app.services.settings import SettingsService

# Security scheme
security = HTTPBearer()


class StubLLM(LLMBase):
    """Offline-safe LLM used for tests and local development with placeholder keys."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        super().__init__(api_key, model or "stub-model")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        return {
            "content": "Test AI response",
            "role": "assistant",
            "model": self.model,
            "usage": {
                "input_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15
            }
        }

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        yield "Test "
        yield "AI "
        yield "response"

    async def embed_text(self, text: str, **kwargs) -> List[float]:
        return [0.1] * 10

    def count_tokens(self, text: str) -> int:
        return len(text.split())


async def get_llm(db: AsyncSession = Depends(get_db)) -> LLMBase:
    """
    Get LLM instance based on configuration.
    Uses runtime settings from SettingsService if available, falls back to environment config.

    Returns:
        LLM instance (Claude, OpenAI, etc.)

    Raises:
        ValueError: If LLM provider is not configured
    """
    # Get runtime settings (may be overridden by admin)
    runtime_settings = await SettingsService(db).get_runtime_settings()
    provider = runtime_settings.llm_provider
    model = runtime_settings.llm_model

    if provider == "claude":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude provider")
        api_key = settings.ANTHROPIC_API_KEY
    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        api_key = settings.OPENAI_API_KEY
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    if "test-key" in api_key:
        return StubLLM(api_key=api_key, model=model)

    return LLMFactory.create(
        provider=provider,
        api_key=api_key,
        model=model
    )


# Note: get_current_user is now available in app.api.v1.auth
# Import it from there to use as a dependency
