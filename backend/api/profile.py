from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field, validator

from services.database_service import DatabaseService
from services.embedding_service import EmbeddingService

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Initialize services lazily to avoid startup errors
db_service = None
embedding_service = None

def get_db_service():
    global db_service
    if db_service is None:
        db_service = DatabaseService()
    return db_service

def get_embedding_service():
    global embedding_service
    if embedding_service is None:
        from services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
    return embedding_service

from fastapi import Header

async def get_current_user_id(x_user_id: str = Header(None)) -> str:
    """Get user ID from request headers"""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not provided in headers"
        )
    return x_user_id


class EducationData(BaseModel):
    """Education information model"""
    degree: Optional[str] = None
    field: Optional[str] = None
    institution: Optional[str] = None
    graduationYear: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    """Request model for profile updates"""
    education: Optional[EducationData] = None
    career_background: Optional[str] = None
    current_role: Optional[str] = None
    target_roles: Optional[List[str]] = None
    additional_details: Optional[str] = None
    
    @validator('target_roles')
    def validate_target_roles(cls, v):
        if v is not None:
            # Remove empty strings and duplicates
            cleaned = list(set([role.strip() for role in v if role.strip()]))
            return cleaned
        return v
    
    @validator('career_background', 'current_role', 'additional_details')
    def validate_text_fields(cls, v):
        if v is not None:
            return v.strip()
        return v


class ProfileResponse(BaseModel):
    """Response model for profile operations"""
    id: str
    user_id: str
    education: Dict
    career_background: Optional[str]
    current_role: Optional[str]
    target_roles: List[str]
    additional_details: Optional[str]
    created_at: datetime
    updated_at: datetime


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """
    Get user profile by user ID
    
    - **user_id**: ID of the user whose profile to retrieve
    - Returns: User profile data
    """
    try:
        # TODO: Add proper authorization check to ensure user can only access their own profile
        
        profile = await get_db_service().get_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )
        
        return ProfileResponse(**profile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve profile: {str(e)}"
        )


@router.post("/{user_id}", response_model=ProfileResponse)
async def create_profile(
    user_id: str,
    profile_data: ProfileUpdateRequest
):
    """
    Create a new user profile
    
    - **user_id**: ID of the user for whom to create the profile
    - **profile_data**: Profile information
    - Returns: Created profile data
    """
    try:
        # TODO: Add proper authorization check to ensure user can only create their own profile
        
        # Convert profile data to dict for database storage
        create_data = profile_data.model_dump(exclude_unset=True)
        
        # Create profile in database
        created_profile = await get_db_service().create_profile(user_id, create_data)
        if not created_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile creation failed - profile may already exist"
            )
        
        # Trigger RAG context update in background
        try:
            await _refresh_user_rag_context(user_id)
            await _refresh_chat_service_context(user_id)
        except Exception as e:
            # Log the error but don't fail the profile creation
            print(f"Warning: Failed to refresh RAG context for user {user_id}: {e}")
        
        return ProfileResponse(**created_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )


@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: str,
    profile_data: ProfileUpdateRequest
):
    """
    Update user profile with validation and RAG context refresh
    
    - **user_id**: ID of the user whose profile to update
    - **profile_data**: Updated profile information
    - Returns: Updated profile data
    """
    try:
        # TODO: Add proper authorization check to ensure user can only update their own profile
        
        # Convert education data to dict for database storage
        update_data = profile_data.model_dump(exclude_unset=True)
        
        # Update profile in database
        updated_profile = await get_db_service().update_profile(user_id, update_data)
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or update failed"
            )
        
        # Trigger RAG context update in background
        # This will refresh the user's context for AI chat and roadmap generation
        try:
            await _refresh_user_rag_context(user_id)
            # Also refresh chat service context
            await _refresh_chat_service_context(user_id)
        except Exception as e:
            # Log the error but don't fail the profile update
            print(f"Warning: Failed to refresh RAG context for user {user_id}: {e}")
        
        return ProfileResponse(**updated_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.post("/{user_id}/refresh-context")
async def refresh_user_context(user_id: str):
    """
    Manually refresh user's RAG context after profile changes
    
    - **user_id**: ID of the user whose context to refresh
    - Returns: Success confirmation
    """
    try:
        # TODO: Add proper authorization check
        
        await _refresh_user_rag_context(user_id)
        
        return {
            "success": True,
            "message": "User RAG context refreshed successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh user context: {str(e)}"
        )


async def _refresh_user_rag_context(user_id: str):
    """
    Internal function to refresh user's RAG context
    This updates the embeddings and context used by AI services
    """
    try:
        # Get updated profile data
        profile = await get_db_service().get_profile(user_id)
        if not profile:
            return
        
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
            get_embedding_service().store_profile_context(user_id, profile_context)
        
    except Exception as e:
        print(f"Error refreshing RAG context for user {user_id}: {e}")
        raise


async def _refresh_chat_service_context(user_id: str):
    """
    Internal function to refresh chat service RAG context
    This notifies the chat service to update its context for the user
    """
    try:
        # Import here to avoid circular imports
        from services.chat_service import get_chat_service
        
        # Get chat service and refresh context
        chat_service = await get_chat_service()
        await chat_service.refresh_user_context(user_id)
        
    except Exception as e:
        print(f"Error refreshing chat service context for user {user_id}: {e}")
        # Don't raise here as this is a background operation


@router.delete("/{user_id}")
async def delete_profile(user_id: str):
    """
    Delete user profile and associated data
    
    - **user_id**: ID of the user whose profile to delete
    - Returns: Success confirmation
    """
    try:
        # TODO: Add proper authorization check
        
        # Delete profile from database
        success = await get_db_service().delete_profile(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found or deletion failed"
            )
        
        # Clean up associated embeddings
        try:
            get_embedding_service().delete_user_embeddings(user_id)
        except Exception as e:
            print(f"Warning: Failed to delete embeddings for user {user_id}: {e}")
        
        return {
            "success": True,
            "message": "Profile deleted successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete profile: {str(e)}"
        )


@router.get("/{user_id}/context-status")
async def get_user_context_status(user_id: str):
    """
    Get status of user's RAG context and embeddings
    
    - **user_id**: ID of the user whose context status to check
    - Returns: Context status information
    """
    try:
        # TODO: Add proper authorization check
        
        # Check if user has profile
        profile = await get_db_service().get_profile(user_id)
        has_profile = profile is not None
        
        # Check if user has resume embeddings
        resume_stats = get_embedding_service().get_user_embedding_stats(user_id, "resume_embeddings")
        
        # Check if user has profile context embeddings
        profile_stats = get_embedding_service().get_user_embedding_stats(user_id, "profile_context")
        
        return {
            "user_id": user_id,
            "has_profile": has_profile,
            "resume_embeddings": {
                "exists": resume_stats["count"] > 0,
                "count": resume_stats["count"],
                "last_updated": resume_stats.get("last_updated")
            },
            "profile_context": {
                "exists": profile_stats["count"] > 0,
                "count": profile_stats["count"],
                "last_updated": profile_stats.get("last_updated")
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context status: {str(e)}"
        )