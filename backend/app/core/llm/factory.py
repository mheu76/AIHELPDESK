"""
LLM factory for creating provider instances based on configuration.
"""
from typing import Optional
from app.core.llm.base import LLMBase
from app.core.llm.claude import ClaudeLLM
from app.core.llm.openai import OpenAILLM
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """
    Factory class for creating LLM provider instances.
    """

    _providers = {
        "claude": ClaudeLLM,
        "openai": OpenAILLM,
    }

    @classmethod
    def create(
        cls,
        provider: str,
        api_key: str,
        model: Optional[str] = None
    ) -> LLMBase:
        """
        Create an LLM instance based on provider name.

        Args:
            provider: Provider name ('claude' or 'openai')
            api_key: API key for the provider
            model: Optional model identifier

        Returns:
            LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()

        if provider not in cls._providers:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: {', '.join(cls._providers.keys())}"
            )

        llm_class = cls._providers[provider]
        logger.info(f"Creating LLM instance for provider: {provider}")
        return llm_class(api_key=api_key, model=model)

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Register a new LLM provider.

        Args:
            name: Provider name
            provider_class: LLM class that inherits from LLMBase
        """
        if not issubclass(provider_class, LLMBase):
            raise ValueError(f"{provider_class} must inherit from LLMBase")

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered new LLM provider: {name}")
