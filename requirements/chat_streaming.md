# Chat Streaming Implementation

**Created**: 2026-04-02  
**Status**: Planning  
**Priority**: Incremental Improvement

## Goal

Implement real-time streaming chat responses for Anthropic Claude provider, enhancing user experience with live typing animation while maintaining backward compatibility.

## Scope

### Included
- Anthropic Claude API streaming integration via `app/core/llm/` abstraction layer
- Backend streaming endpoint using FastAPI `StreamingResponse`
- Frontend streaming client using Fetch API + ReadableStream
- Typing animation UI effect for streamed responses
- Partial response preservation on error with error message display
- Both streaming and non-streaming modes supported

### Excluded
- OpenAI streaming (future enhancement)
- WebSocket implementation (using SSE/fetch streaming instead)
- Removal of existing non-streaming API (maintain compatibility)
- Streaming cancellation button (phase 1)

## Technical Decisions

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **LLM Provider** | Anthropic Claude only | Focus on one provider first, extensible design for others |
| **Frontend Method** | Fetch + ReadableStream | Standard browser API, no extra dependencies |
| **Backend Method** | FastAPI StreamingResponse | Native FastAPI support, SSE-compatible |
| **Compatibility** | Parallel endpoints | `/chat` (non-streaming), `/chat/stream` (streaming) |
| **Error Handling** | Preserve partial + show error | Better UX than discarding partial responses |
| **UI Display** | Typing animation | Character-by-character reveal effect |

## Architecture

### Backend Flow

```
POST /api/v1/chat/stream
  ↓
chat_router.create_streaming_chat_message()
  ↓
ChatService.create_streaming_message()
  ↓
LLMService.stream_chat_completion()  # app/core/llm/service.py
  ↓
AnthropicProvider.stream()            # app/core/llm/providers/anthropic.py
  ↓
yield SSE chunks { "data": "token" }
```

### Frontend Flow

```
fetch('/api/v1/chat/stream')
  ↓
response.body.getReader()
  ↓
read chunks from ReadableStream
  ↓
append to message state
  ↓
React renders with typing effect
```

## Implementation Plan

### Phase 1: Backend Streaming
1. Add `stream_chat_completion()` method to `LLMService`
2. Implement `AnthropicProvider.stream()` using Anthropic SDK streaming
3. Create `/api/v1/chat/stream` endpoint returning `StreamingResponse`
4. Add SSE formatting utilities

### Phase 2: Frontend Streaming
1. Create `useStreamingChat` hook for ReadableStream handling
2. Update chat UI to show typing animation
3. Add error boundary for partial response + error display
4. Update message component to support streaming state

### Phase 3: Testing & Refinement
1. Test streaming with various message lengths
2. Test error scenarios (network interruption, API errors)
3. Test partial response preservation
4. Performance testing (multiple concurrent streams)

## Success Criteria

- [ ] Anthropic Claude responses stream in real-time
- [ ] Frontend displays typing animation character-by-character
- [ ] Network errors preserve already-received text + show error
- [ ] Non-streaming endpoint still works (backward compatibility)
- [ ] No memory leaks from streaming connections
- [ ] Stream cleanup on component unmount

## Constraints

- Must use `app/core/llm/` abstraction layer (no direct API calls)
- Must follow existing async/await patterns
- Must maintain Pydantic v2 validation
- Frontend must use Next.js 14 App Router patterns
- Must handle database session persistence for streamed messages

## Future Enhancements

- OpenAI streaming support
- User-initiated stream cancellation
- Streaming progress indicator (tokens/sec)
- Stream reconnection on network issues
- Streaming for multi-turn conversations
