# Docker Development Setup

This repository now includes a development Docker setup for:

- `db`: PostgreSQL 15
- `backend`: FastAPI with Alembic migrations
- `frontend`: Next.js 14 dev server

## Start

From the repository root:

```bash
docker compose up --build
```

The services will be available at:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- API docs: `http://localhost:8080/docs`
- PostgreSQL: `localhost:5432`

## What happens on backend startup

The backend container runs:

```bash
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

This keeps schema setup aligned with PostgreSQL instead of relying on SQLite-style auto table creation.

## Environment

Backend Docker env values live in:

- `backend/.env.docker`

Update at least these values before using real integrations:

- `ANTHROPIC_API_KEY`
- `JWT_SECRET_KEY`

## Useful commands

```bash
docker compose up --build
docker compose down
docker compose down -v
docker compose logs -f backend
docker compose exec backend alembic upgrade head
docker compose exec backend pytest
```

`docker compose down -v` removes the PostgreSQL volume and resets local DB state.
