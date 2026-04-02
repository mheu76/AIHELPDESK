"""
Tests for chat streaming functionality.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.chat import ChatService
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.schemas.chat import ChatRequest


@pytest.mark.asyncio
async def test_send_streaming_message_yields_chunks(test_db, test_user):
    """Test that send_streaming_message yields NDJSON chunks correctly."""
    # Mock LLM streaming
    async def mock_stream(*args, **kwargs):
        yield "Hello"
        yield " world"
        yield "!"

    mock_llm = MagicMock()
    mock_llm.chat_completion_stream = mock_stream

    # Mock settings service
    mock_settings = AsyncMock()
    mock_settings.get_runtime_settings = AsyncMock(return_value=MagicMock(
        rag_enabled=False,
        llm_temperature=0.7,
        max_tokens=1000
    ))

    chat_service = ChatService(test_db, mock_llm)
    chat_service.settings_service = mock_settings

    request = ChatRequest(message="Test message")

    # Collect chunks
    chunks = []
    async for chunk_str in chat_service.send_streaming_message(test_user, request):
        chunks.append(json.loads(chunk_str))

    # Verify chunks
    assert len(chunks) == 4  # 3 tokens + 1 done
    assert chunks[0] == {"type": "token", "content": "Hello"}
    assert chunks[1] == {"type": "token", "content": " world"}
    assert chunks[2] == {"type": "token", "content": "!"}
    assert chunks[3]["type"] == "done"
    assert "session_id" in chunks[3]
    assert "message_id" in chunks[3]
