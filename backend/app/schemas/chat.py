"""
Pydantic schemas for chat endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

from app.models.chat import MessageRole


class ChatRequest(BaseModel):
    """Chat request schema"""
    message: str = Field(..., min_length=1, max_length=5000, description="User message")
    session_id: Optional[uuid.UUID] = Field(None, description="Existing session ID (for continuing conversation)")


class MessageResponse(BaseModel):
    """Individual chat message response"""
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    token_count: Optional[int] = None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class ChatResponse(BaseModel):
    """Chat response schema"""
    session_id: uuid.UUID = Field(..., description="Chat session ID")
    message: MessageResponse = Field(..., description="AI assistant's response")
    is_resolved: bool = Field(..., description="Whether the issue is resolved")


class SessionResponse(BaseModel):
    """Chat session response"""
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    is_resolved: bool
    ticket_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None

    model_config = {
        "from_attributes": True
    }


class SessionListResponse(BaseModel):
    """List of chat sessions"""
    sessions: List[SessionResponse]
    total: int


class SessionDetailResponse(BaseModel):
    """Detailed session with messages"""
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    is_resolved: bool
    ticket_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    model_config = {
        "from_attributes": True
    }


class CreateTicketRequest(BaseModel):
    """Request to create a ticket from chat session"""
    session_id: uuid.UUID = Field(..., description="Chat session ID")
    additional_notes: Optional[str] = Field(None, max_length=2000, description="Additional notes for the ticket")
