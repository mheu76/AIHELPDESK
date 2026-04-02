# Phase 2 Setup Guide

Last updated: `2026-04-02`

This document records the current frontend setup for the IT AI Helpdesk project.

## Scope

Phase 2 is the Next.js application used by employees, IT staff, and admins.

Implemented route groups:

- auth
- chat
- tickets
- knowledge base
- admin

## Prerequisites

- Node.js 20+
- Backend API running on `http://localhost:8080`

## Local Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL:

- `http://localhost:3000`

## Environment

Create `.env.local` with:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## Current Routes

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

## Current Frontend Behavior

- Root `/` redirects to `/auth/login`
- Authentication state is managed by `AuthProvider`
- Access and refresh tokens are stored client-side
- Ticket list/detail and KB pages are stabilized and type-checked
- Admin settings page reads and writes persistent backend runtime settings

## Validation

Run:

```bash
cd frontend
npm run lint
```

Verified result on `2026-04-02`:

- type-check pass

## Current Gaps

- No frontend automated tests yet
- Chat page still needs UX cleanup
- SSE chat streaming UI is not implemented
- Token refresh and route guards can be centralized further
