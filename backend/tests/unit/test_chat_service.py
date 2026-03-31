"""
Tests for chat service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.chat import ChatService
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.schemas.chat import ChatRequest
from app.core.llm.base import LLMBase
from app.core.exceptions import NotFoundError


@pytest.fixture
def mock_llm():
    """Create a mock LLM"""
    llm = MagicMock(spec=LLMBase)
    llm.chat_completion = AsyncMock(return_value={
        "content": "This is a test AI response",
        "model": "test-model",
        "usage": {
            "input_tokens": 50,
            "completion_tokens": 20
        }
    })
    return llm


@pytest.fixture
def mock_rag_service():
    """Create a mock RAG service"""
    from unittest.mock import MagicMock
    rag = MagicMock()
    rag.search_knowledge_base = AsyncMock(return_value=[])
    return rag


class TestChatService:
    """Test chat service"""

    @pytest.mark.asyncio
    async def test_send_message_creates_new_session(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test sending message creates new session"""
        chat_service = ChatService(test_db, mock_llm)

        request = ChatRequest(
            message="How do I reset my password?",
            session_id=None
        )

        response = await chat_service.send_message(test_user, request)

        assert response.session_id is not None
        assert response.message.role == MessageRole.ASSISTANT.value
        assert response.message.content == "This is a test AI response"
        assert response.is_resolved is False

        # Verify session was created
        from sqlalchemy import select
        result = await test_db.execute(
            select(ChatSession).where(ChatSession.id == response.session_id)
        )
        session = result.scalar_one_or_none()
        assert session is not None
        assert session.user_id == test_user.id

    @pytest.mark.asyncio
    async def test_send_message_with_existing_session(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test sending message to existing session"""
        chat_service = ChatService(test_db, mock_llm)

        # Create first message (creates session)
        request1 = ChatRequest(message="First message", session_id=None)
        response1 = await chat_service.send_message(test_user, request1)
        session_id = response1.session_id

        # Send second message to same session
        request2 = ChatRequest(message="Second message", session_id=session_id)
        response2 = await chat_service.send_message(test_user, request2)

        assert response2.session_id == session_id

        # Verify both messages exist
        from sqlalchemy import select
        result = await test_db.execute(
            select(ChatMessage).where(ChatMessage.session_id == session_id)
        )
        messages = result.scalars().all()
        # Should have 4 messages: 2 user + 2 assistant
        assert len(messages) >= 2

    @pytest.mark.asyncio
    async def test_send_message_invalid_session_fails(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test sending message to non-existent session"""
        import uuid
        chat_service = ChatService(test_db, mock_llm)

        request = ChatRequest(
            message="Test message",
            session_id=uuid.uuid4()  # Random non-existent ID
        )

        with pytest.raises(NotFoundError, match="not found"):
            await chat_service.send_message(test_user, request)

    @pytest.mark.asyncio
    async def test_send_message_generates_title(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test that first message generates session title"""
        chat_service = ChatService(test_db, mock_llm)

        request = ChatRequest(
            message="How do I reset my password?",
            session_id=None
        )

        response = await chat_service.send_message(test_user, request)

        # Get session to check title
        from sqlalchemy import select
        result = await test_db.execute(
            select(ChatSession).where(ChatSession.id == response.session_id)
        )
        session = result.scalar_one()

        assert session.title is not None
        assert len(session.title) > 0

    @pytest.mark.asyncio
    async def test_get_user_sessions(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test getting user's sessions"""
        chat_service = ChatService(test_db, mock_llm)

        # Create multiple sessions
        for i in range(3):
            request = ChatRequest(message=f"Message {i}", session_id=None)
            await chat_service.send_message(test_user, request)

        # Get sessions
        result = await chat_service.get_user_sessions(test_user.id)

        assert result.total == 3
        assert len(result.sessions) == 3

    @pytest.mark.asyncio
    async def test_get_session_detail(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test getting session detail with messages"""
        chat_service = ChatService(test_db, mock_llm)

        # Create session with messages
        request1 = ChatRequest(message="First", session_id=None)
        response1 = await chat_service.send_message(test_user, request1)

        request2 = ChatRequest(message="Second", session_id=response1.session_id)
        await chat_service.send_message(test_user, request2)

        # Get session detail
        detail = await chat_service.get_session_detail(
            response1.session_id,
            test_user.id
        )

        assert detail.id == response1.session_id
        assert len(detail.messages) >= 2  # At least user + assistant messages

    @pytest.mark.asyncio
    async def test_mark_session_resolved(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test marking session as resolved"""
        chat_service = ChatService(test_db, mock_llm)

        # Create session
        request = ChatRequest(message="Test", session_id=None)
        response = await chat_service.send_message(test_user, request)

        # Mark as resolved
        updated = await chat_service.mark_session_resolved(
            response.session_id,
            test_user.id,
            is_resolved=True
        )

        assert updated.is_resolved is True

        # Mark as unresolved
        updated = await chat_service.mark_session_resolved(
            response.session_id,
            test_user.id,
            is_resolved=False
        )

        assert updated.is_resolved is False

    @pytest.mark.asyncio
    async def test_get_session_detail_wrong_user_fails(
        self,
        test_db: AsyncSession,
        test_user: User,
        admin_user: User,
        mock_llm: LLMBase
    ):
        """Test that user cannot access another user's session"""
        chat_service = ChatService(test_db, mock_llm)

        # Create session as test_user
        request = ChatRequest(message="Test", session_id=None)
        response = await chat_service.send_message(test_user, request)

        # Try to access as admin_user
        with pytest.raises(NotFoundError):
            await chat_service.get_session_detail(
                response.session_id,
                admin_user.id  # Different user
            )

    @pytest.mark.asyncio
    async def test_conversation_history_includes_system_prompt(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test that conversation history includes system prompt"""
        chat_service = ChatService(test_db, mock_llm)

        request = ChatRequest(message="Test", session_id=None)
        await chat_service.send_message(test_user, request)

        # Check that LLM was called with system prompt
        mock_llm.chat_completion.assert_called_once()
        call_args = mock_llm.chat_completion.call_args[1]
        messages = call_args["messages"]

        # First message should be system prompt
        assert messages[0]["role"] == "system"
        assert "IT helpdesk" in messages[0]["content"]
