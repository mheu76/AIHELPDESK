"""
Pydantic schemas for ticket endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.ticket import TicketCategory, TicketStatus, TicketPriority


class TicketCreateRequest(BaseModel):
    """Request to create ticket from chat session"""
    session_id: uuid.UUID = Field(..., description="Chat session ID to create ticket from")
    additional_notes: Optional[str] = Field(None, max_length=2000, description="Additional context for the ticket")
    priority: Optional[TicketPriority] = Field(TicketPriority.MEDIUM, description="Ticket priority")


class TicketUpdateRequest(BaseModel):
    """Request to update ticket status/assignment"""
    status: Optional[TicketStatus] = Field(None, description="New ticket status")
    priority: Optional[TicketPriority] = Field(None, description="New ticket priority")
    assignee_id: Optional[uuid.UUID] = Field(None, description="Assign to IT staff user ID")
    category: Optional[TicketCategory] = Field(None, description="Ticket category")


class CommentCreateRequest(BaseModel):
    """Request to add comment to ticket"""
    content: str = Field(..., min_length=1, max_length=5000, description="Comment content")
    is_internal: bool = Field(False, description="Internal note (not visible to requester)")


class CommentResponse(BaseModel):
    """Ticket comment response"""
    id: uuid.UUID
    ticket_id: uuid.UUID
    author_id: uuid.UUID
    author_name: Optional[str] = None
    content: str
    is_internal: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class TicketResponse(BaseModel):
    """Ticket response schema"""
    id: uuid.UUID
    ticket_number: int
    title: str
    description: str
    category: TicketCategory
    status: TicketStatus
    priority: TicketPriority
    requester_id: uuid.UUID
    requester_name: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = None
    assignee_name: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    comment_count: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class TicketListResponse(BaseModel):
    """List of tickets with pagination"""
    tickets: List[TicketResponse]
    total: int
    page: int = 1
    page_size: int = 20


class TicketDetailResponse(BaseModel):
    """Detailed ticket with comments and session info"""
    id: uuid.UUID
    ticket_number: int
    title: str
    description: str
    category: TicketCategory
    status: TicketStatus
    priority: TicketPriority
    requester_id: uuid.UUID
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    assignee_id: Optional[uuid.UUID] = None
    assignee_name: Optional[str] = None
    session_id: Optional[uuid.UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    comments: List[CommentResponse] = []

    model_config = {
        "from_attributes": True
    }


class TicketStatsResponse(BaseModel):
    """Ticket statistics for dashboard"""
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    tickets_by_category: dict[str, int]
    tickets_by_priority: dict[str, int]
    avg_resolution_time_hours: Optional[float] = None
