# IT AI Helpdesk 운영 원칙

> 시스템이 질문을 처리하는 핵심 원칙과 워크플로우를 정의합니다.

---

## 1. 핵심 운영 원칙

### 원칙 1: IT 및 AI 운영 관련 질문만 처리

**목적:** 시스템의 범위를 명확히 하고, 업무와 무관한 질문으로 인한 리소스 낭비 방지

**구현 방식:**
- 모든 사용자 질문은 먼저 **주제 분류(Topic Classification)** 단계를 거침
- LLM을 사용하여 질문이 IT/AI 운영 관련인지 판단
- 범위 밖 질문은 정중하게 거부하고 IT 헬프데스크 용도임을 안내

**허용되는 질문 카테고리:**
```
✅ IT 인프라
  - 네트워크, 서버, 보안, VPN
  - 계정 관리, 권한 요청
  - 하드웨어 (PC, 노트북, 프린터, 주변기기)

✅ 소프트웨어
  - 업무 소프트웨어 설치/사용법
  - 라이선스 문의
  - 버그 신고, 업데이트

✅ AI 시스템 운영
  - 사내 AI 도구 사용법
  - API 키 발급/관리
  - 모델 선택 가이드

✅ 보안 관련
  - 비밀번호 재설정
  - 이상 활동 신고
  - 보안 정책 문의

❌ 범위 밖 (거부)
  - 개인적인 대화
  - 업무와 무관한 질문
  - 타 부서 업무 (인사, 총무 등)
```

**거부 응답 예시:**
```
죄송합니다. 저는 IT 및 AI 운영 관련 질문만 처리할 수 있습니다.

귀하의 질문은 IT 헬프데스크 범위를 벗어나는 것으로 보입니다.
다른 부서의 도움이 필요하시다면 해당 부서에 직접 문의해 주세요.

IT 관련 문의가 있으시면 언제든지 질문해 주세요!
```

---

### 원칙 2: 내부 KB 우선 → 외부 확장 → 담당자 배정

**목적:**
- 내부 지식 기반(KB)을 최우선으로 활용하여 일관된 답변 제공
- KB에 없는 경우에만 외부 LLM 활용
- AI로 해결 불가능한 경우 담당자에게 티켓 생성

**3단계 워크플로우:**

```
┌─────────────────┐
│  사용자 질문     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Step 1: 주제 분류                        │
│ - IT/AI 운영 관련인지 판단              │
│ - 범위 밖이면 거부 응답 → 종료          │
└────────┬────────────────────────────────┘
         │ ✅ IT/AI 관련 질문
         ▼
┌─────────────────────────────────────────┐
│ Step 2: 내부 KB 검색 (RAG)              │
│ - ChromaDB에서 유사 문서 검색           │
│ - Top K개 문서 가져오기 (K=3)           │
│ - 관련도 점수(relevance score) 계산     │
└────────┬────────────────────────────────┘
         │
         ▼
     관련도 충분? (score > threshold)
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    ▼         ▼
┌─────────┐ ┌──────────────────────────────┐
│ Step 3a │ │ Step 3b: 외부 LLM 확장        │
│ KB 기반 │ │ - Claude API로 일반 지식 활용 │
│ 답변 생성│ │ - 답변 생성 시도              │
└────┬────┘ └────┬─────────────────────────┘
     │           │
     └─────┬─────┘
           │
           ▼
       답변 가능?
           │
      ┌────┴────┐
      │         │
     YES       NO
      │         │
      ▼         ▼
┌──────────┐ ┌─────────────────────────────┐
│답변 반환 │ │ Step 4: 티켓 생성 & 담당자  │
│사용자에게│ │ - 자동으로 티켓 생성         │
│         │ │ - 담당자 배정               │
│         │ │ - 사용자에게 티켓 번호 안내  │
└──────────┘ └─────────────────────────────┘
```

---

## 2. 단계별 상세 로직

### Step 1: 주제 분류 (Topic Classification)

**입력:** 사용자 질문 원문

**프롬프트 예시:**
```
다음 질문이 IT 헬프데스크 범위 내의 질문인지 판단해 주세요.

허용 범위: IT 인프라, 소프트웨어, AI 시스템, 보안
거부 대상: 개인 대화, 타 부서 업무

질문: "{user_question}"

응답 형식 (JSON):
{
  "is_it_related": true/false,
  "category": "IT_INFRA|SOFTWARE|AI_SYSTEM|SECURITY|OUT_OF_SCOPE",
  "confidence": 0.0-1.0,
  "reasoning": "판단 근거"
}
```

**출력:**
- `is_it_related: false` → 거부 응답 반환 후 종료
- `is_it_related: true` → Step 2로 진행

**구현 위치:** `backend/app/services/classifier.py`

---

### Step 2: 내부 KB 검색 (RAG)

**입력:**
- 사용자 질문
- 카테고리 정보 (Step 1에서 분류된 결과)

**처리 과정:**
1. 질문을 임베딩 벡터로 변환
2. ChromaDB에서 유사도 검색 (Top K=3)
3. 각 문서의 관련도 점수 계산
4. 임계값(threshold) 이상인 문서가 있는지 확인

**임계값 설정:**
```python
# 설정값 (환경변수로 관리)
RAG_CONFIDENCE_THRESHOLD = 0.75

# 판단 로직
if max_relevance_score >= RAG_CONFIDENCE_THRESHOLD:
    # KB 기반 답변 생성 (Step 3a)
else:
    # 외부 LLM으로 확장 (Step 3b)
```

**구현 위치:** `backend/app/services/rag.py`

---

### Step 3a: KB 기반 답변 생성

**입력:**
- 사용자 질문
- 검색된 관련 문서들 (Top K)

**프롬프트 예시:**
```
당신은 IT 헬프데스크 AI 어시스턴트입니다.
아래의 내부 문서를 참고하여 사용자 질문에 답변해 주세요.

【내부 문서】
{retrieved_documents}

【사용자 질문】
{user_question}

【답변 작성 규칙】
1. 내부 문서의 정보만 사용할 것
2. 문서에 없는 내용은 추측하지 말 것
3. 한국어로 정중하게 답변
4. 구체적인 절차가 있다면 단계별로 설명
5. 답변 끝에 출처 문서 번호 명시

답변:
```

**출력:**
- KB 기반 답변 텍스트
- 출처 문서 ID 목록
- 신뢰도 점수

**구현 위치:** `backend/app/services/chat.py` (generate_answer 메서드)

---

### Step 3b: 외부 LLM 확장

**입력:**
- 사용자 질문
- 카테고리 정보
- (선택) 낮은 점수의 KB 문서들 (참고용)

**프롬프트 예시:**
```
당신은 IT 헬프데스크 AI 어시스턴트입니다.
내부 문서에서 충분한 정보를 찾지 못했으므로, 일반적인 IT 지식을 활용하여 답변합니다.

【사용자 질문】
{user_question}

【카테고리】
{category}

【답변 작성 규칙】
1. 일반적이고 보편적인 IT 지식 활용
2. 회사 특정 정보는 추측하지 말 것
3. 불확실하면 담당자 확인 권장
4. 한국어로 정중하게 답변

답변:
```

**답변 불가 판단 기준:**
- LLM이 "답변 불가" 또는 "담당자 확인 필요"를 명시적으로 반환
- 회사 특정 정보가 필요한 경우 (계정, 권한, 사내 시스템)
- 물리적 조치가 필요한 경우 (하드웨어 수리, 현장 점검)

**출력:**
- 답변 텍스트
- 또는 `requires_human: true` 플래그

**구현 위치:** `backend/app/services/chat.py` (fallback_to_external_llm 메서드)

---

### Step 4: 티켓 생성 & 담당자 배정

**트리거 조건:**
- Step 3b에서 `requires_human: true` 반환
- 사용자가 명시적으로 담당자 연결 요청

**자동 티켓 생성:**
```python
{
  "title": "AI가 해결하지 못한 문의: {질문 요약}",
  "description": "{전체 대화 내용}",
  "category": "{Step 1에서 분류된 카테고리}",
  "priority": "medium",  # 기본값
  "status": "open",
  "created_by": "{user_id}",
  "assigned_to": null,  # 자동 배정 로직 또는 관리자가 수동 배정
}
```

**담당자 배정 로직 (자동):**
```python
# 카테고리별 기본 담당자 매핑
CATEGORY_ASSIGNEE_MAP = {
    "IT_INFRA": "infra_team",
    "SOFTWARE": "software_team",
    "AI_SYSTEM": "ai_team",
    "SECURITY": "security_team",
}

# 담당자 부재 시 관리자에게 배정
```

**사용자 응답:**
```
죄송합니다. 이 문제는 전문 담당자의 도움이 필요합니다.

티켓이 생성되었습니다:
- 티켓 번호: #T-2026-0001
- 담당팀: IT 인프라팀
- 예상 응답 시간: 2시간 이내

담당자가 확인 후 연락드리겠습니다.
티켓 진행 상황은 [티켓 조회] 메뉴에서 확인하실 수 있습니다.
```

**구현 위치:** `backend/app/services/ticket.py`

---

## 3. 구현 체크리스트

### 환경 변수 추가
```env
# AI 응답 설정
RAG_TOP_K=3
RAG_CONFIDENCE_THRESHOLD=0.75
ENABLE_EXTERNAL_LLM=true
AUTO_CREATE_TICKET=true

# 담당자 배정
CATEGORY_ASSIGNEE_MAP={"IT_INFRA":"infra@company.com","SOFTWARE":"dev@company.com"}
DEFAULT_ASSIGNEE=admin@company.com
```

### 데이터베이스 스키마
```sql
-- chat_messages 테이블에 플래그 추가
ALTER TABLE chat_messages ADD COLUMN is_kb_based BOOLEAN DEFAULT false;
ALTER TABLE chat_messages ADD COLUMN source_documents TEXT[];  -- KB 문서 ID 목록
ALTER TABLE chat_messages ADD COLUMN confidence_score FLOAT;
```

### 서비스 레이어 구조
```
backend/app/services/
├── classifier.py       # Step 1: 주제 분류
├── rag.py             # Step 2: KB 검색
├── chat.py            # Step 3: 답변 생성 (KB 기반 + 외부 LLM)
└── ticket.py          # Step 4: 티켓 생성
```

### API 응답 형식
```json
{
  "message_id": "msg-123",
  "content": "답변 내용...",
  "metadata": {
    "is_kb_based": true,
    "source_documents": ["doc-001", "doc-002"],
    "confidence_score": 0.85,
    "ticket_created": false
  }
}
```

---

## 4. 운영 지표 (Metrics)

시스템 성능을 측정하기 위한 핵심 지표:

```python
# 추적할 메트릭
{
  "total_questions": 1000,           # 전체 질문 수
  "out_of_scope": 50,                # 범위 밖 질문 (5%)
  "kb_resolved": 700,                # KB로 해결 (70%)
  "external_llm_resolved": 200,      # 외부 LLM으로 해결 (20%)
  "tickets_created": 50,             # 티켓 생성 (5%)
  "avg_kb_confidence": 0.82,         # 평균 KB 신뢰도
  "avg_response_time_ms": 1500,      # 평균 응답 시간
}
```

**목표 수치:**
- KB 해결률: 70% 이상
- 티켓 생성률: 10% 이하
- 범위 밖 질문: 5% 이하

---

## 5. 프롬프트 템플릿 관리

모든 프롬프트는 DB 또는 설정 파일로 관리하여 운영 중 수정 가능하게 함

**위치:** `backend/app/prompts/`
```
prompts/
├── classifier.yaml     # 주제 분류 프롬프트
├── kb_answer.yaml      # KB 기반 답변 프롬프트
├── external_llm.yaml   # 외부 LLM 프롬프트
└── rejection.yaml      # 거부 응답 템플릿
```

**YAML 예시:**
```yaml
# classifier.yaml
name: topic_classification
version: "1.0"
prompt: |
  다음 질문이 IT 헬프데스크 범위 내의 질문인지 판단해 주세요.

  허용 범위: IT 인프라, 소프트웨어, AI 시스템, 보안
  거부 대상: 개인 대화, 타 부서 업무

  질문: "{user_question}"

  응답 형식 (JSON):
  {{
    "is_it_related": true/false,
    "category": "IT_INFRA|SOFTWARE|AI_SYSTEM|SECURITY|OUT_OF_SCOPE",
    "confidence": 0.0-1.0,
    "reasoning": "판단 근거"
  }}

examples:
  - question: "VPN 접속이 안 돼요"
    output: {"is_it_related": true, "category": "IT_INFRA"}
  - question: "오늘 점심 메뉴가 뭐예요?"
    output: {"is_it_related": false, "category": "OUT_OF_SCOPE"}
```

---

## 6. 테스트 시나리오

### 시나리오 1: KB 기반 정상 답변
```
입력: "VPN 접속이 안 되는데 어떻게 해야 하나요?"
예상 결과:
  - Step 1: IT_INFRA 분류
  - Step 2: KB에서 VPN 문서 검색 (confidence: 0.9)
  - Step 3a: KB 기반 답변 반환
  - 티켓 생성: 없음
```

### 시나리오 2: 외부 LLM 확장
```
입력: "Python에서 JSON 파일을 읽는 방법을 알려주세요"
예상 결과:
  - Step 1: SOFTWARE 분류
  - Step 2: KB에서 관련 문서 없음 (confidence: 0.3)
  - Step 3b: 외부 LLM으로 일반 프로그래밍 지식 답변
  - 티켓 생성: 없음
```

### 시나리오 3: 티켓 생성
```
입력: "제 PC가 부팅이 안 되는데 확인해 주세요"
예상 결과:
  - Step 1: IT_INFRA 분류
  - Step 2: KB에서 부분적 정보만 (confidence: 0.5)
  - Step 3b: 물리적 조치 필요 판단 (requires_human: true)
  - Step 4: 티켓 생성 (#T-2026-0001, 담당팀: IT 인프라)
```

### 시나리오 4: 범위 밖 거부
```
입력: "내일 회의실 예약 가능한가요?"
예상 결과:
  - Step 1: OUT_OF_SCOPE 분류
  - 거부 응답 반환 (총무팀 문의 안내)
  - 종료
```

---

## 7. 구현 우선순위

**Phase 1 (Sprint 1):** 기본 플로우 구축
1. ✅ Step 1: 주제 분류 (간단한 키워드 기반)
2. ✅ Step 3b: 외부 LLM 직접 호출 (KB 없이 먼저 구현)
3. ✅ 기본 채팅 인터페이스

**Phase 2 (Sprint 2):** RAG 시스템 추가
1. ✅ ChromaDB 연동
2. ✅ Step 2: KB 검색 구현
3. ✅ Step 3a: KB 기반 답변 생성
4. ✅ 신뢰도 점수 기반 플로우 분기

**Phase 3 (Sprint 3):** 티켓 시스템 연동
1. ✅ Step 4: 자동 티켓 생성
2. ✅ 담당자 배정 로직
3. ✅ 티켓 상태 추적

**Phase 4 (Sprint 4):** 운영 최적화
1. ✅ 프롬프트 관리 시스템
2. ✅ 메트릭 수집 및 대시보드
3. ✅ A/B 테스트 (임계값 조정)

---

이 문서는 시스템의 핵심 작동 원칙을 정의합니다.
모든 구현은 이 원칙을 준수해야 하며, 변경이 필요한 경우 문서를 먼저 업데이트합니다.
