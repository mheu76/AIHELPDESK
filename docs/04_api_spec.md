# 04. API Spec

Base URL: `http://localhost:8080/api/v1`

인증 방식:

- 대부분 `Authorization: Bearer <access_token>`
- 예외: `/auth/register`, `/auth/login`, `/auth/refresh`

## 1. Auth

### POST `/auth/register`

Request:

```json
{
  "employee_id": "EMP001",
  "email": "user@company.com",
  "full_name": "Test User",
  "password": "SecurePass123!"
}
```

Response `201`:

```json
{
  "id": "uuid",
  "employee_id": "EMP001",
  "email": "user@company.com",
  "name": "Test User",
  "full_name": "Test User",
  "role": "employee",
  "department": null,
  "is_active": true,
  "created_at": "2026-04-01T00:00:00Z",
  "updated_at": "2026-04-01T00:00:00Z"
}
```

### POST `/auth/login`

`employee_id` 또는 `email` 중 하나를 사용합니다.

Request:

```json
{
  "employee_id": "EMP001",
  "password": "SecurePass123!"
}
```

Response `200`:

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "uuid",
    "employee_id": "EMP001",
    "email": "user@company.com",
    "name": "Test User",
    "full_name": "Test User",
    "role": "employee",
    "department": null,
    "is_active": true,
    "created_at": "2026-04-01T00:00:00Z",
    "updated_at": "2026-04-01T00:00:00Z"
  }
}
```

### POST `/auth/refresh`

Request:

```json
{
  "refresh_token": "jwt"
}
```

### GET `/auth/me`

현재 로그인 사용자 조회.

## 2. Chat

### POST `/chat`

Request:

```json
{
  "message": "How do I reset my password?",
  "session_id": "optional-uuid"
}
```

Response `200`:

```json
{
  "session_id": "uuid",
  "message": {
    "id": "uuid",
    "session_id": "uuid",
    "role": "assistant",
    "content": "AI response",
    "token_count": 5,
    "created_at": "2026-04-01T00:00:00Z"
  },
  "is_resolved": false
}
```

### GET `/chat/sessions`

Query:

- `limit` default `50`
- `offset` default `0`

### GET `/chat/sessions/{session_id}`

세션 메시지 전체 조회.

### PATCH `/chat/sessions/{session_id}/resolve`

Request:

```json
{
  "is_resolved": true
}
```

## 3. Knowledge Base

### POST `/kb/upload`

권한: `it_staff`, `admin`

지원 방식:

- `multipart/form-data`
- JSON body

JSON 예시:

```json
{
  "content": "How to reset password...",
  "file_name": "password.txt",
  "title": "Password Reset Guide"
}
```

### GET `/kb/documents`

인증 필요. 전체 사용자 조회 가능.

지원 쿼리:

- `limit`, `offset`
- `page`, `per_page`

### GET `/kb/documents/{doc_id}`

문서 상세 조회.

### DELETE `/kb/documents/{doc_id}`

권한: `it_staff`, `admin`

soft delete 처리.

### POST `/kb/search`

Request:

```json
{
  "query": "password reset",
  "top_k": 5
}
```

## 4. Tickets

### POST `/tickets`

채팅 세션 기반 티켓 생성.

Request:

```json
{
  "session_id": "uuid",
  "additional_notes": "Urgent issue",
  "priority": "high"
}
```

### GET `/tickets`

권한별 동작:

- `employee`: 본인 티켓만 조회
- `it_staff`, `admin`: 전체 조회 가능

Query:

- `status`
- `category`
- `assignee_id`
- `page`
- `page_size`

### GET `/tickets/{ticket_id}`

티켓 상세 및 댓글 조회.

내부 메모 노출:

- `employee`: 내부 메모 숨김
- `it_staff`, `admin`: 내부 메모 포함

### PATCH `/tickets/{ticket_id}`

권한: `it_staff`, `admin`

수정 가능 필드:

- `status`
- `priority`
- `assignee_id`
- `category`

### POST `/tickets/{ticket_id}/comments`

Request:

```json
{
  "content": "We are checking the issue.",
  "is_internal": false
}
```

규칙:

- 직원은 공개 댓글만 가능
- IT/Admin은 내부 메모 가능

### GET `/tickets/stats/overview`

권한: `it_staff`, `admin`

Response 필드:

- `total_tickets`
- `open_tickets`
- `in_progress_tickets`
- `resolved_tickets`
- `tickets_by_category`
- `tickets_by_priority`
- `avg_resolution_time_hours`

## 5. 에러 응답

일반 형식:

```json
{
  "detail": "Invalid credentials",
  "error_code": "INVALID_CREDENTIALS"
}
```

대표 상태 코드:

- `400` 잘못된 요청
- `401` 인증 실패
- `403` 권한 부족
- `404` 리소스 없음
- `422` 입력 검증 실패
- `500` 서버 오류
