# Chat Streaming Implementation Design

**Date**: 2026-04-02  
**Status**: Approved  
**Priority**: Incremental Improvement

## Overview

Implement real-time streaming chat responses for the Anthropic Claude provider. Users will see AI responses appear character-by-character with typing animation, improving perceived responsiveness and user experience. The implementation maintains backward compatibility by keeping the existing non-streaming endpoint operational.

## Goals

1. Stream Claude API responses in real-time to frontend
2. Display typing animation as responses arrive
3. Preserve partial responses on error with error message display
4. Maintain backward compatibility with existing non-streaming API
5. Follow existing LLM abstraction layer patterns

## Non-Goals

- OpenAI streaming (future enhancement)
- WebSocket implementation (using fetch + ReadableStream)
- Stream cancellation button (phase 1)
- Removing non-streaming endpoint

## Architecture

### Endpoint Structure

**Existing (unchanged):**
- `POST /api/v1/chat` - Non-streaming, returns complete response

**New:**
- `POST /api/v1/chat/stream` - Streaming, yields newline-delimited JSON chunks

### Backend Flow

```
ChatRouter (/api/v1/chat/stream)
    ↓ authenticate user
    ↓
ChatService.send_streaming_message()
    ↓ create/get session, save user message
    ↓ search knowledge base (if RAG enabled)
    ↓ build conversation history
    ↓
LLMBase.chat_completion_stream()
    ↓ polymorphic call
    ↓
ClaudeLLM.chat_completion_stream()
    ↓ call Anthropic SDK messages.stream()
    ↓ yield text chunks
    ↓
ChatService yields NDJSON chunks
    ↓
FastAPI StreamingResponse
    ↓ HTTP response with Transfer-Encoding: chunked
    ↓
Frontend ReadableStream
```

### Frontend Flow

```
ChatPage Component
    ↓ user submits message
    ↓
useStreamingChat hook
    ↓
fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { Authorization: 'Bearer ...' },
    body: JSON.stringify({ message, session_id })
})
    ↓
response.body.getReader()
    ↓ read() loop
    ↓
TextDecoder + NDJSON parsing
    ↓
onChunk(text) callback
    ↓
setState(accumulated text)
    ↓
React re-renders with typing animation
```

## Data Format

### Request (same as non-streaming)

```json
POST /api/v1/chat/stream
Authorization: Bearer <token>

{
  "message": "How do I reset my password?",
  "session_id": "uuid-optional"
}
```

### Response (NDJSON stream)

Each line is a JSON object followed by newline (`\n`):

```json
{"type":"token","content":"To"}
{"type":"token","content":" reset"}
{"type":"token","content":" your"}
{"type":"token","content":" password"}
{"type":"token","content":":\n1"}
{"type":"token","content":". Go"}
{"type":"token","content":" to"}
{"type":"done","session_id":"abc-123","message_id":"def-456","usage":{"input_tokens":50,"output_tokens":120}}
```

**Chunk Types:**

| Type | Fields | Description |
|------|--------|-------------|
| `token` | `content` | Text chunk from LLM |
| `done` | `session_id`, `message_id`, `usage` | Stream complete, metadata returned |
| `error` | `message`, `code` | Error occurred during streaming |

**Error Chunk Example:**

```json
{"type":"error","message":"API rate limit exceeded","code":"RATE_LIMIT"}
```

## Components

### Backend Components

#### 1. ChatService.send_streaming_message()

**File**: `backend/app/services/chat.py`

**Signature:**
```python
async def send_streaming_message(
    self,
    user: User,
    request: ChatRequest
) -> AsyncIterator[str]:
    """
    Process user message and stream AI response.
    
    Yields:
        NDJSON chunks (one JSON object per line)
    """
```

**Logic:**
1. Get or create session
2. Save user message to database
3. Search knowledge base (if RAG enabled)
4. Build conversation history
5. Call `self.llm.chat_completion_stream()`
6. Accumulate full response while yielding chunks
7. On completion: save assistant message, yield done chunk
8. On error: yield error chunk with partial content preserved

**Error Handling:**
- Catch exceptions from `chat_completion_stream()`
- Preserve accumulated text before error
- Save partial message to DB with error flag
- Yield error chunk with details

#### 2. ChatRouter: POST /chat/stream

**File**: `backend/app/api/v1/chat.py`

**Implementation:**
```python
@router.post("/chat/stream")
async def create_streaming_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    llm: LLMBase = Depends(get_llm)
) -> StreamingResponse:
    """Stream chat response as NDJSON chunks."""
    chat_service = ChatService(db, llm)
    
    async def generate():
        try:
            async for chunk in chat_service.send_streaming_message(
                current_user, request
            ):
                yield chunk + "\n"
        except Exception as e:
            logger.error(f"Streaming error: {str(e)}")
            error_chunk = json.dumps({
                "type": "error",
                "message": str(e),
                "code": "STREAM_ERROR"
            })
            yield error_chunk + "\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8"
    )
```

#### 3. ClaudeLLM (Already Implemented)

**File**: `backend/app/core/llm/claude.py`

**Existing Method**: `chat_completion_stream()` (lines 99-144)

Already implements:
- Message format conversion (system message separation)
- Anthropic SDK `messages.stream()` call
- `async for text in stream.text_stream` iteration
- Error handling for `anthropic.APIError`

**No changes needed** - already provides the interface required by ChatService.

### Frontend Components

#### 4. useStreamingChat Hook

**File**: `frontend/lib/hooks/useStreamingChat.ts` (new file)

**Interface:**
```typescript
export interface StreamChunkHandlers {
  onChunk: (text: string) => void
  onComplete: (metadata: {
    session_id: string
    message_id: string
    usage: any
  }) => void
  onError: (error: string) => void
}

export function useStreamingChat() {
  const streamMessage = async (
    message: string,
    sessionId: string | undefined,
    handlers: StreamChunkHandlers
  ): Promise<void> => {
    // Implementation details below
  }
  
  return { streamMessage }
}
```

**Implementation:**
```typescript
const response = await fetch(`${API_BASE_URL}/chat/stream`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({ message, session_id: sessionId })
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
  
  buffer += decoder.decode(value, { stream: true })
  const lines = buffer.split('\n')
  buffer = lines.pop() || ''
  
  for (const line of lines) {
    if (!line.trim()) continue
    
    const chunk = JSON.parse(line)
    
    switch (chunk.type) {
      case 'token':
        handlers.onChunk(chunk.content)
        break
      case 'done':
        handlers.onComplete(chunk)
        break
      case 'error':
        handlers.onError(chunk.message)
        break
    }
  }
}
```

#### 5. ChatPage Updates

**File**: `frontend/app/chat/page.tsx`

**New State:**
```typescript
const [isStreaming, setIsStreaming] = useState(false)
const [streamingContent, setStreamingContent] = useState('')
const [useStreaming, setUseStreaming] = useState(true) // toggle
```

**Updated handleSendMessage:**
```typescript
const handleSendMessage = async (e: React.FormEvent) => {
  e.preventDefault()
  if (!inputMessage.trim() || isSending || isStreaming) return
  
  const messageText = inputMessage
  setInputMessage('')
  
  if (useStreaming) {
    // Streaming path
    setIsStreaming(true)
    setStreamingContent('')
    
    try {
      await streamMessage(messageText, currentSessionId, {
        onChunk: (text) => {
          setStreamingContent(prev => prev + text)
        },
        onComplete: ({ session_id, message_id, usage }) => {
          // Add complete message to messages array
          const newMessage = {
            id: message_id,
            role: 'assistant',
            content: streamingContent,
            created_at: new Date().toISOString()
          }
          setMessages(prev => [...prev, newMessage])
          setStreamingContent('')
          setIsStreaming(false)
          
          // Update session if new
          if (session_id !== currentSessionId) {
            setCurrentSessionId(session_id)
            loadSessions()
          }
        },
        onError: (error) => {
          setError(`Streaming error: ${error}`)
          setIsStreaming(false)
          // Keep streamingContent to show partial response
        }
      })
    } catch (err) {
      setError('Failed to stream message')
      setIsStreaming(false)
    }
  } else {
    // Non-streaming path (existing code)
    setIsSending(true)
    // ... existing non-streaming logic
  }
}
```

**Message Rendering:**
```tsx
{/* Show streaming message while in progress */}
{isStreaming && streamingContent && (
  <div className="flex justify-start">
    <div className="max-w-[80%] rounded-lg px-4 py-2 bg-white text-gray-900 border border-gray-200">
      <div className="whitespace-pre-wrap">{streamingContent}</div>
      <div className="text-xs text-gray-500 mt-1">
        <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse mr-1"></span>
        Typing...
      </div>
    </div>
  </div>
)}

{/* Regular messages */}
{messages.map((message) => (
  // ... existing message rendering
))}
```

## Error Handling

### Network Interruption

**Scenario**: Connection drops mid-stream

**Backend**: Stream breaks, client disconnects
**Frontend**: 
- `reader.read()` rejects or returns partial data
- Preserve `streamingContent` accumulated so far
- Display partial text + error banner:
  ```tsx
  {error && streamingContent && (
    <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
      <p className="text-yellow-700">
        Connection interrupted. Partial response shown above.
      </p>
    </div>
  )}
  ```

### Claude API Error

**Scenario**: API rate limit, timeout, or error during streaming

**Backend**:
```python
try:
    async for text in self.llm.chat_completion_stream(...):
        accumulated += text
        yield json.dumps({"type": "token", "content": text})
except anthropic.APIError as e:
    # Save partial response
    if accumulated:
        ai_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=accumulated + "\n\n[Error: " + str(e) + "]",
            token_count=None
        )
        self.db.add(ai_message)
        await self.db.commit()
    
    yield json.dumps({
        "type": "error",
        "message": f"API error: {str(e)}",
        "code": "API_ERROR"
    })
```

**Frontend**: Display error, keep partial content visible

### Database Save Error

**Scenario**: Stream completes but DB save fails

**Backend**:
```python
try:
    # Save assistant message
    ai_message = ChatMessage(...)
    self.db.add(ai_message)
    await self.db.commit()
except Exception as e:
    await self.db.rollback()
    yield json.dumps({
        "type": "error",
        "message": "Failed to save response",
        "code": "DB_ERROR"
    })
    return

yield json.dumps({
    "type": "done",
    "session_id": str(session.id),
    "message_id": str(ai_message.id),
    "usage": {...}
})
```

**Frontend**: Show warning toast, but display full response

### Timeout

**Configuration**:
- FastAPI: No explicit timeout for streaming (relies on nginx/client)
- Nginx (production): Increase timeout for `/chat/stream` to 300s
- Frontend: 60s read timeout

**Handling**:
```typescript
const timeoutId = setTimeout(() => {
  reader.cancel()
  handlers.onError('Request timed out')
}, 60000)

// Clear timeout on completion
clearTimeout(timeoutId)
```

## Testing Strategy

### Backend Tests

**File**: `backend/tests/test_chat_streaming.py`

**Tests**:
1. **Unit test**: `test_send_streaming_message_yields_chunks`
   - Mock `llm.chat_completion_stream()` to return predefined chunks
   - Verify correct NDJSON format
   - Verify done chunk with metadata

2. **Unit test**: `test_send_streaming_message_handles_api_error`
   - Mock LLM to raise error after 3 chunks
   - Verify partial content saved to DB
   - Verify error chunk yielded

3. **Integration test**: `test_chat_stream_endpoint`
   - POST to `/chat/stream` with auth token
   - Verify 200 response with `text/plain` content-type
   - Parse NDJSON chunks, verify structure

4. **Integration test**: `test_chat_stream_creates_session`
   - POST without `session_id`
   - Verify new session created
   - Verify done chunk includes `session_id`

5. **Integration test**: `test_chat_stream_unauthorized`
   - POST without auth token
   - Verify 401 response

### Frontend Tests

**File**: `frontend/__tests__/useStreamingChat.test.ts`

**Tests**:
1. **Mock streaming response**:
   ```typescript
   const mockResponse = new ReadableStream({
     start(controller) {
       controller.enqueue(new TextEncoder().encode(
         '{"type":"token","content":"Hello"}\n'
       ))
       controller.enqueue(new TextEncoder().encode(
         '{"type":"token","content":" world"}\n'
       ))
       controller.enqueue(new TextEncoder().encode(
         '{"type":"done","session_id":"123"}\n'
       ))
       controller.close()
     }
   })
   ```

2. **Test chunk accumulation**:
   - Verify `onChunk` called with each token
   - Verify `onComplete` called with metadata

3. **Test error handling**:
   - Mock response with error chunk
   - Verify `onError` called
   - Verify partial content preserved

4. **Test network error**:
   - Mock fetch rejection
   - Verify error handling

**File**: `frontend/__tests__/ChatPage.test.tsx`

**Tests**:
1. **Streaming message flow**:
   - Type message, click send
   - Verify streaming state active
   - Verify typing indicator shown
   - Verify message added to list on completion

2. **Error display**:
   - Mock streaming error
   - Verify error banner shown
   - Verify partial content visible

### Manual Testing

**Test Cases**:
1. **Long response** (>1000 tokens):
   - Ask: "Explain in detail how to troubleshoot network connectivity issues"
   - Verify: Smooth typing animation, no lag, proper formatting

2. **Multiple concurrent streams**:
   - Open 3 browser tabs
   - Send messages simultaneously
   - Verify: No cross-contamination, each stream independent

3. **Network throttling**:
   - Chrome DevTools → Network → Slow 3G
   - Send message
   - Verify: Graceful handling, visible progress

4. **Browser compatibility**:
   - Test on Chrome, Firefox, Safari, Edge
   - Verify: ReadableStream support, proper rendering

5. **Session persistence**:
   - Start new session with streaming
   - Verify: Session created, title generated
   - Reload page, verify: Messages persist

## Implementation Plan Summary

### Phase 1: Backend Streaming (2-3 hours)

1. Add `send_streaming_message()` to `ChatService`
2. Add `POST /chat/stream` endpoint to ChatRouter
3. Add NDJSON chunk formatting utilities
4. Write backend tests

**Files Modified:**
- `backend/app/services/chat.py`
- `backend/app/api/v1/chat.py`
- `backend/tests/test_chat_streaming.py` (new)

### Phase 2: Frontend Streaming (2-3 hours)

1. Create `useStreamingChat` hook
2. Update `ChatPage` with streaming state
3. Add typing animation UI
4. Implement error boundary for partial responses
5. Write frontend tests

**Files Modified:**
- `frontend/lib/hooks/useStreamingChat.ts` (new)
- `frontend/app/chat/page.tsx`
- `frontend/__tests__/useStreamingChat.test.ts` (new)
- `frontend/__tests__/ChatPage.test.tsx` (new)

### Phase 3: Testing & Refinement (1-2 hours)

1. Run all automated tests
2. Manual testing scenarios
3. Performance profiling
4. Documentation updates

**Files Modified:**
- `docs/04_api_spec.md` (add streaming endpoint docs)
- `README.md` (mention streaming feature)

## Success Criteria

- [x] Design approved
- [ ] Backend streaming endpoint returns proper NDJSON chunks
- [ ] Frontend displays typing animation character-by-character
- [ ] Network errors preserve partial response + show error message
- [ ] Non-streaming endpoint still works (backward compatibility)
- [ ] All automated tests pass
- [ ] Manual testing scenarios verified
- [ ] No memory leaks from streaming connections
- [ ] Stream cleanup on component unmount
- [ ] Documentation updated

## Future Enhancements

1. **OpenAI Streaming**: Implement streaming for OpenAI provider
2. **Stream Cancellation**: Add stop button to cancel mid-stream
3. **Retry Logic**: Auto-retry on transient errors
4. **Progress Indicator**: Show tokens/second, estimated completion time
5. **Streaming for Multi-turn**: Optimize RAG context for streaming
6. **Response Caching**: Cache common responses to reduce API calls
7. **Token Counting**: Display real-time token usage during streaming

## References

- Anthropic SDK Streaming: https://docs.anthropic.com/en/api/messages-streaming
- FastAPI Streaming: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- MDN ReadableStream: https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream
- NDJSON Specification: http://ndjson.org/
