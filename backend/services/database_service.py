import os
import json
import hashlib
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from models.roadmap import Roadmap, RoadmapStatus
from models.chat import ChatSession, ChatMessage
from models.agent import (
    AgentRequest, AgentResponse, AgentWorkflow, AgentMessage, 
    AgentStatus, AgentCollaboration
)
import logging

logger = logging.getLogger(__name__)

# Performance logging for database operations
db_performance_logger = logging.getLogger("database.performance")
db_performance_handler = logging.StreamHandler()
db_performance_formatter = logging.Formatter(
    '%(asctime)s - DB_PERFORMANCE - %(levelname)s - %(message)s'
)
db_performance_handler.setFormatter(db_performance_formatter)
db_performance_logger.addHandler(db_performance_handler)
db_performance_logger.setLevel(logging.INFO)

class DatabaseService:
    """Service for handling database operations with Supabase"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        try:
            # Create Supabase client with explicit parameters only
            self.supabase: Client = create_client(supabase_url, supabase_key)
            
            # Initialize performance tracking
            self.query_count = 0
            self.total_query_time = 0.0
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    def _convert_user_id_to_uuid(self, user_id: str) -> str:
        """Convert string user_id to UUID format if needed"""
        if isinstance(user_id, str) and not user_id.count('-') == 4:
            # Convert string to UUID format by hashing
            hash_object = hashlib.md5(user_id.encode())
            return str(uuid.UUID(hash_object.hexdigest()))
        return user_id
    
    def _track_query_performance(self, operation: str, query_time: float, success: bool = True):
        """Track query performance metrics"""
        self.query_count += 1
        self.total_query_time += query_time
        
        # Log performance details
        db_performance_logger.info(
            f"Database operation: {operation}, "
            f"Time: {query_time:.3f}s, "
            f"Success: {success}, "
            f"Total queries: {self.query_count}, "
            f"Avg time: {self.total_query_time / self.query_count:.3f}s"
        )
    
    # Roadmap operations
    async def save_roadmap(self, roadmap: Roadmap) -> str:
        """Save a roadmap to the database"""
        try:
            # Convert string user_id to UUID format if needed
            user_id = self._convert_user_id_to_uuid(roadmap.user_id)
            
            # Convert roadmap to database format
            roadmap_data = {
                "user_id": user_id,
                "title": roadmap.title,
                "description": roadmap.description,
                "current_role": roadmap.current_role,
                "target_role": roadmap.target_role,
                "status": roadmap.status.value,
                "phases": [phase.dict() for phase in roadmap.phases],
                "total_estimated_weeks": roadmap.total_estimated_weeks,
                "overall_progress_percentage": float(roadmap.overall_progress_percentage),
                "current_phase": roadmap.current_phase,
                "generated_with_model": roadmap.generated_with_model,
                "generation_prompt": roadmap.generation_prompt,
                "user_context_used": roadmap.user_context_used or {},
                "created_date": roadmap.created_date.isoformat(),
                "updated_date": datetime.utcnow().isoformat(),
                "last_accessed_date": datetime.utcnow().isoformat()
            }
            
            if roadmap.id:
                # Update existing roadmap
                result = self.supabase.table("roadmaps").update(roadmap_data).eq("id", roadmap.id).execute()
                # For updates, we just need to check if the operation completed without error
                # Supabase UPDATE operations don't return data by default, but a successful
                # execution without exception means the update was successful
                logger.info(f"Updated roadmap {roadmap.id}")
                return roadmap.id
            else:
                # Create new roadmap
                result = self.supabase.table("roadmaps").insert(roadmap_data).execute()
                if result.data and len(result.data) > 0:
                    roadmap_id = result.data[0]["id"]
                    logger.info(f"Created new roadmap {roadmap_id}")
                    return roadmap_id
                else:
                    logger.error(f"Insert failed - no data returned. Result: {result}")
                    raise Exception(f"Failed to create roadmap - no data returned")
            
        except Exception as e:
            logger.error(f"Error saving roadmap: {str(e)}")
            raise
    
    async def load_roadmap(self, roadmap_id: str) -> Optional[Roadmap]:
        """Load a roadmap by ID"""
        try:
            result = self.supabase.table("roadmaps").select("*").eq("id", roadmap_id).execute()
            
            if result.data:
                data = result.data[0]
                return self._convert_db_to_roadmap(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading roadmap {roadmap_id}: {str(e)}")
            raise
    
    async def load_user_roadmaps(self, user_id: str) -> List[Roadmap]:
        """Load all roadmaps for a user"""
        try:
            # Convert string user_id to UUID format if needed
            converted_user_id = self._convert_user_id_to_uuid(user_id)
            
            result = self.supabase.table("roadmaps").select("*").eq("user_id", converted_user_id).order("updated_date", desc=True).execute()
            
            roadmaps = []
            if result.data:
                for data in result.data:
                    roadmap = self._convert_db_to_roadmap(data)
                    if roadmap:
                        roadmaps.append(roadmap)
            
            return roadmaps
            
        except Exception as e:
            logger.error(f"Error loading roadmaps for user {user_id}: {str(e)}")
            raise
    
    async def update_roadmap_progress(self, roadmap_id: str, progress_data: Dict[str, Any]) -> bool:
        """Update roadmap progress"""
        try:
            update_data = {
                "updated_date": datetime.utcnow().isoformat(),
                "last_accessed_date": datetime.utcnow().isoformat()
            }
            
            if "overall_progress_percentage" in progress_data:
                update_data["overall_progress_percentage"] = float(progress_data["overall_progress_percentage"])
            
            if "current_phase" in progress_data:
                update_data["current_phase"] = progress_data["current_phase"]
            
            if "phases" in progress_data:
                update_data["phases"] = progress_data["phases"]
            
            result = self.supabase.table("roadmaps").update(update_data).eq("id", roadmap_id).execute()
            
            # For updates, we just need to check if the operation completed without error
            # Supabase UPDATE operations don't return data by default, but a successful
            # execution without exception means the update was successful
            return True
            
        except Exception as e:
            logger.error(f"Error updating roadmap progress {roadmap_id}: {str(e)}")
            raise
    
    async def delete_roadmap(self, roadmap_id: str) -> bool:
        """Delete a roadmap"""
        try:
            result = self.supabase.table("roadmaps").delete().eq("id", roadmap_id).execute()
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deleting roadmap {roadmap_id}: {str(e)}")
            raise
    
    # Chat session operations
    async def save_chat_session(self, chat_session: ChatSession) -> str:
        """Save a chat session to the database"""
        try:
            # Convert string user_id to UUID format if needed
            user_id = self._convert_user_id_to_uuid(chat_session.user_id)
            
            # Convert chat session to database format
            session_data = {
                "user_id": user_id,
                "title": chat_session.title,
                "messages": [msg.dict() for msg in chat_session.messages],
                "context_version": chat_session.context_version,
                "created_at": chat_session.created_at.isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "is_active": chat_session.is_active,
                "metadata": chat_session.metadata
            }
            
            if chat_session.id and await self._chat_session_exists(chat_session.id):
                # Update existing session
                result = self.supabase.table("chat_sessions").update(session_data).eq("id", chat_session.id).execute()
                if result.data:
                    logger.info(f"Updated chat session {chat_session.id}")
                    return chat_session.id
            else:
                # Create new session
                result = self.supabase.table("chat_sessions").insert(session_data).execute()
                if result.data:
                    session_id = result.data[0]["id"]
                    logger.info(f"Created new chat session {session_id}")
                    return session_id
            
            raise Exception("Failed to save chat session")
            
        except Exception as e:
            logger.error(f"Error saving chat session: {str(e)}")
            raise
    
    async def load_chat_session(self, session_id: str) -> Optional[ChatSession]:
        """Load a chat session by ID"""
        try:
            result = self.supabase.table("chat_sessions").select("*").eq("id", session_id).execute()
            
            if result.data:
                data = result.data[0]
                return self._convert_db_to_chat_session(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error loading chat session {session_id}: {str(e)}")
            raise
    
    async def load_user_chat_sessions(self, user_id: str, active_only: bool = True) -> List[ChatSession]:
        """Load all chat sessions for a user"""
        try:
            # Convert string user_id to UUID format if needed
            converted_user_id = self._convert_user_id_to_uuid(user_id)
            
            query = self.supabase.table("chat_sessions").select("*").eq("user_id", converted_user_id)
            
            if active_only:
                query = query.eq("is_active", True)
            
            result = query.order("updated_at", desc=True).execute()
            
            sessions = []
            if result.data:
                for data in result.data:
                    session = self._convert_db_to_chat_session(data)
                    if session:
                        sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error loading chat sessions for user {user_id}: {str(e)}")
            raise
    
    async def add_message_to_session(self, session_id: str, message: ChatMessage) -> bool:
        """Add a message to an existing chat session"""
        try:
            # First load the current session
            session = await self.load_chat_session(session_id)
            if not session:
                return False
            
            # Add the new message
            session.messages.append(message)
            session.updated_at = datetime.utcnow()
            
            # Save the updated session
            await self.save_chat_session(session)
            return True
            
        except Exception as e:
            logger.error(f"Error adding message to session {session_id}: {str(e)}")
            raise
    
    async def deactivate_chat_session(self, session_id: str) -> bool:
        """Deactivate a chat session"""
        try:
            result = self.supabase.table("chat_sessions").update({
                "is_active": False,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
            
            return bool(result.data)
            
        except Exception as e:
            logger.error(f"Error deactivating chat session {session_id}: {str(e)}")
            raise
    
    # Helper methods
    def _convert_db_to_roadmap(self, data: Dict[str, Any]) -> Optional[Roadmap]:
        """Convert database row to Roadmap model"""
        try:
            from models.roadmap import RoadmapPhase, Skill, LearningResource, Milestone
            
            # Convert phases from JSON to Pydantic models
            phases = []
            for phase_data in data.get("phases", []):
                # Convert nested objects
                skills = [Skill(**skill) for skill in phase_data.get("skills_to_develop", [])]
                resources = [LearningResource(**resource) for resource in phase_data.get("learning_resources", [])]
                milestones = [Milestone(**milestone) for milestone in phase_data.get("milestones", [])]
                
                phase_data["skills_to_develop"] = skills
                phase_data["learning_resources"] = resources
                phase_data["milestones"] = milestones
                
                phases.append(RoadmapPhase(**phase_data))
            
            return Roadmap(
                id=data["id"],
                user_id=data["user_id"],
                title=data["title"],
                description=data.get("description"),
                current_role=data["current_role"],
                target_role=data["target_role"],
                status=RoadmapStatus(data["status"]),
                phases=phases,
                total_estimated_weeks=data["total_estimated_weeks"],
                overall_progress_percentage=float(data["overall_progress_percentage"]),
                current_phase=data.get("current_phase"),
                generated_with_model=data.get("generated_with_model"),
                generation_prompt=data.get("generation_prompt"),
                user_context_used=data.get("user_context_used", {}),
                created_date=datetime.fromisoformat(data["created_date"].replace("Z", "+00:00")),
                updated_date=datetime.fromisoformat(data["updated_date"].replace("Z", "+00:00")),
                last_accessed_date=datetime.fromisoformat(data["last_accessed_date"].replace("Z", "+00:00")) if data.get("last_accessed_date") else None
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to roadmap: {str(e)}")
            return None
    
    def _convert_db_to_chat_session(self, data: Dict[str, Any]) -> Optional[ChatSession]:
        """Convert database row to ChatSession model"""
        try:
            # Convert messages from JSON to ChatMessage models
            messages = []
            for msg_data in data.get("messages", []):
                messages.append(ChatMessage(**msg_data))
            
            return ChatSession(
                id=data["id"],
                user_id=data["user_id"],
                title=data.get("title"),
                messages=messages,
                context_version=data["context_version"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                is_active=data["is_active"],
                metadata=data.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to chat session: {str(e)}")
            return None
    
    async def _chat_session_exists(self, session_id: str) -> bool:
        """Check if a chat session exists"""
        try:
            result = self.supabase.table("chat_sessions").select("id").eq("id", session_id).execute()
            return bool(result.data)
        except:
            return False
    
    # Profile operations
    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID"""
        try:
            result = self.supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting profile for user {user_id}: {str(e)}")
            raise
    
    async def create_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new user profile"""
        try:
            # Add user_id and timestamps
            insert_data = {
                "user_id": user_id,
                **profile_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("profiles").insert(insert_data).execute()
            
            if result.data:
                logger.info(f"Created profile for user {user_id}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating profile for user {user_id}: {str(e)}")
            raise
    
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user profile"""
        try:
            # Add updated timestamp
            update_data = {
                **profile_data,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("profiles").update(update_data).eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Updated profile for user {user_id}")
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating profile for user {user_id}: {str(e)}")
            raise
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        try:
            result = self.supabase.table("profiles").delete().eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Deleted profile for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting profile for user {user_id}: {str(e)}")
            raise
    
    # Resume operations
    async def save_resume(self, resume_data: Dict[str, Any]) -> str:
        """Save resume data to the database"""
        try:
            # Convert string user_id to UUID format if needed
            user_id = self._convert_user_id_to_uuid(resume_data["user_id"])
            
            # Prepare resume data for database
            db_data = {
                "id": resume_data.get("id", str(uuid.uuid4())),
                "user_id": user_id,
                "filename": resume_data["filename"],
                "file_path": resume_data.get("file_path"),
                "file_size": resume_data.get("file_size"),
                "content_type": resume_data.get("content_type", "application/pdf"),
                "parsed_content": resume_data.get("parsed_content", {}),
                "text_chunks": resume_data.get("text_chunks", []),
                "processing_status": resume_data.get("processing_status", "completed"),
                "error_message": resume_data.get("error_message"),
                "upload_date": resume_data.get("upload_date", datetime.utcnow().isoformat()),
                "processed_date": resume_data.get("processed_date", datetime.utcnow().isoformat())
            }
            
            # Use upsert to handle updates to existing resumes
            result = self.supabase.table("resumes").upsert(db_data, on_conflict="user_id").execute()
            
            if result.data:
                resume_id = result.data[0]["id"]
                logger.info(f"Saved resume {resume_id} for user {user_id}")
                return resume_id
            
            raise Exception("No data returned from resume save operation")
            
        except Exception as e:
            logger.error(f"Error saving resume: {str(e)}")
            raise
    
    async def get_user_resume(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's resume by user ID"""
        try:
            result = self.supabase.table("resumes").select("*").eq("user_id", user_id).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting resume for user {user_id}: {str(e)}")
            raise
    
    async def get_resume_by_id(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """Get resume by resume ID"""
        try:
            result = self.supabase.table("resumes").select("*").eq("id", resume_id).execute()
            
            if result.data:
                return result.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting resume {resume_id}: {str(e)}")
            raise
    
    async def update_resume_status(self, resume_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """Update resume processing status"""
        try:
            update_data = {
                "processing_status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if status == "completed":
                update_data["processed_date"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("resumes").update(update_data).eq("id", resume_id).execute()
            
            if result.data:
                logger.info(f"Updated resume {resume_id} status to {status}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating resume status: {str(e)}")
            raise
    
    async def delete_user_resume(self, user_id: str) -> bool:
        """Delete user's resume"""
        try:
            result = self.supabase.table("resumes").delete().eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Deleted resume for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting resume for user {user_id}: {str(e)}")
            raise
    
    # Agent system operations
    async def save_agent_request(self, request: AgentRequest) -> str:
        """Save an agent request to the database"""
        try:
            request_data = {
                "id": request.id,
                "user_id": request.user_id,
                "request_type": request.request_type.value,
                "content": request.content,
                "context": request.context,
                "priority": request.priority.value,
                "status": request.status.value,
                "assigned_agents": request.assigned_agents,
                "metadata": request.metadata,
                "created_at": request.created_at.isoformat()
            }
            
            result = self.supabase.table("agent_requests").insert(request_data).execute()
            
            if result.data:
                logger.info(f"Saved agent request {request.id}")
                return result.data[0]["id"]
            
            raise Exception("No data returned from agent request save operation")
            
        except Exception as e:
            logger.error(f"Error saving agent request: {str(e)}")
            raise
    
    async def get_agent_request(self, request_id: str) -> Optional[AgentRequest]:
        """Get an agent request by ID"""
        try:
            result = self.supabase.table("agent_requests").select("*").eq("id", request_id).execute()
            
            if result.data:
                data = result.data[0]
                return self._convert_db_to_agent_request(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent request {request_id}: {str(e)}")
            raise
    
    async def update_agent_request_status(self, request_id: str, status: str, assigned_agents: Optional[List[str]] = None) -> bool:
        """Update agent request status"""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if assigned_agents is not None:
                update_data["assigned_agents"] = assigned_agents
            
            result = self.supabase.table("agent_requests").update(update_data).eq("id", request_id).execute()
            
            logger.info(f"Updated agent request {request_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent request status: {str(e)}")
            raise
    
    async def save_agent_response(self, response: AgentResponse) -> str:
        """Save an agent response to the database"""
        try:
            response_data = {
                "id": response.id,
                "request_id": response.request_id,
                "agent_id": response.agent_id,
                "agent_type": response.agent_type.value,
                "response_content": response.response_content,
                "confidence_score": response.confidence_score,
                "processing_time": response.processing_time,
                "metadata": response.metadata,
                "created_at": response.created_at.isoformat()
            }
            
            result = self.supabase.table("agent_responses").insert(response_data).execute()
            
            if result.data:
                logger.info(f"Saved agent response {response.id}")
                return result.data[0]["id"]
            
            raise Exception("No data returned from agent response save operation")
            
        except Exception as e:
            logger.error(f"Error saving agent response: {str(e)}")
            raise
    
    async def get_agent_responses(self, request_id: str) -> List[AgentResponse]:
        """Get all agent responses for a request"""
        try:
            result = self.supabase.table("agent_responses").select("*").eq("request_id", request_id).execute()
            
            responses = []
            if result.data:
                for data in result.data:
                    response = self._convert_db_to_agent_response(data)
                    if response:
                        responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Error getting agent responses for request {request_id}: {str(e)}")
            raise
    
    async def save_agent_workflow(self, workflow: AgentWorkflow) -> str:
        """Save an agent workflow to the database"""
        try:
            workflow_data = {
                "id": workflow.id,
                "request_id": workflow.request_id,
                "orchestrator_id": workflow.orchestrator_id,
                "participating_agents": workflow.participating_agents,
                "workflow_steps": [step.dict() for step in workflow.workflow_steps],
                "current_step": workflow.current_step,
                "status": workflow.status.value,
                "metadata": workflow.metadata,
                "created_at": workflow.created_at.isoformat(),
                "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
            }
            
            if await self._workflow_exists(workflow.id):
                # Update existing workflow
                result = self.supabase.table("agent_workflows").update(workflow_data).eq("id", workflow.id).execute()
                logger.info(f"Updated agent workflow {workflow.id}")
                return workflow.id
            else:
                # Create new workflow
                result = self.supabase.table("agent_workflows").insert(workflow_data).execute()
                if result.data:
                    logger.info(f"Saved agent workflow {workflow.id}")
                    return result.data[0]["id"]
            
            raise Exception("No data returned from agent workflow save operation")
            
        except Exception as e:
            logger.error(f"Error saving agent workflow: {str(e)}")
            raise
    
    async def get_agent_workflow(self, workflow_id: str) -> Optional[AgentWorkflow]:
        """Get an agent workflow by ID"""
        try:
            result = self.supabase.table("agent_workflows").select("*").eq("id", workflow_id).execute()
            
            if result.data:
                data = result.data[0]
                return self._convert_db_to_agent_workflow(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent workflow {workflow_id}: {str(e)}")
            raise
    
    async def save_agent_message(self, message: AgentMessage) -> str:
        """Save an agent message to the database"""
        try:
            message_data = {
                "id": message.id,
                "sender_agent_id": message.sender_agent_id,
                "recipient_agent_id": message.recipient_agent_id,
                "message_type": message.message_type.value,
                "content": message.content,
                "acknowledged": message.acknowledged,
                "metadata": message.metadata,
                "timestamp": message.timestamp.isoformat()
            }
            
            result = self.supabase.table("agent_messages").insert(message_data).execute()
            
            if result.data:
                logger.debug(f"Saved agent message {message.id}")
                return result.data[0]["id"]
            
            raise Exception("No data returned from agent message save operation")
            
        except Exception as e:
            logger.error(f"Error saving agent message: {str(e)}")
            raise
    
    async def update_agent_status(self, status: AgentStatus) -> bool:
        """Update or insert agent status"""
        try:
            status_data = {
                "agent_id": status.agent_id,
                "agent_type": status.agent_type.value,
                "is_active": status.is_active,
                "current_load": status.current_load,
                "max_concurrent_requests": status.max_concurrent_requests,
                "capabilities": [cap.dict() for cap in status.capabilities],
                "performance_metrics": status.performance_metrics,
                "last_heartbeat": status.last_heartbeat.isoformat()
            }
            
            # Use upsert to handle both insert and update
            result = self.supabase.table("agent_status").upsert(status_data, on_conflict="agent_id").execute()
            
            if result.data:
                logger.debug(f"Updated agent status for {status.agent_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating agent status: {str(e)}")
            raise
    
    async def get_agent_status(self, agent_id: str) -> Optional[AgentStatus]:
        """Get agent status by ID"""
        try:
            result = self.supabase.table("agent_status").select("*").eq("agent_id", agent_id).execute()
            
            if result.data:
                data = result.data[0]
                return self._convert_db_to_agent_status(data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent status {agent_id}: {str(e)}")
            raise
    
    async def get_all_agent_statuses(self) -> List[AgentStatus]:
        """Get all agent statuses"""
        try:
            result = self.supabase.table("agent_status").select("*").execute()
            
            statuses = []
            if result.data:
                for data in result.data:
                    status = self._convert_db_to_agent_status(data)
                    if status:
                        statuses.append(status)
            
            return statuses
            
        except Exception as e:
            logger.error(f"Error getting all agent statuses: {str(e)}")
            raise
    
    # Helper methods for agent system
    def _convert_db_to_agent_request(self, data: Dict[str, Any]) -> Optional[AgentRequest]:
        """Convert database row to AgentRequest model"""
        try:
            from models.agent import RequestType, RequestPriority, RequestStatus
            
            return AgentRequest(
                id=data["id"],
                user_id=data["user_id"],
                request_type=RequestType(data["request_type"]),
                content=data["content"],
                context=data["context"],
                priority=RequestPriority(data["priority"]),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                status=RequestStatus(data["status"]),
                assigned_agents=data["assigned_agents"],
                metadata=data["metadata"]
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to agent request: {str(e)}")
            return None
    
    def _convert_db_to_agent_response(self, data: Dict[str, Any]) -> Optional[AgentResponse]:
        """Convert database row to AgentResponse model"""
        try:
            from models.agent import AgentType
            
            return AgentResponse(
                id=data["id"],
                request_id=data["request_id"],
                agent_id=data["agent_id"],
                agent_type=AgentType(data["agent_type"]),
                response_content=data["response_content"],
                confidence_score=data["confidence_score"],
                processing_time=data["processing_time"],
                metadata=data["metadata"],
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to agent response: {str(e)}")
            return None
    
    def _convert_db_to_agent_workflow(self, data: Dict[str, Any]) -> Optional[AgentWorkflow]:
        """Convert database row to AgentWorkflow model"""
        try:
            from models.agent import WorkflowStatus, WorkflowStep
            
            # Convert workflow steps
            steps = []
            for step_data in data.get("workflow_steps", []):
                steps.append(WorkflowStep(**step_data))
            
            return AgentWorkflow(
                id=data["id"],
                request_id=data["request_id"],
                orchestrator_id=data["orchestrator_id"],
                participating_agents=data["participating_agents"],
                workflow_steps=steps,
                current_step=data["current_step"],
                status=WorkflowStatus(data["status"]),
                created_at=datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")),
                completed_at=datetime.fromisoformat(data["completed_at"].replace("Z", "+00:00")) if data.get("completed_at") else None,
                metadata=data["metadata"]
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to agent workflow: {str(e)}")
            return None
    
    def _convert_db_to_agent_status(self, data: Dict[str, Any]) -> Optional[AgentStatus]:
        """Convert database row to AgentStatus model"""
        try:
            from models.agent import AgentType, AgentCapability
            
            # Convert capabilities
            capabilities = []
            for cap_data in data.get("capabilities", []):
                capabilities.append(AgentCapability(**cap_data))
            
            return AgentStatus(
                agent_id=data["agent_id"],
                agent_type=AgentType(data["agent_type"]),
                is_active=data["is_active"],
                current_load=data["current_load"],
                max_concurrent_requests=data["max_concurrent_requests"],
                capabilities=capabilities,
                last_heartbeat=datetime.fromisoformat(data["last_heartbeat"].replace("Z", "+00:00")),
                performance_metrics=data["performance_metrics"]
            )
            
        except Exception as e:
            logger.error(f"Error converting database row to agent status: {str(e)}")
            return None
    
    async def _workflow_exists(self, workflow_id: str) -> bool:
        """Check if a workflow exists"""
        try:
            result = self.supabase.table("agent_workflows").select("id").eq("id", workflow_id).execute()
            return bool(result.data)
        except:
            return False