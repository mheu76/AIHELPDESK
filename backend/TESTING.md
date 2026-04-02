# Backend Testing Guide

Last updated: `2026-04-02`

## Scope

The backend test suite covers:

- auth services and API routes
- chat services and API routes
- KB services and API routes
- ticket services and API routes
- admin services
- LLM abstraction and fallback behavior

## Run Tests

```bash
cd backend
pytest
```

Useful targeted runs:

```bash
pytest tests/unit/test_admin_service.py
pytest tests/unit/test_api_ticket.py
pytest tests/unit/test_rag_service.py
pytest -m integration
```

## Current Verified Result

Verified on `2026-04-02`:

- `141 passed`

## Notes

- Tests primarily use SQLite for isolation and speed
- Migration behavior against existing PostgreSQL databases still needs explicit smoke validation
- Warnings remain around legacy `datetime.utcnow()` usage and should be cleaned up separately

## Recommended CI Checks

- `pytest`
- Alembic upgrade smoke test
- Basic import/startup check for the FastAPI app
