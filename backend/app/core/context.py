"""
Request context management using contextvars.
Allows request-scoped data (request_id, user_id) to be accessed
throughout the request lifecycle without explicit passing.
"""
from contextvars import ContextVar
from typing import Optional
import uuid


# Context variables (thread-safe for async)
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
session_id_var: ContextVar[Optional[str]] = ContextVar("session_id", default=None)


def generate_request_id() -> str:
    """Generate unique request ID"""
    return str(uuid.uuid4())


def get_request_id() -> str:
    """Get current request ID"""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set request ID for current context"""
    request_id_var.set(request_id)


def get_user_id() -> Optional[str]:
    """Get current user ID (if authenticated)"""
    return user_id_var.get()


def set_user_id(user_id: Optional[str]) -> None:
    """Set user ID for current context"""
    user_id_var.set(user_id)


def get_session_id() -> Optional[str]:
    """Get current chat session ID"""
    return session_id_var.get()


def set_session_id(session_id: Optional[str]) -> None:
    """Set session ID for current context"""
    session_id_var.set(session_id)


def get_log_context() -> dict:
    """Get all context for logging"""
    return {
        "request_id": get_request_id(),
        "user_id": get_user_id(),
        "session_id": get_session_id(),
    }
