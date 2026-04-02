# 04. API Spec

Base URL: `http://localhost:8080/api/v1`

Authentication:

- Most routes require `Authorization: Bearer <access_token>`
- Public routes: `/auth/register`, `/auth/login`, `/auth/refresh`

## Auth

- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `GET /auth/me`

Registration accepts either `name` or `full_name`.
Login accepts either `employee_id` or `email`.

## Chat

- `POST /chat`
- `GET /chat/sessions`
- `GET /chat/sessions/{session_id}`
- `PATCH /chat/sessions/{session_id}/resolve`

`POST /chat` request:

```json
{
  "message": "How do I reset my password?",
  "session_id": "optional-uuid"
}
```

Response:

```json
{
  "session_id": "uuid",
  "message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "AI response",
    "token_count": 5,
    "created_at": "2026-04-02T00:00:00Z"
  },
  "is_resolved": false
}
```

## Knowledge Base

- `POST /kb/upload`
- `GET /kb/documents`
- `GET /kb/documents/{doc_id}`
- `DELETE /kb/documents/{doc_id}`
- `POST /kb/search`

Permissions:

- Upload/delete: `it_staff`, `admin`
- List/detail/search: any authenticated user

`POST /kb/search` request:

```json
{
  "query": "password reset",
  "top_k": 5
}
```

## Tickets

- `POST /tickets`
- `GET /tickets`
- `GET /tickets/{ticket_id}`
- `PATCH /tickets/{ticket_id}`
- `POST /tickets/{ticket_id}/comments`
- `GET /tickets/stats/overview`

Permissions:

- `employee`: own tickets only
- `it_staff`, `admin`: all tickets

## Admin

- `GET /admin/dashboard`
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}`
- `GET /admin/settings`
- `PATCH /admin/settings`

Permissions:

- Admin only

`GET /admin/settings` response:

```json
{
  "llm_provider": "claude",
  "llm_model": "claude-sonnet-4-20250514",
  "llm_temperature": 0.7,
  "max_tokens": 1024,
  "rag_enabled": true,
  "rag_top_k": 3
}
```

`PATCH /admin/settings` request:

```json
{
  "llm_provider": "openai",
  "llm_model": "gpt-4.1",
  "llm_temperature": 0.4,
  "max_tokens": 2048,
  "rag_enabled": true,
  "rag_top_k": 5
}
```

## Error Format

```json
{
  "detail": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS"
}
```

Common status codes:

- `400`
- `401`
- `403`
- `404`
- `422`
- `500`
