# 03. DB 스키마

> RDBMS: PostgreSQL 15+
> ORM: SQLAlchemy (async) + Alembic (migration)

---

## 1. ERD 개요

```
users ──────────────┐
  │                 │
  ├── chat_sessions │
  │     └── chat_messages
  │                 │
  └── tickets ◀─────┘
        └── ticket_comments
```

---

## 2. 테이블 정의

### 2-1. users (사용자)

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     VARCHAR(20) UNIQUE NOT NULL,   -- 사번
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    role            VARCHAR(20) NOT NULL DEFAULT 'employee',
                    -- employee | it_staff | admin
    department      VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 2-2. chat_sessions (채팅 세션)

```sql
CREATE TABLE chat_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    title           VARCHAR(255),                  -- AI가 자동 생성 (첫 질문 기반)
    is_resolved     BOOLEAN DEFAULT FALSE,         -- AI 해결 여부
    ticket_id       UUID REFERENCES tickets(id),   -- 티켓 전환 시 연결
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 2-3. chat_messages (채팅 메시지)

```sql
CREATE TABLE chat_messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES chat_sessions(id),
    role            VARCHAR(20) NOT NULL,          -- user | assistant
    content         TEXT NOT NULL,
    token_count     INTEGER,                       -- LLM 토큰 사용량 추적
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);
```

---

### 2-4. tickets (티켓)

```sql
CREATE TABLE tickets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_number   SERIAL UNIQUE,                 -- T-000001 형식 표시용
    title           VARCHAR(500) NOT NULL,         -- AI 자동 생성
    description     TEXT NOT NULL,                 -- AI 요약 내용
    category        VARCHAR(50) NOT NULL,
                    -- account | device | network | system | security | other
    status          VARCHAR(20) NOT NULL DEFAULT 'open',
                    -- open | in_progress | resolved | on_hold | closed
    priority        VARCHAR(20) DEFAULT 'medium',  -- low | medium | high | urgent
    requester_id    UUID NOT NULL REFERENCES users(id),
    assignee_id     UUID REFERENCES users(id),     -- IT 담당자
    session_id      UUID REFERENCES chat_sessions(id),
    resolved_at     TIMESTAMP WITH TIME ZONE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_assignee_id ON tickets(assignee_id);
CREATE INDEX idx_tickets_requester_id ON tickets(requester_id);
```

---

### 2-5. ticket_comments (티켓 코멘트)

```sql
CREATE TABLE ticket_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id       UUID NOT NULL REFERENCES tickets(id),
    author_id       UUID NOT NULL REFERENCES users(id),
    content         TEXT NOT NULL,
    is_internal     BOOLEAN DEFAULT FALSE,         -- 내부 메모 (임직원 비공개)
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 2-6. kb_documents (KB 문서)

```sql
CREATE TABLE kb_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title           VARCHAR(500) NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_type       VARCHAR(20) NOT NULL,          -- pdf | docx | txt | md
    file_size       INTEGER,                       -- bytes
    chunk_count     INTEGER DEFAULT 0,             -- ChromaDB 청크 수
    chroma_ids      TEXT[],                        -- ChromaDB document IDs
    uploaded_by     UUID REFERENCES users(id),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 2-7. system_settings (시스템 설정)

```sql
CREATE TABLE system_settings (
    key             VARCHAR(100) PRIMARY KEY,
    value           TEXT NOT NULL,
    description     VARCHAR(500),
    updated_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 초기 데이터
INSERT INTO system_settings (key, value, description) VALUES
('llm_provider', 'claude', 'LLM Provider: claude | openai'),
('llm_model', 'claude-sonnet-4-20250514', 'LLM 모델명'),
('rag_top_k', '3', 'RAG 검색 결과 수'),
('max_conversation_turns', '10', '대화 맥락 유지 턴 수');
```

---

## 3. ChromaDB 컬렉션

```python
# 컬렉션명: it_knowledge_base
# 메타데이터 구조:
{
    "document_id": "uuid",          # kb_documents.id
    "title": "문서 제목",
    "chunk_index": 0,               # 청크 순서
    "file_type": "pdf",
    "created_at": "2025-01-01"
}
```

---

## 4. 마이그레이션 전략

```bash
# 초기 마이그레이션
alembic init migrations
alembic revision --autogenerate -m "initial schema"
alembic upgrade head

# 스키마 변경 시
alembic revision --autogenerate -m "description"
alembic upgrade head
```
