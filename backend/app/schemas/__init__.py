"""
Pydantic schemas for request/response validation.
"""
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    ChangePasswordRequest
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
    SessionResponse,
    SessionListResponse,
    SessionDetailResponse,
    CreateTicketRequest
)
from app.schemas.kb import (
    KBDocumentUploadResponse,
    KBDocumentResponse,
    KBDocumentListResponse,
    KBSearchRequest,
    KBSearchResult,
    KBSearchResponse
)
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

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "UserResponse",
    "ChangePasswordRequest",
    "ChatRequest",
    "ChatResponse",
    "MessageResponse",
    "SessionResponse",
    "SessionListResponse",
    "SessionDetailResponse",
    "CreateTicketRequest",
    "KBDocumentUploadResponse",
    "KBDocumentResponse",
    "KBDocumentListResponse",
    "KBSearchRequest",
    "KBSearchResult",
    "KBSearchResponse",
    "TicketCreateRequest",
    "TicketUpdateRequest",
    "TicketResponse",
    "TicketListResponse",
    "TicketDetailResponse",
    "CommentCreateRequest",
    "CommentResponse",
    "TicketStatsResponse",
]
