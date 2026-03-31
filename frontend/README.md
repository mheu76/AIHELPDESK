# IT Helpdesk Frontend

Next.js 14-based frontend application for IT AI Helpdesk system.

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create a `.env.local` file:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080/api/v1
```

## Running the Application

### Development Server

```bash
cd frontend
npm run dev
```

The application will be available at http://localhost:3000

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── lib/                   # Core utilities (harness)
│   ├── api.ts            # API client with auth
│   └── auth.ts           # Auth helpers
├── components/            # React components
│   └── ErrorBoundary.tsx # Global error handler
├── app/                   # Next.js App Router pages (to be added)
├── package.json
├── tsconfig.json
└── next.config.js
```

## Harness Features

The frontend harness provides:

✅ **API Client** - Centralized API calls with automatic token injection
✅ **Error Handling** - Custom APIError class with error codes
✅ **Auth Helpers** - Token management and authentication state
✅ **Error Boundary** - Global React error catching
✅ **TypeScript** - Type-safe API calls and state management
✅ **SSE Streaming** - Async generator for real-time chat responses

## API Client Usage

### Login Example

```typescript
import { api, APIError } from '@/lib/api';
import { saveAuthState } from '@/lib/auth';

try {
  const result = await api.auth.login('user@company.com', 'password');
  saveAuthState({
    user: result.user,
    accessToken: result.access_token,
    refreshToken: result.refresh_token,
  });
  console.log('Login success:', result.user);
} catch (error) {
  if (error instanceof APIError) {
    console.error(`[${error.errorCode}]:`, error.message);
  }
}
```

### Chat Streaming Example

```typescript
import { api } from '@/lib/api';

const sessionId = 'some-session-id';

for await (const event of api.chat.streamMessage(sessionId, 'Hello AI')) {
  if (event.type === 'token') {
    console.log('Token:', event.content);
  } else if (event.type === 'done') {
    console.log('Message complete:', event.message_id);
  }
}
```

## Error Boundary Usage

Wrap your app with ErrorBoundary:

```typescript
import { ErrorBoundary } from '@/components/ErrorBoundary';

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </body>
    </html>
  );
}
```

## Authentication Flow

1. User logs in → `api.auth.login()`
2. Save tokens → `saveAuthState()`
3. API client auto-injects token in subsequent requests
4. On 401 error → Refresh token or redirect to login

## Next Steps

After the harness is complete, the next implementation steps are:

1. **App Router Pages** - Create login, chat, tickets pages
2. **UI Components** - Chat bubbles, ticket cards, forms
3. **State Management** - Zustand for global state
4. **Styling** - Tailwind CSS and shadcn/ui components
5. **Real-time Features** - SSE event handling for chat

## Type Safety

All API calls are type-safe:

```typescript
// TypeScript knows the response shape
const response: LoginResponse = await api.auth.login(email, password);
console.log(response.user.name); // ✅ Type-safe

const sessions = await api.chat.getSessions();
sessions.sessions.forEach(s => {
  console.log(s.title); // ✅ Type-safe
});
```

## Troubleshooting

### API Connection Issues

Make sure backend is running:
```bash
curl http://localhost:8080/health
```

Check NEXT_PUBLIC_API_URL in `.env.local`

### CORS Errors

Backend must include frontend URL in ALLOWED_ORIGINS:
```env
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### TypeScript Errors

Run type checking:
```bash
npm run type-check
```
