import os
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import json
import uuid

from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

from models.chat import (
    ChatSession, ChatMessage, MessageRole, 
    ChatInitRequest, ChatMessageRequest, ChatResponse
)
from services.ai_service import AIService, get_ai_service, ModelType
from services.database_service import DatabaseService

# Optional imports with graceful fallback
try:
    from services.embedding_service import EmbeddingService
    EMBEDDING_AVAILABLE = True
except ImportError:
    EmbeddingService = None
    EMBEDDING_AVAILABLE = False

try:
    from services.resume_service import ResumeProcessingService
    RESUME_AVAILABLE = True
except ImportError:
    ResumeProcessingService = None
    RESUME_AVAILABLE = False

logger = logging.getLogger(__name__)

class RAGChatService:
    """RAG-enabled AI chat service with memory management using LangChain"""
    
    def __init__(self):
        self.ai_service: Optional[AIService] = None
        self.db_service = DatabaseService()
        
        # Initialize optional services
        self.embedding_service = EmbeddingService() if EMBEDDING_AVAILABLE else None
        self.resume_service = ResumeProcessingService() if RESUME_AVAILABLE else None
        
        # In-memory session storage for active sessions
        self.active_sessions: Dict[str, ChatSession] = {}
        self.session_memories: Dict[str, ConversationBufferWindowMemory] = {}
        
        # Configuration
        self.max_memory_messages = 10  # Keep last 10 messages in memory
        self.max_context_chunks = 5    # Max RAG context chunks to include
        self.context_similarity_threshold = 0.7  # Minimum similarity for context inclusion
        
        logger.info(f"RAG Chat Service initialized (Embedding: {EMBEDDING_AVAILABLE}, Resume: {RESUME_AVAILABLE})")
    
    async def _get_ai_service(self) -> AIService:
        """Get or initialize AI service"""
        if self.ai_service is None:
            self.ai_service = await get_ai_service()
        return self.ai_service
    
    def _create_session_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Create LangChain memory for a chat session"""
        memory = ConversationBufferWindowMemory(
            k=self.max_memory_messages,
            return_messages=True,
            memory_key="chat_history"
        )
        self.session_memories[session_id] = memory
        return memory
    
    def _get_session_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get existing memory or create new one"""
        if session_id not in self.session_memories:
            return self._create_session_memory(session_id)
        return self.session_memories[session_id]
    
    def _load_session_into_memory(self, session: ChatSession) -> ConversationBufferWindowMemory:
        """Load existing chat session into LangChain memory"""
        memory = self._create_session_memory(session.id)
        
        # Load recent messages into memory
        recent_messages = session.messages[-self.max_memory_messages:]
        
        for message in recent_messages:
            if message.role == MessageRole.USER:
                memory.chat_memory.add_user_message(message.content)
            elif message.role == MessageRole.ASSISTANT:
                memory.chat_memory.add_ai_message(message.content)
        
        return memory
    
    async def _get_user_context(self, user_id: str, query: str) -> Tuple[List[Dict], str]:
        """Retrieve relevant user context using RAG from both resume and profile"""
        try:
            all_context_chunks = []
            context_parts = []
            
            # Try to get comprehensive user context from embedding service
            if self.embedding_service:
                try:
                    # Use the comprehensive search that includes both resume and profile
                    context_chunks = self.embedding_service.search_user_context(
                        user_id=user_id,
                        query=query,
                        n_results=self.max_context_chunks
                    )
                    
                    # Filter by similarity threshold if available
                    filtered_chunks = []
                    for chunk in context_chunks:
                        if chunk.get('distance') is None or chunk['distance'] <= self.context_similarity_threshold:
                            filtered_chunks.append(chunk)
                    
                    all_context_chunks.extend(filtered_chunks)
                    
                    # Group context by source for better formatting
                    resume_chunks = [c for c in filtered_chunks if c.get('source') == 'resume']
                    profile_chunks = [c for c in filtered_chunks if c.get('source') == 'profile']
                    
                    # Format resume context
                    if resume_chunks:
                        resume_context = "\n".join([chunk['content'] for chunk in resume_chunks])
                        context_parts.append(f"Resume Information:\n{resume_context}")
                    
                    # Format profile context
                    if profile_chunks:
                        profile_context = "\n".join([chunk['content'] for chunk in profile_chunks])
                        context_parts.append(f"Profile Information:\n{profile_context}")
                    
                    logger.info(f"Retrieved {len(filtered_chunks)} context chunks for user {user_id} (resume: {len(resume_chunks)}, profile: {len(profile_chunks)})")
                    
                except Exception as e:
                    logger.warning(f"Comprehensive context search failed, falling back to resume-only: {e}")
                    # Fallback to resume-only search if comprehensive search fails
                    if self.resume_service:
                        try:
                            resume_chunks = self.resume_service.search_resume_content(
                                user_id=user_id,
                                query=query,
                                n_results=self.max_context_chunks
                            )
                            
                            filtered_resume_chunks = []
                            for chunk in resume_chunks:
                                if chunk.get('distance') is None or chunk['distance'] <= self.context_similarity_threshold:
                                    filtered_resume_chunks.append(chunk)
                            
                            all_context_chunks.extend(filtered_resume_chunks)
                            
                            if filtered_resume_chunks:
                                resume_context = "\n".join([chunk['content'] for chunk in filtered_resume_chunks])
                                context_parts.append(f"Resume Information:\n{resume_context}")
                                
                            logger.info(f"Retrieved {len(filtered_resume_chunks)} resume chunks for user {user_id}")
                            
                        except Exception as resume_error:
                            logger.error(f"Resume context search also failed: {resume_error}")
            
            # Format final context text
            if context_parts:
                context_text = f"User Background Information:\n\n" + "\n\n".join(context_parts)
            else:
                context_text = "No specific user background information available. Please ask the user to provide relevant details about their background, experience, and goals."
            
            return all_context_chunks, context_text
            
        except Exception as e:
            logger.error(f"Failed to retrieve user context: {e}")
            # Graceful degradation - provide helpful message
            fallback_context = "No user background information available. Please ask the user to provide relevant details about their background, experience, and goals to give more personalized advice."
            return [], fallback_context
    
    def _create_chat_prompt_template(self) -> ChatPromptTemplate:
        """Create LangChain prompt template for career mentoring"""
        system_prompt = """You are an experienced career mentor and advisor. Your role is to provide personalized, actionable career guidance based on the user's background and goals.

Key guidelines:
- ALWAYS use the provided user background information to give personalized advice when available
- Never ask users to re-share information that is already provided in their background
- Be encouraging but realistic about career transitions and timelines
- Provide specific, actionable steps when possible
- Focus on practical skills, experiences, and strategies
- Consider industry trends and market demands
- Be supportive and understanding of career challenges
- If background information is limited, ask targeted questions to fill specific gaps

IMPORTANT: The user background information below contains their resume and profile data. Use this information to provide personalized responses without asking them to repeat what's already known about their experience, education, or goals."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        return prompt
    
    async def initialize_chat_session(self, request: ChatInitRequest) -> ChatSession:
        """Initialize a new chat session"""
        try:
            # Create new session
            session = ChatSession(
                user_id=request.user_id,
                title=request.title or f"Chat Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Store session
            self.active_sessions[session.id] = session
            
            # Create memory for session
            self._create_session_memory(session.id)
            
            # Add initial system message if provided
            if request.initial_message:
                initial_message = ChatMessage(
                    role=MessageRole.USER,
                    content=request.initial_message
                )
                session.messages.append(initial_message)
                
                # Process initial message
                response = await self.send_message(ChatMessageRequest(
                    session_id=session.id,
                    message=request.initial_message
                ))
            
            logger.info(f"Initialized chat session {session.id} for user {request.user_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to initialize chat session: {e}")
            raise
    
    async def send_message(self, request: ChatMessageRequest) -> ChatResponse:
        """Send a message and get AI response with RAG context"""
        try:
            start_time = datetime.utcnow()
            
            # Get session
            if request.session_id not in self.active_sessions:
                raise ValueError(f"Chat session {request.session_id} not found")
            
            session = self.active_sessions[request.session_id]
            
            # Add user message to session
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=request.message
            )
            session.messages.append(user_message)
            session.updated_at = datetime.utcnow()
            
            # Get session memory
            memory = self._get_session_memory(request.session_id)
            
            # Add user message to memory
            memory.chat_memory.add_user_message(request.message)
            
            # Always get user context for personalized responses
            # This ensures RAG integration is automatic and transparent
            try:
                context_chunks, context_text = await self._get_user_context(
                    session.user_id, 
                    request.message
                )
                logger.info(f"Successfully retrieved context for user {session.user_id}")
            except Exception as rag_error:
                logger.error(f"RAG context retrieval failed for user {session.user_id}: {rag_error}")
                # Graceful degradation - continue without context
                context_chunks = []
                context_text = "Unable to retrieve user background information at this time. Please provide relevant details about your background and goals for personalized advice."
            
            # Create prompt template
            prompt_template = self._create_chat_prompt_template()
            
            # Get AI service
            ai_service = await self._get_ai_service()
            
            # Prepare prompt variables
            chat_history = memory.chat_memory.messages
            
            # Format the complete prompt
            formatted_prompt = prompt_template.format(
                context=context_text,
                chat_history=chat_history,
                question=request.message
            )
            
            # Generate AI response
            ai_response = await ai_service.generate_text(
                prompt=formatted_prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=800,
                temperature=0.8
            )
            
            # Create assistant message
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=ai_response,
                metadata={
                    "context_chunks_used": len(context_chunks),
                    "model_used": ModelType.GEMINI_FLASH.value
                }
            )
            
            # Add to session and memory
            session.messages.append(assistant_message)
            memory.chat_memory.add_ai_message(ai_response)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Persist session to database
            await self.persist_session_after_message(request.session_id)
            
            logger.info(f"Generated response for session {request.session_id} in {processing_time:.2f}s")
            
            return ChatResponse(
                session_id=session.id,
                message=assistant_message,
                context_used=context_chunks,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise
    
    def get_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return self.active_sessions.get(session_id)
    
    def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all chat sessions for a user"""
        return [
            session for session in self.active_sessions.values()
            if session.user_id == user_id and session.is_active
        ]
    
    def delete_chat_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            if session_id in self.active_sessions:
                # Mark as inactive instead of deleting (for audit trail)
                self.active_sessions[session_id].is_active = False
                
                # Clean up memory
                if session_id in self.session_memories:
                    del self.session_memories[session_id]
                
                logger.info(f"Deleted chat session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete chat session {session_id}: {e}")
            return False
    
    def clear_session_memory(self, session_id: str) -> bool:
        """Clear memory for a specific session"""
        try:
            if session_id in self.session_memories:
                self.session_memories[session_id].clear()
                logger.info(f"Cleared memory for session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to clear session memory: {e}")
            return False
    
    async def regenerate_response(self, session_id: str, message_id: str) -> Optional[ChatResponse]:
        """Regenerate the last AI response"""
        try:
            if session_id not in self.active_sessions:
                return None
            
            session = self.active_sessions[session_id]
            
            # Find the message and the previous user message
            message_index = None
            for i, msg in enumerate(session.messages):
                if msg.id == message_id and msg.role == MessageRole.ASSISTANT:
                    message_index = i
                    break
            
            if message_index is None or message_index == 0:
                return None
            
            # Get the user message that prompted this response
            user_message = session.messages[message_index - 1]
            if user_message.role != MessageRole.USER:
                return None
            
            # Remove the old AI response from session and memory
            session.messages.pop(message_index)
            memory = self._get_session_memory(session_id)
            
            # Rebuild memory from remaining messages
            memory.clear()
            for msg in session.messages:
                if msg.role == MessageRole.USER:
                    memory.chat_memory.add_user_message(msg.content)
                elif msg.role == MessageRole.ASSISTANT:
                    memory.chat_memory.add_ai_message(msg.content)
            
            # Generate new response
            request = ChatMessageRequest(
                session_id=session_id,
                message=user_message.content,
                include_context=True
            )
            
            return await self.send_message(request)
            
        except Exception as e:
            logger.error(f"Failed to regenerate response: {e}")
            return None
    
    def get_session_stats(self, session_id: str) -> Optional[Dict]:
        """Get statistics for a chat session"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        user_messages = [msg for msg in session.messages if msg.role == MessageRole.USER]
        assistant_messages = [msg for msg in session.messages if msg.role == MessageRole.ASSISTANT]
        
        return {
            "session_id": session_id,
            "user_id": session.user_id,
            "total_messages": len(session.messages),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "duration_minutes": (session.updated_at - session.created_at).total_seconds() / 60,
            "is_active": session.is_active
        }
    
    async def health_check(self) -> Dict:
        """Check the health of the chat service"""
        try:
            # Check AI service
            ai_service = await self._get_ai_service()
            ai_health = await ai_service.health_check()
            
            # Check embedding service if available
            embedding_health = {"status": "not_available"}
            if self.embedding_service:
                try:
                    embedding_health = self.embedding_service.health_check()
                except Exception as e:
                    embedding_health = {"status": "error", "error": str(e)}
            
            return {
                "status": "healthy",
                "active_sessions": len([s for s in self.active_sessions.values() if s.is_active]),
                "total_sessions": len(self.active_sessions),
                "memory_sessions": len(self.session_memories),
                "ai_service_status": ai_health.get("status", "unknown"),
                "embedding_service_status": embedding_health.get("status", "not_available"),
                "embedding_available": EMBEDDING_AVAILABLE,
                "resume_available": RESUME_AVAILABLE,
                "components": {
                    "ai_service": ai_health,
                    "embedding_service": embedding_health
                }
            }
            
        except Exception as e:
            logger.error(f"Chat service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "active_sessions": len([s for s in self.active_sessions.values() if s.is_active]),
                "total_sessions": len(self.active_sessions)
            }
    
    # Database persistence methods
    async def save_chat_session(self, session: ChatSession) -> str:
        """Save chat session to database"""
        session_id = await self.db_service.save_chat_session(session)
        # Keep in active sessions if it's active
        if session.is_active:
            self.active_sessions[session_id] = session
        return session_id
    
    async def load_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Load chat session from database"""
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Load from database
        session = await self.db_service.load_chat_session(session_id)
        if session and session.is_active:
            # Load into active sessions and create memory
            self.active_sessions[session_id] = session
            self._load_session_into_memory(session)
        
        return session
    
    async def load_user_chat_sessions(self, user_id: str, active_only: bool = True) -> List[ChatSession]:
        """Load all chat sessions for a user from database"""
        return await self.db_service.load_user_chat_sessions(user_id, active_only)
    
    async def persist_session_after_message(self, session_id: str) -> bool:
        """Save session to database after adding a message"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                await self.save_chat_session(session)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to persist session {session_id}: {e}")
            return False
    
    async def refresh_user_context(self, user_id: str) -> bool:
        """Refresh user's RAG context after profile or resume updates"""
        try:
            if not self.embedding_service:
                logger.warning("Embedding service not available for context refresh")
                return False
            
            # Get user profile data from database
            try:
                profile = await self.db_service.get_profile(user_id)
                if profile:
                    # Create context text from profile data
                    context_parts = []
                    
                    # Add education information
                    if profile.get('education'):
                        edu = profile['education']
                        edu_text = f"Education: {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')} ({edu.get('graduationYear', '')})"
                        context_parts.append(edu_text)
                    
                    # Add career background
                    if profile.get('career_background'):
                        context_parts.append(f"Career Background: {profile['career_background']}")
                    
                    # Add current role
                    if profile.get('current_role'):
                        context_parts.append(f"Current Role: {profile['current_role']}")
                    
                    # Add target roles
                    if profile.get('target_roles'):
                        target_roles_text = ", ".join(profile['target_roles'])
                        context_parts.append(f"Target Roles: {target_roles_text}")
                    
                    # Add additional details
                    if profile.get('additional_details'):
                        context_parts.append(f"Additional Details: {profile['additional_details']}")
                    
                    # Combine all context
                    profile_context = "\n".join(context_parts)
                    
                    # Store profile context as embeddings for RAG
                    if profile_context.strip():
                        success = self.embedding_service.store_profile_context(user_id, profile_context)
                        if success:
                            logger.info(f"Successfully refreshed RAG context for user {user_id}")
                            return True
                        else:
                            logger.error(f"Failed to store profile context for user {user_id}")
                            return False
                    else:
                        logger.warning(f"No profile context to store for user {user_id}")
                        return True
                else:
                    logger.warning(f"No profile found for user {user_id}")
                    return True
                    
            except Exception as profile_error:
                logger.error(f"Failed to get profile for user {user_id}: {profile_error}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to refresh user context for {user_id}: {e}")
            return False

# Singleton instance for global use
_chat_service_instance = None

async def get_chat_service() -> RAGChatService:
    """Get or create singleton chat service instance"""
    global _chat_service_instance
    
    if _chat_service_instance is None:
        _chat_service_instance = RAGChatService()
    
    return _chat_service_instance