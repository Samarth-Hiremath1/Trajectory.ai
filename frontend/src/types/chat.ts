export enum MessageRole {
  USER = "user",
  ASSISTANT = "assistant",
  SYSTEM = "system"
}

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  metadata: Record<string, unknown>
}

export interface ChatSession {
  id: string
  user_id: string
  title?: string
  messages: ChatMessage[]
  context_version: string
  created_at: Date
  updated_at: Date
  is_active: boolean
  metadata: Record<string, unknown>
}

export interface ChatInitRequest {
  user_id: string
  title?: string
  initial_message?: string
}

export interface ChatMessageRequest {
  session_id: string
  message: string
  include_context: boolean
}

export interface ChatResponse {
  session_id: string
  message: ChatMessage
  context_used?: Array<Record<string, unknown>>
  processing_time?: number
}

export interface ChatSessionResponse {
  session: ChatSession
  message_count: number
  last_activity: Date
}

export interface ChatHistoryResponse {
  sessions: ChatSessionResponse[]
  total_sessions: number
  active_sessions: number
}