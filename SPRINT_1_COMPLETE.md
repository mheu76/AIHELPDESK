# Sprint 1 Status

Last updated: `2026-04-02`

This file records the current interpretation of Sprint 1 deliverables after the recent backend and frontend stabilization work.

## Delivered

- FastAPI backend with auth, chat, KB, ticket, and admin modules
- Next.js frontend with auth, chat, ticket, KB, and admin routes
- JWT access and refresh token flow
- Knowledge base upload, list, detail, delete, and search
- Ticket creation from chat sessions plus comment and status workflows
- Admin dashboard, user management, and persistent runtime settings
- Alembic migrations for the current schema
- Backend automated test suite passing
- Frontend type-check passing

## Important Changes Since Earlier Sprint Notes

- System settings are now persisted in the `system_settings` table
- Chat and LLM dependency wiring now use runtime settings from the database
- Ticket pages, KB page, and auth pages were stabilized to pass frontend type-check
- Prior sprint notes that claimed bcrypt or streaming support are no longer accurate for the current branch

## Verified State

Verified on `2026-04-02`:

- Backend: `141 passed`
- Frontend: `npm run lint` pass

## Still Open

- Replace temporary SHA-256 password hashing
- Validate migrations against real PostgreSQL upgrade paths
- Add SSE streaming chat
- Add CI and production error tracking
