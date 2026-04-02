/**
 * Hook for streaming chat responses using Fetch API + ReadableStream
 */

import { useState, useCallback, useRef } from "react"
import { ApiError } from "@/lib/api"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

interface StreamingChatOptions {
  onChunk?: (chunk: string) => void
  onComplete?: (fullMessage: string) => void
  onError?: (error: Error, partialMessage: string) => void
}

interface StreamingChatResult {
  content: string
  session_id?: string
  message_id?: string
}

export function useStreamingChat() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingMessage, setStreamingMessage] = useState("")
  const abortControllerRef = useRef<AbortController | null>(null)

  const sendStreamingMessage = useCallback(
    async (
      message: string,
      sessionId: string | undefined,
      options?: StreamingChatOptions
    ): Promise<StreamingChatResult> => {
      // Get auth token
      const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null

      if (!token) {
        throw new ApiError(401, "UNAUTHORIZED", "No authentication token found")
      }

      // Create abort controller for cancellation
      abortControllerRef.current = new AbortController()

      setIsStreaming(true)
      setStreamingMessage("")

      let accumulated = ""

      try {
        const response = await fetch(`${API_BASE_URL}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            message,
            session_id: sessionId,
          }),
          signal: abortControllerRef.current.signal,
        })

        if (!response.ok) {
          const error = await response.json().catch(() => ({
            detail: "Streaming failed",
            error_code: "STREAM_ERROR",
          }))
          throw new ApiError(
            response.status,
            error.error_code || "STREAM_ERROR",
            error.detail || error.message || "Streaming failed"
          )
        }

        // Get the reader from the response body
        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error("No response body reader available")
        }

        const decoder = new TextDecoder()
        let buffer = ""
        let sessionIdFromStream: string | undefined
        let messageIdFromStream: string | undefined

        // Read the stream
        while (true) {
          const { done, value } = await reader.read()

          if (done) {
            break
          }

          // Decode the chunk
          const chunk = decoder.decode(value, { stream: true })
          buffer += chunk

          // Parse NDJSON format: each line is a JSON object
          const lines = buffer.split("\n")
          buffer = lines.pop() || "" // Keep incomplete line in buffer

          for (const line of lines) {
            if (!line.trim()) continue

            try {
              const json = JSON.parse(line)

              if (json.type === "token" && json.content) {
                accumulated += json.content
                setStreamingMessage(accumulated)
                options?.onChunk?.(json.content)
              } else if (json.type === "done") {
                sessionIdFromStream = json.session_id
                messageIdFromStream = json.message_id
              } else if (json.type === "error") {
                throw new ApiError(
                  500,
                  json.code || "STREAM_ERROR",
                  json.message || "Streaming error occurred"
                )
              }
            } catch (parseError) {
              if (parseError instanceof ApiError) {
                throw parseError
              }
              console.warn("Failed to parse NDJSON chunk:", line, parseError)
            }
          }
        }

        // Streaming completed successfully
        options?.onComplete?.(accumulated)

        return {
          content: accumulated,
          session_id: sessionIdFromStream || sessionId,
          message_id: messageIdFromStream,
        }
      } catch (error) {
        // Preserve partial response on error
        if (error instanceof Error && error.name === "AbortError") {
          // User cancelled
          console.log("Streaming cancelled by user")
        } else {
          // Network or other error
          options?.onError?.(
            error instanceof Error ? error : new Error("Unknown error"),
            accumulated
          )
        }

        throw error
      } finally {
        setIsStreaming(false)
        abortControllerRef.current = null
      }
    },
    []
  )

  const cancelStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }, [])

  const resetStreamingMessage = useCallback(() => {
    setStreamingMessage("")
  }, [])

  return {
    isStreaming,
    streamingMessage,
    sendStreamingMessage,
    cancelStreaming,
    resetStreamingMessage,
  }
}
