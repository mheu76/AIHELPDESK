# 09. Admin Manual

## Local Start

Recommended:

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`

Stop:

```bash
docker compose down
```

Remove volumes:

```bash
docker compose down -v
```

## Backend Local Run

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## Admin Capabilities

Admin-only backend endpoints:

- `/api/v1/admin/dashboard`
- `/api/v1/admin/users`
- `/api/v1/admin/users/{user_id}`
- `/api/v1/admin/settings`

Admin UI routes:

- `/admin`
- `/admin/users`
- `/admin/settings`

## System Settings

Settings are persistent and stored in `system_settings`.

Editable values:

- `llm_provider`
- `llm_model`
- `llm_temperature`
- `max_tokens`
- `rag_enabled`
- `rag_top_k`

These values affect new runtime requests.

## User Management

Admins can:

- list users
- filter by role and active status
- inspect user details
- change role
- change department
- activate or deactivate users

Safety rule:

- the last active admin cannot be removed or demoted

## KB Operations

Permissions:

- upload/delete: `it_staff`, `admin`
- list/detail/search: all authenticated users

Supported upload formats:

- `pdf`
- `docx`
- `txt`
- `md`

Upload size limit:

- `10MB`

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

Verified on `2026-04-02`:

- Backend tests: `141 passed`
- Frontend type-check: pass

## Current Admin Risks

- Password hashing is still temporary
- No CI/CD guardrails yet
- No production error tracking yet
