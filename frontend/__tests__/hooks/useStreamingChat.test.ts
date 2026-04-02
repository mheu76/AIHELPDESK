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
