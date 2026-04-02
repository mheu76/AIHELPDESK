# 01. Architecture

## Overview

The system is composed of:

1. `frontend`: Next.js 14 App Router application
2. `backend`: FastAPI application
3. `db`: PostgreSQL for Docker-based local development

Optional:

4. ChromaDB for vector search

If ChromaDB is unavailable, the backend falls back to database text matching for KB search.

## High-Level Flow

```text
Browser
  -> Frontend (Next.js, port 3000)
  -> Backend (FastAPI, port 8080)
  -> PostgreSQL (port 5432)
  -> ChromaDB (optional, port 8000)
```

## Backend Layers

### Core

- Pydantic settings
- Structured logging
- Request ID middleware
- Error handling middleware
- CORS configuration

### Domain

- Auth
- Chat
- Knowledge Base
- Tickets
- Admin

### Data

- SQLAlchemy async session
- Alembic migrations
- SQLite for dev/test
- PostgreSQL for Docker/local production-like use

## Auth Flow

1. User calls `/api/v1/auth/login`
2. Backend validates credentials
3. Backend returns access and refresh tokens
4. Frontend stores tokens in `localStorage`
5. Subsequent requests use `Authorization: Bearer <token>`

## Chat Flow

1. User sends a message
2. Backend creates or reuses a chat session
3. User message is stored in `chat_messages`
4. Backend loads runtime settings from `system_settings`
5. KB search runs only if `rag_enabled=true`
6. LLM generates a response using runtime settings
7. Assistant response is stored in `chat_messages`

## Ticket Flow

1. User creates a ticket from a chat session
2. Backend summarizes and categorizes the session with the LLM
3. Ticket is stored in `tickets`
4. Comments are stored in `ticket_comments`
5. IT staff and admins can update status, priority, category, and assignee

## Admin Flow

Admin-only capabilities:

- Dashboard statistics
- User list/detail/update
- Persistent system settings

System settings are stored in the `system_settings` table and used by runtime chat and LLM dependency resolution.

## Current Gaps

- SSE streaming chat not implemented
- Password hashing is not production safe yet
- No production deployment architecture is finalized
