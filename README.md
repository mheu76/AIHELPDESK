# IT AI Helpdesk

Internal IT helpdesk system built with `FastAPI` and `Next.js`.

## Current Status

As of `2026-04-02`, the repository is in a working state with:

- Backend API running on FastAPI
- Frontend running on Next.js 14 App Router
- JWT-based auth with employee, IT staff, and admin roles
- Chat, knowledge base, ticket, and admin endpoints implemented
- Persistent `system_settings` storage in the database
- Backend test suite passing: `141 passed`
- Frontend type-check passing

Important remaining work:

- Password hashing is still using a temporary SHA-256 implementation and is not production safe
- SSE chat streaming is not implemented yet
- ChromaDB is optional; fallback KB search uses database text matching
- CI/CD and production deployment workflows are not finalized

## Project Structure

```text
.
|- backend/                FastAPI, SQLAlchemy, Alembic, pytest
|- frontend/               Next.js 14, TypeScript, Tailwind CSS
|- docs/                   Architecture, features, DB, API, UI, operations
|- docker-compose.yml      Local development stack
|- DOCKER_DEV.md           Docker usage notes
|- NEXT_STEPS.md           Tracked follow-up work
```

## Quick Start

### Docker

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`
- PostgreSQL: `localhost:5432`

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

Backend requires:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`

Common optional settings:

- `LLM_PROVIDER`
- `LLM_MODEL`
- `FRONTEND_URL`
- `ALLOWED_ORIGINS`
- `CHROMA_HOST`
- `CHROMA_PORT`

See:

- [backend/.env.example](/D:/DEV/AIhelpdesk/backend/.env.example)
- [backend/.env.docker](/D:/DEV/AIhelpdesk/backend/.env.docker)

Frontend requires:

- `NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1`

## Implemented Areas

- Auth: register, login, refresh, current user
- Chat: create sessions, continue sessions, list sessions, resolve sessions
- Knowledge Base: upload, list, detail, delete, search
- Tickets: create from chat, list, detail, update, comment, statistics
- Admin: dashboard, user management, persistent system settings

## Verification

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run lint
```

## Documentation

- [docs/01_architecture.md](/D:/DEV/AIhelpdesk/docs/01_architecture.md)
- [docs/02_features.md](/D:/DEV/AIhelpdesk/docs/02_features.md)
- [docs/03_db_schema.md](/D:/DEV/AIhelpdesk/docs/03_db_schema.md)
- [docs/04_api_spec.md](/D:/DEV/AIhelpdesk/docs/04_api_spec.md)
- [docs/05_ui_spec.md](/D:/DEV/AIhelpdesk/docs/05_ui_spec.md)
- [docs/06_operating_principles.md](/D:/DEV/AIhelpdesk/docs/06_operating_principles.md)
- [docs/07.HYBRID RAG SETTING.MD](/D:/DEV/AIhelpdesk/docs/07.HYBRID%20RAG%20SETTING.MD)
- [docs/09_admin_manual.md](/D:/DEV/AIhelpdesk/docs/09_admin_manual.md)
- [NEXT_STEPS.md](/D:/DEV/AIhelpdesk/NEXT_STEPS.md)
