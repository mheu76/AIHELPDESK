# Frontend

Next.js 14 App Router frontend for the IT AI Helpdesk project.

## Routes

- `/`
- `/auth/login`
- `/auth/register`
- `/chat`
- `/tickets`
- `/tickets/[id]`
- `/kb`
- `/admin`
- `/admin/users`
- `/admin/settings`

Root `/` redirects to `/auth/login`.

## Run

```bash
cd frontend
npm install
npm run dev
```

## Environment

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## Current Status

- Auth flow is wired through `AuthProvider`
- Chat, ticket, KB, and admin pages are present
- Ticket list/detail and KB pages were stabilized and type-checked
- Verified type-check passes on `2026-04-02`

## Known Gaps

- Chat page still needs UX cleanup and streaming support
- There are no frontend automated tests yet
- Token refresh and route guarding can be centralized further
