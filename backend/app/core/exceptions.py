"""
Custom exception hierarchy for domain-specific errors.
All exceptions include error_code for API consumers.
"""
from typing import Any, Optional


class HelpDeskException(Exception):
    """
    Base exception for all application errors.
    Provides consistent error_code and message structure.
    """
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 400,
        detail: Optional[dict[str, Any]] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to API error response format"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "detail": self.detail if self.detail else self.message
        }


# Authentication & Authorization Errors
class AuthenticationError(HelpDeskException):
    """User authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__("INVALID_CREDENTIALS", message, 401)

class UnauthorizedError(HelpDeskException):
    """User is not authorized for this action"""
    def __init__(self, message: str = "Not authorized", error_code: str = "UNAUTHORIZED"):
        super().__init__(error_code, message, 401)


class InvalidTokenError(HelpDeskException):
    """JWT token is invalid or expired"""
    def __init__(self, message: str = "인증 토큰이 유효하지 않습니다."):
        super().__init__("INVALID_TOKEN", message, 401)


class ForbiddenError(HelpDeskException):
    """User lacks required permissions"""
    def __init__(self, message: str = "권한이 없습니다."):
        super().__init__("FORBIDDEN", message, 403)


# Resource Errors
class NotFoundError(HelpDeskException):
    """Requested resource not found"""
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(error_code, message, 404)

class ConflictError(HelpDeskException):
    """Resource conflict (e.g. already exists)"""
    def __init__(self, message: str, error_code: str = "CONFLICT"):
        super().__init__(error_code, message, 409)


class ValidationError(HelpDeskException):
    """Request validation failed"""
    def __init__(self, message: str, errors: dict[str, Any]):
        super().__init__("VALIDATION_ERROR", message, 400, {"errors": errors})

class BadRequestError(HelpDeskException):
    """Bad Request"""
    def __init__(self, message: str, error_code: str = "BAD_REQUEST"):
        super().__init__(error_code, message, 400)


# External Service Errors
class LLMUnavailableError(HelpDeskException):
    """LLM API is unavailable or returned error"""
    def __init__(self, message: str = "LLM API 연결 오류", provider: Optional[str] = None):
        super().__init__("LLM_UNAVAILABLE", message, 503, {"provider": provider})


class RateLimitError(HelpDeskException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "요청 한도를 초과했습니다."):
        super().__init__("RATE_LIMIT", message, 429)


# Database Errors
class DatabaseError(HelpDeskException):
    """Database operation failed"""
    def __init__(self, message: str = "Database operation failed"):
        super().__init__("DATABASE_ERROR", message, 500)


# Internal Errors
class InternalError(HelpDeskException):
    """Unexpected internal error"""
    def __init__(self, message: str = "Internal server error"):
        super().__init__("INTERNAL_ERROR", message, 500)
