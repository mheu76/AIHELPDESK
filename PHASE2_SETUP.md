# Phase 2 Setup - Frontend Development

This document covers the frontend setup and integration with the backend API.

## Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`
- PostgreSQL database configured
- ChromaDB running on `http://localhost:8000`

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Features Implemented

### Authentication
- **Login Page** (`/auth/login`): Employee ID + password authentication
- **Register Page** (`/auth/register`): New user registration
- **JWT Token Management**: Access/refresh tokens stored in localStorage
- **Protected Routes**: Auto-redirect to login if not authenticated

### Chat Interface
- **Session Management**: Create new chat sessions, view session history
- **Real-time Messaging**: Send messages and receive AI responses
- **RAG Integration**: AI responses are enhanced with knowledge base context
- **Session History**: View and continue previous conversations
- **Responsive Design**: Mobile-friendly interface

### API Client
- **Type-safe API**: Full TypeScript types for all endpoints
- **Error Handling**: Structured error responses with error codes
- **Token Injection**: Automatic auth token inclusion from localStorage

## Project Structure

```
frontend/
├── app/
│   ├── auth/
│   │   ├── login/page.tsx          # Login page
│   │   ├── register/page.tsx       # Registration page
│   │   └── layout.tsx              # Auth layout
│   ├── chat/
│   │   ├── page.tsx                # Main chat interface
│   │   └── layout.tsx              # Protected chat layout
│   ├── layout.tsx                  # Root layout with AuthProvider
│   ├── page.tsx                    # Home page (redirects to login)
│   └── globals.css                 # Global styles
├── components/
│   └── auth-provider.tsx           # Auth context provider
├── lib/
│   ├── api.ts                      # API client functions
│   └── auth.ts                     # Auth helpers
└── tailwind.config.ts              # Tailwind configuration
```

## API Integration

### Auth API

```typescript
import { authApi } from "@/lib/api"

// Login
const response = await authApi.login("EMP001", "password123")
// Returns: { access_token, refresh_token, user }

// Register
await authApi.register({
  employee_id: "EMP001",
  email: "user@company.com",
  full_name: "John Doe",
  password: "password123"
})

// Get current user
const user = await authApi.getMe(accessToken)

// Refresh token
const newToken = await authApi.refreshToken(refreshToken)
```

### Chat API

```typescript
import { chatApi } from "@/lib/api"

// Send message (creates new session if sessionId is null)
const response = await chatApi.sendMessage("How do I reset my password?", sessionId)
// Returns: { session_id, message, is_resolved }

// Get session list
const sessions = await chatApi.getSessions()

// Get session detail with messages
const sessionDetail = await chatApi.getSessionDetail(sessionId)

// Mark session as resolved
await chatApi.markSessionResolved(sessionId, true)
```

### Knowledge Base API

```typescript
import { kbApi } from "@/lib/api"

// Upload document (admin only)
await kbApi.uploadDocument(file, "Optional Title")

// List documents
const docs = await kbApi.listDocuments()

// Search knowledge base
const results = await kbApi.search("password reset", 5)

// Delete document
await kbApi.deleteDocument(docId)
```

## Testing the Frontend

### 1. Test Authentication Flow

1. Navigate to `http://localhost:3000`
2. You'll be redirected to `/auth/login`
3. Register a new account at `/auth/register`:
   - Employee ID: `EMP001`
   - Email: `test@company.com`
   - Full Name: `Test User`
   - Password: `Test123!@#`
4. Login with the registered credentials
5. You should be redirected to `/chat`

### 2. Test Chat Interface

1. Click "New Chat" button
2. Type a test message: "How do I reset my password?"
3. AI should respond with relevant information
4. If you uploaded KB documents, they will be used for context
5. Check session list in the sidebar

### 3. Test Session Management

1. Start multiple conversations
2. Switch between sessions in the sidebar
3. Verify messages are preserved
4. Check session titles and timestamps

## Common Issues

### Issue: "Failed to fetch" errors

**Solution**: Ensure backend API is running on `http://localhost:8000`

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Issue: CORS errors

**Solution**: Backend CORS is configured to allow `http://localhost:3000`. If using a different port, update `backend/app/core/config.py`:

```python
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",  # Add your port
]
```

### Issue: Authentication not persisting

**Solution**: Check browser localStorage. Clear it and login again:

```javascript
// In browser console
localStorage.clear()
```

### Issue: Tailwind styles not loading

**Solution**: Restart the dev server:

```bash
npm run dev
```

## Next Steps

### Phase 3: Ticket System (Backend)
- Create ticket models and endpoints
- Implement ticket creation from unresolved chats
- Add ticket assignment to IT staff
- Build ticket management APIs

### Phase 3: Ticket System (Frontend)
- Create ticket list page
- Build ticket detail view
- Add ticket management UI for IT staff/admin
- Implement ticket status updates

### Phase 4: Admin Dashboard
- Knowledge base management UI
- User management interface
- System statistics and analytics
- LLM provider switching UI

## Development Tips

1. **Hot Reload**: Next.js automatically reloads on file changes
2. **Type Safety**: Use TypeScript types from `lib/api.ts`
3. **Error Handling**: Wrap API calls in try/catch and use `ApiError` type
4. **Auth State**: Use `useAuth()` hook for authentication
5. **Protected Routes**: Wrap pages in layout.tsx with auth checks

## Build for Production

```bash
# Build the frontend
npm run build

# Start production server
npm start
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Backend API URL |

## API Documentation

For detailed API documentation, see `docs/04_api_spec.md`.

## Component Documentation

### AuthProvider

Manages authentication state globally:

```typescript
const { user, isLoading, login, logout, refreshAuth } = useAuth()
```

### API Client

All API functions automatically inject auth tokens from localStorage. For endpoints requiring authentication, the token is read from `localStorage.getItem('access_token')`.

## Troubleshooting

### Check Backend Logs

```bash
cd backend
tail -f logs/app.log
```

### Check Browser Console

Press F12 and check for JavaScript errors or failed network requests.

### Verify Database Connection

```bash
cd backend
python -c "from app.db.session import engine; print('DB OK')"
```

### Verify ChromaDB Connection

```bash
curl http://localhost:8000/api/v1/heartbeat
```

---

**Phase 2 Complete!** 🎉

Frontend is now fully integrated with backend RAG system. Users can:
- Register and login
- Start AI-assisted IT support conversations
- View conversation history
- Benefit from knowledge base context in AI responses
