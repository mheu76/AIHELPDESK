# Phase 1 Setup Guide

Phase 1 (Sprint 1) 백엔드 구현이 완료되었습니다. 아래 가이드를 따라 설정하고 실행하세요.

## ✅ 완료된 작업

### Backend
1. **Database Models** ✅
   - User (사용자 인증 및 권한)
   - ChatSession (대화 세션)
   - ChatMessage (대화 메시지)

2. **LLM Abstraction Layer** ✅
   - Base interface (LLMBase)
   - Claude implementation (ClaudeLLM)
   - OpenAI implementation (OpenAILLM)
   - Factory pattern (LLMFactory)

3. **Security Module** ✅
   - JWT token creation/verification
   - Password hashing (bcrypt)
   - Token refresh mechanism

4. **Services** ✅
   - AuthService (회원가입, 로그인, 토큰 관리)
   - ChatService (AI 대화, 세션 관리)

5. **API Endpoints** ✅
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login
   - POST /api/v1/auth/refresh
   - GET /api/v1/auth/me
   - POST /api/v1/chat
   - GET /api/v1/chat/sessions
   - GET /api/v1/chat/sessions/{id}
   - PATCH /api/v1/chat/sessions/{id}/resolve

6. **Alembic Migrations** ✅
   - 초기 설정 완료
   - Migration 파일 생성 준비 완료

---

## 🚀 설치 및 실행

### 1. Python 패키지 설치

```bash
cd backend

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cd backend

# .env.example을 복사
cp .env.example .env

# .env 파일 편집
# 필수 설정:
# - ANTHROPIC_API_KEY: Claude API 키
# - JWT_SECRET_KEY: openssl rand -hex 32 로 생성
# - DATABASE_URL: PostgreSQL 연결 문자열
```

### 3. PostgreSQL 데이터베이스 준비

#### Option A: Docker로 PostgreSQL 실행 (권장)

```bash
# PostgreSQL 컨테이너 실행
docker run -d \
  --name helpdesk-postgres \
  -e POSTGRES_USER=helpdesk \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=helpdesk \
  -p 5432:5432 \
  postgres:15

# .env 파일의 DATABASE_URL 설정
# DATABASE_URL=postgresql+asyncpg://helpdesk:password@localhost:5432/helpdesk
```

#### Option B: 로컬 PostgreSQL 사용

```bash
# PostgreSQL 설치 후 데이터베이스 생성
psql -U postgres
CREATE DATABASE helpdesk;
CREATE USER helpdesk WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE helpdesk TO helpdesk;
\q
```

### 4. 데이터베이스 마이그레이션

```bash
cd backend

# 초기 마이그레이션 생성
alembic revision --autogenerate -m "Initial schema"

# 마이그레이션 적용
alembic upgrade head
```

### 5. 백엔드 서버 실행

```bash
cd backend

# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

서버가 실행되면:
- API: http://localhost:8080
- API Docs: http://localhost:8080/docs
- Health Check: http://localhost:8080/health

---

## 🧪 API 테스트

### 1. Health Check

```bash
curl http://localhost:8080/health
```

### 2. 회원가입

```bash
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP001",
    "email": "user@company.com",
    "name": "홍길동",
    "password": "password123",
    "department": "개발팀"
  }'
```

### 3. 로그인

```bash
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@company.com",
    "password": "password123"
  }'
```

응답에서 `access_token`을 복사하세요.

### 4. 프로필 조회

```bash
curl http://localhost:8080/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 5. 채팅 메시지 전송

```bash
curl -X POST http://localhost:8080/api/v1/chat \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "비밀번호를 잊어버렸어요. 어떻게 재설정하나요?"
  }'
```

### 6. 채팅 세션 목록 조회

```bash
curl http://localhost:8080/api/v1/chat/sessions \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🔧 Troubleshooting

### 1. Alembic 명령어가 안 될 때

```bash
# Python 모듈로 직접 실행
python -m alembic revision --autogenerate -m "Initial schema"
python -m alembic upgrade head
```

### 2. PostgreSQL 연결 오류

```bash
# 컨테이너 상태 확인
docker ps -a | grep postgres

# 로그 확인
docker logs helpdesk-postgres

# 재시작
docker restart helpdesk-postgres
```

### 3. Import 오류

```bash
# backend 디렉토리에서 실행하는지 확인
cd backend
python -m app.main
```

### 4. JWT_SECRET_KEY 생성

```bash
# Linux/Mac
openssl rand -hex 32

# Python으로 생성
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## 📋 다음 단계 (Phase 2)

Phase 1 완료 후 다음 기능 개발:

1. **RAG System (Sprint 2)**
   - ChromaDB 연동
   - KB 문서 업로드 및 임베딩
   - Vector search 기반 컨텍스트 제공

2. **Frontend Development**
   - Next.js 로그인 페이지
   - 채팅 인터페이스
   - 세션 관리 UI

3. **Testing**
   - 단위 테스트 추가
   - 통합 테스트
   - E2E 테스트

---

## 📝 참고 문서

- **CLAUDE.md**: 프로젝트 전체 지침
- **docs/01_architecture.md**: 시스템 아키텍처
- **docs/02_features.md**: 기능 명세
- **docs/03_db_schema.md**: 데이터베이스 스키마
- **docs/04_api_spec.md**: API 상세 명세

---

## 🎯 체크리스트

Phase 1 완료 확인:

- [ ] PostgreSQL 실행 중
- [ ] 환경변수 설정 완료 (.env)
- [ ] Python 패키지 설치 완료
- [ ] Alembic 마이그레이션 완료
- [ ] 백엔드 서버 실행 성공
- [ ] Health check 응답 확인
- [ ] 회원가입 API 테스트 성공
- [ ] 로그인 API 테스트 성공
- [ ] 채팅 API 테스트 성공 (Claude API 키 필요)

모든 항목이 완료되면 Phase 2로 진행할 수 있습니다!
