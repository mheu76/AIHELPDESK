# 03. DB Schema

Primary stack:

- SQLAlchemy async
- Alembic migrations

## Tables

- `users`
- `chat_sessions`
- `chat_messages`
- `kb_documents`
- `tickets`
- `ticket_comments`
- `system_settings`

## users

- `id` UUID PK
- `employee_id` unique
- `email` unique
- `name`
- `hashed_password`
- `role`
- `department`
- `is_active`
- `created_at`
- `updated_at`

Roles:

- `employee`
- `it_staff`
- `admin`

## chat_sessions

- `id` UUID PK
- `user_id` FK -> `users.id`
- `title`
- `is_resolved`
- `created_at`
- `updated_at`

## chat_messages

- `id` UUID PK
- `session_id` FK -> `chat_sessions.id`
- `role`
- `content`
- `token_count`
- `created_at`

Roles used in messages:

- `user`
- `assistant`

## kb_documents

- `id` UUID PK
- `title`
- `file_name`
- `file_type`
- `content`
- `file_size`
- `chunk_count`
- `chroma_ids` JSON
- `uploaded_by` FK -> `users.id`
- `is_active`
- `created_at`

Notes:

- Soft delete is represented by `is_active = false`
- `created_by_id` is supported as a compatibility alias in the model layer

## tickets

- `id` UUID PK
- `ticket_number` unique
- `title`
- `description`
- `category`
- `status`
- `priority`
- `requester_id` FK -> `users.id`
- `assignee_id` FK -> `users.id`
- `session_id` FK -> `chat_sessions.id`
- `resolved_at`
- `created_at`
- `updated_at`

Categories:

- `account`
- `device`
- `network`
- `system`
- `security`
- `other`

Statuses:

- `open`
- `in_progress`
- `resolved`
- `on_hold`
- `closed`

Priorities:

- `low`
- `medium`
- `high`
- `urgent`

## ticket_comments

- `id` UUID PK
- `ticket_id` FK -> `tickets.id`
- `author_id` FK -> `users.id`
- `content`
- `is_internal`
- `created_at`

## system_settings

Singleton table used for runtime configuration.

- `id` integer PK, fixed to `1`
- `llm_provider`
- `llm_model`
- `llm_temperature`
- `max_tokens`
- `rag_enabled`
- `rag_top_k`
- `updated_at`

## Relationships

```text
users 1---N chat_sessions
chat_sessions 1---N chat_messages
users 1---N kb_documents
users 1---N tickets (requester)
users 1---N tickets (assignee)
chat_sessions 1---0..1 tickets
tickets 1---N ticket_comments
users 1---N ticket_comments
system_settings 1 row only
```
