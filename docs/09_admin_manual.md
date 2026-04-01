# 09. 관리자 및 IT 담당자 운영 매뉴얼

> IT AI Helpdesk 시스템 설치, 설정 및 운영 가이드

---

## 목차
1. [시스템 요구사항](#1-시스템-요구사항)
2. [초기 설치 및 설정](#2-초기-설치-및-설정)
3. [서비스 시작 및 중지](#3-서비스-시작-및-중지)
4. [관리자 초기 설정](#4-관리자-초기-설정)
5. [KB 문서 관리](#5-kb-문서-관리)
6. [사용자 계정 관리](#6-사용자-계정-관리)
7. [LLM 설정 변경](#7-llm-설정-변경)
8. [모니터링 및 로그](#8-모니터링-및-로그)
9. [백업 및 복구](#9-백업-및-복구)
10. [문제 해결](#10-문제-해결)

---

## 1. 시스템 요구사항

### 1-1. 하드웨어 요구사항

| 구성 요소 | 최소 사양 | 권장 사양 |
|---|---|---|
| CPU | 4 Core | 8 Core |
| RAM | 8 GB | 16 GB |
| 디스크 | 50 GB SSD | 100 GB SSD |
| 네트워크 | 1 Gbps | 1 Gbps |

**예상 디스크 사용량:**
- 시스템 파일: ~5 GB
- PostgreSQL 데이터: ~10 GB (1년 기준)
- ChromaDB 벡터 DB: ~20 GB (KB 문서 1,000개 기준)
- 로그 파일: ~5 GB

### 1-2. 소프트웨어 요구사항

**필수 소프트웨어:**
```
OS: Ubuntu 22.04 LTS / Windows Server 2022
Python: 3.11 or 3.12 (주의: 3.14는 bcrypt 호환성 문제 있음)
Node.js: 18.x or 20.x
PostgreSQL: 15.x
```

**선택 소프트웨어:**
```
Docker: 24.x (컨테이너 배포 시)
Docker Compose: 2.x
ChromaDB: 0.4.x (별도 설치 또는 Docker)
```

### 1-3. 네트워크 요구사항

**내부 포트:**
- Frontend: 3000
- Backend API: 8080
- PostgreSQL: 5432
- ChromaDB: 8000

**외부 연결:**
- Anthropic Claude API: https://api.anthropic.com (HTTPS 443)
- OpenAI API (선택): https://api.openai.com (HTTPS 443)

**방화벽 설정:**
```bash
# 내부 네트워크에서만 접근 허용
sudo ufw allow from 192.168.0.0/16 to any port 3000
sudo ufw allow from 192.168.0.0/16 to any port 8080

# Claude API 외부 접속 허용
sudo ufw allow out to api.anthropic.com port 443
```

---

## 2. 초기 설치 및 설정

### 2-1. 저장소 복제

```bash
# Git 저장소에서 프로젝트 다운로드
cd /opt
sudo git clone https://github.com/your-org/it-helpdesk.git
cd it-helpdesk

# 소유권 설정
sudo chown -R helpdesk:helpdesk /opt/it-helpdesk
```

### 2-2. PostgreSQL 설치 및 초기화

```bash
# PostgreSQL 설치 (Ubuntu)
sudo apt update
sudo apt install postgresql-15 postgresql-contrib

# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 및 사용자 생성
sudo -u postgres psql

postgres=# CREATE DATABASE helpdesk;
postgres=# CREATE USER helpdesk WITH ENCRYPTED PASSWORD 'your-secure-password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE helpdesk TO helpdesk;
postgres=# \q
```

### 2-3. Backend 설정

```bash
cd /opt/it-helpdesk/backend

# Python 가상 환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 환경변수 파일 생성
cp .env.example .env
nano .env
```

**.env 파일 설정 (중요):**

```bash
# Environment
ENVIRONMENT=production
DEBUG=false

# LLM Configuration
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-YOUR-ACTUAL-API-KEY-HERE  # ← 필수 변경!
LLM_MODEL=claude-sonnet-4-20250514
LLM_MAX_TOKENS=1024
LLM_TEMPERATURE=0.7

# Database
DATABASE_URL=postgresql+asyncpg://helpdesk:your-secure-password@localhost:5432/helpdesk
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_ECHO=false

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000
CHROMA_COLLECTION=it_knowledge_base

# Authentication (보안 키 생성 필수!)
JWT_SECRET_KEY=$(openssl rand -hex 32)  # ← 실제로 실행하여 생성된 값으로 교체
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
FRONTEND_URL=http://your-server-ip:3000
ALLOWED_ORIGINS=["http://your-server-ip:3000"]

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # Production에서는 json 권장

# Application
APP_NAME=IT Helpdesk API
APP_VERSION=1.0.0
MAX_CONVERSATION_TURNS=10
RAG_TOP_K=3
```

**보안 키 생성:**
```bash
# JWT_SECRET_KEY 생성 (32자 이상 필수)
openssl rand -hex 32
# 출력 예: 7f3a8b2c9d1e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a
```

### 2-4. 데이터베이스 마이그레이션

```bash
# Backend 디렉토리에서 실행
cd /opt/it-helpdesk/backend
source .venv/bin/activate

# Alembic 마이그레이션 실행
alembic upgrade head

# 마이그레이션 성공 확인
psql -U helpdesk -d helpdesk -c "\dt"
```

**예상 출력:**
```
          List of relations
 Schema |     Name      | Type  |  Owner  
--------+---------------+-------+---------
 public | users         | table | helpdesk
 public | chat_sessions | table | helpdesk
 public | chat_messages | table | helpdesk
 public | tickets       | table | helpdesk
 public | kb_documents  | table | helpdesk
```

### 2-5. ChromaDB 설치 및 실행

**방법 1: Docker로 실행 (권장)**
```bash
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v /opt/chroma-data:/chroma/chroma \
  chromadb/chroma:latest
```

**방법 2: Python으로 직접 실행**
```bash
pip install chromadb
chroma run --host localhost --port 8000
```

**ChromaDB 연결 확인:**
```bash
curl http://localhost:8000/api/v1/heartbeat
# 출력: {"nanosecond heartbeat": 1234567890}
```

### 2-6. Frontend 설정

```bash
cd /opt/it-helpdesk/frontend

# Node.js 의존성 설치
npm install

# 환경변수 파일 생성
nano .env.local
```

**.env.local 파일:**
```bash
NEXT_PUBLIC_API_URL=http://your-server-ip:8080/api/v1
```

**빌드 및 실행:**
```bash
# 프로덕션 빌드
npm run build

# 빌드 확인
ls -la .next/
```

---

## 3. 서비스 시작 및 중지

### 3-1. Backend 서비스 (systemd)

**서비스 파일 생성:**
```bash
sudo nano /etc/systemd/system/helpdesk-backend.service
```

```ini
[Unit]
Description=IT Helpdesk Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=helpdesk
Group=helpdesk
WorkingDirectory=/opt/it-helpdesk/backend
Environment="PATH=/opt/it-helpdesk/backend/.venv/bin"
ExecStart=/opt/it-helpdesk/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 활성화:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable helpdesk-backend
sudo systemctl start helpdesk-backend

# 상태 확인
sudo systemctl status helpdesk-backend
```

### 3-2. Frontend 서비스 (systemd)

**서비스 파일 생성:**
```bash
sudo nano /etc/systemd/system/helpdesk-frontend.service
```

```ini
[Unit]
Description=IT Helpdesk Frontend
After=network.target

[Service]
Type=simple
User=helpdesk
Group=helpdesk
WorkingDirectory=/opt/it-helpdesk/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**서비스 활성화:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable helpdesk-frontend
sudo systemctl start helpdesk-frontend

# 상태 확인
sudo systemctl status helpdesk-frontend
```

### 3-3. 서비스 제어 명령어

```bash
# 시작
sudo systemctl start helpdesk-backend
sudo systemctl start helpdesk-frontend

# 중지
sudo systemctl stop helpdesk-backend
sudo systemctl stop helpdesk-frontend

# 재시작
sudo systemctl restart helpdesk-backend
sudo systemctl restart helpdesk-frontend

# 상태 확인
sudo systemctl status helpdesk-backend
sudo systemctl status helpdesk-frontend

# 로그 확인
sudo journalctl -u helpdesk-backend -f
sudo journalctl -u helpdesk-frontend -f
```

### 3-4. 서비스 헬스 체크

```bash
# Backend API 헬스 체크
curl http://localhost:8080/health

# 예상 출력:
# {"status":"healthy","environment":"production","version":"1.0.0"}

# Frontend 헬스 체크
curl http://localhost:3000

# ChromaDB 헬스 체크
curl http://localhost:8000/api/v1/heartbeat
```

---

## 4. 관리자 초기 설정

### 4-1. 첫 관리자 계정 생성

시스템 최초 실행 시 관리자 계정을 생성해야 합니다.

**방법 1: Python 스크립트 사용**

```bash
cd /opt/it-helpdesk/backend
source .venv/bin/activate

# 대화형 스크립트로 관리자 생성
python scripts/create_admin.py
```

```python
# scripts/create_admin.py (참고용 - 실제 파일은 별도 생성 필요)
import asyncio
from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import get_password_hash

async def create_admin():
    async for db in get_db():
        admin = User(
            employee_id="ADMIN001",
            email="admin@company.com",
            full_name="시스템 관리자",
            hashed_password=get_password_hash("InitialPassword123!"),
            role=UserRole.ADMIN,
            department="IT",
            is_active=True
        )
        db.add(admin)
        await db.commit()
        print(f"관리자 계정 생성 완료: {admin.email}")

if __name__ == "__main__":
    asyncio.run(create_admin())
```

**방법 2: 직접 SQL 실행**

```bash
psql -U helpdesk -d helpdesk
```

```sql
INSERT INTO users (
    id, employee_id, email, full_name, hashed_password, 
    role, department, is_active, created_at
) VALUES (
    gen_random_uuid(),
    'ADMIN001',
    'admin@company.com',
    '시스템 관리자',
    '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918', -- 'admin' SHA256
    'admin',
    'IT',
    true,
    NOW()
);
```

**⚠️ 중요: 초기 비밀번호 변경**
- 생성 후 즉시 로그인하여 비밀번호를 변경하세요
- 초기 비밀번호: `InitialPassword123!` 또는 `admin`

### 4-2. 시스템 설정 확인

관리자 계정으로 로그인 후:

1. **http://your-server:3000/login** 접속
2. 관리자 계정으로 로그인
3. **/admin/settings** 메뉴로 이동
4. LLM 설정 확인:
   - Provider: Claude (Anthropic)
   - API Key: 마스킹되어 표시 (sk-ant-***)
   - Model: claude-sonnet-4-20250514
   - Status: ● 정상 (초록색)

---

## 5. KB 문서 관리

### 5-1. KB 문서 업로드 (Sprint 2 제공 예정)

현재 Sprint 1에서는 KB 업로드 UI가 미제공됩니다. 수동 업로드 방법:

**Python 스크립트로 업로드:**

```bash
cd /opt/it-helpdesk/backend
source .venv/bin/activate

python scripts/upload_kb.py /path/to/document.pdf "IT 매뉴얼" ADMIN001
```

```python
# scripts/upload_kb.py (예시)
import asyncio
import sys
from pathlib import Path
from app.services.rag import RAGService
from app.db.session import get_db
from app.models.user import User

async def upload_document(file_path: str, title: str, user_id: str):
    async for db in get_db():
        # 파일 읽기
        content = Path(file_path).read_text(encoding='utf-8')
        
        # 사용자 조회
        user = await db.get(User, user_id)
        
        # RAG 서비스로 업로드
        rag = RAGService(db)
        doc = await rag.upload_document(
            file_name=Path(file_path).name,
            file_content=content,
            file_type=Path(file_path).suffix[1:],
            title=title,
            user=user
        )
        print(f"업로드 완료: {doc.id} - {doc.title}")

if __name__ == "__main__":
    file_path, title, user_id = sys.argv[1:4]
    asyncio.run(upload_document(file_path, title, user_id))
```

### 5-2. KB 문서 목록 조회

```bash
# PostgreSQL에서 직접 조회
psql -U helpdesk -d helpdesk -c "SELECT id, title, file_name, chunk_count, created_at FROM kb_documents WHERE is_active = true;"
```

### 5-3. KB 문서 삭제

```bash
# Python 스크립트
python scripts/delete_kb.py <document-id>
```

---

## 6. 사용자 계정 관리

### 6-1. 신규 사용자 생성

**일반 임직원 계정:**
```sql
INSERT INTO users (
    id, employee_id, email, full_name, hashed_password, 
    role, department, is_active, created_at
) VALUES (
    gen_random_uuid(),
    'EMP001',
    'hong@company.com',
    '홍길동',
    encode(digest('초기비밀번호', 'sha256'), 'hex'),
    'employee',
    '개발팀',
    true,
    NOW()
);
```

**IT 담당자 계정:**
```sql
-- role을 'it_staff'로 설정
INSERT INTO users (..., role, ...) VALUES (..., 'it_staff', ...);
```

### 6-2. 사용자 역할 변경

```sql
-- 일반 사용자를 IT 담당자로 승격
UPDATE users SET role = 'it_staff' WHERE employee_id = 'EMP001';

-- IT 담당자를 관리자로 승격
UPDATE users SET role = 'admin' WHERE employee_id = 'IT001';
```

### 6-3. 사용자 비활성화

```sql
-- 퇴사자 계정 비활성화
UPDATE users SET is_active = false WHERE employee_id = 'EMP999';

-- 다시 활성화
UPDATE users SET is_active = true WHERE employee_id = 'EMP999';
```

### 6-4. 비밀번호 초기화

```sql
-- 비밀번호를 'TempPassword123!'으로 초기화
UPDATE users 
SET hashed_password = encode(digest('TempPassword123!', 'sha256'), 'hex')
WHERE employee_id = 'EMP001';
```

---

## 7. LLM 설정 변경

### 7-1. Claude → OpenAI 전환

**Backend 환경변수 수정:**
```bash
sudo nano /opt/it-helpdesk/backend/.env
```

```bash
# LLM Configuration
LLM_PROVIDER=openai              # ← claude에서 openai로 변경
ANTHROPIC_API_KEY=sk-ant-...     # 유지
OPENAI_API_KEY=sk-proj-...       # ← OpenAI API Key 추가
LLM_MODEL=gpt-4o                 # ← 모델 변경
```

**서비스 재시작:**
```bash
sudo systemctl restart helpdesk-backend
```

**동작 확인:**
```bash
# 로그에서 LLM Provider 확인
sudo journalctl -u helpdesk-backend | grep "LLM Provider"
# 출력 예: INFO - LLM Provider initialized: openai
```

### 7-2. 모델 변경

**Claude 모델 변경:**
```bash
LLM_MODEL=claude-opus-4-20250514   # Opus로 변경 (더 정확, 느림)
LLM_MODEL=claude-sonnet-4-20250514 # Sonnet (균형)
LLM_MODEL=claude-haiku-4-20250514  # Haiku (빠름, 저렴)
```

**OpenAI 모델 변경:**
```bash
LLM_MODEL=gpt-4o           # GPT-4 Optimized
LLM_MODEL=gpt-4-turbo      # GPT-4 Turbo
LLM_MODEL=gpt-3.5-turbo    # GPT-3.5 (저렴)
```

### 7-3. 응답 품질 튜닝

```bash
# Temperature 조정 (0.0 ~ 1.0)
LLM_TEMPERATURE=0.3   # 더 일관된 답변 (추천)
LLM_TEMPERATURE=0.7   # 균형
LLM_TEMPERATURE=1.0   # 더 창의적 답변

# Max Tokens 조정
LLM_MAX_TOKENS=512    # 짧은 답변
LLM_MAX_TOKENS=1024   # 표준 (추천)
LLM_MAX_TOKENS=2048   # 긴 설명
```

---

## 8. 모니터링 및 로그

### 8-1. 로그 위치

```bash
# Backend 로그 (systemd)
sudo journalctl -u helpdesk-backend -f

# Frontend 로그
sudo journalctl -u helpdesk-frontend -f

# PostgreSQL 로그
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# ChromaDB 로그 (Docker)
docker logs -f chromadb
```

### 8-2. 주요 모니터링 지표

**시스템 리소스:**
```bash
# CPU, 메모리 사용량
htop

# 디스크 사용량
df -h
du -sh /opt/it-helpdesk/*
```

**데이터베이스 크기:**
```sql
-- PostgreSQL 데이터베이스 크기
SELECT pg_size_pretty(pg_database_size('helpdesk'));

-- 테이블별 크기
SELECT 
    schemaname, 
    tablename, 
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**API 응답 시간:**
```bash
# Health endpoint 응답 시간 측정
time curl http://localhost:8080/health

# Chat endpoint 부하 테스트 (Apache Bench)
ab -n 100 -c 10 http://localhost:8080/health
```

### 8-3. 로그 레벨 조정

```bash
# 환경변수 수정
sudo nano /opt/it-helpdesk/backend/.env

# DEBUG 모드 활성화 (문제 해결 시)
LOG_LEVEL=DEBUG
DB_ECHO=true  # SQL 쿼리 로깅

# 서비스 재시작
sudo systemctl restart helpdesk-backend
```

---

## 9. 백업 및 복구

### 9-1. PostgreSQL 백업

**자동 백업 스크립트:**
```bash
sudo nano /opt/scripts/backup-postgres.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="helpdesk_${DATE}.sql"

mkdir -p $BACKUP_DIR
pg_dump -U helpdesk helpdesk > $BACKUP_DIR/$FILENAME
gzip $BACKUP_DIR/$FILENAME

# 30일 이상 된 백업 삭제
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $FILENAME.gz"
```

**Cron 등록 (매일 02:00):**
```bash
sudo crontab -e

0 2 * * * /opt/scripts/backup-postgres.sh >> /var/log/backup.log 2>&1
```

### 9-2. PostgreSQL 복구

```bash
# 백업 파일 압축 해제
gunzip /opt/backups/postgres/helpdesk_20260401_020000.sql.gz

# 데이터베이스 드롭 및 재생성
sudo -u postgres psql
DROP DATABASE helpdesk;
CREATE DATABASE helpdesk;
GRANT ALL PRIVILEGES ON DATABASE helpdesk TO helpdesk;
\q

# 백업 복원
psql -U helpdesk -d helpdesk < /opt/backups/postgres/helpdesk_20260401_020000.sql
```

### 9-3. ChromaDB 백업

```bash
# ChromaDB 데이터 디렉토리 백업
BACKUP_DIR="/opt/backups/chromadb"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/chroma_${DATE}.tar.gz /opt/chroma-data

# 복원
tar -xzf $BACKUP_DIR/chroma_20260401_020000.tar.gz -C /
```

---

## 10. 문제 해결

### 10-1. Backend 서비스가 시작되지 않음

**증상:** `systemctl status helpdesk-backend` 실행 시 `failed` 상태

**진단:**
```bash
# 상세 로그 확인
sudo journalctl -u helpdesk-backend -n 50

# 수동 실행으로 에러 확인
cd /opt/it-helpdesk/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**원인별 해결:**

1. **`.env` 파일 오류**
   ```
   ERROR: ANTHROPIC_API_KEY is required
   ```
   → `.env` 파일에서 API 키 확인

2. **PostgreSQL 연결 실패**
   ```
   ERROR: could not connect to server
   ```
   → PostgreSQL 서비스 확인: `sudo systemctl status postgresql`
   → DATABASE_URL 확인

3. **포트 충돌**
   ```
   ERROR: [Errno 98] Address already in use
   ```
   → 8080 포트 사용 프로세스 확인: `sudo lsof -i:8080`
   → 프로세스 종료: `sudo kill -9 <PID>`

### 10-2. AI 응답이 느림

**증상:** 채팅 응답이 10초 이상 소요

**진단:**
```bash
# Backend 로그에서 LLM API 호출 시간 확인
sudo journalctl -u helpdesk-backend | grep "LLM API"
```

**원인별 해결:**

1. **ChromaDB 응답 느림**
   ```bash
   # ChromaDB 헬스 체크
   curl http://localhost:8000/api/v1/heartbeat
   
   # 느린 경우 재시작
   docker restart chromadb
   ```

2. **LLM API 타임아웃**
   ```bash
   # 환경변수에서 타임아웃 증가
   LLM_TIMEOUT=30  # .env에 추가
   ```

3. **RAG 검색 개수 과다**
   ```bash
   # 검색 결과 수 줄이기
   RAG_TOP_K=3  # 기본값
   RAG_TOP_K=2  # 더 빠르게
   ```

### 10-3. 로그인 실패

**증상:** "인증 실패" 에러

**진단:**
```bash
# 사용자 계정 확인
psql -U helpdesk -d helpdesk -c "SELECT employee_id, email, is_active FROM users WHERE email='user@company.com';"
```

**해결:**
```sql
-- 계정이 비활성화된 경우
UPDATE users SET is_active = true WHERE email='user@company.com';

-- 비밀번호 초기화
UPDATE users 
SET hashed_password = encode(digest('TempPassword123!', 'sha256'), 'hex')
WHERE email='user@company.com';
```

### 10-4. ChromaDB 연결 실패

**증상:** Backend 로그에 "ChromaDB not available" 경고

**진단:**
```bash
# ChromaDB 프로세스 확인
docker ps | grep chromadb

# ChromaDB 로그 확인
docker logs chromadb
```

**해결:**
```bash
# ChromaDB 재시작
docker restart chromadb

# 재시작 후에도 실패 시 재설치
docker rm -f chromadb
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v /opt/chroma-data:/chroma/chroma \
  chromadb/chroma:latest
```

### 10-5. 디스크 공간 부족

**증상:** "No space left on device" 에러

**진단:**
```bash
# 디스크 사용량 확인
df -h

# 큰 파일 찾기
du -sh /opt/it-helpdesk/* | sort -hr | head -10
du -sh /var/log/* | sort -hr | head -10
```

**해결:**
```bash
# 오래된 로그 삭제
sudo journalctl --vacuum-time=7d

# PostgreSQL 오래된 백업 삭제
find /opt/backups/postgres -name "*.sql.gz" -mtime +30 -delete

# ChromaDB 미사용 데이터 정리 (주의!)
# 이 작업은 서비스 중지 후 수행
sudo systemctl stop helpdesk-backend
docker stop chromadb
# 데이터 정리 후 재시작
docker start chromadb
sudo systemctl start helpdesk-backend
```

---

## 부록 A: 긴급 연락처

| 담당 | 이름 | 연락처 | 역할 |
|---|---|---|---|
| 시스템 관리자 | - | ext. XXXX | 시스템 전반 |
| DB 관리자 | - | ext. YYYY | PostgreSQL |
| 네트워크 관리자 | - | ext. ZZZZ | 방화벽, VPN |
| 외부 업체 | Anthropic Support | support@anthropic.com | Claude API |

---

## 부록 B: 유용한 명령어 모음

```bash
# === 서비스 관리 ===
# 전체 서비스 재시작
sudo systemctl restart helpdesk-backend helpdesk-frontend

# 전체 서비스 상태 확인
sudo systemctl status helpdesk-* --no-pager

# === 로그 확인 ===
# 실시간 로그 (모든 서비스)
sudo journalctl -u helpdesk-* -f

# 오늘 로그만
sudo journalctl -u helpdesk-backend --since today

# 에러 로그만
sudo journalctl -u helpdesk-backend -p err

# === 데이터베이스 ===
# 빠른 연결
psql -U helpdesk helpdesk

# 백업
pg_dump -U helpdesk helpdesk | gzip > backup_$(date +%Y%m%d).sql.gz

# === 성능 모니터링 ===
# 실시간 시스템 상태
htop

# API 응답 시간
time curl http://localhost:8080/health

# 네트워크 연결 확인
netstat -tulpn | grep -E '3000|8080|8000|5432'
```

---

**버전:** v1.0  
**최종 업데이트:** 2026-04-01  
**작성자:** IT 헬프데스크 팀  
**문의:** it-support@company.com
