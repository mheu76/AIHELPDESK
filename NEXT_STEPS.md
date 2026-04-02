# Next Steps

Last updated: `2026-04-02`

This file tracks follow-up work after the backend recovery, persistent settings integration, and frontend stabilization work.

## Priority 1

- Replace temporary SHA-256 password hashing with `bcrypt` or `argon2`
- Fix deprecation warnings: replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`
- Fix HTTP_422 constant deprecation in Starlette exception handler
- Verify Alembic upgrades on a real PostgreSQL database with existing data
- Add validation, audit logging, and rollback guidance for admin setting changes

## Priority 2

- Clean up chat page UX and remaining inconsistent copy
- Add SSE streaming chat end-to-end
- Centralize token refresh and route guard behavior in the frontend

## Priority 3

- Add frontend automated tests
- Add CI for backend tests, frontend type-check, and migration checks
- Integrate error tracking and operational logging

## Priority 4

- Improve KB fallback retrieval quality when ChromaDB is unavailable
- Expand admin dashboard metrics
- Add deployment and operations playbooks
