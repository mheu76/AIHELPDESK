# 04. API 명세

> Base URL: `http://[서버IP]:8080/api/v1`
> 인증: Bearer JWT Token (로그인 제외 전 엔드포인트 필수)
> Content-Type: `application/json`

---

## 1. 인증 (Auth)

### POST /auth/login
```json
// Request
{
  "email": "hong@company.com",
  "password": "string"
}

// Response 200
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "name": "홍길동",
    "role": "employee",
    "department": "개발팀"
  }
}
```

### POST /auth/refresh
```json
// Request
{ "refresh_token": "eyJ..." }

// Response 200
{ "access_token": "eyJ..." }
```

---

## 2. 채팅 (Chat)

### POST /chat/sessions
> 새 채팅 세션 생성

```json
// Response 201
{
  "session_id": "uuid",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### POST /chat/sessions/{session_id}/messages
> 메시지 전송 및 AI 응답 수신 (Server-Sent Events Streaming)

```json
// Request
{
  "content": "비밀번호를 초기화하고 싶어요"
}

// Response: text/event-stream
data: {"type": "token", "content": "비밀번호"}
data: {"type": "token", "content": " 초기화는"}
data: {"type": "done", "message_id": "uuid", "is_resolved": false}
data: {"type": "suggest_ticket", "message": "티켓을 생성하시겠습니까?"}
```

### GET /chat/sessions/{session_id}/messages
> 채팅 이력 조회

```json
// Response 200
{
  "session_id": "uuid",
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "비밀번호를 초기화하고 싶어요",
      "created_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": "uuid",
      "role": "assistant",
      "content": "비밀번호 초기화 방법을 안내해 드리겠습니다...",
      "created_at": "2025-01-01T00:00:01Z"
    }
  ]
}
```

### GET /chat/sessions
> 내 채팅 세션 목록

```json
// Response 200
{
  "sessions": [
    {
      "id": "uuid",
      "title": "비밀번호 초기화 문의",
      "is_resolved": true,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

## 3. 티켓 (Tickets)

### POST /tickets
> 티켓 생성 (채팅 세션 기반 자동 요약)

```json
// Request
{
  "session_id": "uuid"    // 채팅 세션 기반 자동 생성
}

// Response 201
{
  "id": "uuid",
  "ticket_number": "T-000001",
  "title": "비밀번호 초기화 요청",
  "description": "사용자가 사내 시스템 비밀번호 초기화를 요청함...",
  "category": "account",
  "status": "open",
  "priority": "medium"
}
```

### GET /tickets
> 티켓 목록 조회

```
// Query Params (임직원: 본인 것만 / IT담당자·관리자: 전체)
?status=open          // open|in_progress|resolved|on_hold|closed
?category=account     // account|device|network|system|security|other
?assignee_id=uuid     // IT담당자 필터
?page=1&size=20
```

```json
// Response 200
{
  "total": 42,
  "page": 1,
  "items": [
    {
      "id": "uuid",
      "ticket_number": "T-000001",
      "title": "비밀번호 초기화 요청",
      "category": "account",
      "status": "open",
      "priority": "medium",
      "requester": { "name": "홍길동", "department": "개발팀" },
      "assignee": null,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

### GET /tickets/{ticket_id}
> 티켓 상세 조회 (대화 이력 포함)

### PATCH /tickets/{ticket_id}
> 티켓 업데이트 (IT담당자·관리자 전용)

```json
// Request (변경할 필드만 전송)
{
  "status": "in_progress",
  "assignee_id": "uuid",
  "priority": "high"
}
```

### POST /tickets/{ticket_id}/comments
> 티켓 코멘트 추가

```json
// Request
{
  "content": "확인 중입니다. 잠시만 기다려주세요.",
  "is_internal": false    // true: IT담당자 내부 메모
}
```

---

## 4. KB 관리 (Knowledge Base) — IT담당자·관리자

### POST /kb/documents
> 문서 업로드 (multipart/form-data)

```
Form Data:
  file: [binary]
  title: "비밀번호 초기화 매뉴얼"
```

```json
// Response 201
{
  "id": "uuid",
  "title": "비밀번호 초기화 매뉴얼",
  "file_name": "password_reset.pdf",
  "chunk_count": 12,
  "status": "processing"    // 임베딩 처리 중
}
```

### GET /kb/documents
> KB 문서 목록

### DELETE /kb/documents/{document_id}
> KB 문서 삭제 (ChromaDB 청크도 함께 삭제)

---

## 5. 관리자 (Admin)

### GET /admin/stats
> 통계 조회

```json
// Response 200
{
  "period": "2025-01",
  "total_sessions": 150,
  "ai_resolved": 112,
  "ai_resolve_rate": 0.747,
  "total_tickets": 38,
  "avg_response_time_sec": 2.3,
  "category_breakdown": {
    "account": 45,
    "device": 30,
    "network": 20,
    "system": 40,
    "security": 15
  }
}
```

### GET /admin/settings
> 시스템 설정 조회

### PATCH /admin/settings
> 시스템 설정 변경

```json
// Request
{
  "llm_provider": "openai",
  "llm_model": "gpt-4o"
}
```

---

## 6. 공통 에러 응답

```json
// 4xx / 5xx
{
  "error_code": "INVALID_TOKEN",
  "message": "인증 토큰이 유효하지 않습니다.",
  "detail": null
}
```

| HTTP | error_code | 설명 |
|---|---|---|
| 400 | VALIDATION_ERROR | 요청 파라미터 오류 |
| 401 | INVALID_TOKEN | 인증 토큰 오류 |
| 403 | FORBIDDEN | 권한 없음 |
| 404 | NOT_FOUND | 리소스 없음 |
| 429 | RATE_LIMIT | LLM API 한도 초과 |
| 500 | INTERNAL_ERROR | 서버 오류 |
| 503 | LLM_UNAVAILABLE | LLM API 연결 오류 |
