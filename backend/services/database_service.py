import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client
from models.roadmap import Roadmap, RoadmapStatus
from models.chat import ChatSession, ChatMessage
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling database operations with Supabase"""
    
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
    
    # Roadmap operations
    async def save_roadmap(self, roadmap: Roadmap) -> str:
        """Save a roadmap to the database"""
        try:
            # Convert roadmap to database format
            roadmap_data = {
                "user_id": roadmap.user_id,
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
                if result.data:
                    logger.info(f"Updated roadmap {roadmap.id}")
                    return roadmap.id
            else:
                # Create new roadmap
                result = self.supabase.table("roadmaps").insert(roadmap_data).execute()
                if result.data:
                    roadmap_id = result.data[0]["id"]
                    logger.info(f"Created new roadmap {roadmap_id}")
                    return roadmap_id
            
            raise Exception("Failed to save roadmap")
            
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
            result = self.supabase.table("roadmaps").select("*").eq("user_id", user_id).order("updated_date", desc=True).execute()
            
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
            
            return bool(result.data)
            
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
            # Convert chat session to database format
            session_data = {
                "user_id": chat_session.user_id,
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
            query = self.supabase.table("chat_sessions").select("*").eq("user_id", user_id)
            
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