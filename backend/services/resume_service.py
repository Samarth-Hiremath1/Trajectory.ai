import os
import uuid
import pdfplumber
import tempfile
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime
import logging

from models.resume import Resume, ResumeChunk, ResumeParseResult, ProcessingStatus
from services.embedding_service import EmbeddingService
from services.supabase_storage_service import SupabaseStorageService
from services.storage_quota_manager import StorageQuotaManager

logger = logging.getLogger(__name__)


class ResumeProcessingService:
    """Service for processing resume uploads and parsing PDF content"""
    
    def __init__(self, use_cloud_storage: bool = True):
        # Storage configuration
        self.use_cloud_storage = use_cloud_storage
        
        if self.use_cloud_storage:
            # Use Supabase Storage for cloud storage
            self.storage_service = SupabaseStorageService()
            self.quota_manager = StorageQuotaManager(self.storage_service)
            logger.info("Using Supabase Storage for file storage with quota management")
        else:
            # Fallback to local storage
            self.upload_dir = Path("uploads/resumes")
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            self.quota_manager = None
            logger.info("Using local file storage")
        
        # Text chunking parameters
        self.chunk_size = 500  # characters per chunk
        self.chunk_overlap = 50  # overlap between chunks
        
        # Initialize embedding service
        self.embedding_service = EmbeddingService()
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: str, temporary: bool = False) -> Tuple[str, Optional[str], Dict]:
        """
        Save uploaded file and return storage path, URL, and storage info
        
        Returns:
            Tuple of (storage_path, public_url, storage_info)
        """
        storage_info = {"temporary": temporary, "quota_status": None}
        
        if self.use_cloud_storage:
            # Check quota status if quota manager is available
            if self.quota_manager:
                quota_status = await self.quota_manager.check_storage_status()
                storage_info["quota_status"] = quota_status
                temporary = quota_status["mode"].value == "temporary"
                storage_info["temporary"] = temporary
            
            # Use Supabase Storage
            storage_path, public_url = await self.storage_service.save_uploaded_file(
                file_content, filename, user_id, temporary=temporary
            )
            return storage_path, public_url, storage_info
        else:
            # Fallback to local storage
            file_extension = Path(filename).suffix
            unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
            file_path = self.upload_dir / unique_filename
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            return str(file_path), None, storage_info
    
    def validate_pdf_file(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate uploaded PDF file"""
        # Check file extension
        if not filename.lower().endswith('.pdf'):
            return False, "File must be a PDF"
        
        # Check file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if len(file_content) > max_size:
            return False, "File size must be less than 10MB"
        
        # Check if file is empty
        if len(file_content) == 0:
            return False, "File cannot be empty"
        
        # Basic PDF header check
        if not file_content.startswith(b'%PDF'):
            return False, "Invalid PDF file format"
        
        return True, None
    
    def parse_pdf_content(self, file_content: bytes, filename: str) -> ResumeParseResult:
        """Extract text content from PDF using pdfplumber"""
        try:
            text_content = ""
            metadata = {
                "page_count": 0,
                "extraction_method": "pdfplumber",
                "filename": filename
            }
            
            # Create temporary file for pdfplumber processing
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                with pdfplumber.open(temp_file_path) as pdf:
                    metadata["page_count"] = len(pdf.pages)
                    
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            text_content += f"\n--- Page {page_num + 1} ---\n"
                            text_content += page_text
                            text_content += "\n"
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
            
            # Clean up the extracted text
            text_content = self._clean_text(text_content)
            
            if not text_content.strip():
                return ResumeParseResult(
                    success=False,
                    text_content="",
                    chunks=[],
                    metadata=metadata,
                    error_message="No text content could be extracted from the PDF"
                )
            
            # Create text chunks
            chunks = self._create_text_chunks(text_content)
            
            return ResumeParseResult(
                success=True,
                text_content=text_content,
                chunks=chunks,
                metadata=metadata
            )
            
        except Exception as e:
            return ResumeParseResult(
                success=False,
                text_content="",
                chunks=[],
                metadata={"error": str(e)},
                error_message=f"Failed to parse PDF: {str(e)}"
            )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers we added
        text = re.sub(r'\n--- Page \d+ ---\n', '\n', text)
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _create_text_chunks(self, text: str) -> List[ResumeChunk]:
        """Split text into overlapping chunks for better context preservation"""
        chunks = []
        
        # Split text into sentences for better chunk boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size and current_chunk:
                # Create chunk from current content
                chunk = ResumeChunk(
                    chunk_id=str(uuid.uuid4()),
                    content=current_chunk.strip(),
                    chunk_index=chunk_index,
                    metadata={
                        "char_count": len(current_chunk),
                        "sentence_count": len(re.split(r'[.!?]', current_chunk))
                    }
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                current_chunk = overlap_text + " " + sentence
                chunk_index += 1
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
        
        # Add final chunk if there's remaining content
        if current_chunk.strip():
            chunk = ResumeChunk(
                chunk_id=str(uuid.uuid4()),
                content=current_chunk.strip(),
                chunk_index=chunk_index,
                metadata={
                    "char_count": len(current_chunk),
                    "sentence_count": len(re.split(r'[.!?]', current_chunk))
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    async def delete_resume_file(self, file_path: str) -> bool:
        """Delete resume file from storage"""
        try:
            if self.use_cloud_storage:
                return await self.storage_service.delete_file(file_path)
            else:
                # Local file deletion
                if os.path.exists(file_path):
                    os.remove(file_path)
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to delete resume file: {e}")
            return False
    
    async def process_resume_with_embeddings(self, user_id: str, file_content: bytes, filename: str) -> Dict:
        """Complete resume processing pipeline with embedding generation"""
        try:
            logger.info(f"Starting resume processing for user {user_id}")
            
            # Validate file
            is_valid, error_message = self.validate_pdf_file(file_content, filename)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_message,
                    "processing_status": ProcessingStatus.FAILED
                }
            
            # Save file (quota manager will determine if temporary)
            file_path, public_url, storage_info = await self.save_uploaded_file(file_content, filename, user_id)
            
            # Parse PDF content
            parse_result = self.parse_pdf_content(file_content, filename)
            if not parse_result.success:
                return {
                    "success": False,
                    "error": parse_result.error_message,
                    "processing_status": ProcessingStatus.FAILED
                }
            
            # Generate and store embeddings
            embedding_success = self.embedding_service.store_resume_embeddings(user_id, parse_result.chunks)
            if not embedding_success:
                logger.warning(f"Failed to store embeddings for user {user_id}, but continuing...")
            
            # Refresh chat service context after successful resume processing
            try:
                await self._refresh_chat_service_context(user_id)
            except Exception as context_error:
                logger.warning(f"Failed to refresh chat context for user {user_id}: {context_error}")
                # Don't fail the resume processing for this
            
            # Handle temporary file cleanup if needed
            cleanup_info = None
            user_notification = None
            
            if storage_info.get("temporary", False):
                # File will be deleted after processing
                try:
                    await self.delete_resume_file(file_path)
                    cleanup_info = {
                        "file_deleted": True,
                        "reason": "storage_limit_reached"
                    }
                    logger.info(f"Deleted temporary resume file for user {user_id} due to storage limits")
                except Exception as cleanup_error:
                    logger.error(f"Failed to delete temporary file: {cleanup_error}")
                    cleanup_info = {
                        "file_deleted": False,
                        "error": str(cleanup_error)
                    }
                
                # Get user notification message
                if self.quota_manager and storage_info.get("quota_status"):
                    user_notification = self.quota_manager.get_user_notification_message(
                        storage_info["quota_status"]
                    )
            
            logger.info(f"Successfully processed resume for user {user_id} (temporary: {storage_info.get('temporary', False)})")
            
            result = {
                "success": True,
                "file_path": file_path,
                "public_url": public_url,
                "text_content": parse_result.text_content,
                "chunks": parse_result.chunks,
                "chunk_count": len(parse_result.chunks),
                "metadata": parse_result.metadata,
                "embeddings_stored": embedding_success,
                "processing_status": ProcessingStatus.COMPLETED,
                "storage_info": storage_info
            }
            
            # Add cleanup and notification info if applicable
            if cleanup_info:
                result["cleanup_info"] = cleanup_info
            if user_notification:
                result["user_notification"] = user_notification
            
            return result
            
        except Exception as e:
            logger.error(f"Resume processing failed for user {user_id}: {e}")
            return {
                "success": False,
                "error": f"Processing failed: {str(e)}",
                "processing_status": ProcessingStatus.FAILED
            }
    
    def search_resume_content(self, user_id: str, query: str, n_results: int = 5) -> List[Dict]:
        """Search user's resume content using semantic similarity"""
        try:
            return self.embedding_service.search_resume_embeddings(user_id, query, n_results)
        except Exception as e:
            logger.error(f"Resume search failed for user {user_id}: {e}")
            return []
    
    def delete_user_resume_data(self, user_id: str, file_path: Optional[str] = None) -> bool:
        """Delete all resume data for a user including embeddings"""
        try:
            # Delete embeddings from ChromaDB
            embeddings_deleted = self.embedding_service.delete_user_embeddings(user_id)
            
            # Delete file if path provided
            file_deleted = True
            if file_path:
                file_deleted = await self.delete_resume_file(file_path)
            
            logger.info(f"Deleted resume data for user {user_id}")
            return embeddings_deleted and file_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete resume data for user {user_id}: {e}")
            return False
    
    async def _refresh_chat_service_context(self, user_id: str):
        """
        Internal function to refresh chat service RAG context after resume updates
        This notifies the chat service to update its context for the user
        """
        try:
            # Import here to avoid circular imports
            from services.chat_service import get_chat_service
            
            # Get chat service and refresh context
            chat_service = await get_chat_service()
            await chat_service.refresh_user_context(user_id)
            logger.info(f"Successfully refreshed chat service context for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error refreshing chat service context for user {user_id}: {e}")
            # Don't raise here as this is a background operation