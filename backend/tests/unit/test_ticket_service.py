"""
Tests for ticket service
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.services.ticket import TicketService
from app.models.user import User, UserRole
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.models.ticket import Ticket, TicketComment, TicketCategory, TicketStatus, TicketPriority
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketUpdateRequest,
    CommentCreateRequest
)
from app.core.llm.base import LLMBase
from app.core.exceptions import NotFoundError, BadRequestError, PermissionDeniedError


@pytest.fixture
def mock_llm():
    """Create a mock LLM for ticket service"""
    llm = MagicMock(spec=LLMBase)
    # Mock categorization response
    llm.generate = AsyncMock(side_effect=[
        "account",  # First call: categorization
        "TITLE: Password Reset Request\nDESCRIPTION: User unable to reset password after multiple attempts"  # Second call: summarization
    ])
    return llm


@pytest.fixture
async def test_chat_session(test_db: AsyncSession, test_user: User):
    """Create a test chat session with messages"""
    session = ChatSession(
        user_id=test_user.id,
        title="Password reset issue",
        is_resolved=False
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    # Add messages
    messages = [
        ChatMessage(
            session_id=session.id,
            role=MessageRole.USER.value,
            content="I can't reset my password"
        ),
        ChatMessage(
            session_id=session.id,
            role=MessageRole.ASSISTANT.value,
            content="Let me help you with that. Have you tried the forgot password link?"
        ),
        ChatMessage(
            session_id=session.id,
            role=MessageRole.USER.value,
            content="Yes, but I'm not receiving the reset email"
        )
    ]
    for msg in messages:
        test_db.add(msg)
    await test_db.commit()

    return session


@pytest.fixture
async def it_staff_user(test_db: AsyncSession):
    """Create an IT staff user for testing"""
    from app.core.security import get_password_hash

    user = User(
        employee_id="IT001",
        email="it.staff@example.com",
        name="IT Staff",
        hashed_password=get_password_hash("password123"),
        role=UserRole.IT_STAFF,
        department="IT Support"
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


class TestTicketService:
    """Test ticket service"""

    @pytest.mark.asyncio
    async def test_create_ticket_from_session(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test creating ticket from chat session"""
        ticket_service = TicketService(test_db, mock_llm)

        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            additional_notes="Urgent - user locked out",
            priority=TicketPriority.HIGH
        )

        response = await ticket_service.create_ticket_from_session(test_user, request)

        assert response.ticket_number > 0
        assert response.title == "Password Reset Request"
        assert "unable to reset password" in response.description.lower()
        assert response.category == TicketCategory.ACCOUNT
        assert response.status == TicketStatus.OPEN
        assert response.priority == TicketPriority.HIGH
        assert response.requester_id == test_user.id
        assert response.session_id == test_chat_session.id
        assert mock_llm.generate.call_count == 2  # Categorization + summarization

    @pytest.mark.asyncio
    async def test_create_ticket_from_session_already_exists(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test creating ticket from session that already has a ticket"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create first ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        await ticket_service.create_ticket_from_session(test_user, request)

        # Try to create second ticket from same session
        with pytest.raises(BadRequestError, match="already exists"):
            await ticket_service.create_ticket_from_session(test_user, request)

    @pytest.mark.asyncio
    async def test_create_ticket_session_not_found(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test creating ticket from non-existent session"""
        ticket_service = TicketService(test_db, mock_llm)

        request = TicketCreateRequest(
            session_id=uuid.uuid4(),
            priority=TicketPriority.MEDIUM
        )

        with pytest.raises(NotFoundError, match="Chat session not found"):
            await ticket_service.create_ticket_from_session(test_user, request)

    @pytest.mark.asyncio
    async def test_get_ticket_as_requester(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test getting ticket as requester"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Get ticket
        response = await ticket_service.get_ticket(created.id, test_user)

        assert response.id == created.id
        assert response.ticket_number == created.ticket_number
        assert response.requester_id == test_user.id

    @pytest.mark.asyncio
    async def test_get_ticket_permission_denied(
        self,
        test_db: AsyncSession,
        test_user: User,
        it_staff_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test getting ticket as different employee (should fail)"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket as test_user
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Try to get as different employee (create another employee)
        other_user = User(
            employee_id="EMP999",
            email="other@example.com",
            name="Other User",
            hashed_password="hash",
            role=UserRole.EMPLOYEE
        )
        test_db.add(other_user)
        await test_db.commit()
        await test_db.refresh(other_user)

        with pytest.raises(PermissionDeniedError):
            await ticket_service.get_ticket(created.id, other_user)

    @pytest.mark.asyncio
    async def test_get_ticket_as_it_staff(
        self,
        test_db: AsyncSession,
        test_user: User,
        it_staff_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test getting ticket as IT staff (should succeed)"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket as employee
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Get as IT staff
        response = await ticket_service.get_ticket(created.id, it_staff_user, include_internal=True)

        assert response.id == created.id
        assert response.requester_id == test_user.id

    @pytest.mark.asyncio
    async def test_list_tickets_as_employee(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test listing tickets as employee (only own tickets)"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        await ticket_service.create_ticket_from_session(test_user, request)

        # List tickets
        response = await ticket_service.list_tickets(
            user=test_user,
            page=1,
            page_size=20
        )

        assert response.total == 1
        assert len(response.tickets) == 1
        assert response.tickets[0].requester_id == test_user.id

    @pytest.mark.asyncio
    async def test_list_tickets_with_filters(
        self,
        test_db: AsyncSession,
        it_staff_user: User,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test listing tickets with status filter"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Update to in_progress
        update_request = TicketUpdateRequest(status=TicketStatus.IN_PROGRESS)
        await ticket_service.update_ticket(created.id, it_staff_user, update_request)

        # List with status filter
        response = await ticket_service.list_tickets(
            user=it_staff_user,
            status=TicketStatus.IN_PROGRESS,
            page=1,
            page_size=20
        )

        assert response.total == 1
        assert response.tickets[0].status == TicketStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_update_ticket_status(
        self,
        test_db: AsyncSession,
        test_user: User,
        it_staff_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test updating ticket status"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Update status
        update_request = TicketUpdateRequest(status=TicketStatus.RESOLVED)
        response = await ticket_service.update_ticket(created.id, it_staff_user, update_request)

        assert response.status == TicketStatus.RESOLVED
        assert response.resolved_at is not None

    @pytest.mark.asyncio
    async def test_update_ticket_assign(
        self,
        test_db: AsyncSession,
        test_user: User,
        it_staff_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test assigning ticket to IT staff"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Assign to IT staff
        update_request = TicketUpdateRequest(assignee_id=it_staff_user.id)
        response = await ticket_service.update_ticket(created.id, it_staff_user, update_request)

        assert response.assignee_id == it_staff_user.id
        assert response.assignee_name == it_staff_user.name

    @pytest.mark.asyncio
    async def test_update_ticket_permission_denied(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test updating ticket as employee (should fail)"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Try to update as employee
        update_request = TicketUpdateRequest(status=TicketStatus.RESOLVED)

        with pytest.raises(PermissionDeniedError, match="Only IT staff"):
            await ticket_service.update_ticket(created.id, test_user, update_request)

    @pytest.mark.asyncio
    async def test_add_comment(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test adding comment to ticket"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Add comment
        comment_request = CommentCreateRequest(
            content="I tried again but still not working",
            is_internal=False
        )
        comment = await ticket_service.add_comment(created.id, test_user, comment_request)

        assert comment.ticket_id == created.id
        assert comment.author_id == test_user.id
        assert comment.content == comment_request.content
        assert comment.is_internal is False

    @pytest.mark.asyncio
    async def test_add_internal_comment_as_it_staff(
        self,
        test_db: AsyncSession,
        test_user: User,
        it_staff_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test adding internal comment as IT staff"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Add internal comment
        comment_request = CommentCreateRequest(
            content="Internal note: Password reset completed manually",
            is_internal=True
        )
        comment = await ticket_service.add_comment(created.id, it_staff_user, comment_request)

        assert comment.is_internal is True

    @pytest.mark.asyncio
    async def test_add_internal_comment_as_employee_denied(
        self,
        test_db: AsyncSession,
        test_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test adding internal comment as employee (should fail)"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.MEDIUM
        )
        created = await ticket_service.create_ticket_from_session(test_user, request)

        # Try to add internal comment
        comment_request = CommentCreateRequest(
            content="Internal note",
            is_internal=True
        )

        with pytest.raises(PermissionDeniedError, match="Only IT staff"):
            await ticket_service.add_comment(created.id, test_user, comment_request)

    @pytest.mark.asyncio
    async def test_get_ticket_stats(
        self,
        test_db: AsyncSession,
        test_user: User,
        it_staff_user: User,
        test_chat_session: ChatSession,
        mock_llm: LLMBase
    ):
        """Test getting ticket statistics"""
        ticket_service = TicketService(test_db, mock_llm)

        # Create ticket
        request = TicketCreateRequest(
            session_id=test_chat_session.id,
            priority=TicketPriority.HIGH
        )
        await ticket_service.create_ticket_from_session(test_user, request)

        # Get stats
        stats = await ticket_service.get_ticket_stats(it_staff_user)

        assert stats.total_tickets == 1
        assert stats.open_tickets == 1
        assert stats.in_progress_tickets == 0
        assert stats.resolved_tickets == 0
        assert TicketCategory.ACCOUNT.value in stats.tickets_by_category
        assert TicketPriority.HIGH.value in stats.tickets_by_priority

    @pytest.mark.asyncio
    async def test_get_ticket_stats_permission_denied(
        self,
        test_db: AsyncSession,
        test_user: User,
        mock_llm: LLMBase
    ):
        """Test getting ticket stats as employee (should fail)"""
        ticket_service = TicketService(test_db, mock_llm)

        with pytest.raises(PermissionDeniedError, match="Only IT staff"):
            await ticket_service.get_ticket_stats(test_user)
