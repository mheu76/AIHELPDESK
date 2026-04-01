"""
Tests for ticket API endpoints
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock

from app.models.user import User, UserRole
from app.models.chat import ChatSession, ChatMessage, MessageRole


@pytest.fixture
def mock_llm_for_ticket_api():
    """Mock LLM for ticket API tests"""
    with patch('app.api.v1.deps.get_llm') as mock:
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=[
            "account",  # Categorization
            "TITLE: Test Ticket\nDESCRIPTION: Test description"  # Summarization
        ])
        mock.return_value = llm
        yield mock


@pytest.fixture
async def test_chat_session_for_api(test_db, test_user):
    """Create a test chat session with messages"""
    session = ChatSession(
        user_id=test_user.id,
        title="Test issue",
        is_resolved=False
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)

    messages = [
        ChatMessage(
            session_id=session.id,
            role=MessageRole.USER.value,
            content="I have a problem"
        ),
        ChatMessage(
            session_id=session.id,
            role=MessageRole.ASSISTANT.value,
            content="Let me help you"
        )
    ]
    for msg in messages:
        test_db.add(msg)
    await test_db.commit()

    return session


@pytest.fixture
async def it_staff_headers(test_client: AsyncClient, test_db):
    """Get auth headers for IT staff user"""
    from app.core.security import get_password_hash

    # Create IT staff user
    it_user = User(
        employee_id="IT001",
        email="it@example.com",
        name="IT Staff",
        hashed_password=get_password_hash("password123"),
        role=UserRole.IT_STAFF,
        department="IT"
    )
    test_db.add(it_user)
    await test_db.commit()

    # Login
    response = await test_client.post(
        "/api/v1/auth/login",
        json={
            "employee_id": "IT001",
            "password": "password123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestTicketAPI:
    """Test ticket endpoints"""

    @pytest.mark.asyncio
    async def test_create_ticket(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test creating ticket from chat session"""
        response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "additional_notes": "Urgent issue",
                "priority": "high"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert "ticket_number" in data
        assert data["title"] == "Test Ticket"
        assert data["description"] == "Test description"
        assert data["category"] == "account"
        assert data["status"] == "open"
        assert data["priority"] == "high"
        assert data["requester_id"] == str(test_user.id)
        assert data["session_id"] == str(test_chat_session_for_api.id)

    @pytest.mark.asyncio
    async def test_create_ticket_duplicate(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test creating duplicate ticket from same session fails"""
        # Create first ticket
        response1 = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        assert response1.status_code == 201

        # Try to create second ticket
        mock_llm_for_ticket_api.return_value.generate = AsyncMock(side_effect=[
            "account",
            "TITLE: Test\nDESCRIPTION: Test"
        ])

        response2 = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_tickets_as_employee(
        self,
        test_client: AsyncClient,
        test_user: User,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test listing tickets as employee (only own tickets)"""
        # Create ticket
        await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )

        # List tickets
        response = await test_client.get(
            "/api/v1/tickets",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["tickets"]) == 1
        assert data["tickets"][0]["requester_id"] == str(test_user.id)

    @pytest.mark.asyncio
    async def test_list_tickets_with_status_filter(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        it_staff_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test listing tickets with status filter"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Update status to in_progress
        await test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            headers=it_staff_headers,
            json={"status": "in_progress"}
        )

        # List with filter
        response = await test_client.get(
            "/api/v1/tickets?status=in_progress",
            headers=it_staff_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tickets"][0]["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_get_ticket_detail(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test getting ticket details"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Get detail
        response = await test_client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ticket_id
        assert "ticket_number" in data
        assert "comments" in data

    @pytest.mark.asyncio
    async def test_get_ticket_permission_denied(
        self,
        test_client: AsyncClient,
        test_db,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test getting other user's ticket fails for employee"""
        # Create ticket as test_user
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Create another employee
        from app.core.security import get_password_hash
        other_user = User(
            employee_id="EMP999",
            email="other@example.com",
            name="Other User",
            hashed_password=get_password_hash("password123"),
            role=UserRole.EMPLOYEE
        )
        test_db.add(other_user)
        await test_db.commit()

        # Login as other user
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={"employee_id": "EMP999", "password": "password123"}
        )
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to get ticket
        response = await test_client.get(
            f"/api/v1/tickets/{ticket_id}",
            headers=other_headers
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_update_ticket_status(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        it_staff_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test updating ticket status as IT staff"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Update status
        response = await test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            headers=it_staff_headers,
            json={"status": "resolved"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "resolved"
        assert data["resolved_at"] is not None

    @pytest.mark.asyncio
    async def test_update_ticket_assign(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        it_staff_headers: dict,
        test_db,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test assigning ticket to IT staff"""
        # Get IT staff user ID
        from sqlalchemy import select
        from app.models.user import User
        result = await test_db.execute(
            select(User).where(User.email == "it@example.com")
        )
        it_user = result.scalar_one()

        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Assign
        response = await test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            headers=it_staff_headers,
            json={"assignee_id": str(it_user.id)}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["assignee_id"] == str(it_user.id)
        assert data["assignee_name"] == "IT Staff"

    @pytest.mark.asyncio
    async def test_update_ticket_as_employee_denied(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test updating ticket as employee fails"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Try to update
        response = await test_client.patch(
            f"/api/v1/tickets/{ticket_id}",
            headers=auth_headers,
            json={"status": "resolved"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_add_comment(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test adding comment to ticket"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Add comment
        response = await test_client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=auth_headers,
            json={
                "content": "This is a comment",
                "is_internal": False
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["ticket_id"] == ticket_id
        assert data["content"] == "This is a comment"
        assert data["is_internal"] is False

    @pytest.mark.asyncio
    async def test_add_internal_comment_as_it_staff(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        it_staff_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test adding internal comment as IT staff"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Add internal comment
        response = await test_client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=it_staff_headers,
            json={
                "content": "Internal note",
                "is_internal": True
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_internal"] is True

    @pytest.mark.asyncio
    async def test_add_internal_comment_as_employee_denied(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test adding internal comment as employee fails"""
        # Create ticket
        create_response = await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "medium"
            }
        )
        ticket_id = create_response.json()["id"]

        # Try to add internal comment
        response = await test_client.post(
            f"/api/v1/tickets/{ticket_id}/comments",
            headers=auth_headers,
            json={
                "content": "Internal note",
                "is_internal": True
            }
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_get_ticket_stats(
        self,
        test_client: AsyncClient,
        auth_headers: dict,
        it_staff_headers: dict,
        test_chat_session_for_api: ChatSession,
        mock_llm_for_ticket_api
    ):
        """Test getting ticket statistics as IT staff"""
        # Create ticket
        await test_client.post(
            "/api/v1/tickets",
            headers=auth_headers,
            json={
                "session_id": str(test_chat_session_for_api.id),
                "priority": "high"
            }
        )

        # Get stats
        response = await test_client.get(
            "/api/v1/tickets/stats/overview",
            headers=it_staff_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_tickets" in data
        assert "open_tickets" in data
        assert "tickets_by_category" in data
        assert "tickets_by_priority" in data
        assert data["total_tickets"] >= 1

    @pytest.mark.asyncio
    async def test_get_ticket_stats_as_employee_denied(
        self,
        test_client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting ticket stats as employee fails"""
        response = await test_client.get(
            "/api/v1/tickets/stats/overview",
            headers=auth_headers
        )

        assert response.status_code == 403
