"""
OpenAI LLM implementation.
"""
from typing import List, Dict, Any, Optional, AsyncIterator
import openai
from openai import AsyncOpenAI

from app.core.llm.base import LLMBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class OpenAILLM(LLMBase):
    """
    OpenAI implementation of LLMBase.
    """

    # Default models
    DEFAULT_CHAT_MODEL = "gpt-4-turbo-preview"
    DEFAULT_EMBED_MODEL = "text-embedding-3-small"

    def __init__(self, api_key: str, model: Optional[str] = None):
        """
        Initialize OpenAI LLM.

        Args:
            api_key: OpenAI API key
            model: Model identifier (defaults to GPT-4 Turbo)
        """
        super().__init__(api_key, model or self.DEFAULT_CHAT_MODEL)
        self.client = AsyncOpenAI(api_key=api_key)
        self.embed_model = self.DEFAULT_EMBED_MODEL
        logger.info(f"Initialized OpenAI LLM with model: {self.model}")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a chat completion using OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream (if True, raises ValueError)
            **kwargs: Additional parameters for OpenAI API

        Returns:
            Dict with 'content', 'role', and 'usage' keys
        """
        if stream:
            raise ValueError("Use chat_completion_stream() for streaming responses")

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return {
                "content": response.choices[0].message.content,
                "role": "assistant",
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion using OpenAI.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for OpenAI API

        Yields:
            Content chunks as they arrive
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except openai.APIError as e:
            logger.error(f"OpenAI streaming API error: {str(e)}")
            raise

    async def embed_text(
        self,
        text: str,
        **kwargs
    ) -> List[float]:
        """
        Generate embeddings for text using OpenAI.

        Args:
            text: Text to embed
            **kwargs: Additional parameters for OpenAI API

        Returns:
            List of embedding values
        """
        try:
            response = await self.client.embeddings.create(
                model=self.embed_model,
                input=text,
                **kwargs
            )

            return response.data[0].embedding
        except openai.APIError as e:
            logger.error(f"OpenAI embedding API error: {str(e)}")
            raise

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            Number of tokens (approximate)
        """
        # Rough approximation: 1 token ≈ 4 characters
        # For production, use tiktoken library
        return len(text) // 4
