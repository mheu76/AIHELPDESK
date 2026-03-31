"""
FastAPI application initialization.
Configures all harness components and middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import HelpDeskException
from app.core.error_handlers import (
    helpdesk_exception_handler,
    validation_exception_handler,
    database_exception_handler,
    generic_exception_handler,
)
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.error_middleware import ErrorContextMiddleware
from app.db.session import init_db, close_db

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    Runs on startup and shutdown.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    if settings.is_development:
        # Initialize DB in development (use Alembic in production)
        await init_db()

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ============================================================
# MIDDLEWARE (Order matters - executed in reverse order)
# ============================================================

# 1. CORS (outermost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# 2. Error context collection
app.add_middleware(ErrorContextMiddleware)

# 3. Request ID injection (innermost - runs first)
app.add_middleware(RequestIDMiddleware)

# ============================================================
# EXCEPTION HANDLERS
# ============================================================

app.add_exception_handler(HelpDeskException, helpdesk_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ============================================================
# ROUTES
# ============================================================

# Health check (no auth required)
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
    }


# Root redirect
@app.get("/")
async def root():
    return {"message": "IT Helpdesk API", "docs": "/docs"}


# API v1 routes will be added later
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
