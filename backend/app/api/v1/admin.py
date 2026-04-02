"""
Admin API endpoints for user management, dashboard, and system settings
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.api.v1.deps import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.schemas.admin import (
    DashboardResponse,
    UserListResponse,
    UserDetailResponse,
    UserUpdateRequest,
    SystemSettingsResponse,
    SystemSettingsUpdateRequest
)
from app.services.admin import AdminService
from app.services.user import UserService
from app.services.settings import SettingsService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get admin dashboard statistics"
)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide statistics for admin dashboard.

    Requires admin role.
    """
    service = AdminService(db)
    return await service.get_dashboard_stats(current_user)


@router.get(
    "/users",
    response_model=UserListResponse,
    summary="List all users"
)
async def list_users(
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of users with optional filters.

    Requires admin role.
    """
    service = UserService(db)
    return await service.get_users(
        current_user=current_user,
        role=role,
        is_active=is_active,
        page=page,
        page_size=page_size
    )


@router.get(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    summary="Get user details"
)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific user.

    Requires admin role.
    """
    service = UserService(db)
    return await service.get_user(current_user, user_id)


@router.patch(
    "/users/{user_id}",
    response_model=UserDetailResponse,
    summary="Update user"
)
async def update_user(
    user_id: UUID,
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user information (role, department, active status).

    Requires admin role.
    """
    service = UserService(db)
    return await service.update_user(current_user, user_id, update_data)


@router.get(
    "/settings",
    response_model=SystemSettingsResponse,
    summary="Get system settings"
)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current system settings including LLM configuration.

    Requires admin role.
    """
    service = SettingsService(db)
    return await service.get_settings(current_user)


@router.patch(
    "/settings",
    response_model=SystemSettingsResponse,
    summary="Update system settings"
)
async def update_settings(
    update_data: SystemSettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update system settings. Changes apply immediately.

    Warning: Changing llm_provider will affect all subsequent chat requests.

    Requires admin role.
    """
    service = SettingsService(db)
    return await service.update_settings(current_user, update_data)
