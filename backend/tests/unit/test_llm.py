"""
Tests for LLM abstraction layer
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.llm.base import LLMBase
from app.core.llm.claude import ClaudeLLM
from app.core.llm.openai import OpenAILLM
from app.core.llm.factory import LLMFactory


class TestLLMFactory:
    """Test LLM factory pattern"""

    def test_create_claude_provider(self):
        """Test creating Claude provider"""
        llm = LLMFactory.create(provider="claude", api_key="test-key")
        assert isinstance(llm, ClaudeLLM)
        assert llm.api_key == "test-key"

    def test_create_openai_provider(self):
        """Test creating OpenAI provider"""
        llm = LLMFactory.create(provider="openai", api_key="test-key")
        assert isinstance(llm, OpenAILLM)
        assert llm.api_key == "test-key"

    def test_create_with_custom_model(self):
        """Test creating provider with custom model"""
        llm = LLMFactory.create(
            provider="claude",
            api_key="test-key",
            model="claude-3-opus-20240229"
        )
        assert llm.model == "claude-3-opus-20240229"

    def test_unsupported_provider_raises_error(self):
        """Test that unsupported provider raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            LLMFactory.create(provider="unsupported", api_key="test-key")


class TestClaudeLLM:
    """Test Claude LLM implementation"""

    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        """Test successful chat completion"""
        llm = ClaudeLLM(api_key="test-key")

        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]
        mock_response.usage = MagicMock(
            input_tokens=10,
            output_tokens=20
        )
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch.object(llm.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            messages = [
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"}
            ]

            result = await llm.chat_completion(messages)

            assert result["content"] == "Test response"
            assert result["model"] == "claude-3-5-sonnet-20241022"
            assert result["usage"]["input_tokens"] == 10
            assert result["usage"]["output_tokens"] == 20

    @pytest.mark.asyncio
    async def test_chat_completion_separates_system_message(self):
        """Test that system message is separated from conversation"""
        llm = ClaudeLLM(api_key="test-key")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_response.model = "claude-3-5-sonnet-20241022"

        with patch.object(llm.client.messages, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            messages = [
                {"role": "system", "content": "System prompt"},
                {"role": "user", "content": "Hello"}
            ]

            await llm.chat_completion(messages)

            # Verify that system message was passed separately
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["system"] == "System prompt"
            assert len(call_kwargs["messages"]) == 1
            assert call_kwargs["messages"][0]["role"] == "user"


class TestOpenAILLM:
    """Test OpenAI LLM implementation"""

    @pytest.mark.asyncio
    async def test_chat_completion_success(self):
        """Test successful chat completion"""
        llm = OpenAILLM(api_key="test-key")

        # Mock the OpenAI client response
        mock_message = MagicMock()
        mock_message.content = "Test response"
        mock_choice = MagicMock()
        mock_choice.message = mock_message

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock(
            prompt_tokens=10,
            completion_tokens=20
        )
        mock_response.model = "gpt-4-turbo-preview"

        with patch.object(llm.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            messages = [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"}
            ]

            result = await llm.chat_completion(messages)

            assert result["content"] == "Test response"
            assert result["model"] == "gpt-4-turbo-preview"
            assert result["usage"]["input_tokens"] == 10
            assert result["usage"]["completion_tokens"] == 20

    @pytest.mark.asyncio
    async def test_embed_text_success(self):
        """Test text embedding"""
        llm = OpenAILLM(api_key="test-key")

        # Mock embedding response
        mock_embedding = MagicMock()
        mock_embedding.embedding = [0.1, 0.2, 0.3]

        mock_response = MagicMock()
        mock_response.data = [mock_embedding]

        with patch.object(llm.client.embeddings, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await llm.embed_text("Test text")

            assert result == [0.1, 0.2, 0.3]
            mock_create.assert_called_once()


class TestLLMInterface:
    """Test LLM interface compliance"""

    def test_claude_implements_interface(self):
        """Test that Claude implements LLMBase interface"""
        llm = ClaudeLLM(api_key="test-key")
        assert isinstance(llm, LLMBase)
        assert hasattr(llm, 'chat_completion')
        assert hasattr(llm, 'chat_completion_stream')

    def test_openai_implements_interface(self):
        """Test that OpenAI implements LLMBase interface"""
        llm = OpenAILLM(api_key="test-key")
        assert isinstance(llm, LLMBase)
        assert hasattr(llm, 'chat_completion')
        assert hasattr(llm, 'embed_text')
