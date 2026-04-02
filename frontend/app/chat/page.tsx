"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import { chatApi, ticketApi, ApiError, type ChatSession, type ChatMessage } from "@/lib/api"
import { useStreamingChat } from "@/hooks/useStreamingChat"

export default function ChatPage() {
  const router = useRouter()
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState("")
  const [isCreatingTicket, setIsCreatingTicket] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Streaming chat hook
  const { isStreaming, streamingMessage, sendStreamingMessage, resetStreamingMessage } = useStreamingChat()

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Load messages when session changes
  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId)
    }
  }, [currentSessionId])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const loadSessions = async () => {
    try {
      const response = await chatApi.getSessions()
      setSessions(response.sessions)
    } catch (err) {
      console.error("Failed to load sessions:", err)
    }
  }

  const loadMessages = async (sessionId: string) => {
    setIsLoading(true)
    try {
      const response = await chatApi.getSessionDetail(sessionId)
      setMessages(response.messages)
      setError("")
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError("Failed to load messages")
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || isSending || isStreaming) return

    const messageText = inputMessage
    setInputMessage("")
    setIsSending(true)
    setError("")
    resetStreamingMessage()

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: messageText,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    try {
      // Try streaming first
      const result = await sendStreamingMessage(messageText, currentSessionId || undefined, {
        onComplete: async (fullMessage) => {
          // Create assistant message
          const assistantMessage: ChatMessage = {
            id: `temp-${Date.now()}-assistant`,
            role: "assistant",
            content: fullMessage,
            created_at: new Date().toISOString(),
          }

          setMessages((prev) => [...prev, assistantMessage])
        },
        onError: (err, partialMessage) => {
          if (partialMessage) {
            // Preserve partial response
            const partialAssistantMessage: ChatMessage = {
              id: `temp-${Date.now()}-partial`,
              role: "assistant",
              content: partialMessage,
              created_at: new Date().toISOString(),
            }
            setMessages((prev) => [...prev, partialAssistantMessage])
          }

          if (err instanceof ApiError) {
            setError(`Streaming error: ${err.message}`)
          } else {
            setError(`Streaming error: ${err.message}`)
          }
        },
      })

      // Update session ID if it was a new session
      if (result.session_id && !currentSessionId) {
        setCurrentSessionId(result.session_id)
      }

      // Refresh sessions list
      await loadSessions()
    } catch (err) {
      // Streaming failed, don't fallback to non-streaming to avoid duplicate messages
      console.error("Streaming error:", err)
      if (!error) {
        // Only set error if onError callback didn't already set it
        if (err instanceof ApiError) {
          setError(err.message)
        } else {
          setError("Failed to send message")
        }
      }
    } finally {
      setIsSending(false)
      resetStreamingMessage()
    }
  }

  const startNewChat = () => {
    setCurrentSessionId(null)
    setMessages([])
    setError("")
  }

  const handleCreateTicket = async () => {
    if (!currentSessionId) return

    setIsCreatingTicket(true)
    setError("")

    try {
      const ticket = await ticketApi.createTicket({
        session_id: currentSessionId,
        priority: "medium"
      })

      // Navigate to the created ticket
      router.push(`/tickets/${ticket.id}`)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError("Failed to create ticket")
      }
    } finally {
      setIsCreatingTicket(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-73px)]">
      {/* Session List Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={startNewChat}
            className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md transition-colors"
          >
            + New Chat
          </button>
        </div>
        <div className="p-2">
          {sessions.length === 0 ? (
            <div className="text-center py-8 text-gray-500 text-sm">
              No conversations yet
            </div>
          ) : (
            sessions.map((session) => (
              <button
                key={session.id}
                onClick={() => setCurrentSessionId(session.id)}
                className={`w-full text-left p-3 rounded-md mb-2 transition-colors ${
                  currentSessionId === session.id
                    ? "bg-primary-50 border border-primary-200"
                    : "hover:bg-gray-50"
                }`}
              >
                <div className="font-medium text-gray-900 truncate">
                  {session.title}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {new Date(session.updated_at).toLocaleDateString()}
                  {session.is_resolved && (
                    <span className="ml-2 text-green-600">✓ Resolved</span>
                  )}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col bg-gray-50">
        {currentSessionId ? (
          <>
            {/* Chat Header with Create Ticket Button */}
            <div className="bg-white border-b border-gray-200 px-4 py-3">
              <div className="max-w-3xl mx-auto flex items-center justify-between">
                <div className="text-sm text-gray-600">
                  {sessions.find(s => s.id === currentSessionId)?.title || "Current Conversation"}
                </div>
                <button
                  onClick={handleCreateTicket}
                  disabled={isCreatingTicket}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  {isCreatingTicket ? "생성 중..." : "티켓 생성"}
                </button>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4">
              {isLoading ? (
                <div className="text-center py-8 text-gray-500">
                  Loading messages...
                </div>
              ) : messages.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  No messages yet
                </div>
              ) : (
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

                  {/* Streaming message indicator */}
                  {isStreaming && streamingMessage && (
                    <div className="flex justify-start">
                      <div className="max-w-[80%] rounded-lg px-4 py-2 bg-white text-gray-900 border border-gray-200">
                        <div className="whitespace-pre-wrap">{streamingMessage}</div>
                        <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                          <span className="inline-block w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                          Streaming...
                        </div>
                      </div>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>

            {/* Error Display */}
            {error && (
              <div className="px-4 py-2 bg-red-50 border-t border-red-200 text-red-800 text-sm">
                {error}
              </div>
            )}

            {/* Input Area */}
            <div className="bg-white border-t border-gray-200 p-4">
              <form onSubmit={handleSendMessage} className="max-w-3xl mx-auto">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    placeholder="Type your IT question..."
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    disabled={isSending || isStreaming}
                  />
                  <button
                    type="submit"
                    disabled={isSending || isStreaming || !inputMessage.trim()}
                    className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-6 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isStreaming ? "Streaming..." : isSending ? "Sending..." : "Send"}
                  </button>
                </div>
              </form>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Welcome to IT AI Helpdesk
              </h2>
              <p className="text-gray-600 mb-6">
                Select a conversation or start a new chat
              </p>
              <button
                onClick={startNewChat}
                className="bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-6 rounded-md transition-colors"
              >
                Start New Chat
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
