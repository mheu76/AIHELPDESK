"""
Middleware to collect error context automatically.
Captures request details when errors occur.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
from typing import Callable

from app.core.context import get_log_context

logger = logging.getLogger(__name__)


class ErrorContextMiddleware(BaseHTTPMiddleware):
    """
    Captures error context (timing, path, method) when errors occur.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)

            # Log slow requests
            duration = time.time() - start_time
            if duration > 5.0:  # 5 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {duration:.2f}s",
                    extra={
                        **get_log_context(),
                        "duration": duration,
                        "method": request.method,
                        "path": request.url.path
                    }
                )

            return response

        except Exception as exc:
            duration = time.time() - start_time

            # Log error with full context
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    **get_log_context(),
                    "duration": duration,
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else None,
                }
            )

            # Re-raise for exception handlers
            raise
