"""
Abstract base class for LLM providers.

Defines the interface that all LLM implementations must follow.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator


class LLMBase(ABC):
    """
    Abstract base class for LLM providers.

    All LLM implementations (Claude, OpenAI, etc.) must inherit from this
    and implement all abstract methods.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize the LLM provider.

        Args:
            api_key: API key for the provider
            model: Model identifier (provider-specific)
        """
        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Provider-specific additional parameters

        Returns:
            Dict with 'content', 'role', and optional 'usage' keys
        """
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific additional parameters

        Yields:
            Content chunks as they arrive
        """
        pass

    @abstractmethod
    async def embed_text(
        self,
        text: str,
        **kwargs
    ) -> List[float]:
        """
        Generate embeddings for text.

        Args:
            text: Text to embed
            **kwargs: Provider-specific additional parameters

        Returns:
            List of embedding values
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens
        """
        pass

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Simplified wrapper around chat_completion that returns just the content.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific additional parameters

        Returns:
            Generated text content
        """
        response = await self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )
        return response.get("content", "")
