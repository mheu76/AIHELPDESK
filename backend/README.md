# Backend

FastAPI 기반 백엔드입니다. 인증, 채팅, KB, 티켓 API를 제공합니다.

## 현재 구현 범위

- 사용자 등록, 로그인, 토큰 갱신, 내 정보 조회
- 채팅 세션 생성 및 메시지 저장
- KB 문서 업로드, 목록, 상세, 검색, 삭제
- 채팅 세션 기반 티켓 생성
- 티켓 목록, 상세, 댓글, 상태/우선순위/담당자 변경
- 티켓 통계 조회
- Alembic 마이그레이션 및 pytest 기반 테스트

## 실행

### 로컬

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Docker

루트에서 실행:

```bash
docker compose up --build
```

## 환경 변수

필수:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ANTHROPIC_API_KEY` 또는 `OPENAI_API_KEY`

주요 선택:

- `LLM_PROVIDER=claude|openai`
- `LLM_MODEL`
- `FRONTEND_URL`
- `ALLOWED_ORIGINS`
- `CHROMA_HOST`
- `CHROMA_PORT`

예시는 [backend/.env.example](/D:/DEV/AIhelpdesk/backend/.env.example), Docker 전용 값은 [backend/.env.docker](/D:/DEV/AIhelpdesk/backend/.env.docker)에 있습니다.

## 데이터베이스

기본 전제:

- 개발/테스트: SQLite 가능
- Docker 개발환경: PostgreSQL 사용
- 스키마 변경: Alembic 사용

마이그레이션:

```bash
cd backend
alembic upgrade head
```

현재 초기 마이그레이션은 `users`, `chat_sessions`, `chat_messages`, `kb_documents`, `tickets`, `ticket_comments`를 포함합니다.

## API 라우트

### Auth

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/auth/me`

### Chat

- `POST /api/v1/chat`
- `GET /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions/{session_id}`
- `PATCH /api/v1/chat/sessions/{session_id}/resolve`

### Knowledge Base

- `POST /api/v1/kb/upload`
- `GET /api/v1/kb/documents`
- `GET /api/v1/kb/documents/{doc_id}`
- `DELETE /api/v1/kb/documents/{doc_id}`
- `POST /api/v1/kb/search`

### Tickets

- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{ticket_id}`
- `PATCH /api/v1/tickets/{ticket_id}`
- `POST /api/v1/tickets/{ticket_id}/comments`
- `GET /api/v1/tickets/stats/overview`

## 테스트

```bash
cd backend
pytest
pytest -m integration
pytest tests/unit/test_api_ticket.py
```

## 구현상 메모

- `test-key` 계열 API 키를 쓰면 오프라인용 `StubLLM`이 사용됩니다.
- ChromaDB 미연결 시 KB 검색은 DB 텍스트 검색으로 폴백합니다.
- Postgres 개발환경에서는 `create_all()` 대신 Alembic 경로를 사용합니다.
