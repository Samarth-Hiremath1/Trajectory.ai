'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { TypingIndicator } from './TypingIndicator'
import { ChatSession, ChatMessage as ChatMessageType, MessageRole } from '@/types/chat'
import { ApiErrorBoundary } from '@/components/error/ApiErrorBoundary'
import { ErrorDisplay } from '@/components/ui/ErrorDisplay'
import { ChatLoadingState } from '@/components/ui/LoadingState'
import { useAsyncOperation } from '@/hooks/useAsyncOperation'
import { AppError, normalizeError } from '@/lib/error-utils'

interface ChatInterfaceProps {
  className?: string
}

export function ChatInterface({ className = '' }: ChatInterfaceProps) {
  const { user } = useAuth()
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [messageError, setMessageError] = useState<AppError | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Use async operation hook for chat initialization
  const initializeChatOp = useAsyncOperation(
    async () => {
      if (!user) throw new Error('User not authenticated')

      const response = await fetch('/api/chat/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user.id,
          title: 'Career Chat Session'
        }),
      })

      if (!response.ok) {
        const error = new Error(`Failed to initialize chat: ${response.statusText}`)
        ;(error as any).status = response.status
        throw error
      }

      return response.json()
    },
    {
      onSuccess: (newSession: ChatSession) => {
        setSession(newSession)
        setMessages(newSession.messages || [])
      }
    }
  )

  // State for current message being sent
  const [currentMessage, setCurrentMessage] = useState<string>('')

  // Use async operation hook for sending messages
  const sendMessageOp = useAsyncOperation(
    async () => {
      if (!session || !currentMessage.trim()) return

      const response = await fetch(`/api/chat/sessions/${session.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: session.id,
          message: currentMessage.trim(),
          include_context: true
        }),
      })

      if (!response.ok) {
        const error = new Error(`Failed to send message: ${response.statusText}`)
        ;(error as any).status = response.status
        throw error
      }

      return response.json()
    }
  )

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize chat session
  useEffect(() => {
    if (user && !session && !initializeChatOp.loading) {
      initializeChatOp.execute()
    }
  }, [user, session, initializeChatOp])

  // Polling for new messages (simple real-time implementation)
  useEffect(() => {
    if (!session) return

    const pollForUpdates = async () => {
      try {
        const response = await fetch(`/api/chat/sessions/${session.id}`)
        if (response.ok) {
          const updatedSession: ChatSession = await response.json()
          if (updatedSession.messages.length !== messages.length) {
            setMessages(updatedSession.messages)
          }
        }
      } catch (err) {
        console.error('Polling error:', err)
      }
    }

    // Poll every 2 seconds for updates
    pollingIntervalRef.current = setInterval(pollForUpdates, 2000)

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
      }
    }
  }, [session, messages.length])

  const sendMessage = async (content: string) => {
    if (!session || !content.trim()) return

    setMessageError(null)
    setIsTyping(true)
    setCurrentMessage(content.trim())

    // Add user message immediately to UI
    const userMessage: ChatMessageType = {
      id: `temp-${Date.now()}`,
      role: MessageRole.USER,
      content: content.trim(),
      timestamp: new Date(),
      metadata: {}
    }
    setMessages(prev => [...prev, userMessage])

    try {
      const chatResponse = await sendMessageOp.execute()
      
      // Replace temp user message and add AI response
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== userMessage.id)
        return [...filtered, userMessage, chatResponse.message]
      })
    } catch (error) {
      const normalizedError = normalizeError(error)
      setMessageError(normalizedError)
      
      // Remove the temporary user message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id))
    } finally {
      setIsTyping(false)
      setCurrentMessage('')
    }
  }

  const retryLastMessage = () => {
    if (messages.length > 0) {
      const lastUserMessage = [...messages].reverse().find(msg => msg.role === MessageRole.USER)
      if (lastUserMessage) {
        sendMessage(lastUserMessage.content)
      }
    }
  }

  // Show loading state during initialization
  if (initializeChatOp.loading) {
    return (
      <div className={className}>
        <ChatLoadingState />
      </div>
    )
  }

  // Show error state if initialization failed
  if (initializeChatOp.error) {
    return (
      <div className={className}>
        <ErrorDisplay
          error={initializeChatOp.error}
          onRetry={initializeChatOp.retry}
          variant="inline"
        />
      </div>
    )
  }

  if (!session) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <div className="text-center">
          <p className="text-gray-600 mb-4">No chat session available</p>
          <button
            onClick={initializeChatOp.retry}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm"
          >
            Initialize Chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <ApiErrorBoundary operation="chat" onRetry={initializeChatOp.retry}>
      <div className={`flex flex-col h-full bg-white rounded-lg shadow ${className}`}>
        {/* Chat Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">AI Career Mentor</h3>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-sm text-gray-600">Online</span>
          </div>
        </div>

        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <p className="mb-2">👋 Welcome to your AI Career Mentor!</p>
              <p className="text-sm">Ask me anything about your career goals, interview preparation, or skill development.</p>
            </div>
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
          
          {isTyping && <TypingIndicator />}
          
          {messageError && (
            <ErrorDisplay
              error={messageError}
              onRetry={retryLastMessage}
              onDismiss={() => setMessageError(null)}
              variant="inline"
            />
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Chat Input */}
        <div className="border-t border-gray-200 p-4">
          <ChatInput
            onSendMessage={sendMessage}
            disabled={sendMessageOp.loading}
            placeholder="Ask me about your career goals..."
          />
        </div>
      </div>
    </ApiErrorBoundary>
  )
}