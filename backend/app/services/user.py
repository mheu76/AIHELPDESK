"""
User management service for admin operations
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import math
from uuid import UUID

from app.models.user import User, UserRole
from app.models.ticket import Ticket
from app.models.chat import ChatSession
from app.schemas.admin import (
    UserListResponse,
    UserListItem,
    UserDetailResponse,
    UserUpdateRequest
)
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_users(
        self,
        current_user: User,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 50
    ) -> UserListResponse:
        """
        Get paginated list of users with filters.

        Args:
            current_user: Current authenticated user
            role: Filter by role
            is_active: Filter by active status
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Paginated user list

        Raises:
            ForbiddenError: If user is not admin
        """
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only admins can list users")

        # Build query
        query = select(User)
        count_query = select(func.count(User.id))

        # Apply filters
        filters = []
        if role is not None:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)

        if filters:
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Calculate pagination
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        offset = (page - 1) * page_size

        # Get paginated results
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        result = await self.db.execute(query)
        users = result.scalars().all()

        items = [
            UserListItem(
                id=user.id,
                employee_id=user.employee_id,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                department=user.department,
                is_active=user.is_active,
                created_at=user.created_at
            )
            for user in users
        ]

        return UserListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    async def get_user(
        self,
        current_user: User,
        user_id: UUID
    ) -> UserDetailResponse:
        """
        Get detailed user information.

        Args:
            current_user: Current authenticated user
            user_id: Target user ID

        Returns:
            Detailed user info with statistics

        Raises:
            ForbiddenError: If user is not admin
            NotFoundError: If user not found
        """
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only admins can view user details")

        # Get user
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # Get ticket count
        ticket_count_query = select(func.count(Ticket.id)).where(
            Ticket.requester_id == user_id
        )
        ticket_count_result = await self.db.execute(ticket_count_query)
        ticket_count = ticket_count_result.scalar_one()

        # Get session count
        session_count_query = select(func.count(ChatSession.id)).where(
            ChatSession.user_id == user_id
        )
        session_count_result = await self.db.execute(session_count_query)
        session_count = session_count_result.scalar_one()

        return UserDetailResponse(
            id=user.id,
            employee_id=user.employee_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            department=user.department,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            ticket_count=ticket_count,
            session_count=session_count
        )

    async def update_user(
        self,
        current_user: User,
        user_id: UUID,
        update_data: UserUpdateRequest
    ) -> UserDetailResponse:
        """
        Update user information.

        Args:
            current_user: Current authenticated user
            user_id: Target user ID
            update_data: Update fields

        Returns:
            Updated user details

        Raises:
            ForbiddenError: If user is not admin
            NotFoundError: If user not found
        """
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenError("Only admins can update users")

        # Get user
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(f"User {user_id} not found")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        logger.info(f"Admin {current_user.employee_id} updated user {user.employee_id}")

        # Return detailed response
        return await self.get_user(current_user, user_id)
