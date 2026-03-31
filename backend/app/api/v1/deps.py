"""
FastAPI dependencies for request handling.
Provides database sessions, current user, LLM instances, etc.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.llm import LLMFactory, LLMBase

# Security scheme
security = HTTPBearer()


def get_llm() -> LLMBase:
    """
    Get LLM instance based on configuration.

    Returns:
        LLM instance (Claude, OpenAI, etc.)

    Raises:
        ValueError: If LLM provider is not configured
    """
    if settings.LLM_PROVIDER == "claude":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude provider")
        api_key = settings.ANTHROPIC_API_KEY
    elif settings.LLM_PROVIDER == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        api_key = settings.OPENAI_API_KEY
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

    return LLMFactory.create(
        provider=settings.LLM_PROVIDER,
        api_key=api_key,
        model=settings.LLM_MODEL if settings.LLM_MODEL else None
    )


# Note: get_current_user is now available in app.api.v1.auth
# Import it from there to use as a dependency
