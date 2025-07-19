from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Optional
import uuid
from datetime import datetime

from models.resume import Resume, ResumeResponse, ProcessingStatus
from services.resume_service import ResumeProcessingService

router = APIRouter(prefix="/api/resume", tags=["resume"])

# Initialize resume processing service
resume_service = ResumeProcessingService()

# TODO: Replace with actual user authentication
async def get_current_user_id() -> str:
    """Temporary function to get user ID - replace with actual auth"""
    return "temp_user_123"


@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload and process a PDF resume file with embedding generation
    
    - **file**: PDF file to upload (max 10MB)
    - Returns: Resume processing status and metadata
    """
    
    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file: {str(e)}"
        )
    
    # Process resume with embeddings
    try:
        result = await resume_service.process_resume_with_embeddings(
            user_id, file_content, file.filename
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        # Create resume record
        resume_id = str(uuid.uuid4())
        resume = Resume(
            id=resume_id,
            user_id=user_id,
            filename=file.filename,
            file_path=result["file_path"],
            file_size=len(file_content),
            content_type=file.content_type or "application/pdf",
            parsed_content={
                "text_content": result["text_content"],
                "metadata": result["metadata"]
            },
            text_chunks=result["chunks"],
            processing_status=result["processing_status"],
            processed_date=datetime.utcnow()
        )
        
        # TODO: Save resume to database (Supabase integration)
        # For now, we'll just return the response
        
        return ResumeResponse(
            id=resume.id,
            filename=resume.filename,
            processing_status=resume.processing_status,
            upload_date=resume.upload_date,
            processed_date=resume.processed_date,
            error_message=resume.error_message,
            chunk_count=result["chunk_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process resume: {str(e)}"
        )


@router.get("/status/{resume_id}", response_model=ResumeResponse)
async def get_resume_status(
    resume_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get processing status of a resume
    
    - **resume_id**: ID of the resume to check
    - Returns: Resume processing status and metadata
    """
    # TODO: Implement database lookup for resume status
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume status lookup not yet implemented - requires database integration"
    )


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a resume and its associated file
    
    - **resume_id**: ID of the resume to delete
    - Returns: Success confirmation
    """
    # TODO: Implement database lookup and file deletion
    # For now, return a placeholder response
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Resume deletion not yet implemented - requires database integration"
    )


@router.get("/list", response_model=list[ResumeResponse])
async def list_user_resumes(
    user_id: str = Depends(get_current_user_id)
):
    """
    List all resumes for the current user
    
    - Returns: List of user's resumes with processing status
    """
    # TODO: Implement database lookup for user resumes
    # For now, return empty list
    return []


@router.post("/search")
async def search_resume_content(
    query: str,
    n_results: int = 5,
    user_id: str = Depends(get_current_user_id)
):
    """
    Search resume content using semantic similarity
    
    - **query**: Search query text
    - **n_results**: Number of results to return (default: 5)
    - Returns: List of relevant resume chunks with similarity scores
    """
    try:
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        results = resume_service.search_resume_content(user_id, query, n_results)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Check the health of the resume processing and embedding services
    
    - Returns: Health status of all components
    """
    try:
        # Get embedding service health
        embedding_health = resume_service.embedding_service.health_check()
        
        # Get collection stats
        collection_stats = resume_service.embedding_service.get_collection_stats("resume_embeddings")
        
        return {
            "status": "healthy" if embedding_health["status"] == "healthy" else "degraded",
            "embedding_service": embedding_health,
            "collections": {
                "resume_embeddings": collection_stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }