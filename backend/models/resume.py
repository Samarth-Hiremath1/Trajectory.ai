from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ResumeUploadRequest(BaseModel):
    """Request model for resume upload"""
    pass

class ResumeChunk(BaseModel):
    """Model for resume text chunks"""
    chunk_id: str
    content: str
    chunk_index: int
    metadata: Dict = Field(default_factory=dict)

class Resume(BaseModel):
    """Resume data model"""
    id: Optional[str] = None
    user_id: str
    filename: str
    file_path: str
    file_size: int
    content_type: str = "application/pdf"
    parsed_content: Optional[Dict] = None
    text_chunks: Optional[List[ResumeChunk]] = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    error_message: Optional[str] = None
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    processed_date: Optional[datetime] = None

class ResumeResponse(BaseModel):
    """Response model for resume operations"""
    id: str
    filename: str
    processing_status: ProcessingStatus
    upload_date: datetime
    processed_date: Optional[datetime] = None
    error_message: Optional[str] = None
    chunk_count: Optional[int] = None

class ResumeParseResult(BaseModel):
    """Result of resume parsing operation"""
    success: bool
    text_content: str
    chunks: List[ResumeChunk]
    metadata: Dict
    error_message: Optional[str] = None