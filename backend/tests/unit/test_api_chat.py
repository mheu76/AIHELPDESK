"""
Tests for chat API endpoints
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

from app.models.user import User


@pytest.fixture
def mock_llm_for_api():
    """Mock LLM for API tests"""
    with patch('app.api.v1.deps.get_llm') as mock:
        from unittest.mock import MagicMock
        llm = MagicMock()
        llm.chat_completion = AsyncMock(return_value={
            "content": "Test AI response",
            "model": "test-model",
            "usage": {"input_tokens": 10, "completion_tokens": 5}
        })
        mock.return_value = llm
        yield mock


class TestChatAPI:
    """Test chat endpoints"""

    @pytest.mark.asyncio
    async def test_send_message_creates_session(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_llm_for_api
    ):
        """Test sending message creates new session"""
        response = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "message": "How do I reset my password?"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["message"]["role"] == "assistant"
        assert data["message"]["content"] == "Test AI response"
        assert data["is_resolved"] is False

    @pytest.mark.asyncio
    async def test_send_message_to_existing_session(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_llm_for_api
    ):
        """Test sending message to existing session"""
        # Create first message
        response1 = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": "First message"}
        )
        session_id = response1.json()["session_id"]

        # Send second message to same session
        response2 = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={
                "message": "Second message",
                "session_id": session_id
            }
        )

        assert response2.status_code == 200
        data = response2.json()
        assert data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_send_message_unauthenticated(self, test_client: AsyncClient):
        """Test sending message without authentication"""
        response = await test_client.post(
            "/api/v1/chat",
            json={"message": "Test"}
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_send_message_empty_message(
        self,
        test_client: AsyncClient,
        auth_headers: dict
    ):
        """Test sending empty message"""
        response = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": ""}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_sessions(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_llm_for_api
    ):
        """Test getting user's sessions"""
        # Create some sessions
        for i in range(3):
            await test_client.post(
                "/api/v1/chat",
                headers=auth_headers,
                json={"message": f"Message {i}"}
            )

        # Get sessions
        response = await test_client.get(
            "/api/v1/chat/sessions",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert data["total"] == 3
        assert len(data["sessions"]) == 3

    @pytest.mark.asyncio
    async def test_get_sessions_pagination(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_llm_for_api
    ):
        """Test session pagination"""
        # Create 5 sessions
        for i in range(5):
            await test_client.post(
                "/api/v1/chat",
                headers=auth_headers,
                json={"message": f"Message {i}"}
            )

        # Get first 2
        response = await test_client.get(
            "/api/v1/chat/sessions?limit=2&offset=0",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 2
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_get_session_detail(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_llm_for_api
    ):
        """Test getting session detail"""
        # Create session
        create_response = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": "Test message"}
        )
        session_id = create_response.json()["session_id"]

        # Get session detail
        response = await test_client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert "messages" in data
        assert len(data["messages"]) >= 2  # User + assistant

    @pytest.mark.asyncio
    async def test_get_session_detail_wrong_user(
        self,
        test_client: AsyncClient,
        test_user: User,
        admin_user: User,
        auth_headers: dict,
        admin_headers: dict,
        mock_llm_for_api
    ):
        """Test that user cannot access another user's session"""
        # Create session as test_user
        create_response = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": "Test"}
        )
        session_id = create_response.json()["session_id"]

        # Try to access as admin_user
        response = await test_client.get(
            f"/api/v1/chat/sessions/{session_id}",
            headers=admin_headers
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_session_resolved(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        mock_llm_for_api
    ):
        """Test marking session as resolved"""
        # Create session
        create_response = await test_client.post(
            "/api/v1/chat",
            headers=auth_headers,
            json={"message": "Test"}
        )
        session_id = create_response.json()["session_id"]

        # Mark as resolved
        response = await test_client.patch(
            f"/api/v1/chat/sessions/{session_id}/resolve",
            headers=auth_headers,
            json={"is_resolved": True}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is True

        # Mark as unresolved
        response = await test_client.patch(
            f"/api/v1/chat/sessions/{session_id}/resolve",
            headers=auth_headers,
            json={"is_resolved": False}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_resolved"] is False

    @pytest.mark.asyncio
    async def test_mark_session_resolved_unauthenticated(
        self,
        test_client: AsyncClient
    ):
        """Test marking session resolved without auth"""
        import uuid
        session_id = uuid.uuid4()

        response = await test_client.patch(
            f"/api/v1/chat/sessions/{session_id}/resolve",
            json={"is_resolved": True}
        )

        assert response.status_code == 401
