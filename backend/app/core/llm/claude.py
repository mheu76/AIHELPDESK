"""
Claude (Anthropic) LLM implementation.
"""
from typing import List, Dict, Any, Optional, AsyncIterator
import anthropic
from anthropic import AsyncAnthropic

from app.core.llm.base import LLMBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class ClaudeLLM(LLMBase):
    """
    Claude (Anthropic) implementation of LLMBase.
    """

    # Default models
    DEFAULT_CHAT_MODEL = "claude-3-5-sonnet-20241022"
    DEFAULT_EMBED_MODEL = None  # Claude doesn't provide embeddings yet

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize Claude LLM.

        Args:
            api_key: Anthropic API key
            model: Model identifier (defaults to Claude 3.5 Sonnet)
        """
        super().__init__(api_key, model or self.DEFAULT_CHAT_MODEL)
        self.client = AsyncAnthropic(api_key=api_key)
        logger.info(f"Initialized Claude LLM with model: {self.model}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using Claude.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (default: 4096)
            stream: Whether to stream (if True, raises ValueError)
            **kwargs: Additional parameters for Claude API

        Returns:
            Dict with 'content', 'role', and 'usage' keys
        """
        if stream:
            raise ValueError("Use chat_completion_stream() for streaming responses")

        # Convert messages to Claude format
        # Claude expects system message separate from messages array
        system_message = None
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 4096,
                temperature=temperature,
                system=system_message,
                messages=claude_messages,
                **kwargs
            )

            return {
                "content": response.content[0].text,
                "role": "assistant",
                "model": response.model,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "prompt_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                }
            }
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {str(e)}")
            raise

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion using Claude.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (default: 4096)
            **kwargs: Additional parameters for Claude API

        Yields:
            Content chunks as they arrive
        """
        # Convert messages to Claude format
        system_message = None
        claude_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens or 4096,
                temperature=temperature,
                system=system_message,
                messages=claude_messages,
                **kwargs
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.APIError as e:
            logger.error(f"Claude streaming API error: {str(e)}")
            raise

    async def embed_text(
        self,
        text: str,
        **kwargs
    ) -> List[float]:
        """
        Generate embeddings for text.

        Note: Claude doesn't provide embeddings. This will raise NotImplementedError.
        Use Voyage AI or another embedding provider instead.

        Args:
            text: Text to embed
            **kwargs: Additional parameters

        Raises:
            NotImplementedError: Claude doesn't provide embeddings
        """
        raise NotImplementedError(
            "Claude doesn't provide embeddings. "
            "Use Voyage AI, OpenAI, or another embedding provider."
        )

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text using Claude's tokenizer.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens (approximate)
        """
        # Claude uses a similar tokenizer to GPT
        # Rough approximation: 1 token ≈ 4 characters
        # For production, use the official Anthropic tokenizer
        return len(text) // 4
