# Repository Working Notes

Last updated: `2026-04-02`

This file is a lightweight repository guide for coding agents and maintainers.

## Project Summary

IT AI Helpdesk is an internal support system built with:

- FastAPI backend
- Next.js 14 frontend
- PostgreSQL
- Optional ChromaDB for vector retrieval

Primary domains:

- auth
- chat
- knowledge base
- tickets
- admin

## Current Verified State

- Runtime system settings are persisted in the database
- Chat and LLM dependency wiring use runtime settings
- Ticket numbering uses PostgreSQL SEQUENCE for safe concurrent creation
- Ticket-to-session relationship enforced with unique constraint
- Admin account protection prevents removing last active admin
- Backend tests pass: `141 passed`
- Frontend type-check passes

## Important Risks

- `backend/app/core/security.py` still uses temporary SHA-256 password hashing
- Several deprecation warnings need addressing (datetime.utcnow, HTTP_422 constant)
- Chat is not streaming yet
- CI/CD and production observability are not complete

## Working Conventions

- Prefer updating documentation when behavior changes
- Treat `docs/` as the product and operations source of truth
- Do not assume ChromaDB is always available; fallback KB search exists
- Do not describe bcrypt as implemented until the security module is replaced

## Useful Entry Points

- Root overview: `README.md`
- Backend overview: `backend/README.md`
- Frontend overview: `frontend/README.md`
- Architecture: `docs/01_architecture.md`
- API spec: `docs/04_api_spec.md`
- Admin manual: `docs/09_admin_manual.md`
