"""
Chat endpoints for AI conversation.
"""
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import json

from app.api.v1.deps import get_db, get_llm
from app.api.v1.auth import get_current_user
from app.services.chat import ChatService
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    SessionListResponse,
    SessionDetailResponse,
    SessionResponse,
    SessionResolveRequest
)
from app.models.user import User
from app.core.llm import LLMBase

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a chat message"
)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Send a message to the AI assistant.

    - **message**: User's message (1-5000 characters)
    - **session_id**: Optional - existing session ID to continue conversation

    If session_id is not provided, a new session will be created.
    """
    chat_service = ChatService(db, llm)
    return await chat_service.send_message(current_user, request)


@router.post(
    "/stream",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Stream a chat message"
)
async def send_streaming_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Send a message to the AI assistant with streaming response.

    Returns NDJSON (newline-delimited JSON) chunks:
    - `{"type": "token", "content": "text"}` - Content chunk
    - `{"type": "done", "session_id": "...", "message_id": "..."}` - Completion
    - `{"type": "error", "message": "...", "code": "..."}` - Error

    - **message**: User's message (1-5000 characters)
    - **session_id**: Optional - existing session ID to continue conversation

    If session_id is not provided, a new session will be created.
    """
    chat_service = ChatService(db, llm)

    async def generate():
        try:
            async for chunk in chat_service.send_streaming_message(
                current_user, request
            ):
                yield chunk + "\n"
        except Exception as e:
            error_chunk = json.dumps({
                "type": "error",
                "message": str(e),
                "code": "ENDPOINT_ERROR"
            })
            yield error_chunk + "\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8"
    )


@router.get(
    "/sessions",
    response_model=SessionListResponse,
    summary="Get user's chat sessions"
)
async def get_sessions(
    limit: int = Query(50, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Get list of user's chat sessions.

    Returns sessions ordered by most recent first.
    """
    chat_service = ChatService(db, llm)
    return await chat_service.get_user_sessions(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session detail with messages"
)
async def get_session_detail(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Get detailed session information including all messages.

    Only returns sessions owned by the current user.
    """
    chat_service = ChatService(db, llm)
    return await chat_service.get_session_detail(
        session_id=session_id,
        user_id=current_user.id
    )


@router.patch(
    "/sessions/{session_id}/resolve",
    response_model=SessionResponse,
    summary="Mark session as resolved/unresolved"
)
async def update_session_resolution(
    session_id: uuid.UUID,
    request: SessionResolveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Mark a chat session as resolved or unresolved.

    - **session_id**: Session ID
    - **is_resolved**: True to mark as resolved, False to mark as unresolved
    """
    chat_service = ChatService(db, llm)
    return await chat_service.mark_session_resolved(
        session_id=session_id,
        user_id=current_user.id,
        is_resolved=request.is_resolved
    )
