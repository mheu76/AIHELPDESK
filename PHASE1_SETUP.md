# Phase 1 Setup Guide

Last updated: `2026-04-02`

This document records the current backend setup for the IT AI Helpdesk project.

## Scope

Phase 1 is the backend foundation:

- FastAPI API
- SQLAlchemy async models and sessions
- Alembic migrations
- JWT authentication
- Chat, KB, tickets, and admin modules
- Persistent `system_settings`

## Prerequisites

- Python 3.12+
- PostgreSQL 15+ for local Docker or production-like runs
- Optional LLM API key:
  - `ANTHROPIC_API_KEY`
  - `OPENAI_API_KEY`

SQLite remains valid for tests and lightweight local development.

## Local Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Required Environment

Minimum backend values:

```env
DATABASE_URL=postgresql+asyncpg://helpdesk:password@localhost:5432/helpdesk
JWT_SECRET_KEY=change-me
```

At least one LLM provider key is needed for real chat responses:

```env
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
```

Useful optional values:

```env
LLM_PROVIDER=claude
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=helpdesk-kb
```

## What Phase 1 Delivers

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`
- `POST /api/v1/chat`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}`
- `PATCH /api/v1/chat/sessions/{session_id}/resolve`
- `POST /api/v1/kb/upload`
- `GET /api/v1/kb/documents`
- `GET /api/v1/kb/documents/{doc_id}`
- `DELETE /api/v1/kb/documents/{doc_id}`
- `POST /api/v1/kb/search`
- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- `PATCH /api/v1/tickets/{ticket_id}`
- `POST /api/v1/tickets/{ticket_id}/comments`
- `GET /api/v1/tickets/stats/overview`
- `GET /api/v1/admin/dashboard`
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{user_id}`
- `PATCH /api/v1/admin/users/{user_id}`
- `GET /api/v1/admin/settings`
- `PATCH /api/v1/admin/settings`

## Validation

Run:

```bash
cd backend
pytest
```

Verified result on `2026-04-02`:

- `141 passed`

## Current Gaps

- Password hashing still uses a temporary SHA-256 implementation and must be replaced before production use
- Chat is request/response only; SSE streaming is not implemented
- Existing PostgreSQL migration validation still needs explicit smoke coverage
