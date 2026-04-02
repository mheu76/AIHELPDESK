# Chat Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real-time streaming chat responses for Anthropic Claude with typing animation and partial error recovery.

**Architecture:** New `/chat/stream` endpoint yields NDJSON chunks from `ClaudeLLM.chat_completion_stream()`. Frontend uses fetch + ReadableStream to parse chunks and update UI character-by-character. Non-streaming `/chat` endpoint remains unchanged.

**Tech Stack:** FastAPI StreamingResponse, Anthropic SDK streaming, React hooks, fetch API ReadableStream, NDJSON

---

## File Structure

**Backend (Create):**
- `backend/tests/test_chat_streaming.py` - Unit and integration tests for streaming

**Backend (Modify):**
- `backend/app/services/chat.py` - Add `send_streaming_message()` method
- `backend/app/api/v1/chat.py` - Add `POST /stream` endpoint

**Frontend (Create):**
- `frontend/lib/hooks/useStreamingChat.ts` - Custom hook for streaming chat
- `frontend/__tests__/hooks/useStreamingChat.test.ts` - Hook tests

**Frontend (Modify):**
- `frontend/app/chat/page.tsx` - Add streaming UI and state management

**Docs (Modify):**
- `docs/04_api_spec.md` - Document streaming endpoint

---

## Task 1: Backend - Add streaming method to ChatService

**Files:**
- Modify: `backend/app/services/chat.py`
- Test: `backend/tests/test_chat_streaming.py` (create)

### Step 1.1: Write failing test for streaming message flow

- [ ] **Create test file and write first test**

Create `backend/tests/test_chat_streaming.py`:

```python
"""
Tests for chat streaming functionality.
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.chat import ChatService
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, MessageRole
from app.schemas.chat import ChatRequest


@pytest.mark.asyncio
async def test_send_streaming_message_yields_chunks(db_session):
    """Test that send_streaming_message yields NDJSON chunks correctly."""
    # Setup
    user = User(
        id=uuid4(),
        employee_id="TEST001",
        email="test@example.com",
        full_name="Test User"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Mock LLM streaming
    async def mock_stream(*args, **kwargs):
        yield "Hello"
        yield " world"
        yield "!"
    
    mock_llm = MagicMock()
    mock_llm.chat_completion_stream = mock_stream
    
    # Mock settings service
    mock_settings = MagicMock()
    mock_settings.rag_enabled = False
    mock_settings.llm_temperature = 0.7
    mock_settings.max_tokens = 1000
    
    with patch.object(ChatService, '_settings_service', mock_settings):
        chat_service = ChatService(db_session, mock_llm)
        request = ChatRequest(message="Test message")
        
        # Collect chunks
        chunks = []
        async for chunk_str in chat_service.send_streaming_message(user, request):
            chunks.append(json.loads(chunk_str))
        
        # Verify chunks
        assert len(chunks) == 4  # 3 tokens + 1 done
        assert chunks[0] == {"type": "token", "content": "Hello"}
        assert chunks[1] == {"type": "token", "content": " world"}
        assert chunks[2] == {"type": "token", "content": "!"}
        assert chunks[3]["type"] == "done"
        assert "session_id" in chunks[3]
        assert "message_id" in chunks[3]
```

- [ ] **Run test to verify it fails**

Run: `cd backend && pytest tests/test_chat_streaming.py::test_send_streaming_message_yields_chunks -v`

Expected: FAIL with "AttributeError: 'ChatService' object has no attribute 'send_streaming_message'"

### Step 1.2: Implement send_streaming_message method

- [ ] **Add streaming method to ChatService**

Edit `backend/app/services/chat.py`, add after `send_message()` method (around line 159):

```python
    async def send_streaming_message(
        self,
        user: User,
        request: ChatRequest
    ) -> AsyncIterator[str]:
        """
        Process user message and stream AI response as NDJSON chunks.

        Args:
            user: Current user
            request: Chat request with message and optional session_id

        Yields:
            NDJSON strings (one JSON object per yield)

        Raises:
            NotFoundError: If session_id is provided but not found
        """
        import json
        from typing import AsyncIterator
        
        # Get or create session
        if request.session_id:
            session = await self._get_session(request.session_id, user.id)
        else:
            session = await self._create_session(user.id)

        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            role=MessageRole.USER.value,
            content=request.message
        )
        self.db.add(user_message)
        await self.db.flush()

        # Search knowledge base for relevant context
        runtime_settings = await self.settings_service.get_runtime_settings()
        kb_results = []
        if runtime_settings.rag_enabled:
            kb_results = await self.rag_service.search_knowledge_base(
                query=request.message,
                top_k=runtime_settings.rag_top_k
            )

        # Get conversation history with RAG context
        messages = await self._get_conversation_history(session.id, kb_results)

        # Stream AI response
        accumulated_content = ""
        token_count = 0
        
        try:
            async for text_chunk in self.llm.chat_completion_stream(
                messages=messages,
                temperature=runtime_settings.llm_temperature,
                max_tokens=runtime_settings.max_tokens
            ):
                accumulated_content += text_chunk
                token_count += 1
                
                # Yield token chunk
                yield json.dumps({
                    "type": "token",
                    "content": text_chunk
                })

            # Save AI message to database
            ai_message = ChatMessage(
                session_id=session.id,
                role=MessageRole.ASSISTANT.value,
                content=accumulated_content,
                token_count=token_count
            )
            self.db.add(ai_message)

            # Generate title when starting a new session
            if not session.title and request.session_id is None:
                session.title = await self._generate_session_title(request.message)

            await self.db.commit()
            await self.db.refresh(ai_message)

            logger.info(f"Streaming chat completed for session {session.id}")

            # Yield done chunk with metadata
            yield json.dumps({
                "type": "done",
                "session_id": str(session.id),
                "message_id": str(ai_message.id),
                "usage": {
                    "completion_tokens": token_count
                }
            })

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error streaming AI response: {str(e)}")
            
            # Try to save partial response if we have content
            if accumulated_content:
                try:
                    ai_message = ChatMessage(
                        session_id=session.id,
                        role=MessageRole.ASSISTANT.value,
                        content=accumulated_content + f"\n\n[Error: {str(e)}]",
                        token_count=token_count
                    )
                    self.db.add(ai_message)
                    await self.db.commit()
                except Exception as db_error:
                    logger.error(f"Failed to save partial response: {str(db_error)}")
            
            # Yield error chunk
            yield json.dumps({
                "type": "error",
                "message": f"Streaming error: {str(e)}",
                "code": "STREAM_ERROR"
            })
```

Add import at top of file:

```python
from typing import List, Optional, Dict, Any, AsyncIterator
```

- [ ] **Run test to verify it passes**

Run: `cd backend && pytest tests/test_chat_streaming.py::test_send_streaming_message_yields_chunks -v`

Expected: PASS

- [ ] **Commit**

```bash
git add backend/app/services/chat.py backend/tests/test_chat_streaming.py
git commit -m "feat(backend): add streaming message method to ChatService

- Add send_streaming_message() that yields NDJSON chunks
- Stream from llm.chat_completion_stream()
- Accumulate content and save to DB on completion
- Handle errors with partial response preservation
- Add test for basic streaming flow

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Step 1.3: Write test for error handling during stream

- [ ] **Write test for API error mid-stream**

Add to `backend/tests/test_chat_streaming.py`:

```python
@pytest.mark.asyncio
async def test_send_streaming_message_handles_stream_error(db_session):
    """Test that streaming handles errors and preserves partial content."""
    # Setup
    user = User(
        id=uuid4(),
        employee_id="TEST002",
        email="test2@example.com",
        full_name="Test User 2"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Mock LLM streaming that fails after 2 chunks
    async def mock_stream_with_error(*args, **kwargs):
        yield "Partial"
        yield " response"
        raise Exception("API timeout")
    
    mock_llm = MagicMock()
    mock_llm.chat_completion_stream = mock_stream_with_error
    
    # Mock settings service
    mock_settings = MagicMock()
    mock_settings.rag_enabled = False
    mock_settings.llm_temperature = 0.7
    mock_settings.max_tokens = 1000
    
    with patch.object(ChatService, '_settings_service', mock_settings):
        chat_service = ChatService(db_session, mock_llm)
        request = ChatRequest(message="Test error handling")
        
        # Collect chunks
        chunks = []
        async for chunk_str in chat_service.send_streaming_message(user, request):
            chunks.append(json.loads(chunk_str))
        
        # Verify partial content yielded + error
        assert len(chunks) == 3  # 2 tokens + 1 error
        assert chunks[0] == {"type": "token", "content": "Partial"}
        assert chunks[1] == {"type": "token", "content": " response"}
        assert chunks[2]["type"] == "error"
        assert "API timeout" in chunks[2]["message"]
```

- [ ] **Run test to verify it passes**

Run: `cd backend && pytest tests/test_chat_streaming.py::test_send_streaming_message_handles_stream_error -v`

Expected: PASS (implementation already handles this)

- [ ] **Commit**

```bash
git add backend/tests/test_chat_streaming.py
git commit -m "test(backend): add streaming error handling test

Verify that API errors mid-stream:
- Yield partial content received before error
- Save partial response to database
- Yield error chunk with details

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Backend - Add streaming endpoint to ChatRouter

**Files:**
- Modify: `backend/app/api/v1/chat.py`
- Test: `backend/tests/test_chat_streaming.py`

### Step 2.1: Write failing integration test for streaming endpoint

- [ ] **Write endpoint integration test**

Add to `backend/tests/test_chat_streaming.py`:

```python
import httpx
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_chat_stream_endpoint_returns_ndjson(client: AsyncClient, auth_headers: dict):
    """Test that /chat/stream endpoint returns NDJSON stream."""
    # Send streaming request
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"message": "Hello"},
        headers=auth_headers
    ) as response:
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        
        # Read chunks
        chunks = []
        async for line in response.aiter_lines():
            if line.strip():
                chunks.append(json.loads(line))
        
        # Verify structure
        assert len(chunks) > 0
        assert chunks[-1]["type"] == "done"
        assert all(c["type"] in ["token", "done", "error"] for c in chunks)


@pytest.mark.asyncio
async def test_chat_stream_endpoint_requires_auth(client: AsyncClient):
    """Test that streaming endpoint requires authentication."""
    async with client.stream(
        "POST",
        "/api/v1/chat/stream",
        json={"message": "Hello"}
    ) as response:
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

- [ ] **Run test to verify it fails**

Run: `cd backend && pytest tests/test_chat_streaming.py::test_chat_stream_endpoint_returns_ndjson -v`

Expected: FAIL with "404 Not Found" (endpoint doesn't exist yet)

### Step 2.2: Implement streaming endpoint

- [ ] **Add streaming endpoint to router**

Edit `backend/app/api/v1/chat.py`, add after `send_message()` endpoint (around line 47):

```python
from fastapi.responses import StreamingResponse
import json


@router.post(
    "/stream",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,
    summary="Stream a chat message"
)
async def send_streaming_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
):
    """
    Send a message to the AI assistant with streaming response.

    Returns NDJSON (newline-delimited JSON) chunks:
    - `{"type": "token", "content": "text"}` - Content chunk
    - `{"type": "done", "session_id": "...", "message_id": "..."}` - Completion
    - `{"type": "error", "message": "...", "code": "..."}` - Error

    - **message**: User's message (1-5000 characters)
    - **session_id**: Optional - existing session ID to continue conversation

    If session_id is not provided, a new session will be created.
    """
    chat_service = ChatService(db, llm)
    
    async def generate():
        try:
            async for chunk in chat_service.send_streaming_message(
                current_user, request
            ):
                yield chunk + "\n"
        except Exception as e:
            error_chunk = json.dumps({
                "type": "error",
                "message": str(e),
                "code": "ENDPOINT_ERROR"
            })
            yield error_chunk + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8"
    )
```

- [ ] **Run test to verify it passes**

Run: `cd backend && pytest tests/test_chat_streaming.py::test_chat_stream_endpoint_returns_ndjson -v`

Expected: PASS

- [ ] **Run auth test to verify it passes**

Run: `cd backend && pytest tests/test_chat_streaming.py::test_chat_stream_endpoint_requires_auth -v`

Expected: PASS

- [ ] **Commit**

```bash
git add backend/app/api/v1/chat.py backend/tests/test_chat_streaming.py
git commit -m "feat(backend): add POST /chat/stream endpoint

- New streaming endpoint returns NDJSON chunks
- Uses FastAPI StreamingResponse
- Requires authentication
- Catches endpoint-level errors
- Add integration tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Backend - Run all tests

**Files:**
- None (verification task)

### Step 3.1: Run full backend test suite

- [ ] **Run all backend tests**

Run: `cd backend && pytest -v`

Expected: All tests PASS (including new streaming tests)

- [ ] **Fix any failures**

If any tests fail, debug and fix issues before proceeding.

- [ ] **Commit if fixes were needed**

```bash
git add .
git commit -m "fix(backend): resolve test failures from streaming implementation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Frontend - Create useStreamingChat hook

**Files:**
- Create: `frontend/lib/hooks/useStreamingChat.ts`
- Create: `frontend/__tests__/hooks/useStreamingChat.test.ts`

### Step 4.1: Write failing test for streaming hook

- [ ] **Create test file and write first test**

Create directory: `mkdir -p frontend/__tests__/hooks`

Create `frontend/__tests__/hooks/useStreamingChat.test.ts`:

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useStreamingChat } from '@/lib/hooks/useStreamingChat'

// Mock fetch
global.fetch = jest.fn()

describe('useStreamingChat', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    localStorage.setItem('access_token', 'test-token')
  })

  it('should stream message chunks and call onChunk for each token', async () => {
    const mockChunks = [
      '{"type":"token","content":"Hello"}\n',
      '{"type":"token","content":" world"}\n',
      '{"type":"done","session_id":"session-123","message_id":"msg-456"}\n'
    ]

    // Mock ReadableStream
    const mockReader = {
      read: jest.fn()
        .mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode(mockChunks[0])
        })
        .mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode(mockChunks[1])
        })
        .mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode(mockChunks[2])
        })
        .mockResolvedValueOnce({ done: true })
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader
      }
    })

    const { result } = renderHook(() => useStreamingChat())

    const onChunk = jest.fn()
    const onComplete = jest.fn()
    const onError = jest.fn()

    await result.current.streamMessage(
      'Hello',
      undefined,
      { onChunk, onComplete, onError }
    )

    await waitFor(() => {
      expect(onChunk).toHaveBeenCalledWith('Hello')
      expect(onChunk).toHaveBeenCalledWith(' world')
      expect(onComplete).toHaveBeenCalledWith({
        session_id: 'session-123',
        message_id: 'msg-456'
      })
      expect(onError).not.toHaveBeenCalled()
    })
  })

  it('should handle streaming errors', async () => {
    const mockChunks = [
      '{"type":"token","content":"Partial"}\n',
      '{"type":"error","message":"API timeout","code":"STREAM_ERROR"}\n'
    ]

    const mockReader = {
      read: jest.fn()
        .mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode(mockChunks[0])
        })
        .mockResolvedValueOnce({
          done: false,
          value: new TextEncoder().encode(mockChunks[1])
        })
        .mockResolvedValueOnce({ done: true })
    }

    ;(global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      body: {
        getReader: () => mockReader
      }
    })

    const { result } = renderHook(() => useStreamingChat())

    const onChunk = jest.fn()
    const onComplete = jest.fn()
    const onError = jest.fn()

    await result.current.streamMessage(
      'Test',
      undefined,
      { onChunk, onComplete, onError }
    )

    await waitFor(() => {
      expect(onChunk).toHaveBeenCalledWith('Partial')
      expect(onError).toHaveBeenCalledWith('API timeout')
      expect(onComplete).not.toHaveBeenCalled()
    })
  })
})
```

- [ ] **Run test to verify it fails**

Run: `cd frontend && npm test -- hooks/useStreamingChat.test.ts`

Expected: FAIL with "Cannot find module '@/lib/hooks/useStreamingChat'"

### Step 4.2: Implement useStreamingChat hook

- [ ] **Create hook implementation**

Create directory: `mkdir -p frontend/lib/hooks`

Create `frontend/lib/hooks/useStreamingChat.ts`:

```typescript
/**
 * Custom hook for streaming chat messages
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export interface StreamChunkHandlers {
  onChunk: (text: string) => void
  onComplete: (metadata: {
    session_id: string
    message_id: string
    usage?: any
  }) => void
  onError: (error: string) => void
}

export function useStreamingChat() {
  /**
   * Stream a chat message to the backend
   * 
   * @param message - User message text
   * @param sessionId - Optional session ID to continue conversation
   * @param handlers - Callbacks for chunk, complete, and error events
   */
  const streamMessage = async (
    message: string,
    sessionId: string | undefined,
    handlers: StreamChunkHandlers
  ): Promise<void> => {
    const token = getAuthToken()
    
    if (!token) {
      handlers.onError('Not authenticated')
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message,
          session_id: sessionId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()

        if (done) break

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true })
        
        // Split by newlines to get complete JSON objects
        const lines = buffer.split('\n')
        
        // Keep incomplete line in buffer
        buffer = lines.pop() || ''

        // Process complete lines
        for (const line of lines) {
          if (!line.trim()) continue

          try {
            const chunk = JSON.parse(line)

            switch (chunk.type) {
              case 'token':
                handlers.onChunk(chunk.content)
                break
              
              case 'done':
                handlers.onComplete({
                  session_id: chunk.session_id,
                  message_id: chunk.message_id,
                  usage: chunk.usage
                })
                break
              
              case 'error':
                handlers.onError(chunk.message)
                break
            }
          } catch (parseError) {
            console.error('Failed to parse chunk:', line, parseError)
          }
        }
      }
    } catch (error) {
      handlers.onError(error instanceof Error ? error.message : 'Streaming failed')
    }
  }

  return { streamMessage }
}

/**
 * Get auth token from localStorage
 */
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('access_token')
}
```

- [ ] **Run test to verify it passes**

Run: `cd frontend && npm test -- hooks/useStreamingChat.test.ts`

Expected: PASS

- [ ] **Commit**

```bash
git add frontend/lib/hooks/useStreamingChat.ts frontend/__tests__/hooks/useStreamingChat.test.ts
git commit -m "feat(frontend): add useStreamingChat hook

- Fetch + ReadableStream for streaming
- Parse NDJSON chunks line-by-line
- Handle token, done, and error chunk types
- Callbacks for onChunk, onComplete, onError
- Add comprehensive tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Frontend - Update ChatPage for streaming UI

**Files:**
- Modify: `frontend/app/chat/page.tsx`

### Step 5.1: Add streaming state to ChatPage

- [ ] **Add streaming state and import hook**

Edit `frontend/app/chat/page.tsx`, add imports after line 5:

```typescript
import { useStreamingChat } from "@/lib/hooks/useStreamingChat"
```

Add state after line 17:

```typescript
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingContent, setStreamingContent] = useState("")
  const { streamMessage } = useStreamingChat()
```

- [ ] **Run type check**

Run: `cd frontend && npm run typecheck`

Expected: PASS (no errors)

- [ ] **Commit**

```bash
git add frontend/app/chat/page.tsx
git commit -m "feat(frontend): add streaming state to ChatPage

- Import useStreamingChat hook
- Add isStreaming and streamingContent state
- Prepare for streaming UI integration

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Step 5.2: Update handleSendMessage for streaming

- [ ] **Replace handleSendMessage with streaming logic**

Edit `frontend/app/chat/page.tsx`, replace `handleSendMessage` function (lines 62-93):

```typescript
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || isSending || isStreaming) return

    const messageText = inputMessage
    setInputMessage("")
    setError("")

    // Add user message to UI immediately
    const userMsg = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: messageText,
      created_at: new Date().toISOString()
    }
    setMessages((prev) => [...prev, userMsg])

    // Start streaming
    setIsStreaming(true)
    setStreamingContent("")

    try {
      await streamMessage(messageText, currentSessionId || undefined, {
        onChunk: (text) => {
          setStreamingContent((prev) => prev + text)
        },
        onComplete: ({ session_id, message_id }) => {
          // Add complete message to messages array
          const assistantMsg = {
            id: message_id,
            role: "assistant",
            content: streamingContent,
            created_at: new Date().toISOString()
          }
          setMessages((prev) => [...prev, assistantMsg])
          setStreamingContent("")
          setIsStreaming(false)

          // Update session if new
          if (session_id !== currentSessionId) {
            setCurrentSessionId(session_id)
            loadSessions()
          }
        },
        onError: (errorMessage) => {
          setError(`Streaming error: ${errorMessage}`)
          setIsStreaming(false)
          // Keep streamingContent to show partial response
        }
      })
    } catch (err) {
      setError("Failed to send message")
      setIsStreaming(false)
      setInputMessage(messageText) // Restore message on error
    }
  }
```

- [ ] **Run type check**

Run: `cd frontend && npm run typecheck`

Expected: PASS

- [ ] **Commit**

```bash
git add frontend/app/chat/page.tsx
git commit -m "feat(frontend): integrate streaming into handleSendMessage

- Call streamMessage with onChunk/onComplete/onError handlers
- Accumulate streamingContent as chunks arrive
- Add complete message to list on completion
- Preserve partial content on error
- Update session when new session created

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Step 5.3: Add streaming message rendering

- [ ] **Add streaming message UI to render**

Edit `frontend/app/chat/page.tsx`, find the messages rendering section (around line 203), add before the `messages.map()`:

```typescript
                <div className="max-w-3xl mx-auto space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${
                        message.role === "user" ? "justify-end" : "justify-start"
                      }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg px-4 py-2 ${
                          message.role === "user"
                            ? "bg-primary-600 text-white"
                            : "bg-white text-gray-900 border border-gray-200"
                        }`}
                      >
                        <div className="whitespace-pre-wrap">{message.content}</div>
                        <div
                          className={`text-xs mt-1 ${
                            message.role === "user"
                              ? "text-primary-100"
                              : "text-gray-500"
                          }`}
                        >
                          {new Date(message.created_at).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  ))}

                  {/* Show streaming message while in progress */}
                  {isStreaming && streamingContent && (
                    <div className="flex justify-start">
                      <div className="max-w-[80%] rounded-lg px-4 py-2 bg-white text-gray-900 border border-gray-200">
                        <div className="whitespace-pre-wrap">{streamingContent}</div>
                        <div className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                          Typing...
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
```

Replace the existing message rendering (lines 203-232).

- [ ] **Update error display to show partial content warning**

Edit `frontend/app/chat/page.tsx`, replace error display section (around line 236):

```typescript
            {/* Error Display */}
            {error && (
              <div className="px-4 py-2 bg-red-50 border-t border-red-200">
                <div className="max-w-3xl mx-auto">
                  <div className="text-red-800 text-sm font-medium">{error}</div>
                  {streamingContent && (
                    <div className="text-red-600 text-xs mt-1">
                      Partial response shown above. You can continue the conversation.
                    </div>
                  )}
                </div>
              </div>
            )}
```

- [ ] **Update input disabled state**

Edit `frontend/app/chat/page.tsx`, update input `disabled` prop (around line 252):

```typescript
                    disabled={isSending || isStreaming}
```

Update button `disabled` prop:

```typescript
                    disabled={isSending || isStreaming || !inputMessage.trim()}
```

Update button text:

```typescript
                    {isSending || isStreaming ? "Sending..." : "Send"}
```

- [ ] **Run type check**

Run: `cd frontend && npm run typecheck`

Expected: PASS

- [ ] **Commit**

```bash
git add frontend/app/chat/page.tsx
git commit -m "feat(frontend): add streaming message UI with typing animation

- Show streaming message with typing indicator
- Display partial content during streaming
- Enhanced error message for partial responses
- Disable input during streaming
- Auto-scroll to streaming message

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Frontend - Add hook tests to CI

**Files:**
- Modify: `frontend/package.json` (if needed)

### Step 6.1: Run frontend tests

- [ ] **Run all frontend tests**

Run: `cd frontend && npm test`

Expected: All tests PASS (including useStreamingChat tests)

- [ ] **Fix any test failures**

If tests fail, debug and fix before proceeding.

- [ ] **Commit if fixes were needed**

```bash
git add .
git commit -m "fix(frontend): resolve test failures

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Update API documentation

**Files:**
- Modify: `docs/04_api_spec.md`

### Step 7.1: Document streaming endpoint

- [ ] **Add streaming endpoint documentation**

Edit `docs/04_api_spec.md`, find the Chat Endpoints section and add after the `POST /chat` endpoint:

```markdown
#### POST /chat/stream

Stream chat message with real-time response chunks.

**Request:**
```json
{
  "message": "How do I reset my password?",
  "session_id": "uuid-optional"
}
```

**Response:** NDJSON stream (newline-delimited JSON)

**Content-Type:** `text/plain; charset=utf-8`

**Chunk Types:**

**Token Chunk:**
```json
{"type": "token", "content": "Hello"}
```

**Completion Chunk:**
```json
{
  "type": "done",
  "session_id": "abc-123-...",
  "message_id": "def-456-...",
  "usage": {
    "completion_tokens": 120
  }
}
```

**Error Chunk:**
```json
{
  "type": "error",
  "message": "API rate limit exceeded",
  "code": "STREAM_ERROR"
}
```

**Authentication:** Required (Bearer token)

**Status Codes:**
- 200: Streaming started (chunks follow)
- 401: Unauthorized
- 404: Session not found
- 422: Validation error

**Notes:**
- Backend uses `ClaudeLLM.chat_completion_stream()` from Anthropic SDK
- Partial responses preserved on error
- Session created if `session_id` not provided
- Compatible with fetch + ReadableStream on frontend
```

- [ ] **Commit**

```bash
git add docs/04_api_spec.md
git commit -m "docs: add streaming endpoint to API spec

Document POST /chat/stream:
- NDJSON chunk format (token, done, error)
- Request/response examples
- Status codes and authentication
- Frontend integration notes

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 8: Manual testing and verification

**Files:**
- None (manual testing)

### Step 8.1: Start backend and frontend

- [ ] **Start backend server**

Run in terminal 1:
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn app.main:app --reload
```

Expected: Server starts on http://localhost:8000

- [ ] **Start frontend dev server**

Run in terminal 2:
```bash
cd frontend
npm run dev
```

Expected: Frontend starts on http://localhost:3000

### Step 8.2: Test streaming flow

- [ ] **Test 1: Basic streaming**

1. Navigate to http://localhost:3000/chat
2. Login if needed
3. Click "New Chat"
4. Type: "Explain how to reset a password"
5. Click Send
6. Verify:
   - Typing animation appears character-by-character
   - "Typing..." indicator shows during streaming
   - Complete message appears in chat history
   - Message saved to database

- [ ] **Test 2: Long response**

1. In same chat session
2. Type: "Write a detailed guide on troubleshooting network connectivity issues"
3. Click Send
4. Verify:
   - Smooth streaming with no lag
   - Proper line breaks and formatting
   - Complete response saves correctly

- [ ] **Test 3: Error handling**

1. Stop backend server (Ctrl+C)
2. Try to send a message
3. Verify:
   - Error message displayed
   - Partial content (if any) preserved
   - User can retry after restarting backend

- [ ] **Test 4: Session persistence**

1. Restart backend
2. Send new message in existing session
3. Verify:
   - Session continues correctly
   - Conversation history maintained
   - Streaming works in existing session

### Step 8.3: Browser compatibility check

- [ ] **Test on Chrome**

Verify: Streaming works, typing animation smooth

- [ ] **Test on Firefox**

Verify: Streaming works, typing animation smooth

- [ ] **Test on Safari (if available)**

Verify: ReadableStream supported, streaming works

### Step 8.4: Document test results

- [ ] **Create test results summary**

Create `docs/superpowers/plans/2026-04-02-chat-streaming-test-results.md`:

```markdown
# Chat Streaming Test Results

**Date:** 2026-04-02
**Tester:** [Your name]

## Automated Tests

- Backend unit tests: ✅ PASS
- Backend integration tests: ✅ PASS
- Frontend hook tests: ✅ PASS

## Manual Tests

### Test 1: Basic Streaming
- Status: ✅ PASS
- Notes: Typing animation smooth, message saved correctly

### Test 2: Long Response
- Status: ✅ PASS
- Notes: No lag, proper formatting maintained

### Test 3: Error Handling
- Status: ✅ PASS
- Notes: Error displayed, partial content preserved

### Test 4: Session Persistence
- Status: ✅ PASS
- Notes: Session continues across messages

## Browser Compatibility

- Chrome: ✅ PASS
- Firefox: ✅ PASS
- Safari: ✅ PASS / ❌ FAIL / ⚠️ NOT TESTED

## Issues Found

[List any issues discovered]

## Recommendations

[Any recommendations for future improvements]
```

- [ ] **Commit test results**

```bash
git add docs/superpowers/plans/2026-04-02-chat-streaming-test-results.md
git commit -m "docs: add manual testing results for chat streaming

All automated and manual tests passing.
Streaming works smoothly across browsers.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Self-Review Checklist

### Spec Coverage

✅ **Goal 1**: Stream Claude API responses in real-time
- Task 1: `send_streaming_message()` yields chunks from `chat_completion_stream()`
- Task 2: `/chat/stream` endpoint exposes streaming

✅ **Goal 2**: Display typing animation
- Task 5: Streaming message UI with "Typing..." indicator

✅ **Goal 3**: Preserve partial responses on error
- Task 1.3: Error handling with partial content save
- Task 5.2: `onError` preserves `streamingContent`

✅ **Goal 4**: Backward compatibility
- Non-streaming `/chat` endpoint unchanged

✅ **Goal 5**: Follow LLM abstraction layer
- Uses `self.llm.chat_completion_stream()` interface

### Placeholder Check

✅ No TBD, TODO, or "implement later"
✅ All code blocks complete and executable
✅ All test assertions specific
✅ All commands have expected output

### Type Consistency

✅ `send_streaming_message()` returns `AsyncIterator[str]` consistently
✅ Chunk format `{"type": "token"|"done"|"error"}` used throughout
✅ Handler interface `StreamChunkHandlers` matches usage in ChatPage
✅ NDJSON format (JSON + `\n`) consistent backend → frontend

---

## Summary

**Total Tasks:** 8
**Estimated Time:** 6-8 hours
**Testing:** Unit, integration, and manual tests included

**Key Deliverables:**
- ✅ Backend streaming endpoint `/chat/stream`
- ✅ Frontend `useStreamingChat` hook
- ✅ Typing animation UI
- ✅ Error handling with partial response preservation
- ✅ Comprehensive tests
- ✅ API documentation

**Next Steps After Implementation:**
1. Monitor production logs for streaming errors
2. Gather user feedback on typing animation speed
3. Consider adding stream cancellation button
4. Extend to OpenAI provider (future enhancement)
