# 03. DB Schema

기준 구현: SQLAlchemy async + Alembic

## 현재 핵심 테이블

- `users`
- `chat_sessions`
- `chat_messages`
- `kb_documents`
- `tickets`
- `ticket_comments`

## users

사용자 계정과 역할 정보.

주요 컬럼:

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

역할 값:

- `employee`
- `it_staff`
- `admin`

## chat_sessions

사용자별 대화 세션.

주요 컬럼:

- `id` UUID PK
- `user_id` FK -> `users.id`
- `title`
- `is_resolved`
- `created_at`
- `updated_at`

참고:

- 현재 모델에는 `ticket_id` 컬럼이 없고, 티켓 쪽에서 `session_id`를 참조합니다.

## chat_messages

대화 메시지 저장.

주요 컬럼:

- `id` UUID PK
- `session_id` FK -> `chat_sessions.id`
- `role`
- `content`
- `token_count`
- `created_at`

역할 값 예시:

- `user`
- `assistant`
- `system`

## kb_documents

지식베이스 문서 메타데이터와 본문 저장.

주요 컬럼:

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

참고:

- ChromaDB가 연결되면 청크 ID를 `chroma_ids`에 저장합니다.
- soft delete는 `is_active = false`로 처리합니다.

## tickets

헬프데스크 티켓 본문.

주요 컬럼:

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

카테고리:

- `account`
- `device`
- `network`
- `system`
- `security`
- `other`

상태:

- `open`
- `in_progress`
- `resolved`
- `on_hold`
- `closed`

우선순위:

- `low`
- `medium`
- `high`
- `urgent`

## ticket_comments

티켓 댓글 및 내부 메모.

주요 컬럼:

- `id` UUID PK
- `ticket_id` FK -> `tickets.id`
- `author_id` FK -> `users.id`
- `content`
- `is_internal`
- `created_at`

## 관계 요약

```text
users 1---N chat_sessions
chat_sessions 1---N chat_messages
users 1---N kb_documents
users 1---N tickets (requester)
users 1---N tickets (assignee)
chat_sessions 1---0..1 tickets
tickets 1---N ticket_comments
users 1---N ticket_comments
```

## 마이그레이션

초기 스키마 적용:

```bash
cd backend
alembic upgrade head
```

현재 Alembic 초기 마이그레이션은 위 6개 테이블을 생성하도록 정리되어 있습니다.
