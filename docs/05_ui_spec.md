# 05. UI Spec

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

## Route Behavior

### `/`

- Redirects to `/auth/login`

### `/auth/login`

- Employee ID and password login form
- Successful login navigates to `/chat`

### `/auth/register`

- Self-service registration form
- Successful registration navigates to `/auth/login`

### `/chat`

- Left panel: chat sessions
- Main panel: current conversation
- Ticket creation from a selected conversation

Current gap:

- No SSE/streaming response UI yet

### `/tickets`

- Ticket table
- Status/category filters
- IT staff quick actions
- Row click navigates to detail page

### `/tickets/[id]`

- Ticket header and metadata
- Description
- Comments
- Comment form
- IT staff edit controls

### `/kb`

- File upload
- Document list
- Search panel
- Detail panel

### `/admin`

- Dashboard summary cards
- Recent activities

### `/admin/users`

- User list
- Filters
- Inline edit modal

### `/admin/settings`

- Runtime LLM and RAG configuration
- Save and reset interactions

## Shared UI Components

- `AuthProvider`
- `ErrorBoundary`
- `TicketQuickActions`
