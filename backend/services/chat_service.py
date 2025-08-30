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

# Multi-Agent System import
try:
    from services.multi_agent_service import get_multi_agent_service, MultiAgentService
    from models.agent import RequestType
    MULTI_AGENT_AVAILABLE = True
except ImportError:
    get_multi_agent_service = None
    MultiAgentService = None
    RequestType = None
    MULTI_AGENT_AVAILABLE = False

logger = logging.getLogger(__name__)

class RAGChatService:
    """RAG-enabled AI chat service with memory management using LangChain"""
    
    def __init__(self):
        self.ai_service: Optional[AIService] = None
        self.db_service = DatabaseService()
        
        # Initialize optional services
        self.embedding_service = EmbeddingService() if EMBEDDING_AVAILABLE else None
        self.resume_service = ResumeProcessingService() if RESUME_AVAILABLE else None
        
        # Multi-Agent System
        self.multi_agent_service: Optional[MultiAgentService] = None
        
        # In-memory session storage for active sessions
        self.active_sessions: Dict[str, ChatSession] = {}
        self.session_memories: Dict[str, ConversationBufferWindowMemory] = {}
        
        # Configuration
        self.max_memory_messages = 10  # Keep last 10 messages in memory
        self.max_context_chunks = 5    # Max RAG context chunks to include
        self.context_similarity_threshold = 0.7  # Minimum similarity for context inclusion
        
        # Workflow routing patterns
        self.workflow_patterns = self._initialize_workflow_patterns()
        
        logger.info(f"RAG Chat Service initialized (Embedding: {EMBEDDING_AVAILABLE}, Resume: {RESUME_AVAILABLE}, MultiAgent: {MULTI_AGENT_AVAILABLE})")
    
    async def _get_ai_service(self) -> AIService:
        """Get or initialize AI service"""
        if self.ai_service is None:
            self.ai_service = await get_ai_service()
        return self.ai_service
    
    async def _get_multi_agent_service(self) -> Optional[MultiAgentService]:
        """Get or initialize Multi-Agent Service"""
        if not MULTI_AGENT_AVAILABLE:
            return None
            
        if self.multi_agent_service is None:
            try:
                self.multi_agent_service = await get_multi_agent_service()
                logger.info("Multi-Agent Service initialized for chat service")
            except Exception as e:
                logger.warning(f"Failed to initialize multi-agent service: {e}")
                return None
        
        return self.multi_agent_service
    
    def _initialize_workflow_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for routing chat requests to workflows"""
        return {
            "career_transition": {
                "keywords": ["transition", "switch careers", "change roles", "move from", "become a"],
                "workflow": "career_transition",
                "confidence_threshold": 0.7
            },
            "roadmap_generation": {
                "keywords": ["roadmap", "plan", "path to", "how to become", "steps to"],
                "workflow": "career_transition",
                "confidence_threshold": 0.6
            },
            "skill_analysis": {
                "keywords": ["skills", "what skills", "skill gap", "competencies", "abilities"],
                "workflow": "comprehensive_analysis",
                "confidence_threshold": 0.5
            },
            "comprehensive_analysis": {
                "keywords": ["analyze", "assessment", "evaluation", "comprehensive", "detailed analysis"],
                "workflow": "comprehensive_analysis",
                "confidence_threshold": 0.6
            }
        }
    
    def _should_use_workflow(self, message: str, user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Determine if a message should be routed through multi-agent system"""
        if not MULTI_AGENT_AVAILABLE:
            return None
        
        message_lower = message.lower()
        
        # Check for workflow patterns
        for pattern_name, pattern_config in self.workflow_patterns.items():
            keyword_matches = sum(1 for keyword in pattern_config["keywords"] if keyword in message_lower)
            confidence = keyword_matches / len(pattern_config["keywords"])
            
            if confidence >= pattern_config["confidence_threshold"]:
                return {
                    "workflow_name": pattern_config["workflow"],
                    "pattern_matched": pattern_name,
                    "confidence": confidence,
                    "request_type": self._map_pattern_to_request_type(pattern_name)
                }
        
        # Check message length and complexity for comprehensive analysis
        if len(message.split()) > 20 and any(word in message_lower for word in ["help me", "advice", "guidance", "recommend"]):
            return {
                "workflow_name": "comprehensive_analysis",
                "pattern_matched": "complex_request",
                "confidence": 0.6,
                "request_type": RequestType.CAREER_ADVICE
            }
        
        return None
    
    def _map_pattern_to_request_type(self, pattern_name: str) -> 'RequestType':
        """Map workflow pattern to RequestType enum"""
        if not MULTI_AGENT_AVAILABLE:
            return None
            
        mapping = {
            "career_transition": RequestType.CAREER_TRANSITION,
            "roadmap_generation": RequestType.ROADMAP_GENERATION,
            "skill_analysis": RequestType.SKILL_ANALYSIS,
            "comprehensive_analysis": RequestType.CAREER_ADVICE
        }
        return mapping.get(pattern_name, RequestType.CAREER_ADVICE)
    
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
            
            logger.info(f"Starting user context retrieval for user {user_id}")
            
            # Always try to get profile data from database first
            try:
                profile = await self.db_service.get_profile(user_id)
                if profile:
                    logger.info(f"Found profile data for user {user_id}")
                    # Create context text from profile data
                    profile_context_parts = []
                    
                    # Add name
                    if profile.get('name'):
                        profile_context_parts.append(f"Name: {profile['name']}")
                    
                    # Add education information
                    if profile.get('education'):
                        edu = profile['education']
                        if isinstance(edu, dict):
                            edu_text = f"Education: {edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')} ({edu.get('graduationYear', '')})"
                            profile_context_parts.append(edu_text)
                    
                    # Add career background
                    if profile.get('career_background'):
                        profile_context_parts.append(f"Career Background: {profile['career_background']}")
                    
                    # Add current role
                    if profile.get('current_role'):
                        profile_context_parts.append(f"Current Role: {profile['current_role']}")
                    
                    # Add target roles
                    if profile.get('target_roles'):
                        if isinstance(profile['target_roles'], list):
                            target_roles_text = ", ".join(profile['target_roles'])
                        else:
                            target_roles_text = str(profile['target_roles'])
                        profile_context_parts.append(f"Target Roles: {target_roles_text}")
                    
                    # Add additional details
                    if profile.get('additional_details'):
                        profile_context_parts.append(f"Additional Details: {profile['additional_details']}")
                    
                    # Combine profile context
                    if profile_context_parts:
                        profile_context = "\n".join(profile_context_parts)
                        context_parts.append(f"Profile Information:\n{profile_context}")
                        logger.info(f"Added profile context for user {user_id}")
                else:
                    logger.warning(f"No profile found for user {user_id}")
            except Exception as profile_error:
                logger.error(f"Failed to get profile for user {user_id}: {profile_error}")
            
            # Try to get resume data from database
            try:
                resume = await self.db_service.get_user_resume(user_id)
                if resume and resume.get('parsed_content'):
                    logger.info(f"Found resume data for user {user_id}")
                    
                    # Extract text content from parsed resume
                    parsed_content = resume['parsed_content']
                    if isinstance(parsed_content, dict) and parsed_content.get('text_content'):
                        resume_text = parsed_content['text_content']
                        
                        # Limit resume text to avoid token overflow (keep first 2000 characters)
                        if len(resume_text) > 2000:
                            resume_text = resume_text[:2000] + "... [resume content truncated]"
                        
                        context_parts.append(f"Resume Content:\n{resume_text}")
                        logger.info(f"Added full resume content for user {user_id}")
                else:
                    logger.warning(f"No resume found for user {user_id}")
            except Exception as resume_error:
                logger.error(f"Failed to get resume for user {user_id}: {resume_error}")
            
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
                    embedding_profile_chunks = [c for c in filtered_chunks if c.get('source') == 'profile']
                    
                    # Format resume context
                    if resume_chunks:
                        resume_context = "\n".join([chunk['content'] for chunk in resume_chunks])
                        context_parts.append(f"Resume Information:\n{resume_context}")
                        logger.info(f"Added resume context from embeddings for user {user_id}")
                    
                    # Format profile context from embeddings (if different from direct profile)
                    if embedding_profile_chunks:
                        embedding_profile_context = "\n".join([chunk['content'] for chunk in embedding_profile_chunks])
                        context_parts.append(f"Additional Profile Information:\n{embedding_profile_context}")
                        logger.info(f"Added embedding profile context for user {user_id}")
                    
                    logger.info(f"Retrieved {len(filtered_chunks)} context chunks for user {user_id} (resume: {len(resume_chunks)}, profile: {len(embedding_profile_chunks)})")
                    
                    # Debug logging
                    if len(resume_chunks) == 0:
                        logger.warning(f"No resume chunks found for user {user_id}. This might indicate the resume hasn't been uploaded or processed.")
                    
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
                                logger.info(f"Added resume context from fallback for user {user_id}")
                                
                            logger.info(f"Retrieved {len(filtered_resume_chunks)} resume chunks for user {user_id}")
                            
                        except Exception as resume_error:
                            logger.error(f"Resume context search also failed: {resume_error}")
            else:
                logger.warning("Embedding service not available")
            
            # Format final context text
            if context_parts:
                context_text = f"User Background Information:\n\n" + "\n\n".join(context_parts)
                logger.info(f"Successfully created context for user {user_id} with {len(context_parts)} sections")
            else:
                context_text = "No specific user background information available. Please ask the user to provide relevant details about their background, experience, and goals."
                logger.warning(f"No context found for user {user_id}")
            
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
- If you see profile information, resume content, or other background details, USE THEM immediately in your response
- When a user asks about their strengths, weaknesses, or career advice, reference their specific background, education, experience, and goals
- When analyzing their resume, provide specific examples from their actual experience, education, and skills
- Never provide hypothetical examples when you have access to their real resume content
- Be encouraging but realistic about career transitions and timelines
- Provide specific, actionable steps when possible
- Focus on practical skills, experiences, and strategies
- Consider industry trends and market demands
- Be supportive and understanding of career challenges
- If background information is limited, ask targeted questions to fill specific gaps

CRITICAL: The user background information provided contains their actual resume content and profile data. You have access to their real experience, education, skills, and career history. You must reference and use this specific information in your responses. Do not ask them to provide information that is already available in their background context. When they ask you to analyze or critique their resume, use their actual resume content, not hypothetical examples."""

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
        """Send a message and get AI response with RAG context or workflow routing"""
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
            
            # Check if request should be routed through workflow
            user_context = {"context_text": context_text, "context_chunks": context_chunks}
            workflow_routing = self._should_use_workflow(request.message, user_context)
            
            ai_response = None
            workflow_used = False
            
            if workflow_routing:
                # Route through Multi-Agent System
                try:
                    ai_response = await self._process_with_multi_agent_system(
                        request.message, 
                        session.user_id, 
                        workflow_routing, 
                        user_context
                    )
                    workflow_used = True
                    logger.info(f"Processed message through multi-agent system: {workflow_routing['request_type']}")
                except Exception as workflow_error:
                    logger.warning(f"Multi-agent processing failed, falling back to direct AI: {workflow_error}")
                    # Fall back to direct AI processing
                    ai_response = None
            
            # If no workflow was used or workflow failed, use direct AI processing
            if not ai_response:
                ai_response = await self._process_with_direct_ai(
                    request.message, 
                    context_text, 
                    memory.chat_memory.messages
                )
            
            # Ensure ai_response is a string
            if isinstance(ai_response, dict):
                if "error" in ai_response:
                    ai_response = f"I apologize, but I encountered an issue: {ai_response['error']}"
                else:
                    ai_response = str(ai_response)
            elif not isinstance(ai_response, str):
                ai_response = str(ai_response)
            
            # Create assistant message
            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=ai_response,
                metadata={
                    "context_chunks_used": len(context_chunks),
                    "model_used": ModelType.GEMINI_FLASH.value,
                    "workflow_used": workflow_used,
                    "workflow_name": workflow_routing.get("workflow_name") if workflow_routing else None
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
    
    async def _process_with_multi_agent_system(
        self, 
        message: str, 
        user_id: str, 
        workflow_routing: Dict[str, Any], 
        user_context: Dict[str, Any]
    ) -> str:
        """Process message using Multi-Agent System"""
        multi_agent_service = await self._get_multi_agent_service()
        if not multi_agent_service:
            raise Exception("Multi-Agent Service not available")
        
        # Prepare request content for multi-agent processing
        request_content = {
            "user_message": message,
            "user_background": user_context.get("context_text", ""),
            "context_chunks": user_context.get("context_chunks", []),
            "chat_context": True,
            "question": message
        }
        
        # Process through multi-agent system
        result = await multi_agent_service.process_request(
            user_id=user_id,
            request_type=workflow_routing["request_type"],
            content=request_content,
            context=user_context
        )
        
        if result["success"]:
            # Extract response from multi-agent result
            final_response = result.get("final_response", {})
            
            if isinstance(final_response, dict):
                # If it's a comprehensive response, extract the synthesis
                if "synthesized_response" in final_response:
                    return final_response["synthesized_response"]
                elif "response" in final_response:
                    return final_response["response"]
                elif "individual_responses" in final_response and final_response["individual_responses"]:
                    # Use the best individual response
                    return str(final_response["individual_responses"][0])
                else:
                    # Format the response nicely
                    return self._format_multi_agent_response(final_response)
            else:
                return str(final_response)
        else:
            raise Exception(f"Multi-agent processing failed: {result.get('error', 'Unknown error')}")
    
    async def _process_with_direct_ai(
        self, 
        message: str, 
        context_text: str, 
        chat_history: List[BaseMessage]
    ) -> str:
        """Process message using direct AI service"""
        # Create prompt template
        prompt_template = self._create_chat_prompt_template()
        
        # Get AI service
        ai_service = await self._get_ai_service()
        
        # Format the complete prompt
        formatted_prompt = prompt_template.format(
            context=context_text,
            chat_history=chat_history,
            question=message
        )
        
        # Generate AI response
        return await ai_service.generate_text(
            prompt=formatted_prompt,
            model_type=ModelType.GEMINI_FLASH,
            max_tokens=800,
            temperature=0.8
        )
    
    def _format_multi_agent_response(self, response_data: Dict[str, Any]) -> str:
        """Format multi-agent response data into a readable string"""
        if not response_data:
            return "I apologize, but I wasn't able to generate a comprehensive response. Please try rephrasing your question."
        
        formatted_parts = []
        
        # Check for error responses
        if "error" in response_data:
            return f"I encountered an issue while processing your request: {response_data['error']}"
        
        # Format different types of responses
        if isinstance(response_data, str):
            return response_data
        
        # If it's a dict, try to extract meaningful content
        if isinstance(response_data, dict):
            # Look for common response fields
            for field in ["content", "advice", "recommendation", "analysis", "response"]:
                if field in response_data and response_data[field]:
                    return str(response_data[field])
            
            # If no standard fields, format as a structured response
            return json.dumps(response_data, indent=2)
        
        # Add skills analysis
        if "skills_analysis" in response_data:
            skills = response_data["skills_analysis"]
            if isinstance(skills, dict):
                if skills.get("skill_gaps"):
                    formatted_parts.append("**Key Skill Areas to Develop:**")
                    for gap in skills["skill_gaps"][:3]:  # Limit to top 3
                        formatted_parts.append(f"• {gap}")
                    formatted_parts.append("")
        
        # Add learning resources
        if "learning_resources" in response_data:
            resources = response_data["learning_resources"]
            if isinstance(resources, dict) and resources.get("recommended_resources"):
                formatted_parts.append("**Recommended Learning Resources:**")
                for resource in resources["recommended_resources"][:3]:  # Limit to top 3
                    if isinstance(resource, dict):
                        title = resource.get("title", "Resource")
                        description = resource.get("description", "")
                        formatted_parts.append(f"• **{title}**: {description}")
                    else:
                        formatted_parts.append(f"• {resource}")
                formatted_parts.append("")
        
        # Add workflow metadata if available
        if "workflow_metadata" in response_data:
            metadata = response_data["workflow_metadata"]
            formatted_parts.append(f"*This response was generated using our multi-agent analysis system.*")
        
        return "\n".join(formatted_parts) if formatted_parts else "I've analyzed your request using multiple specialized agents. Please let me know if you'd like me to elaborate on any specific aspect."
    
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