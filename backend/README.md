# IT Helpdesk Backend

FastAPI-based backend service for IT AI Helpdesk system.

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set your values
# IMPORTANT: Set ANTHROPIC_API_KEY and JWT_SECRET_KEY
```

Generate a secure JWT secret key:
```bash
openssl rand -hex 32
```

### 3. Database Setup

The harness includes automatic database initialization in development mode.
For production, use Alembic migrations.

## Running the Application

### Development Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The API will be available at:
- API: http://localhost:8080
- Interactive Docs: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- Health Check: http://localhost:8080/health

## Running Tests

```bash
cd backend
pytest
```

Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

Run specific test types:
```bash
# Integration tests only
pytest -m integration

# Unit tests only
pytest -m unit
```

## Project Structure

```
backend/
├── app/
│   ├── core/              # Core infrastructure (harness)
│   │   ├── config.py      # Settings management
│   │   ├── logging.py     # Logging setup
│   │   ├── context.py     # Request context
│   │   ├── exceptions.py  # Custom exceptions
│   │   └── error_handlers.py
│   ├── middleware/        # Request/response middleware
│   │   ├── request_id.py
│   │   └── error_middleware.py
│   ├── db/                # Database session management
│   │   ├── base.py
│   │   └── session.py
│   ├── api/v1/            # API endpoints
│   │   └── deps.py        # FastAPI dependencies
│   ├── models/            # SQLAlchemy models (to be added)
│   ├── schemas/           # Pydantic schemas (to be added)
│   ├── services/          # Business logic (to be added)
│   └── main.py            # Application entry point
├── tests/
│   ├── conftest.py        # Test fixtures
│   └── integration/       # Integration tests
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Harness Features

The backend harness provides:

✅ **Configuration Management** - Type-safe settings with Pydantic
✅ **Logging System** - Human-readable logs with request context
✅ **Request ID Tracking** - Unique ID for each request in logs and headers
✅ **Error Handling** - Consistent error responses with error codes
✅ **Database Session Management** - Async SQLAlchemy with connection pooling
✅ **Middleware Stack** - Request ID injection, error context collection, CORS
✅ **Test Infrastructure** - Pytest fixtures with SQLite in-memory database

## Verification

### 1. Configuration Test

```python
python -c "from app.core.config import settings; print(settings.model_dump())"
```

### 2. Logging Test

```python
from app.core.logging import setup_logging, get_logger
from app.core.context import set_request_id, set_user_id

setup_logging()
logger = get_logger(__name__)

set_request_id("test-1234")
set_user_id("user-5678")

logger.info("Test log message")
```

### 3. Health Check Test

```bash
# Start server
uvicorn app.main:app --reload

# Test health endpoint
curl http://localhost:8080/health

# Test with request ID
curl -H "X-Request-ID: test-123" http://localhost:8080/health
```

## Next Steps

After the harness is complete, the next implementation steps are:

1. **Models** - Create SQLAlchemy models (User, ChatSession, Ticket, etc.)
2. **Security** - Implement JWT authentication and password hashing
3. **LLM Layer** - Create LLM abstraction layer (Claude, OpenAI)
4. **Services** - Implement business logic (Auth, Chat, Tickets)
5. **API Endpoints** - Create REST API routes
6. **Alembic Migrations** - Setup database migrations

## Troubleshooting

### Import Errors

If you see import errors, make sure you're running from the backend directory:
```bash
cd backend
python -m app.main
```

### Database Connection Issues

Check your DATABASE_URL in .env file. For development, you can use SQLite:
```
DATABASE_URL=sqlite+aiosqlite:///./helpdesk.db
```

### Missing Dependencies

Install all dependencies including optional ones:
```bash
pip install -r requirements.txt
```
