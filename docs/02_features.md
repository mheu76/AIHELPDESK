# 02. Features

## Completed

- User registration, login, token refresh, current-user lookup
- Chat session creation and continuation
- Chat session listing and detail retrieval
- Chat session resolve/unresolve
- Knowledge base upload, list, detail, delete, search
- Ticket creation from chat sessions
- Ticket list, detail, update, comments, and statistics
- Admin dashboard
- Admin user management
- Admin system settings backed by the database
- Docker local development stack
- Backend automated tests
- Frontend type-check

## Partially Implemented

- RAG quality depends on ChromaDB availability
- Ticket title/category generation depends on LLM success and falls back safely
- Frontend admin pages exist but still need UX hardening
- Chat page works but still needs cleanup and streaming UX

## Not Implemented

- SSE streaming chat
- Frontend automated tests
- Error tracking integration
- CI/CD
- Production deployment playbooks

## Roles

### Employee

- Access own chat sessions
- Access own tickets
- Add public comments to own tickets
- Search and read KB documents

### IT Staff

- All employee capabilities
- View all tickets
- Update ticket workflow fields
- Add internal comments
- Upload and delete KB documents
- View ticket statistics

### Admin

- All IT staff capabilities
- View admin dashboard
- Manage users
- Manage persistent system settings
