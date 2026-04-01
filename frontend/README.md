# Frontend

Next.js 14 App Router 기반 프론트엔드입니다.

## 현재 구현 화면

- `/auth/login`
- `/auth/register`
- `/chat`
- `/tickets`
- `/tickets/[id]`
- `/kb`

루트 `/`는 `/auth/login`으로 리다이렉트됩니다.

## 실행

```bash
cd frontend
npm install
npm run dev
```

또는 루트에서 Docker:

```bash
docker compose up --build
```

## 환경 변수

필수:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## 현재 프론트 기능

- 로그인/회원가입
- 토큰 기반 인증 상태 유지
- 채팅 세션 목록 및 대화 화면
- 채팅에서 티켓 생성
- 티켓 목록 필터링
- 티켓 상세 조회 및 댓글 작성
- IT 담당자의 빠른 티켓 처리 버튼
- KB 문서 업로드, 검색, 상세 조회, 삭제

## 현재 제약

- 관리자 대시보드 화면은 아직 없음
- 채팅 응답은 단건 응답 방식이며 SSE 스트리밍 UI는 아직 없음
- 일부 화면 문자열은 한글 인코딩 정리가 더 필요함
- 타입 일부는 백엔드 응답 구조와 완전히 일치하지 않는 호환 필드를 포함함

## 주요 파일

- [frontend/lib/api.ts](/D:/DEV/AIhelpdesk/frontend/lib/api.ts)
- [frontend/lib/auth.ts](/D:/DEV/AIhelpdesk/frontend/lib/auth.ts)
- [frontend/app/chat/page.tsx](/D:/DEV/AIhelpdesk/frontend/app/chat/page.tsx)
- [frontend/app/tickets/page.tsx](/D:/DEV/AIhelpdesk/frontend/app/tickets/page.tsx)
- [frontend/app/tickets/[id]/page.tsx](/D:/DEV/AIhelpdesk/frontend/app/tickets/[id]/page.tsx)
- [frontend/app/kb/page.tsx](/D:/DEV/AIhelpdesk/frontend/app/kb/page.tsx)
