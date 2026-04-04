# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Last updated: `2026-04-04`

## Project Summary

IT AI Helpdesk is an internal support system that provides AI-powered first-line IT support.

**Tech Stack:**
- Backend: FastAPI + SQLAlchemy (async) + Alembic
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind CSS
- Database: PostgreSQL (primary), SQLite (dev/test)
- Optional: ChromaDB for vector search (fallback exists)
- LLM: Anthropic Claude or OpenAI (runtime switchable)

**Primary Domains:**
- Auth (JWT-based, employee/IT staff/admin roles)
- Chat (AI conversation with RAG)
- Knowledge Base (document upload, search)
- Tickets (created from chat sessions)
- Admin (dashboard, user management, system settings)

## Development Commands

### Backend

```bash
cd backend

# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Test
pytest                                      # All tests (141 passing as of 2026-04-02)
pytest -m integration                       # Integration tests only
pytest tests/unit/test_api_ticket.py        # Single test file
pytest -v -s tests/unit/                    # Unit tests with output

# Database
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

### Frontend

```bash
cd frontend

# Setup
npm install

# Run
npm run dev                                 # Development server on port 3000

# Verify
npm run lint                                # Type-check (passes as of 2026-04-02)
npm run type-check                          # Same as lint
npm run build                               # Production build
```

### Docker

```bash
docker compose up --build                   # Full stack

# Services:
# - Frontend: http://localhost:3000
# - Backend: http://localhost:8080
# - Swagger: http://localhost:8080/docs
# - PostgreSQL: localhost:5432
```

## Architecture Essentials

### LLM Abstraction Layer (CRITICAL)

**Never make direct Anthropic or OpenAI API calls.** All LLM interaction MUST go through `backend/app/core/llm/`:

- `base.py` - Abstract interface (`LLMBase`)
- `claude.py` - Anthropic implementation
- `openai.py` - OpenAI implementation
- `factory.py` - Runtime provider selection

**Why:** System uses runtime settings to switch LLM providers without restart. Direct API calls bypass this mechanism and break runtime configuration.

**How to use:**
```python
from app.core.llm.factory import create_llm_client

# In service layer
llm = await create_llm_client(session)  # Reads runtime settings from DB
response = await llm.chat_completion(messages, temperature=0.7)
```

### Backend Structure

```
backend/app/
├── core/           # Config, logging, security, exceptions, LLM abstraction
├── db/             # SQLAlchemy session, base model
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic request/response schemas
├── services/       # Business logic (auth, chat, rag, ticket, admin, user, settings)
├── api/            # FastAPI routers
├── middleware/     # Request ID, CORS
└── utils/          # Document parsing, helpers
```

**Key patterns:**
- Services depend on `AsyncSession` (DB) and runtime settings
- API routers are thin - delegate to services
- All async (SQLAlchemy async, async LLM clients)
- Dependency injection via FastAPI `Depends`

### Frontend Structure

```
frontend/
├── app/            # Next.js App Router pages
│   ├── auth/
│   ├── chat/
│   ├── tickets/
│   ├── kb/
│   └── admin/
├── components/     # React components (AuthProvider, AuthGuard, etc.)
├── hooks/          # Custom React hooks (useAuth)
└── lib/            # API client utilities
```

**Key patterns:**
- App Router only (no Pages Router)
- `AuthProvider` wraps entire app for auth state
- `AuthGuard` protects routes requiring authentication
- API calls use `fetch` with `NEXT_PUBLIC_API_URL` from env

### Runtime Settings Pattern

System settings are persisted in the `system_settings` table and loaded at runtime:
- LLM provider selection (anthropic/openai)
- LLM model selection
- RAG enabled/disabled
- Temperature, max tokens

**Critical:** Services read settings from DB on each request to allow admin to change behavior without restart. This is an **in-memory override pattern**, not just static config.

### Database Patterns

- Async SQLAlchemy sessions throughout
- Alembic for migrations
- Ticket numbering uses PostgreSQL SEQUENCE for concurrent safety
- Unique constraint: one ticket per chat session
- Admin protection: cannot remove last active admin

## Known Limitations

**Security (CRITICAL):** `backend/app/core/security.py` uses temporary **SHA-256** password hashing. **Not production safe.** Must replace with bcrypt or argon2 before deployment.

**Other gaps:**
- SSE streaming chat not implemented (API exists, not wired to frontend)
- Several deprecation warnings (`datetime.utcnow`, `HTTP_422` constant)
- ChromaDB is optional - if unavailable, KB search falls back to DB text matching
- No frontend automated tests yet
- CI/CD not finalized

## Testing

Backend uses pytest with:
- `conftest.py` - Fixtures for test DB, client, auth tokens
- `tests/unit/` - Unit tests for APIs and services
- `tests/integration/` - Integration tests
- Markers: `@pytest.mark.integration`

Test DB is SQLite in-memory, isolated per test.

## Documentation

**Source of truth:** `docs/` directory
- `01_architecture.md` - System design
- `03_db_schema.md` - Database schema
- `04_api_spec.md` - API contracts
- `09_admin_manual.md` - Admin operations

**When changing behavior:** Update relevant docs in `docs/` along with code.

## Environment

**Backend** (see `backend/.env.example`):
```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/helpdesk
JWT_SECRET_KEY=<secret>
ANTHROPIC_API_KEY=<key>   # or OPENAI_API_KEY
LLM_PROVIDER=anthropic     # or openai (can override at runtime via admin)
LLM_MODEL=claude-3-5-sonnet-20241022
```

**Frontend:**
```
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## Working Principles

1. **LLM abstraction is mandatory** - Never bypass `app.core.llm`
2. **Docs drive behavior** - Update `docs/` when implementation changes
3. **ChromaDB is optional** - Code must handle fallback
4. **Runtime settings are dynamic** - Don't assume static config
5. **Async everywhere** - Use `async/await` for DB and LLM calls
6. **Type safety** - Pydantic schemas for all API boundaries, TypeScript strict mode

## Current State (2026-04-02)

✅ All 4 sprints complete
✅ Backend: 141 tests passing
✅ Frontend: Type-check passing
✅ Runtime settings persistence working
✅ Ticket numbering safe for concurrency
✅ Admin account protection in place

🚧 Password hashing is temporary (SHA-256)
🚧 Chat streaming exists but not wired to frontend
🚧 Deprecation warnings need addressing

See `NEXT_STEPS.md` for prioritized follow-up work.
