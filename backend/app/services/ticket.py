"""
Ticket service for IT helpdesk ticketing system.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_
from sqlalchemy.orm import selectinload, joinedload
import uuid
from datetime import datetime

from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketComment, TicketCategory, TicketStatus, TicketPriority
from app.models.chat import ChatSession, ChatMessage
from app.schemas.ticket import (
    TicketCreateRequest,
    TicketUpdateRequest,
    TicketResponse,
    TicketListResponse,
    TicketDetailResponse,
    CommentCreateRequest,
    CommentResponse,
    TicketStatsResponse
)
from app.core.llm import LLMBase
from app.core.exceptions import NotFoundError, BadRequestError, PermissionDeniedError
from app.core.logging import get_logger

logger = get_logger(__name__)


class TicketService:
    """Service for ticket management and AI-powered ticket creation"""

    CATEGORIZATION_PROMPT = """You are an IT helpdesk ticket categorization assistant.
Analyze the conversation and categorize the IT issue into ONE of these categories:

- account: Login issues, password resets, account access, permissions
- device: Hardware problems, laptops, monitors, keyboards, printers
- network: WiFi, VPN, internet connectivity, network drives
- system: Software installation, OS issues, application errors, performance
- security: Security concerns, malware, phishing, data protection
- other: Issues that don't fit the above categories

Conversation:
{conversation}

Respond with ONLY the category name (lowercase), nothing else."""

    SUMMARIZATION_PROMPT = """You are an IT helpdesk ticket summarization assistant.
Create a concise ticket based on this conversation between an employee and the AI assistant.

Conversation:
{conversation}

Generate:
1. A clear, concise title (max 100 characters)
2. A detailed description summarizing the issue and any troubleshooting attempts

Format your response EXACTLY as:
TITLE: [ticket title here]
DESCRIPTION: [detailed description here]"""

    def __init__(self, db: AsyncSession, llm: LLMBase):
        self.db = db
        self.llm = llm

    async def create_ticket_from_session(
        self,
        user: User,
        request: TicketCreateRequest
    ) -> TicketDetailResponse:
        """
        Create a ticket from a chat session with AI-powered summarization.

        Args:
            user: User creating the ticket
            request: Ticket creation request

        Returns:
            Created ticket details

        Raises:
            NotFoundError: If session not found
            BadRequestError: If session already has a ticket
        """
        # Get chat session
        session = await self._get_session(request.session_id, user.id)

        # Check if ticket already exists
        if session.ticket:
            raise BadRequestError("Ticket already exists for this chat session")

        # Get conversation history
        conversation = await self._format_conversation(session)

        # Use AI to categorize and summarize
        category = await self._categorize_issue(conversation)
        title, description = await self._summarize_conversation(conversation, request.additional_notes)

        # Create ticket
        ticket = Ticket(
            title=title,
            description=description,
            category=category,
            status=TicketStatus.OPEN,
            priority=request.priority or TicketPriority.MEDIUM,
            requester_id=user.id,
            session_id=session.id
        )

        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)

        logger.info(f"Created ticket {ticket.ticket_number} from session {session.id}")

        # Load relationships for response
        await self.db.refresh(ticket, ["requester", "assignee", "comments"])

        return await self._build_ticket_detail_response(ticket)

    async def get_ticket(
        self,
        ticket_id: uuid.UUID,
        user: User,
        include_internal: bool = False
    ) -> TicketDetailResponse:
        """
        Get ticket details.

        Args:
            ticket_id: Ticket ID
            user: Current user
            include_internal: Include internal comments (IT staff only)

        Returns:
            Ticket details

        Raises:
            NotFoundError: If ticket not found
            PermissionDeniedError: If user cannot access ticket
        """
        ticket = await self._get_ticket_by_id(ticket_id)

        # Check permissions
        can_view_all = user.role in [UserRole.IT_STAFF, UserRole.ADMIN]
        if not can_view_all and ticket.requester_id != user.id:
            raise PermissionDeniedError("Cannot access this ticket")

        # Load relationships
        await self.db.refresh(ticket, ["requester", "assignee", "comments"])

        return await self._build_ticket_detail_response(ticket, include_internal=include_internal)

    async def list_tickets(
        self,
        user: User,
        status: Optional[TicketStatus] = None,
        category: Optional[TicketCategory] = None,
        assignee_id: Optional[uuid.UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> TicketListResponse:
        """
        List tickets with filters.

        Args:
            user: Current user
            status: Filter by status
            category: Filter by category
            assignee_id: Filter by assignee (IT staff only)
            page: Page number
            page_size: Items per page

        Returns:
            Paginated ticket list
        """
        # Build query
        query = select(Ticket).options(
            joinedload(Ticket.requester),
            joinedload(Ticket.assignee),
            selectinload(Ticket.comments)
        )

        # Apply filters based on role
        if user.role == UserRole.EMPLOYEE:
            # Employees see only their own tickets
            query = query.where(Ticket.requester_id == user.id)
        elif assignee_id:
            # IT staff can filter by assignee
            query = query.where(Ticket.assignee_id == assignee_id)

        if status:
            query = query.where(Ticket.status == status)
        if category:
            query = query.where(Ticket.category == category)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        query = query.order_by(desc(Ticket.created_at))
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        tickets = result.unique().scalars().all()

        # Build response
        ticket_responses = [
            await self._build_ticket_response(ticket)
            for ticket in tickets
        ]

        return TicketListResponse(
            tickets=ticket_responses,
            total=total,
            page=page,
            page_size=page_size
        )

    async def update_ticket(
        self,
        ticket_id: uuid.UUID,
        user: User,
        request: TicketUpdateRequest
    ) -> TicketDetailResponse:
        """
        Update ticket status, assignment, or priority.

        Args:
            ticket_id: Ticket ID
            user: Current user (must be IT staff or admin)
            request: Update request

        Returns:
            Updated ticket details

        Raises:
            PermissionDeniedError: If user is not IT staff/admin
        """
        if user.role not in [UserRole.IT_STAFF, UserRole.ADMIN]:
            raise PermissionDeniedError("Only IT staff can update tickets")

        ticket = await self._get_ticket_by_id(ticket_id)

        # Apply updates
        if request.status is not None:
            ticket.status = request.status
            if request.status == TicketStatus.RESOLVED:
                ticket.resolved_at = datetime.utcnow()

        if request.priority is not None:
            ticket.priority = request.priority

        if request.assignee_id is not None:
            # Verify assignee exists and is IT staff
            assignee = await self._get_user_by_id(request.assignee_id)
            if assignee.role not in [UserRole.IT_STAFF, UserRole.ADMIN]:
                raise BadRequestError("Can only assign to IT staff or admin")
            ticket.assignee_id = request.assignee_id

        if request.category is not None:
            ticket.category = request.category

        await self.db.commit()
        await self.db.refresh(ticket, ["requester", "assignee", "comments"])

        logger.info(f"Updated ticket {ticket.ticket_number} by user {user.id}")

        return await self._build_ticket_detail_response(ticket)

    async def add_comment(
        self,
        ticket_id: uuid.UUID,
        user: User,
        request: CommentCreateRequest
    ) -> CommentResponse:
        """
        Add a comment to a ticket.

        Args:
            ticket_id: Ticket ID
            user: Current user
            request: Comment request

        Returns:
            Created comment

        Raises:
            PermissionDeniedError: If employee tries to create internal comment
        """
        ticket = await self._get_ticket_by_id(ticket_id)

        # Check permissions
        can_access = (
            ticket.requester_id == user.id or
            user.role in [UserRole.IT_STAFF, UserRole.ADMIN]
        )
        if not can_access:
            raise PermissionDeniedError("Cannot access this ticket")

        # Only IT staff can create internal comments
        if request.is_internal and user.role not in [UserRole.IT_STAFF, UserRole.ADMIN]:
            raise PermissionDeniedError("Only IT staff can create internal comments")

        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=user.id,
            content=request.content,
            is_internal=request.is_internal
        )

        self.db.add(comment)
        await self.db.commit()
        await self.db.refresh(comment, ["author"])

        logger.info(f"Added comment to ticket {ticket.ticket_number}")

        return CommentResponse(
            id=comment.id,
            ticket_id=comment.ticket_id,
            author_id=comment.author_id,
            author_name=comment.author.name,
            content=comment.content,
            is_internal=comment.is_internal,
            created_at=comment.created_at
        )

    async def get_ticket_stats(self, user: User) -> TicketStatsResponse:
        """
        Get ticket statistics for dashboard.

        Args:
            user: Current user (must be IT staff or admin)

        Returns:
            Ticket statistics

        Raises:
            PermissionDeniedError: If user is not IT staff/admin
        """
        if user.role not in [UserRole.IT_STAFF, UserRole.ADMIN]:
            raise PermissionDeniedError("Only IT staff can view statistics")

        # Total tickets
        total_query = select(func.count(Ticket.id))
        total_result = await self.db.execute(total_query)
        total_tickets = total_result.scalar_one()

        # By status
        open_query = select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.OPEN)
        open_result = await self.db.execute(open_query)
        open_tickets = open_result.scalar_one()

        in_progress_query = select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.IN_PROGRESS)
        in_progress_result = await self.db.execute(in_progress_query)
        in_progress_tickets = in_progress_result.scalar_one()

        resolved_query = select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.RESOLVED)
        resolved_result = await self.db.execute(resolved_query)
        resolved_tickets = resolved_result.scalar_one()

        # By category
        category_query = select(
            Ticket.category,
            func.count(Ticket.id)
        ).group_by(Ticket.category)
        category_result = await self.db.execute(category_query)
        tickets_by_category = {
            str(cat): count for cat, count in category_result.all()
        }

        # By priority
        priority_query = select(
            Ticket.priority,
            func.count(Ticket.id)
        ).group_by(Ticket.priority)
        priority_result = await self.db.execute(priority_query)
        tickets_by_priority = {
            str(pri): count for pri, count in priority_result.all()
        }

        return TicketStatsResponse(
            total_tickets=total_tickets,
            open_tickets=open_tickets,
            in_progress_tickets=in_progress_tickets,
            resolved_tickets=resolved_tickets,
            tickets_by_category=tickets_by_category,
            tickets_by_priority=tickets_by_priority
        )

    # Private helper methods

    async def _get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession:
        """Get chat session by ID and verify ownership"""
        query = select(ChatSession).where(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id
            )
        ).options(
            selectinload(ChatSession.messages),
            selectinload(ChatSession.ticket)
        )

        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError("Chat session not found")

        return session

    async def _get_ticket_by_id(self, ticket_id: uuid.UUID) -> Ticket:
        """Get ticket by ID"""
        query = select(Ticket).where(Ticket.id == ticket_id)
        result = await self.db.execute(query)
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise NotFoundError("Ticket not found")

        return ticket

    async def _get_user_by_id(self, user_id: uuid.UUID) -> User:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError("User not found")

        return user

    async def _format_conversation(self, session: ChatSession) -> str:
        """Format chat messages into conversation text"""
        lines = []
        for msg in session.messages:
            role = "Employee" if msg.role == "user" else "AI Assistant"
            lines.append(f"{role}: {msg.content}")

        return "\n\n".join(lines)

    async def _categorize_issue(self, conversation: str) -> TicketCategory:
        """Use AI to categorize the IT issue"""
        try:
            prompt = self.CATEGORIZATION_PROMPT.format(conversation=conversation)
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.0
            )

            category_str = response.strip().lower()

            # Map to enum
            category_map = {
                "account": TicketCategory.ACCOUNT,
                "device": TicketCategory.DEVICE,
                "network": TicketCategory.NETWORK,
                "system": TicketCategory.SYSTEM,
                "security": TicketCategory.SECURITY,
                "other": TicketCategory.OTHER
            }

            return category_map.get(category_str, TicketCategory.OTHER)

        except Exception as e:
            logger.warning(f"Failed to categorize ticket: {e}")
            return TicketCategory.OTHER

    async def _summarize_conversation(
        self,
        conversation: str,
        additional_notes: Optional[str] = None
    ) -> tuple[str, str]:
        """Use AI to generate ticket title and description"""
        try:
            prompt_text = conversation
            if additional_notes:
                prompt_text += f"\n\nAdditional Notes: {additional_notes}"

            prompt = self.SUMMARIZATION_PROMPT.format(conversation=prompt_text)
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )

            # Parse response
            title = ""
            description = ""

            for line in response.split("\n"):
                if line.startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    description = line.replace("DESCRIPTION:", "").strip()

            # Fallback if parsing fails
            if not title:
                title = "IT Support Request"
            if not description:
                description = conversation[:500]

            return title[:500], description

        except Exception as e:
            logger.warning(f"Failed to summarize ticket: {e}")
            return "IT Support Request", conversation[:500]

    async def _build_ticket_response(self, ticket: Ticket) -> TicketResponse:
        """Build ticket response with relationships"""
        return TicketResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            title=ticket.title,
            description=ticket.description,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            requester_id=ticket.requester_id,
            requester_name=ticket.requester.name if ticket.requester else None,
            assignee_id=ticket.assignee_id,
            assignee_name=ticket.assignee.name if ticket.assignee else None,
            session_id=ticket.session_id,
            resolved_at=ticket.resolved_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            comment_count=len(ticket.comments) if ticket.comments else 0
        )

    async def _build_ticket_detail_response(
        self,
        ticket: Ticket,
        include_internal: bool = False
    ) -> TicketDetailResponse:
        """Build detailed ticket response with comments"""
        comments = []
        for comment in (ticket.comments or []):
            # Filter internal comments for non-IT staff
            if comment.is_internal and not include_internal:
                continue

            comments.append(CommentResponse(
                id=comment.id,
                ticket_id=comment.ticket_id,
                author_id=comment.author_id,
                author_name=comment.author.name if comment.author else None,
                content=comment.content,
                is_internal=comment.is_internal,
                created_at=comment.created_at
            ))

        return TicketDetailResponse(
            id=ticket.id,
            ticket_number=ticket.ticket_number,
            title=ticket.title,
            description=ticket.description,
            category=ticket.category,
            status=ticket.status,
            priority=ticket.priority,
            requester_id=ticket.requester_id,
            requester_name=ticket.requester.name if ticket.requester else None,
            requester_email=ticket.requester.email if ticket.requester else None,
            assignee_id=ticket.assignee_id,
            assignee_name=ticket.assignee.name if ticket.assignee else None,
            session_id=ticket.session_id,
            resolved_at=ticket.resolved_at,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
            comments=comments
        )
