'use client'

import { ChatMessage as ChatMessageType, MessageRole } from '@/types/chat'
import { formatDistanceToNow } from '@/lib/utils'

interface ChatMessageProps {
  message: ChatMessageType
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === MessageRole.USER
  const isAssistant = message.role === MessageRole.ASSISTANT

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-xs lg:max-w-md ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {/* Avatar */}
        <div className={`flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
            isUser 
              ? 'bg-indigo-600 text-white' 
              : 'bg-gray-300 text-gray-700'
          }`}>
            {isUser ? 'U' : '🤖'}
          </div>
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
          <div className={`px-4 py-2 rounded-lg ${
            isUser
              ? 'bg-indigo-600 text-white'
              : 'bg-gray-100 text-gray-900'
          }`}>
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>
          
          {/* Timestamp */}
          <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right' : 'text-left'}`}>
            {formatDistanceToNow(message.timestamp)}
          </div>

          {/* Message Status for User Messages */}
          {isUser && (
            <div className="mt-1 text-xs text-gray-400">
              <span>✓ Sent</span>
            </div>
          )}

          {/* Context indicator for AI messages */}
          {isAssistant && (
            <div className="mt-1 text-xs text-gray-400">
              <span>🤖 AI Response</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}