# 09. Admin Manual

현재 레포 기준으로 실제 운영/개발 관리자가 사용할 수 있는 항목만 정리합니다.

## 1. 개발 환경 시작

권장 방식:

```bash
docker compose up --build
```

기본 주소:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8080`
- Swagger: `http://localhost:8080/docs`

종료:

```bash
docker compose down
```

DB 볼륨까지 제거:

```bash
docker compose down -v
```

## 2. 백엔드 로컬 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## 3. 환경 변수 관리

주요 파일:

- 개발 일반: [backend/.env.example](/D:/DEV/AIhelpdesk/backend/.env.example)
- Docker 개발: [backend/.env.docker](/D:/DEV/AIhelpdesk/backend/.env.docker)

반드시 점검할 값:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `LLM_PROVIDER`
- `ANTHROPIC_API_KEY` 또는 `OPENAI_API_KEY`
- `FRONTEND_URL`
- `ALLOWED_ORIGINS`

## 4. 마이그레이션

초기 스키마 또는 최신 스키마 반영:

```bash
cd backend
alembic upgrade head
```

현재 초기 스키마에는 다음이 포함됩니다.

- users
- chat_sessions
- chat_messages
- kb_documents
- tickets
- ticket_comments

## 5. 테스트 실행

```bash
cd backend
pytest
```

특정 범위:

```bash
pytest tests/unit/test_api_auth.py
pytest tests/unit/test_api_chat.py
pytest tests/unit/test_api_kb.py
pytest tests/unit/test_api_ticket.py
```

## 6. 계정과 권한

현재 별도 관리자 UI는 없습니다. 권한 제어는 DB 데이터 기준입니다.

역할 값:

- `employee`
- `it_staff`
- `admin`

직접 계정 생성/수정이 필요하면 DB 또는 기존 유틸 스크립트를 사용해야 합니다.

레포 내 유틸 예시:

- [backend/create_test_users.py](/D:/DEV/AIhelpdesk/backend/create_test_users.py)
- [backend/quick_create_user.py](/D:/DEV/AIhelpdesk/backend/quick_create_user.py)
- [backend/update_user_role.py](/D:/DEV/AIhelpdesk/backend/update_user_role.py)

사용 전 환경 변수를 먼저 맞춰야 합니다.

## 7. KB 운영

권한:

- 업로드/삭제: `it_staff`, `admin`
- 목록/상세/검색: 인증 사용자 전체

현재 UI:

- `/kb`

지원 형식:

- PDF
- DOCX
- TXT
- MD

파일 제한:

- 최대 10MB

## 8. 티켓 운영

권한:

- 직원: 본인 티켓 조회/공개 댓글
- IT/Admin: 전체 티켓 조회, 내부 메모, 상태 변경, 담당자 지정, 통계 조회

현재 UI:

- `/tickets`
- `/tickets/[id]`

현재 API:

- `POST /api/v1/tickets`
- `GET /api/v1/tickets`
- `GET /api/v1/tickets/{id}`
- `PATCH /api/v1/tickets/{id}`
- `POST /api/v1/tickets/{id}/comments`
- `GET /api/v1/tickets/stats/overview`

## 9. 장애 확인 포인트

### API 서버 확인

```bash
curl http://localhost:8080/health
```

### Docker 로그

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### 흔한 문제

- `401`: 토큰 없음 또는 만료
- `403`: 역할 부족
- KB 검색 품질 저하: ChromaDB 미연결 상태일 수 있음
- LLM 호출 실패: API 키 또는 외부 네트워크 문제

## 10. 현재 운영상 제한

- 완전한 운영 배포 문서는 아직 없음
- 관리자 대시보드/설정 UI는 아직 없음
- 알림, 백업 자동화, 모니터링 체계는 수동 수준
