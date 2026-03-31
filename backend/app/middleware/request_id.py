"""
Request ID middleware.
Generates unique ID for each request and injects into context.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

from app.core.context import generate_request_id, set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generates unique request ID and injects into:
    1. Request context (for logging)
    2. Response headers (X-Request-ID)
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or generate_request_id()

        # Set in context
        set_request_id(request_id)

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response
