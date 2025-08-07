from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from datetime import datetime
import logging

from models.chat import (
    ChatInitRequest, ChatMessageRequest, ChatResponse,
    ChatSession, ChatSessionResponse, ChatHistoryResponse
)
from services.chat_service import get_chat_service, RAGChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

async def get_chat_service_dependency() -> RAGChatService:
    """Dependency to get chat service instance"""
    return await get_chat_service()

@router.post("/sessions", response_model=ChatSession)
async def initialize_chat_session(
    request: ChatInitRequest,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Initialize a new chat session"""
    try:
        logger.info(f"Initializing chat session for user {request.user_id}")
        session = await chat_service.initialize_chat_session(request)
        
        # Save session to database
        await chat_service.save_chat_session(session)
        
        return session
        
    except Exception as e:
        logger.error(f"Failed to initialize chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize chat session: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: str,
    request: ChatMessageRequest,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Send a message in a chat session"""
    try:
        # Ensure session_id matches request
        if request.session_id != session_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID in URL must match request body"
            )
        
        logger.info(f"Sending message to session {session_id}")
        response = await chat_service.send_message(request)
        return response
        
    except ValueError as e:
        logger.error(f"Chat session not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=ChatSession)
async def get_chat_session(
    session_id: str,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Get a specific chat session"""
    try:
        # Try to load from database first
        session = await chat_service.load_chat_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat session: {str(e)}"
        )

@router.get("/users/{user_id}/sessions", response_model=List[ChatSession])
async def get_user_chat_sessions(
    user_id: str,
    active_only: bool = True,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Get all chat sessions for a user"""
    try:
        # Load from database
        sessions = await chat_service.load_user_chat_sessions(user_id, active_only)
        return sessions
        
    except Exception as e:
        logger.error(f"Failed to get user chat sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user chat sessions: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Delete a chat session"""
    try:
        success = chat_service.delete_chat_session(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        return {"message": f"Chat session {session_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete chat session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete chat session: {str(e)}"
        )

@router.post("/sessions/{session_id}/clear-memory")
async def clear_session_memory(
    session_id: str,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Clear memory for a chat session"""
    try:
        success = chat_service.clear_session_memory(session_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        return {"message": f"Memory cleared for session {session_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear session memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session memory: {str(e)}"
        )

@router.post("/sessions/{session_id}/messages/{message_id}/regenerate", response_model=ChatResponse)
async def regenerate_response(
    session_id: str,
    message_id: str,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Regenerate an AI response"""
    try:
        response = await chat_service.regenerate_response(session_id, message_id)
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found or cannot be regenerated"
            )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate response: {str(e)}"
        )

@router.get("/sessions/{session_id}/stats")
async def get_session_stats(
    session_id: str,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Get statistics for a chat session"""
    try:
        stats = chat_service.get_session_stats(session_id)
        if not stats:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat session {session_id} not found"
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session stats: {str(e)}"
        )

@router.post("/users/{user_id}/refresh-context")
async def refresh_user_context(
    user_id: str,
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Refresh user's RAG context after profile or resume updates"""
    try:
        success = await chat_service.refresh_user_context(user_id)
        
        if success:
            return {
                "success": True,
                "message": f"RAG context refreshed successfully for user {user_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Failed to refresh RAG context for user {user_id}",
                "timestamp": datetime.utcnow().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failed to refresh user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh user context: {str(e)}"
        )

@router.get("/health")
async def chat_health_check(
    chat_service: RAGChatService = Depends(get_chat_service_dependency)
):
    """Check the health of the chat service"""
    try:
        health = await chat_service.health_check()
        return health
        
    except Exception as e:
        logger.error(f"Chat health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }