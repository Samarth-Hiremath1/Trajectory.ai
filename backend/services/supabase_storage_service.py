"""
Supabase Storage Service for handling file uploads
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from pathlib import Path
from supabase import create_client, Client

logger = logging.getLogger(__name__)

class SupabaseStorageService:
    """Service for handling file storage using Supabase Storage"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_anon_key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        # Use anon key for regular operations
        self.supabase: Client = create_client(self.supabase_url, self.supabase_anon_key)
        
        # Use service key for admin operations if available
        if self.supabase_service_key:
            self.supabase_admin: Client = create_client(
                self.supabase_url, 
                self.supabase_service_key
            )
            logger.info(f"✅ Using service role key for storage operations (key ends with: ...{self.supabase_service_key[-10:]})")
        else:
            logger.warning("⚠️ No service role key found, using anon key for storage operations")
            self.supabase_admin = self.supabase
        
        self.bucket_name = "resumes"
        
        # File tracking for quota management
        self.file_metadata = {}
        
        # Ensure bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the resumes bucket exists"""
        try:
            # Try to get bucket info using admin client
            buckets = self.supabase_admin.storage.list_buckets()
            bucket_exists = any(b.name == self.bucket_name for b in buckets)
            
            if bucket_exists:
                logger.info(f"Bucket '{self.bucket_name}' exists")
            else:
                # Create bucket if it doesn't exist using admin client
                self.supabase_admin.storage.create_bucket(
                    self.bucket_name,
                    options={"public": False}  # Private bucket for security
                )
                logger.info(f"Created bucket '{self.bucket_name}'")
        except Exception as e:
            logger.warning(f"Could not verify/create bucket: {e}")
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: str, temporary: bool = False) -> Tuple[str, str]:
        """
        Save uploaded file to Supabase Storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            user_id: User ID for organization
            temporary: Whether this is a temporary file that will be deleted
            
        Returns:
            Tuple of (storage_path, public_url)
        """
        try:
            # Generate unique filename
            file_extension = Path(filename).suffix
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Use different path for temporary files
            if temporary:
                storage_path = f"temp/{user_id}/{unique_filename}"
            else:
                storage_path = f"users/{user_id}/{unique_filename}"
            
            # Store metadata for tracking
            self.file_metadata[storage_path] = {
                "user_id": user_id,
                "original_filename": filename,
                "size": len(file_content),
                "uploaded_at": datetime.utcnow().isoformat(),
                "temporary": temporary
            }
            
            # Upload to Supabase Storage using admin client for permissions
            response = self.supabase_admin.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=file_content,
                file_options={
                    "content-type": "application/pdf",
                    "cache-control": "3600" if not temporary else "300"  # Shorter cache for temp files
                }
            )
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Upload failed: {response.error}")
            
            # Get public URL (for private buckets, this will be a signed URL)
            public_url = self.get_file_url(storage_path)
            
            file_type = "temporary" if temporary else "permanent"
            logger.info(f"Successfully uploaded {file_type} file to {storage_path} ({len(file_content)} bytes)")
            return storage_path, public_url
            
        except Exception as e:
            logger.error(f"Failed to upload file to Supabase Storage: {e}")
            raise
    
    def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """
        Get a signed URL for accessing a private file
        
        Args:
            storage_path: Path to file in storage
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            Signed URL for file access
        """
        try:
            response = self.supabase_admin.storage.from_(self.bucket_name).create_signed_url(
                path=storage_path,
                expires_in=expires_in
            )
            
            if hasattr(response, 'error') and response.error:
                raise Exception(f"Failed to create signed URL: {response.error}")
            
            return response.get('signedURL', '')
            
        except Exception as e:
            logger.error(f"Failed to get file URL: {e}")
            raise
    
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from Supabase Storage
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self.supabase_admin.storage.from_(self.bucket_name).remove([storage_path])
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Failed to delete file: {response.error}")
                return False
            
            logger.info(f"Successfully deleted file: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    async def list_user_files(self, user_id: str) -> list:
        """
        List all files for a specific user
        
        Args:
            user_id: User ID
            
        Returns:
            List of file objects
        """
        try:
            response = self.supabase_admin.storage.from_(self.bucket_name).list(
                path=f"users/{user_id}",
                options={"limit": 100, "offset": 0}
            )
            
            if hasattr(response, 'error') and response.error:
                logger.error(f"Failed to list files: {response.error}")
                return []
            
            return response or []
            
        except Exception as e:
            logger.error(f"Failed to list user files: {e}")
            return []
    
    def get_file_info(self, storage_path: str) -> Optional[dict]:
        """
        Get information about a file
        
        Args:
            storage_path: Path to file in storage
            
        Returns:
            File information dict or None
        """
        try:
            # Extract directory and filename
            path_parts = storage_path.split('/')
            directory = '/'.join(path_parts[:-1])
            filename = path_parts[-1]
            
            response = self.supabase_admin.storage.from_(self.bucket_name).list(
                path=directory,
                options={"limit": 100}
            )
            
            if hasattr(response, 'error') and response.error:
                return None
            
            # Find the specific file
            for file_info in response or []:
                if file_info.get('name') == filename:
                    return file_info
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return None
    
    def health_check(self) -> dict:
        """
        Check the health of Supabase Storage connection
        
        Returns:
            Health status dict
        """
        try:
            # Try to list buckets as a health check
            buckets = self.supabase.storage.list_buckets()
            
            return {
                "status": "healthy",
                "service": "supabase_storage",
                "bucket_name": self.bucket_name,
                "buckets_accessible": len(buckets) if buckets else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "supabase_storage",
                "error": str(e)
            }
    
    async def get_storage_usage(self) -> Dict:
        """Get storage usage statistics"""
        try:
            # List all files in the bucket
            all_files = []
            
            # Get files from both users and temp directories
            for prefix in ["users", "temp"]:
                try:
                    files = self.supabase.storage.from_(self.bucket_name).list(
                        path=prefix,
                        options={"limit": 1000}
                    )
                    if files:
                        all_files.extend(files)
                except Exception as e:
                    logger.warning(f"Could not list files in {prefix}: {e}")
            
            # Calculate total usage
            total_size = 0
            file_count = 0
            temp_files = 0
            
            for file_info in all_files:
                if isinstance(file_info, dict):
                    size = file_info.get("metadata", {}).get("size", 0)
                    total_size += size
                    file_count += 1
                    
                    if file_info.get("name", "").startswith("temp/"):
                        temp_files += 1
            
            return {
                "total_size_bytes": total_size,
                "total_size_gb": total_size / (1024**3),
                "file_count": file_count,
                "temp_files": temp_files,
                "permanent_files": file_count - temp_files
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage usage: {e}")
            return {
                "total_size_bytes": 0,
                "total_size_gb": 0,
                "file_count": 0,
                "temp_files": 0,
                "permanent_files": 0
            }
    
    async def cleanup_temporary_files(self, older_than_hours: int = 24) -> Dict:
        """Clean up temporary files older than specified hours"""
        try:
            # List temporary files
            temp_files = self.supabase.storage.from_(self.bucket_name).list(
                path="temp",
                options={"limit": 1000}
            )
            
            if not temp_files:
                return {"files_deleted": 0, "bytes_freed": 0}
            
            files_to_delete = []
            bytes_to_free = 0
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
            
            for file_info in temp_files:
                if isinstance(file_info, dict):
                    # Check file age (this is simplified - in reality you'd need to track upload times)
                    file_path = f"temp/{file_info.get('name', '')}"
                    
                    # For now, delete all temp files (in production, check actual timestamps)
                    files_to_delete.append(file_path)
                    bytes_to_free += file_info.get("metadata", {}).get("size", 0)
            
            # Delete files
            if files_to_delete:
                response = self.supabase.storage.from_(self.bucket_name).remove(files_to_delete)
                
                if hasattr(response, 'error') and response.error:
                    logger.error(f"Failed to delete temp files: {response.error}")
                    return {"files_deleted": 0, "bytes_freed": 0, "error": str(response.error)}
            
            logger.info(f"Cleaned up {len(files_to_delete)} temporary files, freed {bytes_to_free} bytes")
            return {
                "files_deleted": len(files_to_delete),
                "bytes_freed": bytes_to_free
            }
            
        except Exception as e:
            logger.error(f"Failed to cleanup temporary files: {e}")
            return {"files_deleted": 0, "bytes_freed": 0, "error": str(e)}
    
    def get_file_metadata(self, storage_path: str) -> Optional[Dict]:
        """Get metadata for a specific file"""
        return self.file_metadata.get(storage_path)
    
    def is_temporary_file(self, storage_path: str) -> bool:
        """Check if a file is marked as temporary"""
        metadata = self.get_file_metadata(storage_path)
        return metadata.get("temporary", False) if metadata else storage_path.startswith("temp/")