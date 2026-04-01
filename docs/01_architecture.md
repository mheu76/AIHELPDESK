# 01. Architecture

## 개요

현재 시스템은 다음 3개 핵심 레이어로 구성됩니다.

1. Next.js 프론트엔드
2. FastAPI 백엔드
3. PostgreSQL 데이터베이스

선택적으로 ChromaDB를 붙여 KB 검색 품질을 높일 수 있습니다. ChromaDB가 없더라도 시스템은 동작하며, 이 경우 KB 검색은 DB 텍스트 검색으로 폴백합니다.

## 현재 아키텍처

```text
Browser
  -> Frontend (Next.js, port 3000)
  -> Backend (FastAPI, port 8080)
  -> PostgreSQL (port 5432)
  -> ChromaDB (optional, port 8000)
```

개발용 Docker Compose 기준 서비스:

- `frontend`
- `backend`
- `db`

ChromaDB는 현재 Compose 기본 구성에는 포함하지 않았습니다.

## 백엔드 구성

### Core

- Pydantic Settings 기반 설정 관리
- 구조화된 로깅
- 커스텀 예외 및 에러 핸들러
- Request ID 미들웨어
- CORS 설정

### Domain

- Auth
- Chat
- Knowledge Base
- Tickets

### Data Layer

- SQLAlchemy async session
- Alembic migration
- SQLite(dev/test) 및 PostgreSQL 지원

## 인증 흐름

1. 사용자가 `/api/v1/auth/login` 호출
2. 백엔드가 계정과 비밀번호 검증
3. Access token / Refresh token 발급
4. 프론트가 `localStorage`에 토큰 저장
5. 이후 API 호출 시 `Authorization: Bearer ...` 사용

## 채팅 흐름

1. 사용자가 메시지 전송
2. 세션이 없으면 새 `chat_sessions` 생성
3. 사용자 메시지를 `chat_messages`에 저장
4. KB 검색 수행
5. LLM 응답 생성
6. AI 응답을 `chat_messages`에 저장
7. 프론트로 단건 응답 반환

현재는 동기식 단건 응답이며, SSE 스트리밍은 아직 구현되지 않았습니다.

## KB 흐름

1. 관리자 또는 IT 담당자가 문서 업로드
2. 문서 파싱(PDF/DOCX/TXT/MD)
3. 텍스트 청킹
4. ChromaDB 연결 시 벡터 저장
5. 메타데이터와 본문을 `kb_documents`에 저장
6. 검색 시 ChromaDB 우선, 실패 시 DB 텍스트 검색

## 티켓 흐름

1. 사용자가 채팅 세션 기반 티켓 생성
2. 백엔드가 세션 메시지들을 묶어 LLM으로 요약
3. 카테고리와 제목/설명을 생성
4. `tickets`에 저장
5. 댓글은 `ticket_comments`로 관리
6. IT 담당자가 상태/우선순위/담당자 변경

## 현재 구현 제약

- 관리자 전용 통합 대시보드 계층은 아직 없음
- 티켓 번호 생성은 DB auto increment 형태를 기대하지만, 실제 운영 DB 제약 검증은 추가 필요
- ChromaDB 없는 환경에서는 검색 정확도가 낮을 수 있음
