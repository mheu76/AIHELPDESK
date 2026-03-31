# CLAUDE.md — IT AI Helpdesk 프로젝트 지시서

> Claude Code가 이 프로젝트를 작업할 때 반드시 먼저 읽어야 하는 파일입니다.
> 모든 코드 생성·수정은 이 문서의 원칙을 준수합니다.

---

## 1. 프로젝트 개요

**프로젝트명:** IT AI Helpdesk (내부 웹 기반)
**목적:** 임직원 IT 문의를 AI가 1차 처리하고, 미해결 시 담당자에게 티켓으로 전달
**배포 환경:** 사내 서버 (On-premise)
**개발 방식:** Vibe Coding with Claude Code

---

## 2. 기술 스택

| 구분 | 기술 | 버전 |
|---|---|---|
| Frontend | Next.js (App Router) | 14+ |
| Backend | Python FastAPI | 0.110+ |
| LLM | Claude API (anthropic SDK) | 교체 가능 추상화 |
| Vector DB | ChromaDB | 0.4+ |
| RDBMS | PostgreSQL | 15+ |
| ORM | SQLAlchemy + Alembic | - |
| 인증 | JWT (추후 SSO 연동) | - |
| 컨테이너 | Docker + Docker Compose | - |

---

## 3. 폴더 구조

```
it-helpdesk/
├── CLAUDE.md                  ← 현재 파일 (항상 먼저 읽을 것)
├── docs/
│   ├── 01_architecture.md     ← 시스템 아키텍처
│   ├── 02_features.md         ← 기능 스펙
│   ├── 03_db_schema.md        ← DB 스키마
│   ├── 04_api_spec.md         ← API 명세
│   └── 05_ui_spec.md          ← 화면 설계
├── frontend/                  ← Next.js 앱
│   ├── app/
│   │   ├── (auth)/
│   │   ├── chat/
│   │   ├── tickets/
│   │   └── admin/
│   ├── components/
│   └── lib/
├── backend/                   ← FastAPI 앱
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   │   ├── config.py      ← 환경변수 관리
│   │   │   └── llm/
│   │   │       ├── base.py    ← LLM 추상화 레이어
│   │   │       ├── claude.py  ← Claude 구현체
│   │   │       └── openai.py  ← OpenAI 구현체 (교체용)
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── db/
│   ├── migrations/            ← Alembic 마이그레이션
│   └── tests/
├── docker-compose.yml
└── .env.example
```

---

## 4. 코딩 컨벤션

### 공통
- 모든 주석·변수명: **영어**
- 커밋 메시지: `feat:` `fix:` `docs:` `refactor:` 프리픽스 사용
- 환경변수는 반드시 `.env` 파일로 관리, 하드코딩 금지

### Backend (Python)
- PEP8 준수
- Type hint 필수 (모든 함수 인자·반환값)
- Pydantic v2 스키마 사용
- 비동기(async/await) 우선
- 에러 핸들링: HTTPException + 커스텀 에러 코드

### Frontend (Next.js)
- TypeScript 필수
- App Router 사용 (Pages Router 사용 금지)
- Server Component 우선, 필요 시 Client Component
- Tailwind CSS로 스타일링
- shadcn/ui 컴포넌트 활용

---

## 5. LLM 추상화 원칙 (핵심)

> LLM Provider는 언제든 교체 가능해야 합니다.
> 직접 API 호출 코드를 서비스 레이어에 작성하지 마세요.

```python
# 반드시 이 패턴을 따를 것
from app.core.llm.base import LLMBase

# 설정값으로 provider 결정
# LLM_PROVIDER=claude 또는 LLM_PROVIDER=openai
```

---

## 6. 개발 순서 (Sprint)

| Sprint | 기간 | 목표 | 참고 문서 |
|---|---|---|---|
| **S1** | 1~2주차 | 프로젝트 셋업 + Claude API 채팅 기본 구현 | 01, 04 |
| **S2** | 3~4주차 | RAG 구축 (ChromaDB + KB 문서 업로드) | 01, 02 |
| **S3** | 5~6주차 | 티켓 시스템 (생성·조회·담당자 배정) | 02, 03 |
| **S4** | 7~8주차 | 관리자 대시보드 + LLM 전환 기능 | 02, 05 |

---

## 7. 환경변수 목록

```env
# LLM
LLM_PROVIDER=claude          # claude | openai | gemini
ANTHROPIC_API_KEY=sk-...
OPENAI_API_KEY=sk-...        # 교체 시 사용

# DB
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/helpdesk
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Auth
JWT_SECRET_KEY=...
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

# App
ENVIRONMENT=development      # development | production
FRONTEND_URL=http://localhost:3000
```

---

## 8. 작업 시 주의사항

1. **새 기능 추가 전** `docs/02_features.md` 확인
2. **DB 변경 시** `docs/03_db_schema.md` 먼저 업데이트 후 코드 작성
3. **API 추가 시** `docs/04_api_spec.md` 먼저 업데이트 후 코드 작성
4. **LLM 직접 호출 금지** — 반드시 `app/core/llm/` 레이어 통해서
5. **테스트 없는 PR 금지** — 각 서비스 함수에 단위 테스트 필수
