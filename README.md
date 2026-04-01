# IT AI Helpdesk

사내 IT 문의를 AI 채팅, 지식베이스 검색, 티켓 관리로 처리하는 헬프데스크 시스템입니다.

## 현재 상태

현재 레포 기준으로 구현된 범위는 아래와 같습니다.

- 백엔드 FastAPI 기본 인프라 완료
- 사용자 회원가입, 로그인, 토큰 갱신, 내 정보 조회 구현
- AI 채팅 세션 생성, 대화 저장, 세션 목록/상세 조회 구현
- KB 문서 업로드, 목록, 상세, 검색, 삭제 구현
- 티켓 생성, 목록, 상세, 댓글, 상태 변경, 통계 API 구현
- Next.js 기반 로그인, 회원가입, 채팅, 티켓 목록/상세, KB 관리 화면 구현
- 개발용 Docker Compose 환경 추가

아직 미구현 또는 부분 구현 상태인 항목도 있습니다.

- 실시간 SSE 스트리밍 채팅 미구현
- 관리자 전용 대시보드 API/화면 미구현
- ChromaDB는 선택 사항이며, 미연결 시 DB `LIKE` 검색으로 폴백
- 운영 배포용 프록시, 시크릿 관리, CI/CD는 미정리

## 프로젝트 구조

```text
.
├─ backend/                FastAPI, SQLAlchemy, Alembic, pytest
├─ frontend/               Next.js 14 App Router
├─ docs/                   아키텍처 / 기능 / DB / API / UI / 운영 문서
├─ docker-compose.yml      개발용 Docker Compose
└─ DOCKER_DEV.md           Docker 개발 실행 가이드
```

## 빠른 시작

### 1. Docker로 실행

가장 쉬운 개발 시작 방법입니다.

```bash
docker compose up --build
```

기본 접속 주소:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`
- PostgreSQL: `localhost:5432`

실행 전 [backend/.env.docker](/D:/DEV/AIhelpdesk/backend/.env.docker)의 주요 값은 필요에 따라 수정하세요.

- `ANTHROPIC_API_KEY`
- `JWT_SECRET_KEY`

### 2. 로컬로 직접 실행

#### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 환경 변수

백엔드에서 필수로 사용하는 주요 환경 변수:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `ANTHROPIC_API_KEY` 또는 `OPENAI_API_KEY`
- `LLM_PROVIDER`
- `FRONTEND_URL`
- `ALLOWED_ORIGINS`

기본 예시는 [backend/.env.example](/D:/DEV/AIhelpdesk/backend/.env.example)에 있습니다.

## 기술 스택

- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Backend: FastAPI, SQLAlchemy async, Alembic, Pydantic v2
- Database: PostgreSQL 15 또는 SQLite(dev/test)
- Vector Search: ChromaDB 선택 사용
- Auth: JWT
- LLM: Claude / OpenAI 추상화 레이어

## 구현된 핵심 API

- Auth: `/api/v1/auth/register`, `/login`, `/refresh`, `/me`
- Chat: `/api/v1/chat`, `/chat/sessions`, `/chat/sessions/{id}`
- KB: `/api/v1/kb/upload`, `/kb/documents`, `/kb/search`
- Tickets: `/api/v1/tickets`, `/tickets/{id}`, `/tickets/{id}/comments`, `/tickets/stats/overview`

상세 명세는 [docs/04_api_spec.md](/D:/DEV/AIhelpdesk/docs/04_api_spec.md)를 참고하세요.

## 테스트

```bash
cd backend
pytest
```

현재 테스트 범위:

- 헬스체크
- 인증 API
- 채팅 API
- KB API
- 티켓 API

## 문서 목록

- [docs/01_architecture.md](/D:/DEV/AIhelpdesk/docs/01_architecture.md)
- [docs/02_features.md](/D:/DEV/AIhelpdesk/docs/02_features.md)
- [docs/03_db_schema.md](/D:/DEV/AIhelpdesk/docs/03_db_schema.md)
- [docs/04_api_spec.md](/D:/DEV/AIhelpdesk/docs/04_api_spec.md)
- [docs/05_ui_spec.md](/D:/DEV/AIhelpdesk/docs/05_ui_spec.md)
- [docs/09_admin_manual.md](/D:/DEV/AIhelpdesk/docs/09_admin_manual.md)
- [DOCKER_DEV.md](/D:/DEV/AIhelpdesk/DOCKER_DEV.md)
