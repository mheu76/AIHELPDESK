"""
Admin-related Pydantic schemas
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.models.user import UserRole


# Dashboard
class RecentActivity(BaseModel):
    """Recent activity item"""
    model_config = ConfigDict(from_attributes=True)

    type: str = Field(..., description="Activity type")
    user_id: UUID = Field(..., description="User who performed action")
    user_name: str = Field(..., description="User's full name")
    timestamp: datetime = Field(..., description="Activity timestamp")
    description: str = Field(..., description="Activity description")


class DashboardResponse(BaseModel):
    """Admin dashboard statistics"""
    model_config = ConfigDict(from_attributes=True)

    total_users: int = Field(..., description="Total registered users")
    active_users: int = Field(..., description="Active users")
    total_sessions: int = Field(..., description="Total chat sessions")
    total_tickets: int = Field(..., description="Total tickets")
    total_kb_documents: int = Field(..., description="Total KB documents")
    llm_provider: str = Field(..., description="Current LLM provider")
    recent_activities: List[RecentActivity] = Field(
        default_factory=list,
        description="Recent system activities"
    )


# User Management
class UserListItem(BaseModel):
    """User list item"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    is_active: bool
    created_at: datetime


class UserListResponse(BaseModel):
    """Paginated user list"""
    model_config = ConfigDict(from_attributes=True)

    items: List[UserListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDetailResponse(BaseModel):
    """Detailed user information"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    employee_id: str
    email: str
    full_name: str
    role: UserRole
    department: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    ticket_count: int = 0
    session_count: int = 0


class UserUpdateRequest(BaseModel):
    """User update request"""
    model_config = ConfigDict(from_attributes=True)

    role: Optional[UserRole] = Field(None, description="User role")
    department: Optional[str] = Field(None, description="Department name")
    is_active: Optional[bool] = Field(None, description="Active status")


# System Settings
class SystemSettingsResponse(BaseModel):
    """System settings"""
    model_config = ConfigDict(from_attributes=True)

    llm_provider: str = Field(..., description="Current LLM provider")
    llm_model: str = Field(..., description="LLM model name")
    llm_temperature: float = Field(..., description="Temperature setting")
    max_tokens: int = Field(..., description="Max tokens per response")
    rag_enabled: bool = Field(..., description="RAG feature enabled")
    rag_top_k: int = Field(..., description="Top K documents for RAG")


class SystemSettingsUpdateRequest(BaseModel):
    """System settings update"""
    model_config = ConfigDict(from_attributes=True)

    llm_provider: Optional[str] = Field(None, description="LLM provider (claude|openai)")
    llm_model: Optional[str] = Field(None, description="Model name")
    llm_temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=100000, description="Max tokens")
    rag_enabled: Optional[bool] = Field(None, description="Enable RAG")
    rag_top_k: Optional[int] = Field(None, ge=1, le=20, description="Top K")

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        """Validate LLM provider"""
        if v is not None and v not in ["claude", "openai"]:
            raise ValueError("llm_provider must be 'claude' or 'openai'")
        return v
