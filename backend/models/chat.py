from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum
import uuid

class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    """Individual chat message model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatSession(BaseModel):
    """Chat session model with conversation history"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    context_version: str = Field(default="1.0")  # For tracking RAG context updates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatInitRequest(BaseModel):
    """Request model for initializing a new chat session"""
    user_id: str
    title: Optional[str] = None
    initial_message: Optional[str] = None

class ChatMessageRequest(BaseModel):
    """Request model for sending a message in a chat session"""
    session_id: str
    message: str
    include_context: bool = True  # Whether to use RAG context

class ChatResponse(BaseModel):
    """Response model for chat operations"""
    session_id: str
    message: ChatMessage
    context_used: Optional[List[Dict]] = None  # RAG context that was used
    processing_time: Optional[float] = None

class ChatSessionResponse(BaseModel):
    """Response model for chat session operations"""
    session: ChatSession
    message_count: int
    last_activity: datetime

class ChatHistoryResponse(BaseModel):
    """Response model for chat history"""
    sessions: List[ChatSessionResponse]
    total_sessions: int
    active_sessions: int