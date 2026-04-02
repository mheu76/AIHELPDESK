"""
Tests for chat streaming functionality.
"""
import pytest
import json
import httpx
from httpx import AsyncClient
from fastapi import status
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


@pytest.mark.asyncio
async def test_send_streaming_message_handles_stream_error(test_db, test_user):
    """Test that streaming handles errors and preserves partial content."""
    # Mock LLM streaming that fails after 2 chunks
    async def mock_stream_with_error(*args, **kwargs):
        yield "Partial"
        yield " response"
        raise Exception("API timeout")

    mock_llm = MagicMock()
    mock_llm.chat_completion_stream = mock_stream_with_error

    # Mock settings service
    mock_settings = AsyncMock()
    mock_settings.get_runtime_settings = AsyncMock(return_value=MagicMock(
        rag_enabled=False,
        llm_temperature=0.7,
        max_tokens=1000
    ))

    chat_service = ChatService(test_db, mock_llm)
    chat_service.settings_service = mock_settings

    request = ChatRequest(message="Test error handling")

    # Collect chunks
    chunks = []
    async for chunk_str in chat_service.send_streaming_message(test_user, request):
        chunks.append(json.loads(chunk_str))

    # Verify partial content yielded + error
    assert len(chunks) == 3  # 2 tokens + 1 error
    assert chunks[0] == {"type": "token", "content": "Partial"}
    assert chunks[1] == {"type": "token", "content": " response"}
    assert chunks[2]["type"] == "error"
    assert "API timeout" in chunks[2]["message"]


@pytest.mark.asyncio
async def test_chat_stream_endpoint_returns_ndjson(client: AsyncClient, auth_headers: dict):
    """Test that /chat/stream endpoint returns NDJSON stream."""
    # Send streaming request
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"message": "Hello"},
        headers=auth_headers
    ) as response:
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"

        # Read chunks
        chunks = []
        async for line in response.aiter_lines():
            if line.strip():
                chunks.append(json.loads(line))

        # Verify structure
        assert len(chunks) > 0
        assert chunks[-1]["type"] == "done"
        assert all(c["type"] in ["token", "done", "error"] for c in chunks)


@pytest.mark.asyncio
async def test_chat_stream_endpoint_requires_auth(client: AsyncClient):
    """Test that streaming endpoint requires authentication."""
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"message": "Hello"}
    ) as response:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
