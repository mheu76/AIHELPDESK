"""
FastAPI exception handlers.
Catches exceptions and converts to consistent API responses.
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging
from typing import Any

from .exceptions import HelpDeskException
from .context import get_log_context

logger = logging.getLogger(__name__)


async def helpdesk_exception_handler(
    request: Request,
    exc: HelpDeskException
) -> JSONResponse:
    """
    Handle custom HelpDeskException.
    Logs error with full context, returns client-safe response.
    """
    context = get_log_context()

    # Log with context
    logger.error(
        f"HelpDeskException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "detail": exc.detail,
            **context
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    Transforms into our standard error format.
    """
    context = get_log_context()

    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={**context, "errors": exc.errors()}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "요청 데이터가 유효하지 않습니다.",
            "detail": {"errors": exc.errors()}
        }
    )


async def database_exception_handler(
    request: Request,
    exc: SQLAlchemyError
) -> JSONResponse:
    """
    Handle SQLAlchemy database errors.
    Logs full error, returns generic message to client.
    """
    context = get_log_context()

    logger.error(
        f"Database error: {str(exc)}",
        exc_info=True,
        extra=context
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "DATABASE_ERROR",
            "message": "데이터베이스 오류가 발생했습니다.",
            "detail": None
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Catch-all for unexpected exceptions.
    Logs full stack trace, returns generic error.
    """
    context = get_log_context()

    logger.critical(
        f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
        exc_info=True,
        extra=context
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "서버 오류가 발생했습니다.",
            "detail": None
        }
    )
