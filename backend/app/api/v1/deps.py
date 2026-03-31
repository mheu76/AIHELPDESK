"""
FastAPI dependencies for request handling.
Provides database sessions, current user, etc.
"""
from typing import AsyncGenerator, Optional
from fastapi import Depends
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

# Security scheme
security = HTTPBearer()

# Note: get_current_user and other auth dependencies will be implemented
# after we create the User model and security module in the next phase
