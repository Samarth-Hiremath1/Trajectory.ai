from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from models.chat import (
    ChatInitRequest, ChatMessageRequest, ChatResponse,
    ChatSession, ChatSessionResponse, ChatHistoryResponse
)
from services.roadmap_chat_service import get_roadmap_chat_service, RoadmapChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/roadmap", tags=["roadmap-chat"])

async def get_roadmap_chat_service_dependency() -> RoadmapChatService:
    """Dependency to get roadmap chat service instance"""
    return await get_roadmap_chat_service()

@router.post("/{roadmap_id}/chat/sessions", response_model=ChatSession)
async def initialize_roadmap_chat_session(
    roadmap_id: str,
    user_id: str,
    title: Optional[str] = None,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Initialize a new roadmap-specific chat session"""
    try:
        logger.info(f"Initializing roadmap chat session for roadmap {roadmap_id}, user {user_id}")
        session = await roadmap_chat_service.initialize_roadmap_chat_session(
            roadmap_id=roadmap_id,
            user_id=user_id,
            title=title
        )
        
        # Save session to database
        await roadmap_chat_service.save_roadmap_chat_session(session)
        
        return session
        
    except ValueError as e:
        logger.error(f"Invalid roadmap or user: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to initialize roadmap chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize roadmap chat session: {str(e)}"
        )

@router.post("/{roadmap_id}/chat/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_roadmap_message(
    roadmap_id: str,
    session_id: str,
    message: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Send a message in a roadmap-specific chat session"""
    try:
        logger.info(f"Sending message to roadmap chat session {session_id} for roadmap {roadmap_id}")
        response = await roadmap_chat_service.send_roadmap_message(
            session_id=session_id,
            message=message,
            roadmap_id=roadmap_id
        )
        return response
        
    except ValueError as e:
        logger.error(f"Roadmap chat session not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to send roadmap message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send roadmap message: {str(e)}"
        )

@router.post("/{roadmap_id}/chat/edit", response_model=Dict[str, Any])
async def process_roadmap_edit_request(
    roadmap_id: str,
    session_id: str,
    edit_request: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Process a request to edit the roadmap based on chat conversation"""
    try:
        logger.info(f"Processing edit request for roadmap {roadmap_id}")
        edit_analysis = await roadmap_chat_service.process_roadmap_edit_request(
            session_id=session_id,
            roadmap_id=roadmap_id,
            edit_request=edit_request
        )
        
        return {
            "success": True,
            "roadmap_id": roadmap_id,
            "edit_analysis": edit_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process roadmap edit request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process edit request: {str(e)}"
        )

@router.get("/{roadmap_id}/chat/sessions/{session_id}", response_model=ChatSession)
async def get_roadmap_chat_session(
    roadmap_id: str,
    session_id: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Get a specific roadmap chat session"""
    try:
        # Try to load from database first
        session = await roadmap_chat_service.load_roadmap_chat_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Roadmap chat session {session_id} not found"
            )
        
        # Verify session belongs to the roadmap
        if session.metadata.get("roadmap_id") != roadmap_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} is not associated with roadmap {roadmap_id}"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get roadmap chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get roadmap chat session: {str(e)}"
        )

@router.get("/{roadmap_id}/chat/sessions", response_model=List[ChatSession])
async def get_roadmap_chat_sessions(
    roadmap_id: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Get all chat sessions for a specific roadmap"""
    try:
        sessions = roadmap_chat_service.get_roadmap_sessions(roadmap_id)
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get roadmap chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get roadmap chat sessions: {str(e)}"
        )

@router.delete("/{roadmap_id}/chat/sessions/{session_id}")
async def delete_roadmap_chat_session(
    roadmap_id: str,
    session_id: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Delete a roadmap chat session"""
    try:
        # Verify session belongs to roadmap first
        session = roadmap_chat_service.get_roadmap_chat_session(session_id)
        if not session or session.metadata.get("roadmap_id") != roadmap_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Roadmap chat session {session_id} not found for roadmap {roadmap_id}"
            )
        
        success = roadmap_chat_service.delete_roadmap_chat_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Roadmap chat session {session_id} not found"
            )
        
        return {"message": f"Roadmap chat session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete roadmap chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete roadmap chat session: {str(e)}"
        )

@router.post("/{roadmap_id}/chat/clear-context")
async def clear_roadmap_context_cache(
    roadmap_id: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Clear cached context for a roadmap (call when roadmap is updated)"""
    try:
        success = roadmap_chat_service.clear_roadmap_context_cache(roadmap_id)
        
        return {
            "success": success,
            "message": f"Context cache cleared for roadmap {roadmap_id}" if success else f"No cached context found for roadmap {roadmap_id}",
            "roadmap_id": roadmap_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to clear roadmap context cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear context cache: {str(e)}"
        )

@router.get("/{roadmap_id}/chat/health")
async def roadmap_chat_health_check(
    roadmap_id: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Check the health of the roadmap chat service"""
    try:
        health = await roadmap_chat_service.health_check()
        
        # Add roadmap-specific information
        roadmap_sessions = roadmap_chat_service.get_roadmap_sessions(roadmap_id)
        health["roadmap_specific"] = {
            "roadmap_id": roadmap_id,
            "active_sessions": len(roadmap_sessions),
            "has_cached_context": roadmap_id in roadmap_chat_service.roadmap_contexts
        }
        
        # Add workflow integration status
        health["workflow_integration"] = {
            "available": hasattr(roadmap_chat_service, 'workflow_orchestrator') and roadmap_chat_service.workflow_orchestrator is not None,
            "orchestrator_initialized": roadmap_chat_service.workflow_orchestrator is not None if hasattr(roadmap_chat_service, 'workflow_orchestrator') else False,
            "workflow_patterns": len(roadmap_chat_service.roadmap_workflow_patterns) if hasattr(roadmap_chat_service, 'roadmap_workflow_patterns') else 0
        }
        
        if hasattr(roadmap_chat_service, 'workflow_orchestrator') and roadmap_chat_service.workflow_orchestrator:
            workflow_health = await roadmap_chat_service.workflow_orchestrator.health_check()
            health["workflow_orchestrator"] = workflow_health
        
        return health
        
    except Exception as e:
        logger.error(f"Roadmap chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "roadmap_id": roadmap_id
        }

@router.get("/{roadmap_id}/chat/workflow-patterns")
async def get_roadmap_chat_workflow_patterns(
    roadmap_id: str,
    roadmap_chat_service: RoadmapChatService = Depends(get_roadmap_chat_service_dependency)
):
    """Get workflow patterns available for roadmap chat"""
    try:
        patterns = {}
        
        if hasattr(roadmap_chat_service, 'roadmap_workflow_patterns'):
            patterns = roadmap_chat_service.roadmap_workflow_patterns
        
        return {
            "roadmap_id": roadmap_id,
            "workflow_patterns": patterns,
            "pattern_count": len(patterns),
            "workflow_available": hasattr(roadmap_chat_service, 'workflow_orchestrator') and roadmap_chat_service.workflow_orchestrator is not None
        }
        
    except Exception as e:
        logger.error(f"Failed to get roadmap chat workflow patterns: {e}")
        return {
            "roadmap_id": roadmap_id,
            "workflow_patterns": {},
            "error": str(e)
        }