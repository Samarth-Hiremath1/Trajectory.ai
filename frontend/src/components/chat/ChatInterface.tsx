'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-context'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { TypingIndicator } from './TypingIndicator'
import { ChatSession, ChatMessage as ChatMessageType, MessageRole } from '@/types/chat'

interface ChatInterfaceProps {
  className?: string
}

export function ChatInterface({ className = '' }: ChatInterfaceProps) {
  const { user } = useAuth()
  const [session, setSession] = useState<ChatSession | null>(null)
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isInitializing, setIsInitializing] = useState(true)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Initialize chat session
  useEffect(() => {
    if (!user) return

    const initializeChat = async () => {
      try {
        setIsInitializing(true)
        setError(null)

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
          throw new Error(`Failed to initialize chat: ${response.statusText}`)
        }

        const newSession: ChatSession = await response.json()
        setSession(newSession)
        setMessages(newSession.messages || [])
      } catch (err) {
        console.error('Failed to initialize chat:', err)
        setError(err instanceof Error ? err.message : 'Failed to initialize chat')
      } finally {
        setIsInitializing(false)
      }
    }

    initializeChat()
  }, [user])

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

    try {
      setIsLoading(true)
      setIsTyping(true)
      setError(null)

      // Add user message immediately to UI
      const userMessage: ChatMessageType = {
        id: `temp-${Date.now()}`,
        role: MessageRole.USER,
        content: content.trim(),
        timestamp: new Date(),
        metadata: {}
      }
      setMessages(prev => [...prev, userMessage])

      const response = await fetch(`/api/chat/sessions/${session.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: session.id,
          message: content.trim(),
          include_context: true
        }),
      })

      if (!response.ok) {
        throw new Error(`Failed to send message: ${response.statusText}`)
      }

      const chatResponse = await response.json()
      
      // Replace temp user message and add AI response
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== userMessage.id)
        return [...filtered, userMessage, chatResponse.message]
      })

    } catch (err) {
      console.error('Failed to send message:', err)
      setError(err instanceof Error ? err.message : 'Failed to send message')
      
      // Remove the temporary user message on error
      setMessages(prev => prev.filter(msg => msg.id !== `temp-${Date.now()}`))
    } finally {
      setIsLoading(false)
      setIsTyping(false)
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

  if (isInitializing) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Initializing chat...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    return (
      <div className={`flex items-center justify-center h-96 ${className}`}>
        <div className="text-center">
          <p className="text-red-600 mb-4">Failed to initialize chat session</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
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
        
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
            <div className="flex items-center justify-between">
              <p className="text-red-800 text-sm">{error}</p>
              <button
                onClick={retryLastMessage}
                className="text-red-600 hover:text-red-800 text-sm underline ml-2"
              >
                Retry
              </button>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div className="border-t border-gray-200 p-4">
        <ChatInput
          onSendMessage={sendMessage}
          disabled={isLoading}
          placeholder="Ask me about your career goals..."
        />
      </div>
    </div>
  )
}