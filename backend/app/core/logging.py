"""
Logging configuration with request context injection.
Provides human-readable logs with automatic context (request_id, user_id).
"""
import logging
import sys
from typing import Any
from .config import settings
from .context import get_log_context


class ContextualFormatter(logging.Formatter):
    """
    Custom formatter that injects request context into log messages.
    Format: [LEVEL] [request_id] [user_id] module.function - message
    """

    def format(self, record: logging.LogRecord) -> str:
        # Get context
        context = get_log_context()
        request_id = context.get("request_id", "no-request")
        user_id = context.get("user_id", "anonymous")

        # Add context to record
        record.request_id = request_id[:8]  # Short ID for readability
        record.user_id = user_id or "anonymous"

        return super().format(record)


def setup_logging() -> None:
    """
    Setup application logging.
    - Human-readable format with context
    - Color-coded levels (if terminal supports)
    - Async-safe
    """

    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL)

    # Create formatter
    if settings.LOG_FORMAT == "human":
        log_format = (
            "%(asctime)s | %(levelname)-8s | "
            "%(request_id)s | %(user_id)-12s | "
            "%(name)s.%(funcName)s - %(message)s"
        )
    else:  # JSON format for production (future)
        log_format = "%(message)s"  # Will be JSON serialized

    formatter = ContextualFormatter(
        fmt=log_format,
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Setup handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.INFO)

    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized | Level: {settings.LOG_LEVEL} | "
        f"Format: {settings.LOG_FORMAT} | Env: {settings.ENVIRONMENT}"
    )


# Helper to get logger with context
def get_logger(name: str) -> logging.Logger:
    """Get logger for a module"""
    return logging.getLogger(name)
