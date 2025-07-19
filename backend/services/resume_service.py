import os
import uuid
import pdfplumber
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
from datetime import datetime

from models.resume import Resume, ResumeChunk, ResumeParseResult, ProcessingStatus


class ResumeProcessingService:
    """Service for processing resume uploads and parsing PDF content"""
    
    def __init__(self, upload_dir: str = "uploads/resumes"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Text chunking parameters
        self.chunk_size = 500  # characters per chunk
        self.chunk_overlap = 50  # overlap between chunks
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: str) -> str:
        """Save uploaded file to disk and return file path"""
        # Generate unique filename to avoid conflicts
        file_extension = Path(filename).suffix
        unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path)
    
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
    
    def parse_pdf_content(self, file_path: str) -> ResumeParseResult:
        """Extract text content from PDF using pdfplumber"""
        try:
            text_content = ""
            metadata = {
                "page_count": 0,
                "extraction_method": "pdfplumber"
            }
            
            with pdfplumber.open(file_path) as pdf:
                metadata["page_count"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text
                        text_content += "\n"
            
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
    
    def delete_resume_file(self, file_path: str) -> bool:
        """Delete resume file from disk"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False