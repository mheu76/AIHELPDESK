"""
Ticket endpoints for IT helpdesk ticketing system.
"""
from fastapi import APIRouter, Depends, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import Optional

from app.api.v1.deps import get_db, get_llm
from app.api.v1.auth import get_current_user
from app.services.ticket import TicketService
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
from app.models.user import User
from app.models.ticket import TicketStatus, TicketCategory
from app.core.llm import LLMBase

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post(
    "",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ticket from chat session"
)
async def create_ticket(
    request: TicketCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Create a ticket from an unresolved chat session.

    - **session_id**: Chat session ID to create ticket from
    - **additional_notes**: Optional additional context for the ticket
    - **priority**: Ticket priority (default: medium)

    The system will automatically:
    - Summarize the conversation into a ticket title and description
    - Categorize the issue (account/device/network/system/security/other)
    - Assign a unique ticket number
    """
    ticket_service = TicketService(db, llm)
    return await ticket_service.create_ticket_from_session(current_user, request)


@router.get(
    "",
    response_model=TicketListResponse,
    summary="List tickets with filters"
)
async def list_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status", description="Filter by ticket status"),
    category: Optional[TicketCategory] = Query(None, description="Filter by category"),
    assignee_id: Optional[uuid.UUID] = Query(None, description="Filter by assignee (IT staff only)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    List tickets with optional filters.

    **Employee users**: See only their own tickets
    **IT staff/Admin**: See all tickets, can filter by assignee

    Supports pagination and filtering by status, category, and assignee.
    """
    ticket_service = TicketService(db, llm)
    return await ticket_service.list_tickets(
        user=current_user,
        status=status_filter,
        category=category,
        assignee_id=assignee_id,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Get ticket details"
)
async def get_ticket(
    ticket_id: uuid.UUID = Path(..., description="Ticket ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Get detailed ticket information including comments.

    **Employee users**: Can view only their own tickets
    **IT staff/Admin**: Can view all tickets including internal comments

    Returns full ticket details, conversation history, and comments.
    """
    from app.models.user import UserRole

    # IT staff can see internal comments
    include_internal = current_user.role in [UserRole.IT_STAFF, UserRole.ADMIN]

    ticket_service = TicketService(db, llm)
    return await ticket_service.get_ticket(
        ticket_id=ticket_id,
        user=current_user,
        include_internal=include_internal
    )


@router.patch(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Update ticket"
)
async def update_ticket(
    ticket_id: uuid.UUID = Path(..., description="Ticket ID"),
    request: TicketUpdateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Update ticket status, priority, assignee, or category.

    **Requires**: IT staff or admin role

    - **status**: Update ticket status (open/in_progress/resolved/on_hold/closed)
    - **priority**: Update priority (low/medium/high/urgent)
    - **assignee_id**: Assign to IT staff member
    - **category**: Update category

    Automatically sets resolved_at timestamp when status is changed to 'resolved'.
    """
    ticket_service = TicketService(db, llm)
    return await ticket_service.update_ticket(
        ticket_id=ticket_id,
        user=current_user,
        request=request
    )


@router.post(
    "/{ticket_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add comment to ticket"
)
async def add_comment(
    ticket_id: uuid.UUID = Path(..., description="Ticket ID"),
    request: CommentCreateRequest = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Add a comment to a ticket.

    **Employee users**: Can comment on their own tickets (public comments only)
    **IT staff/Admin**: Can comment on any ticket, can create internal notes

    - **content**: Comment text (1-5000 characters)
    - **is_internal**: Mark as internal note (IT staff only, not visible to requester)
    """
    ticket_service = TicketService(db, llm)
    return await ticket_service.add_comment(
        ticket_id=ticket_id,
        user=current_user,
        request=request
    )


@router.get(
    "/stats/overview",
    response_model=TicketStatsResponse,
    summary="Get ticket statistics"
)
async def get_ticket_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Get ticket statistics for dashboard.

    **Requires**: IT staff or admin role

    Returns:
    - Total ticket counts by status
    - Breakdown by category
    - Breakdown by priority
    - Average resolution time

    Used for admin dashboard and reporting.
    """
    ticket_service = TicketService(db, llm)
    return await ticket_service.get_ticket_stats(current_user)
