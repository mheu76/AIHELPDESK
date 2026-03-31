"""
Chat service for AI conversation management.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
import uuid

from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    MessageResponse,
    SessionResponse,
    SessionListResponse,
    SessionDetailResponse
)
from app.core.llm import LLMBase
from app.core.exceptions import NotFoundError, BadRequestError
from app.core.logging import get_logger
from app.core.config import settings
from app.services.rag import RAGService

logger = get_logger(__name__)


class ChatService:
    """Chat service for AI conversation management"""

    SYSTEM_PROMPT = """You are an IT helpdesk assistant for an internal company system.
Your role is to help employees with IT-related issues including:
- Account and password problems
- Hardware and device issues
- Network connectivity problems
- Software installation and troubleshooting
- Security questions
- System access issues

Guidelines:
1. Be helpful, professional, and concise
2. Ask clarifying questions when needed
3. Provide step-by-step instructions for technical issues
4. If you cannot resolve the issue, let the user know it will be escalated to IT staff
5. Use clear, non-technical language when possible

Always maintain a friendly and supportive tone."""

    SYSTEM_PROMPT_WITH_CONTEXT = """You are an IT helpdesk assistant for an internal company system.
Your role is to help employees with IT-related issues including:
- Account and password problems
- Hardware and device issues
- Network connectivity problems
- Software installation and troubleshooting
- Security questions
- System access issues

Guidelines:
1. Be helpful, professional, and concise
2. Ask clarifying questions when needed
3. Provide step-by-step instructions for technical issues
4. If you cannot resolve the issue, let the user know it will be escalated to IT staff
5. Use clear, non-technical language when possible
6. Use the knowledge base information below to provide accurate answers

Always maintain a friendly and supportive tone.

=== KNOWLEDGE BASE CONTEXT ===
{context}
=== END OF CONTEXT ===

Use the above information to help answer the user's question. If the context is relevant, reference it in your answer."""

    def __init__(self, db: AsyncSession, llm: LLMBase):
        self.db = db
        self.llm = llm
        self.rag_service = RAGService(db)

    async def send_message(
        self,
        user: User,
        request: ChatRequest
    ) -> ChatResponse:
        """
        Process user message and get AI response.

        Args:
            user: Current user
            request: Chat request with message and optional session_id

        Returns:
            Chat response with AI message

        Raises:
            NotFoundError: If session_id is provided but not found
        """
        # Get or create session
        if request.session_id:
            session = await self._get_session(request.session_id, user.id)
        else:
            session = await self._create_session(user.id)

        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER.value,
            content=request.message
        )
        self.db.add(user_message)
        await self.db.flush()

        # Search knowledge base for relevant context
        kb_results = await self.rag_service.search_knowledge_base(
            query=request.message,
            top_k=settings.RAG_TOP_K
        )

        # Get conversation history with RAG context
        messages = await self._get_conversation_history(session.id, kb_results)

        # Generate AI response
        try:
            ai_response = await self._generate_ai_response(messages)
            token_count = ai_response.get("usage", {}).get("completion_tokens")

            # Save AI message
            ai_message = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT.value,
                content=ai_response["content"],
                token_count=token_count
            )
            self.db.add(ai_message)

            # Generate title for new sessions (from first user message)
            if not session.title and len(messages) == 1:
                session.title = await self._generate_session_title(request.message)

            await self.db.commit()
            await self.db.refresh(ai_message)

            logger.info(f"Chat message processed for session {session.id}")

            return ChatResponse(
                session_id=session.id,
                message=MessageResponse.model_validate(ai_message),
                is_resolved=session.is_resolved
            )

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error generating AI response: {str(e)}")
            raise

    async def get_user_sessions(
        self,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> SessionListResponse:
        """
        Get user's chat sessions.

        Args:
            user_id: User ID
            limit: Number of sessions to return
            offset: Pagination offset

        Returns:
            List of chat sessions
        """
        # Get sessions with message count
        result = await self.db.execute(
            select(
                ChatSession,
                func.count(ChatMessage.id).label("message_count")
            )
            .outerjoin(ChatMessage)
            .where(ChatSession.user_id == user_id)
            .group_by(ChatSession.id)
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
            .offset(offset)
        )
        rows = result.all()

        # Get total count
        count_result = await self.db.execute(
            select(func.count(ChatSession.id))
            .where(ChatSession.user_id == user_id)
        )
        total = count_result.scalar_one()

        sessions = []
        for session, message_count in rows:
            session_data = SessionResponse.model_validate(session)
            session_data.message_count = message_count
            sessions.append(session_data)

        return SessionListResponse(sessions=sessions, total=total)

    async def get_session_detail(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> SessionDetailResponse:
        """
        Get detailed session with all messages.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)

        Returns:
            Session with messages

        Raises:
            NotFoundError: If session not found or unauthorized
        """
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError(
                message="Chat session not found",
                error_code="SESSION_NOT_FOUND"
            )

        return SessionDetailResponse.model_validate(session)

    async def mark_session_resolved(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        is_resolved: bool
    ) -> SessionResponse:
        """
        Mark a session as resolved or unresolved.

        Args:
            session_id: Session ID
            user_id: User ID (for authorization)
            is_resolved: Resolution status

        Returns:
            Updated session

        Raises:
            NotFoundError: If session not found or unauthorized
        """
        session = await self._get_session(session_id, user_id)
        session.is_resolved = is_resolved
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(f"Session {session_id} marked as resolved={is_resolved}")
        return SessionResponse.model_validate(session)

    # Private helper methods

    async def _get_session(
        self,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> ChatSession:
        """Get session by ID and verify ownership"""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.id == session_id, ChatSession.user_id == user_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise NotFoundError(
                message="Chat session not found",
                error_code="SESSION_NOT_FOUND"
            )

        return session

    async def _create_session(self, user_id: uuid.UUID) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(user_id=user_id)
        self.db.add(session)
        await self.db.flush()
        logger.info(f"Created new chat session {session.id} for user {user_id}")
        return session

    async def _get_conversation_history(
        self,
        session_id: uuid.UUID,
        kb_results: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, str]]:
        """
        Get conversation history formatted for LLM.

        Args:
            session_id: Session ID
            kb_results: Optional knowledge base search results to include as context

        Returns:
            List of message dicts with role and content
        """
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .limit(settings.MAX_CONVERSATION_TURNS * 2)  # user + assistant pairs
        )
        messages = result.scalars().all()

        # Format KB results into context string
        if kb_results:
            context_parts = []
            for idx, result in enumerate(kb_results, 1):
                context_parts.append(
                    f"[{idx}] {result['content']}\n"
                    f"Source: {result['metadata'].get('title', 'Unknown')}"
                )
            context_str = "\n\n".join(context_parts)
            system_prompt = self.SYSTEM_PROMPT_WITH_CONTEXT.format(context=context_str)
        else:
            system_prompt = self.SYSTEM_PROMPT

        # Format for LLM
        history = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })

        return history

    async def _generate_ai_response(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate AI response using LLM.

        Args:
            messages: Conversation history

        Returns:
            AI response with content and usage info
        """
        response = await self.llm.chat_completion(
            messages=messages,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS
        )
        return response

    async def _generate_session_title(self, first_message: str) -> str:
        """
        Generate a session title from the first user message.

        Args:
            first_message: First user message

        Returns:
            Generated title (max 50 chars)
        """
        # Simple implementation: use first 50 chars of message
        # Can be enhanced with LLM to generate better titles
        title = first_message[:50]
        if len(first_message) > 50:
            title += "..."
        return title
