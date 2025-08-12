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
from models.roadmap import Roadmap, RoadmapPhase
from services.ai_service import AIService, get_ai_service, ModelType
from services.database_service import DatabaseService
from services.roadmap_service import get_roadmap_service

# Optional imports with graceful fallback
try:
    from services.embedding_service import EmbeddingService
    EMBEDDING_AVAILABLE = True
except ImportError:
    EmbeddingService = None
    EMBEDDING_AVAILABLE = False

logger = logging.getLogger(__name__)

class RoadmapChatService:
    """Roadmap-specific chat service with context-aware responses"""
    
    def __init__(self):
        self.ai_service: Optional[AIService] = None
        self.db_service = DatabaseService()
        self.roadmap_service = None
        
        # Initialize optional services
        self.embedding_service = EmbeddingService() if EMBEDDING_AVAILABLE else None
        
        # In-memory session storage for active roadmap chat sessions
        self.active_sessions: Dict[str, ChatSession] = {}
        self.session_memories: Dict[str, ConversationBufferWindowMemory] = {}
        self.roadmap_contexts: Dict[str, Dict[str, Any]] = {}  # Cache roadmap contexts
        
        # Configuration
        self.max_memory_messages = 8  # Keep last 8 messages in memory for roadmap chat
        self.max_context_chunks = 3   # Max roadmap context chunks to include
        
        logger.info(f"Roadmap Chat Service initialized (Embedding: {EMBEDDING_AVAILABLE})")
    
    async def _get_ai_service(self) -> AIService:
        """Get or initialize AI service"""
        if self.ai_service is None:
            self.ai_service = await get_ai_service()
        return self.ai_service
    
    async def _get_roadmap_service(self):
        """Get or initialize roadmap service"""
        if self.roadmap_service is None:
            self.roadmap_service = await get_roadmap_service()
        return self.roadmap_service
    
    def _create_session_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Create LangChain memory for a roadmap chat session"""
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
        """Load existing roadmap chat session into LangChain memory"""
        memory = self._create_session_memory(session.id)
        
        # Load recent messages into memory
        recent_messages = session.messages[-self.max_memory_messages:]
        
        for message in recent_messages:
            if message.role == MessageRole.USER:
                memory.chat_memory.add_user_message(message.content)
            elif message.role == MessageRole.ASSISTANT:
                memory.chat_memory.add_ai_message(message.content)
        
        return memory
    
    async def _get_roadmap_context(self, roadmap_id: str, query: str) -> Tuple[Dict[str, Any], str]:
        """Retrieve roadmap context for the chat"""
        try:
            # Check if we have cached context
            if roadmap_id in self.roadmap_contexts:
                cached_context = self.roadmap_contexts[roadmap_id]
                # Check if cache is still fresh (within 5 minutes)
                if (datetime.utcnow() - cached_context['cached_at']).total_seconds() < 300:
                    return cached_context['roadmap_data'], cached_context['context_text']
            
            # Load fresh roadmap data
            roadmap_service = await self._get_roadmap_service()
            roadmap = await roadmap_service.load_roadmap(roadmap_id)
            
            if not roadmap:
                raise ValueError(f"Roadmap {roadmap_id} not found")
            
            # Create comprehensive roadmap context
            context_parts = []
            
            # Basic roadmap info
            context_parts.append(f"Roadmap Title: {roadmap.title}")
            context_parts.append(f"Career Transition: {roadmap.current_role} → {roadmap.target_role}")
            context_parts.append(f"Description: {roadmap.description}")
            context_parts.append(f"Total Timeline: {roadmap.total_estimated_weeks} weeks")
            context_parts.append(f"Overall Progress: {roadmap.overall_progress_percentage}%")
            
            # Phase information
            context_parts.append("\nRoadmap Phases:")
            for phase in roadmap.phases:
                phase_status = "✓ Completed" if phase.is_completed else "⏳ In Progress" if phase.started_date else "📋 Not Started"
                context_parts.append(f"\nPhase {phase.phase_number}: {phase.title} ({phase_status})")
                context_parts.append(f"Duration: {phase.duration_weeks} weeks")
                context_parts.append(f"Description: {phase.description}")
                
                # Skills to develop
                if phase.skills_to_develop:
                    skills_text = ", ".join([f"{skill.name} ({skill.current_level.value} → {skill.target_level.value})" 
                                           for skill in phase.skills_to_develop])
                    context_parts.append(f"Skills: {skills_text}")
                
                # Milestones
                if phase.milestones:
                    milestones_text = []
                    for milestone in phase.milestones:
                        status = "✓" if milestone.is_completed else "○"
                        milestones_text.append(f"{status} {milestone.title}")
                    context_parts.append(f"Milestones: {'; '.join(milestones_text)}")
                
                # Learning resources
                if phase.learning_resources:
                    resources_text = ", ".join([resource.title for resource in phase.learning_resources])
                    context_parts.append(f"Resources: {resources_text}")
            
            # Prerequisites and outcomes
            if roadmap.phases:
                all_prerequisites = []
                all_outcomes = []
                for phase in roadmap.phases:
                    all_prerequisites.extend(phase.prerequisites)
                    all_outcomes.extend(phase.outcomes)
                
                if all_prerequisites:
                    context_parts.append(f"\nKey Prerequisites: {'; '.join(set(all_prerequisites))}")
                if all_outcomes:
                    context_parts.append(f"\nExpected Outcomes: {'; '.join(set(all_outcomes))}")
            
            # Create final context text
            context_text = "\n".join(context_parts)
            
            # Cache the context
            roadmap_data = {
                "id": roadmap.id,
                "title": roadmap.title,
                "current_role": roadmap.current_role,
                "target_role": roadmap.target_role,
                "phases": roadmap.phases,
                "total_weeks": roadmap.total_estimated_weeks,
                "progress": roadmap.overall_progress_percentage
            }
            
            self.roadmap_contexts[roadmap_id] = {
                "roadmap_data": roadmap_data,
                "context_text": context_text,
                "cached_at": datetime.utcnow()
            }
            
            logger.info(f"Retrieved roadmap context for {roadmap_id}")
            return roadmap_data, context_text
            
        except Exception as e:
            logger.error(f"Failed to retrieve roadmap context for {roadmap_id}: {e}")
            # Graceful degradation
            fallback_context = f"Unable to retrieve roadmap context. Please ensure roadmap {roadmap_id} exists and is accessible."
            return {}, fallback_context
    
    def _create_roadmap_chat_prompt_template(self) -> ChatPromptTemplate:
        """Create LangChain prompt template for roadmap-specific chat"""
        system_prompt = """You are an expert career coach and roadmap advisor. You are helping a user with their specific career roadmap and can provide detailed guidance, answer questions, and help with minor edits.

Your capabilities:
- Answer questions about the roadmap phases, skills, milestones, and resources
- Provide detailed explanations about why certain skills or steps are important
- Suggest modifications to timelines, resources, or approaches
- Help prioritize tasks and milestones
- Offer encouragement and motivation
- Clarify any confusing aspects of the roadmap

Key guidelines:
- ALWAYS reference the specific roadmap context provided below
- Be specific about phase numbers, skill names, and milestone titles when discussing the roadmap
- If asked about edits, provide clear, actionable suggestions
- Focus on practical, implementable advice
- Be encouraging but realistic about timelines and challenges
- If you don't have enough context about something, ask clarifying questions

IMPORTANT: You are discussing the user's specific roadmap shown in the context below. Always reference specific details from their roadmap when providing advice."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Here is the user's roadmap context:\n\n{roadmap_context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        return prompt
    
    async def initialize_roadmap_chat_session(
        self, 
        roadmap_id: str, 
        user_id: str, 
        title: Optional[str] = None
    ) -> ChatSession:
        """Initialize a new roadmap-specific chat session"""
        try:
            # Verify roadmap exists and get basic info
            roadmap_data, _ = await self._get_roadmap_context(roadmap_id, "")
            
            if not roadmap_data:
                raise ValueError(f"Cannot initialize chat for roadmap {roadmap_id}")
            
            # Create new session with roadmap-specific metadata
            session = ChatSession(
                user_id=user_id,
                title=title or f"Chat: {roadmap_data.get('title', 'Roadmap')}",
                metadata={
                    "roadmap_id": roadmap_id,
                    "roadmap_title": roadmap_data.get('title'),
                    "chat_type": "roadmap_specific"
                }
            )
            
            # Store session
            self.active_sessions[session.id] = session
            
            # Create memory for session
            self._create_session_memory(session.id)
            
            logger.info(f"Initialized roadmap chat session {session.id} for roadmap {roadmap_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to initialize roadmap chat session: {e}")
            raise
    
    async def send_roadmap_message(
        self, 
        session_id: str, 
        message: str, 
        roadmap_id: str
    ) -> ChatResponse:
        """Send a message in a roadmap-specific chat session"""
        try:
            start_time = datetime.utcnow()
            
            # Get session
            if session_id not in self.active_sessions:
                raise ValueError(f"Roadmap chat session {session_id} not found")
            
            session = self.active_sessions[session_id]
            
            # Verify session is for the correct roadmap
            if session.metadata.get("roadmap_id") != roadmap_id:
                raise ValueError(f"Session {session_id} is not associated with roadmap {roadmap_id}")
            
            # Add user message to session
            user_message = ChatMessage(
                role=MessageRole.USER,
                content=message
            )
            session.messages.append(user_message)
            session.updated_at = datetime.utcnow()
            
            # Get session memory
            memory = self._get_session_memory(session_id)
            
            # Add user message to memory
            memory.chat_memory.add_user_message(message)
            
            # Get roadmap context
            roadmap_data, roadmap_context = await self._get_roadmap_context(roadmap_id, message)
            
            # Create prompt template
            prompt_template = self._create_roadmap_chat_prompt_template()
            
            # Get AI service
            ai_service = await self._get_ai_service()
            
            # Prepare prompt variables
            chat_history = memory.chat_memory.messages
            
            # Format the complete prompt
            formatted_prompt = prompt_template.format(
                roadmap_context=roadmap_context,
                chat_history=chat_history,
                question=message
            )
            
            # Generate AI response
            ai_response = await ai_service.generate_text(
                prompt=formatted_prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=600,
                temperature=0.7
            )
            
            # Create assistant message
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=ai_response,
                metadata={
                    "roadmap_id": roadmap_id,
                    "roadmap_context_used": True,
                    "model_used": ModelType.GEMINI_FLASH.value
                }
            )
            
            # Add to session and memory
            session.messages.append(assistant_message)
            memory.chat_memory.add_ai_message(ai_response)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Persist session to database
            await self.persist_roadmap_session(session_id)
            
            logger.info(f"Generated roadmap response for session {session_id} in {processing_time:.2f}s")
            
            return ChatResponse(
                session_id=session.id,
                message=assistant_message,
                context_used=[{"roadmap_id": roadmap_id, "context_type": "roadmap_specific"}],
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Failed to send roadmap message: {e}")
            raise
    
    async def process_roadmap_edit_request(
        self, 
        session_id: str, 
        roadmap_id: str, 
        edit_request: str
    ) -> Dict[str, Any]:
        """Process a request to edit the roadmap based on chat conversation"""
        try:
            # Get current roadmap context
            roadmap_data, roadmap_context = await self._get_roadmap_context(roadmap_id, edit_request)
            
            # Create edit analysis prompt
            edit_prompt = f"""Analyze the following edit request for a career roadmap and determine what changes should be made.

Current Roadmap Context:
{roadmap_context}

User Edit Request: {edit_request}

Analyze the request and provide a structured response in the following JSON format:
{{
    "edit_type": "timeline_adjustment|resource_addition|milestone_modification|phase_reorder|skill_priority_change|other",
    "confidence": 0.8,
    "suggested_changes": [
        {{
            "target": "phase_1|phase_2|milestone_x|skill_y",
            "change_type": "modify|add|remove|reorder",
            "description": "Clear description of the change",
            "new_value": "The new value or content"
        }}
    ],
    "explanation": "Why these changes make sense for the user's goals",
    "requires_regeneration": false
}}

Only suggest changes that are reasonable and align with the user's career goals. If the request is unclear or too vague, set confidence to low and ask for clarification."""

            # Get AI service
            ai_service = await self._get_ai_service()
            
            # Generate edit analysis
            edit_response = await ai_service.generate_text(
                prompt=edit_prompt,
                model_type=ModelType.GEMINI_FLASH,
                max_tokens=800,
                temperature=0.3  # Lower temperature for more consistent structured output
            )
            
            # Try to parse JSON response
            try:
                edit_analysis = json.loads(edit_response)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                edit_analysis = {
                    "edit_type": "other",
                    "confidence": 0.5,
                    "suggested_changes": [],
                    "explanation": "Unable to parse edit request. Please be more specific about what you'd like to change.",
                    "requires_regeneration": False
                }
            
            logger.info(f"Processed edit request for roadmap {roadmap_id}")
            return edit_analysis
            
        except Exception as e:
            logger.error(f"Failed to process roadmap edit request: {e}")
            return {
                "edit_type": "error",
                "confidence": 0.0,
                "suggested_changes": [],
                "explanation": f"Error processing edit request: {str(e)}",
                "requires_regeneration": False
            }
    
    def get_roadmap_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a roadmap chat session by ID"""
        return self.active_sessions.get(session_id)
    
    def get_roadmap_sessions(self, roadmap_id: str) -> List[ChatSession]:
        """Get all chat sessions for a specific roadmap"""
        return [
            session for session in self.active_sessions.values()
            if session.metadata.get("roadmap_id") == roadmap_id and session.is_active
        ]
    
    def delete_roadmap_chat_session(self, session_id: str) -> bool:
        """Delete a roadmap chat session"""
        try:
            if session_id in self.active_sessions:
                # Mark as inactive instead of deleting (for audit trail)
                self.active_sessions[session_id].is_active = False
                
                # Clean up memory
                if session_id in self.session_memories:
                    del self.session_memories[session_id]
                
                logger.info(f"Deleted roadmap chat session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete roadmap chat session {session_id}: {e}")
            return False
    
    def clear_roadmap_context_cache(self, roadmap_id: str) -> bool:
        """Clear cached context for a roadmap (call when roadmap is updated)"""
        try:
            if roadmap_id in self.roadmap_contexts:
                del self.roadmap_contexts[roadmap_id]
                logger.info(f"Cleared context cache for roadmap {roadmap_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to clear context cache for roadmap {roadmap_id}: {e}")
            return False
    
    async def health_check(self) -> Dict:
        """Check the health of the roadmap chat service"""
        try:
            # Check AI service
            ai_service = await self._get_ai_service()
            ai_health = await ai_service.health_check()
            
            return {
                "status": "healthy",
                "active_sessions": len([s for s in self.active_sessions.values() if s.is_active]),
                "total_sessions": len(self.active_sessions),
                "cached_roadmaps": len(self.roadmap_contexts),
                "ai_service_status": ai_health.get("status", "unknown"),
                "embedding_available": EMBEDDING_AVAILABLE,
                "components": {
                    "ai_service": ai_health
                }
            }
            
        except Exception as e:
            logger.error(f"Roadmap chat service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "active_sessions": len([s for s in self.active_sessions.values() if s.is_active]),
                "total_sessions": len(self.active_sessions)
            }
    
    # Database persistence methods
    async def save_roadmap_chat_session(self, session: ChatSession) -> str:
        """Save roadmap chat session to database"""
        session_id = await self.db_service.save_chat_session(session)
        # Keep in active sessions if it's active
        if session.is_active:
            self.active_sessions[session_id] = session
        return session_id
    
    async def load_roadmap_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Load roadmap chat session from database"""
        # Check active sessions first
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        
        # Load from database
        session = await self.db_service.load_chat_session(session_id)
        if session and session.is_active and session.metadata.get("chat_type") == "roadmap_specific":
            # Load into active sessions and create memory
            self.active_sessions[session_id] = session
            self._load_session_into_memory(session)
        
        return session
    
    async def persist_roadmap_session(self, session_id: str) -> bool:
        """Save roadmap session to database after adding a message"""
        try:
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                await self.save_roadmap_chat_session(session)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to persist roadmap session {session_id}: {e}")
            return False

# Singleton instance for global use
_roadmap_chat_service_instance = None

async def get_roadmap_chat_service() -> RoadmapChatService:
    """Get or create singleton roadmap chat service instance"""
    global _roadmap_chat_service_instance
    
    if _roadmap_chat_service_instance is None:
        _roadmap_chat_service_instance = RoadmapChatService()
    
    return _roadmap_chat_service_instance