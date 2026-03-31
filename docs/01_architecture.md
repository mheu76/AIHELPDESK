# 01. 시스템 아키텍처

---

## 1. 전체 구성도

```
┌─────────────────────────────────────────────────────────┐
│                     사내 네트워크                          │
│                                                          │
│  [임직원 브라우저]                                          │
│       │ HTTPS                                            │
│       ▼                                                  │
│  ┌─────────────┐                                         │
│  │  Next.js    │  Frontend (Port 3000)                   │
│  │  Web App    │  - 채팅 UI                               │
│  │             │  - 티켓 조회                              │
│  │             │  - 관리자 화면                             │
│  └──────┬──────┘                                         │
│         │ REST API (HTTPS)                               │
│         ▼                                                │
│  ┌─────────────┐     ┌──────────────┐                   │
│  │  FastAPI    │────▶│  ChromaDB    │  Vector DB         │
│  │  Backend    │     │  (Port 8000) │  - KB 문서 임베딩   │
│  │  (Port 8080)│     └──────────────┘                   │
│  │             │     ┌──────────────┐                   │
│  │             │────▶│  PostgreSQL  │  RDBMS             │
│  │             │     │  (Port 5432) │  - 티켓, 유저, 이력 │
│  └──────┬──────┘     └──────────────┘                   │
│         │ HTTPS (외부)                                    │
│         ▼                                                │
│  ┌─────────────┐                                         │
│  │  Claude API │  LLM (교체 가능)                         │
│  │  (Anthropic)│                                         │
│  └─────────────┘                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 요청 처리 흐름

### 2-1. 일반 AI 채팅 응답

```
임직원 질문 입력
    │
    ▼
[Backend] 질문 수신
    │
    ▼
[RAG] ChromaDB에서 관련 KB 문서 검색 (Top-K)
    │
    ▼
[LLM Layer] 검색된 문서 + 질문 → Claude API 호출
    │
    ├─ 해결 가능 → AI 답변 반환 + 대화 이력 저장
    │
    └─ 해결 불가 → "티켓 생성하시겠습니까?" 안내
```

### 2-2. 티켓 생성 흐름

```
임직원 티켓 생성 요청
    │
    ▼
[Backend] 대화 내용 요약 (Claude API)
    │
    ▼
[DB] 티켓 생성 (PostgreSQL)
    │
    ▼
[알림] IT 담당자에게 새 티켓 알림 (이메일 or 내부 알림)
    │
    ▼
[IT 담당자] 티켓 확인 → 처리 → 상태 업데이트
```

---

## 3. LLM 추상화 레이어

> Provider 교체 시 `LLM_PROVIDER` 환경변수 값만 변경하면 됩니다.

```python
# backend/app/core/llm/base.py
from abc import ABC, abstractmethod

class LLMBase(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], context: str = "") -> str:
        """RAG context를 포함한 채팅 응답"""
        pass

    @abstractmethod
    async def summarize(self, text: str) -> str:
        """티켓 생성을 위한 대화 요약"""
        pass

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """KB 문서 임베딩 (ChromaDB 저장용)"""
        pass
```

```python
# backend/app/core/llm/claude.py
import anthropic
from .base import LLMBase

class ClaudeLLM(LLMBase):
    def __init__(self):
        self.client = anthropic.AsyncAnthropic()
        self.model = "claude-sonnet-4-20250514"

    async def chat(self, messages: list[dict], context: str = "") -> str:
        system_prompt = f"""
        당신은 IT Helpdesk AI 어시스턴트입니다.
        아래 참고 문서를 바탕으로 임직원의 IT 문의에 답변하세요.
        참고 문서에 없는 내용은 모른다고 답하고 티켓 생성을 안내하세요.

        [참고 문서]
        {context}
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
```

---

## 4. RAG 처리 흐름

```
[KB 문서 업로드] (관리자)
    │
    ▼
텍스트 추출 (PDF/DOCX/TXT)
    │
    ▼
청크 분할 (Chunk Size: 500 tokens, Overlap: 50)
    │
    ▼
임베딩 생성 (Claude Embeddings API)
    │
    ▼
ChromaDB 저장 (컬렉션: "it_knowledge_base")

────────────────────────────────

[임직원 질문 수신]
    │
    ▼
질문 임베딩 생성
    │
    ▼
ChromaDB 유사도 검색 (Top-3 문서)
    │
    ▼
검색 결과 → LLM 프롬프트 컨텍스트로 주입
```

---

## 5. 배포 구성 (Docker Compose)

```yaml
# docker-compose.yml 구조
services:
  frontend:     # Next.js (Port 3000)
  backend:      # FastAPI (Port 8080)
  chromadb:     # ChromaDB (Port 8000)
  postgres:     # PostgreSQL (Port 5432)

# 모든 서비스는 사내 서버 단일 호스트에서 실행
# 외부 인터넷 접근: Claude API만 허용 (방화벽 설정 필요)
```

---

## 6. 보안 고려사항

| 항목 | 적용 방안 |
|---|---|
| 인증 | JWT 토큰 (추후 SSO 연동) |
| API 키 보호 | 환경변수, 절대 코드에 하드코딩 금지 |
| 사내망 격리 | 내부 IP만 접근 허용 (Nginx 설정) |
| Claude API 통신 | HTTPS, 사내 데이터 최소화 전송 |
| DB 암호화 | PostgreSQL TLS 연결 |
