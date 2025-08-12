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

from fastapi import Header

async def get_current_user_id(x_user_id: str = Header(None)) -> str:
    """Get user ID from request headers"""
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not provided in headers"
        )
    return x_user_id


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
        
        # Save resume to database
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        
        resume_data = {
            "id": resume.id,
            "user_id": resume.user_id,
            "filename": resume.filename,
            "file_path": resume.file_path,
            "file_size": resume.file_size,
            "content_type": resume.content_type,
            "parsed_content": resume.parsed_content,
            "text_chunks": [chunk.dict() for chunk in resume.text_chunks],
            "processing_status": resume.processing_status.value,
            "upload_date": resume.upload_date.isoformat(),
            "processed_date": resume.processed_date.isoformat() if resume.processed_date else None
        }
        
        saved_resume_id = await db_service.save_resume(resume_data)
        resume.id = saved_resume_id
        
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


@router.get("/user/{user_id}")
async def get_user_resume(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get the resume for a specific user
    
    - **user_id**: ID of the user whose resume to retrieve
    - Returns: User's resume data
    """
    try:
        # For security, ensure user can only access their own resume
        if user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own resume"
            )
        
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        
        resume_data = await db_service.get_user_resume(user_id)
        
        if not resume_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No resume found for this user"
            )
        
        return resume_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user resume: {str(e)}"
        )

@router.get("/list", response_model=list[ResumeResponse])
async def list_user_resumes(
    user_id: str = Depends(get_current_user_id)
):
    """
    List all resumes for the current user
    
    - Returns: List of user's resumes with processing status
    """
    try:
        from services.database_service import DatabaseService
        db_service = DatabaseService()
        
        resume_data = await db_service.get_user_resume(user_id)
        
        if not resume_data:
            return []
        
        # Convert to ResumeResponse format
        resume_response = ResumeResponse(
            id=resume_data['id'],
            filename=resume_data['filename'],
            processing_status=ProcessingStatus(resume_data['processing_status']),
            upload_date=resume_data['upload_date'],
            processed_date=resume_data.get('processed_date'),
            error_message=resume_data.get('error_message'),
            chunk_count=len(resume_data.get('text_chunks', []))
        )
        
        return [resume_response]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list user resumes: {str(e)}"
        )


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