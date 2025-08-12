'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { ChatMessage } from '../chat/ChatMessage'
import { ChatInput } from '../chat/ChatInput'
import { TypingIndicator } from '../chat/TypingIndicator'
import { ChatSession, ChatMessage as ChatMessageType, MessageRole } from '@/types/chat'
import { Roadmap } from '@/types/roadmap'
import { ApiErrorBoundary } from '@/components/error/ApiErrorBoundary'
import { ErrorDisplay } from '@/components/ui/ErrorDisplay'
import { ChatLoadingState } from '@/components/ui/LoadingState'
import { useAsyncOperation } from '@/hooks/useAsyncOperation'
import { AppError } from '@/lib/error-utils'

interface RoadmapChatProps {
  roadmap: Roadmap
  className?: string
  onRoadmapUpdate?: (roadmapId: string) => void
}

export function RoadmapChat({ roadmap, className = '', onRoadmapUpdate }: RoadmapChatProps) {
  const { user } = useAuth()
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [messageError, setMessageError] = useState<AppError | null>(null)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Store the current message being sent
  const currentMessageRef = useRef<string>('')

  // Initialize roadmap chat session
  const initializeChatOp = useAsyncOperation(
    async () => {
      if (!user || !roadmap) throw new Error('User or roadmap not available')

      // Check if we have an existing session for this roadmap
      try {
        const existingSessionsResponse = await fetch(`/api/roadmap/${roadmap.id}/chat/sessions`)
        if (existingSessionsResponse.ok) {
          const existingSessions = await existingSessionsResponse.json()
          if (existingSessions && existingSessions.length > 0) {
            // Use the most recent session
            const recentSession = existingSessions[0]
            return recentSession
          }
        }
      } catch (error) {
        console.log('No existing roadmap chat sessions found, creating new one')
      }

      // Create new roadmap-specific session
      const response = await fetch(`/api/roadmap/${roadmap.id}/chat/sessions?user_id=${user.id}&title=Roadmap Chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      })

      if (!response.ok) {
        const error = new Error(`Failed to initialize roadmap chat: ${response.statusText}`)
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

  // Send message operation
  const sendMessageOp = useAsyncOperation(
    async () => {
      const messageContent = currentMessageRef.current
      
      if (!session || !messageContent.trim() || !roadmap) {
        console.log('Missing requirements for sending message:', { 
          session: !!session, 
          message: messageContent, 
          roadmap: !!roadmap 
        })
        return
      }

      console.log('Sending roadmap message:', { 
        roadmapId: roadmap.id, 
        sessionId: session.id, 
        message: messageContent.trim() 
      })

      const response = await fetch(`/api/roadmap/${roadmap.id}/chat/sessions/${session.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageContent.trim()
        }),
      })

      if (!response.ok) {
        const error = new Error(`Failed to send roadmap message: ${response.statusText}`)
        ;(error as any).status = response.status
        throw error
      }

      const result = await response.json()
      console.log('Roadmap chat response:', result)
      return result
    }
  )

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize chat session when roadmap changes
  useEffect(() => {
    if (user && roadmap && !session && !initializeChatOp.loading) {
      initializeChatOp.execute()
    }
  }, [user, roadmap, session, initializeChatOp])

  const sendMessage = async (content: string) => {
    if (!session || !content.trim() || !roadmap) return

    setMessageError(null)
    setIsTyping(true)

    // Store the message content in the ref for the async operation
    currentMessageRef.current = content.trim()

    // Add user message immediately to UI
    const userMessage: ChatMessageType = {
      id: `temp-${Date.now()}`,
      role: MessageRole.USER,
      content: content.trim(),
      timestamp: new Date(),
      metadata: { roadmap_id: roadmap.id }
    }
    setMessages(prev => [...prev, userMessage])

    const chatResponse = await sendMessageOp.execute()
    
    // Check if there was an error in the operation
    if (sendMessageOp.error) {
      setMessageError(sendMessageOp.error)
      // Remove the temporary user message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id))
    } else if (chatResponse && chatResponse.message) {
      // Replace temp user message and add AI response
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== userMessage.id)
        return [...filtered, userMessage, chatResponse.message]
      })
    } else {
      // Handle case where response is invalid
      const errorMessage = 'Invalid response from roadmap chat service'
      setMessageError({
        type: 'UNKNOWN' as any,
        message: errorMessage,
        retryable: true
      })
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id))
    }
    
    setIsTyping(false)
  }

  const retryLastMessage = () => {
    if (messages.length > 0) {
      const lastUserMessage = [...messages].reverse().find(msg => msg.role === MessageRole.USER)
      if (lastUserMessage) {
        sendMessage(lastUserMessage.content)
      }
    }
  }

  const handleEditRequest = async (editRequest: string) => {
    if (!session || !roadmap) return

    try {
      const response = await fetch(`/api/roadmap/${roadmap.id}/chat/edit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: session.id,
          edit_request: editRequest
        }),
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Edit analysis:', result.edit_analysis)
        
        // If the edit has high confidence, notify parent component
        if (result.edit_analysis.confidence > 0.7 && onRoadmapUpdate) {
          onRoadmapUpdate(roadmap.id)
        }
        
        // Add a system message about the edit analysis
        const systemMessage: ChatMessageType = {
          id: `edit-analysis-${Date.now()}`,
          role: MessageRole.ASSISTANT,
          content: `I've analyzed your edit request. ${result.edit_analysis.explanation}`,
          timestamp: new Date(),
          metadata: { 
            edit_analysis: result.edit_analysis,
            message_type: 'edit_analysis'
          }
        }
        setMessages(prev => [...prev, systemMessage])
      }
    } catch (error) {
      console.error('Failed to process edit request:', error)
    }
  }

  // Show loading state during initialization
  if (initializeChatOp.loading) {
    return (
      <div className={`bg-white rounded-lg shadow border ${className}`}>
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900">Roadmap Assistant</h4>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-gray-600">Connecting...</span>
          </div>
        </div>
        <div className="p-4 flex items-center justify-center">
          <div className="text-center">
            <ChatLoadingState />
            <p className="mt-2 text-xs text-gray-600">Initializing roadmap assistant</p>
          </div>
        </div>
      </div>
    )
  }

  // Show error state if initialization failed
  if (initializeChatOp.error) {
    return (
      <div className={`bg-white rounded-lg shadow border ${className}`}>
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900">Roadmap Assistant</h4>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-red-500 rounded-full"></div>
            <span className="text-xs text-gray-600">Offline</span>
          </div>
        </div>
        <div className="p-4">
          <ErrorDisplay
            error={initializeChatOp.error}
            onRetry={initializeChatOp.retry}
            variant="inline"
          />
        </div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className={`bg-white rounded-lg shadow border ${className}`}>
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <h4 className="text-sm font-semibold text-gray-900">Roadmap Assistant</h4>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
            <span className="text-xs text-gray-600">Disconnected</span>
          </div>
        </div>
        <div className="p-4 text-center">
          <p className="text-sm text-gray-600 mb-3">No chat session available</p>
          <button
            onClick={initializeChatOp.retry}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded text-xs transition-colors"
          >
            Initialize Chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <ApiErrorBoundary operation="roadmap-chat" onRetry={initializeChatOp.retry}>
      <div className={`bg-white rounded-lg shadow border ${className}`}>
        {/* Chat Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <h4 className="text-sm font-semibold text-gray-900">Roadmap Assistant</h4>
            <span className="text-xs text-gray-500">for {roadmap.title}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="text-xs text-gray-600">Online</span>
            <button
              onClick={() => setIsCollapsed(!isCollapsed)}
              className="text-gray-400 hover:text-gray-600 p-1"
            >
              <svg 
                className={`w-4 h-4 transition-transform ${isCollapsed ? 'rotate-180' : ''}`} 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>

        {/* Chat Content */}
        {!isCollapsed && (
          <>
            {/* Messages Container */}
            <div className="h-64 overflow-y-auto p-3 space-y-3 bg-gray-50">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-4">
                  <p className="text-sm mb-1">💬 Ask me about your roadmap!</p>
                  <p className="text-xs">I can help explain phases, suggest edits, or answer questions about your career plan.</p>
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
            <div className="border-t border-gray-200 p-3">
              <ChatInput
                onSendMessage={sendMessage}
                disabled={sendMessageOp.loading}
                placeholder="Ask about this roadmap or request edits..."
              />
              <div className="mt-2 flex flex-wrap gap-1">
                <button
                  onClick={() => sendMessage("Can you explain the next phase I should focus on?")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
                  disabled={sendMessageOp.loading}
                >
                  Next phase?
                </button>
                <button
                  onClick={() => sendMessage("What skills should I prioritize first?")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
                  disabled={sendMessageOp.loading}
                >
                  Priority skills?
                </button>
                <button
                  onClick={() => sendMessage("Can you suggest better learning resources?")}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
                  disabled={sendMessageOp.loading}
                >
                  Better resources?
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </ApiErrorBoundary>
  )
}