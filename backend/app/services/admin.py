"""
Admin dashboard service for system-wide statistics and monitoring
"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta

from app.models.user import User, UserRole
from app.models.chat import ChatSession
from app.models.ticket import Ticket
from app.models.kb_document import KBDocument
from app.schemas.admin import DashboardResponse, RecentActivity
from app.core.exceptions import ForbiddenError
from app.core.logging import get_logger
from app.services.settings import SettingsService

logger = get_logger(__name__)


class AdminService:
    """Service for admin dashboard operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self, current_user: User) -> DashboardResponse:
        """
        Get admin dashboard statistics.

        Args:
            current_user: Current authenticated user

        Returns:
            Dashboard statistics

        Raises:
            ForbiddenError: If user is not admin
        """
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only admins can view dashboard")

        # Total users
        total_users_query = select(func.count(User.id))
        total_users_result = await self.db.execute(total_users_query)
        total_users = total_users_result.scalar_one()

        # Active users
        active_users_query = select(func.count(User.id)).where(User.is_active == True)
        active_users_result = await self.db.execute(active_users_query)
        active_users = active_users_result.scalar_one()

        # Total sessions
        total_sessions_query = select(func.count(ChatSession.id))
        total_sessions_result = await self.db.execute(total_sessions_query)
        total_sessions = total_sessions_result.scalar_one()

        # Total tickets
        total_tickets_query = select(func.count(Ticket.id))
        total_tickets_result = await self.db.execute(total_tickets_query)
        total_tickets = total_tickets_result.scalar_one()

        # Total KB documents
        total_kb_query = select(func.count(KBDocument.id)).where(
            KBDocument.is_active == True
        )
        total_kb_result = await self.db.execute(total_kb_query)
        total_kb_documents = total_kb_result.scalar_one()

        # Current LLM provider
        runtime_settings = await SettingsService(self.db).get_runtime_settings()
        llm_provider = runtime_settings.llm_provider

        # Recent activities
        recent_activities = await self._get_recent_activities()

        return DashboardResponse(
            total_users=total_users,
            active_users=active_users,
            total_sessions=total_sessions,
            total_tickets=total_tickets,
            total_kb_documents=total_kb_documents,
            llm_provider=llm_provider,
            recent_activities=recent_activities
        )

    async def _get_recent_activities(self, limit: int = 10) -> List[RecentActivity]:
        """
        Get recent system activities.

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of recent activities
        """
        activities = []

        # Get recent tickets
        ticket_query = (
            select(Ticket)
            .options()
            .order_by(desc(Ticket.created_at))
            .limit(limit)
        )
        ticket_result = await self.db.execute(ticket_query)
        recent_tickets = ticket_result.scalars().all()

        for ticket in recent_tickets:
            # Get requester info
            user_query = select(User).where(User.id == ticket.requester_id)
            user_result = await self.db.execute(user_query)
            user = user_result.scalar_one_or_none()

            if user:
                activities.append(
                    RecentActivity(
                        type="ticket_created",
                        user_id=user.id,
                        user_name=user.full_name,
                        timestamp=ticket.created_at,
                        description=f"Ticket #{ticket.ticket_number} created: {ticket.title[:50]}"
                    )
                )

        # Sort by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)

        return activities[:limit]
