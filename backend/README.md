# Backend

FastAPI backend for the IT AI Helpdesk project.

## Scope

Implemented modules:

- Auth
- Chat
- Knowledge Base
- Tickets
- Admin dashboard
- Admin user management
- Admin system settings

## Runtime Notes

- SQLite is supported for development and tests
- PostgreSQL is the main target for local Docker and production-like environments
- ChromaDB is optional
- If ChromaDB is unavailable, KB search falls back to database text matching
- Runtime settings are persisted in the `system_settings` table

## Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Test

```bash
cd backend
pytest
pytest -m integration
pytest tests/unit/test_api_ticket.py
```

Current verified result on `2026-04-02`:

- `141 passed`

## Important Limitation

`app/core/security.py` still uses temporary SHA-256 password hashing and must be replaced before production use.
