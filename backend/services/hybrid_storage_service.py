"""
Hybrid Storage Service that maximizes free tiers and provides fallbacks
"""
import os
import logging
from typing import Optional, Tuple, Dict, Any
from enum import Enum
import asyncio

from services.supabase_storage_service import SupabaseStorageService

logger = logging.getLogger(__name__)

class StorageStrategy(Enum):
    """Storage strategies for different deployment scenarios"""
    DEVELOPMENT = "development"  # Local storage for dev
    FREE_TIER = "free_tier"     # Supabase free tier
    PRODUCTION = "production"   # Paid cloud storage
    HYBRID = "hybrid"           # Smart combination

class HybridStorageService:
    """
    Smart storage service that adapts to deployment environment and usage
    """
    
    def __init__(self):
        self.strategy = self._determine_strategy()
        self.primary_storage = None
        self.fallback_storage = None
        
        # Initialize storage services based on strategy
        self._initialize_storage_services()
        
        logger.info(f"Initialized hybrid storage with strategy: {self.strategy.value}")
    
    def _determine_strategy(self) -> StorageStrategy:
        """Determine the best storage strategy based on environment"""
        
        # Check environment variables
        env_strategy = os.getenv("STORAGE_STRATEGY", "").lower()
        if env_strategy:
            try:
                return StorageStrategy(env_strategy)
            except ValueError:
                pass
        
        # Auto-detect based on environment
        if os.getenv("VERCEL") or os.getenv("NETLIFY"):
            return StorageStrategy.FREE_TIER  # Serverless deployment
        elif os.getenv("HEROKU_APP_NAME"):
            return StorageStrategy.FREE_TIER  # Heroku deployment
        elif os.getenv("RAILWAY_ENVIRONMENT"):
            return StorageStrategy.FREE_TIER  # Railway deployment
        elif os.getenv("NODE_ENV") == "production":
            return StorageStrategy.PRODUCTION
        else:
            return StorageStrategy.DEVELOPMENT
    
    def _initialize_storage_services(self):
        """Initialize storage services based on strategy"""
        
        if self.strategy == StorageStrategy.DEVELOPMENT:
            # Local storage for development
            self.primary_storage = LocalStorageService()
            self.fallback_storage = None
            
        elif self.strategy == StorageStrategy.FREE_TIER:
            # Supabase free tier
            try:
                self.primary_storage = SupabaseStorageService()
                self.fallback_storage = None  # No fallback for cloud deployment
            except Exception as e:
                logger.error(f"Failed to initialize Supabase storage: {e}")
                raise Exception("Cloud storage required for deployment but not available")
                
        elif self.strategy == StorageStrategy.PRODUCTION:
            # Production with fallback
            try:
                self.primary_storage = SupabaseStorageService()
                # Could add AWS S3 as fallback here
                self.fallback_storage = None
            except Exception as e:
                logger.error(f"Failed to initialize production storage: {e}")
                raise
                
        elif self.strategy == StorageStrategy.HYBRID:
            # Smart hybrid approach
            try:
                self.primary_storage = SupabaseStorageService()
                self.fallback_storage = LocalStorageService() if self._can_use_local() else None
            except Exception:
                if self._can_use_local():
                    self.primary_storage = LocalStorageService()
                    self.fallback_storage = None
                else:
                    raise Exception("No storage options available")
    
    def _can_use_local(self) -> bool:
        """Check if local storage can be used in current environment"""
        # Don't use local storage in cloud deployments
        cloud_indicators = [
            "VERCEL", "NETLIFY", "HEROKU_APP_NAME", "RAILWAY_ENVIRONMENT",
            "AWS_LAMBDA_FUNCTION_NAME", "GOOGLE_CLOUD_PROJECT"
        ]
        return not any(os.getenv(indicator) for indicator in cloud_indicators)
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: str) -> Tuple[str, Optional[str]]:
        """Save file using primary storage with fallback"""
        
        try:
            # Try primary storage
            return await self.primary_storage.save_uploaded_file(file_content, filename, user_id)
            
        except Exception as e:
            logger.warning(f"Primary storage failed: {e}")
            
            # Try fallback if available
            if self.fallback_storage:
                logger.info("Attempting fallback storage")
                try:
                    return await self.fallback_storage.save_uploaded_file(file_content, filename, user_id)
                except Exception as fallback_error:
                    logger.error(f"Fallback storage also failed: {fallback_error}")
            
            # If all fails, raise the original error
            raise e
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from storage"""
        try:
            return await self.primary_storage.delete_file(file_path)
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False
    
    def get_file_url(self, storage_path: str, expires_in: int = 3600) -> str:
        """Get URL for file access"""
        if hasattr(self.primary_storage, 'get_file_url'):
            return self.primary_storage.get_file_url(storage_path, expires_in)
        else:
            # For local storage, return a placeholder or local path
            return f"/api/files/{storage_path}"
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about current storage configuration"""
        return {
            "strategy": self.strategy.value,
            "primary_storage": type(self.primary_storage).__name__,
            "fallback_storage": type(self.fallback_storage).__name__ if self.fallback_storage else None,
            "can_use_local": self._can_use_local(),
            "environment_indicators": {
                "vercel": bool(os.getenv("VERCEL")),
                "heroku": bool(os.getenv("HEROKU_APP_NAME")),
                "railway": bool(os.getenv("RAILWAY_ENVIRONMENT")),
                "netlify": bool(os.getenv("NETLIFY")),
                "production": os.getenv("NODE_ENV") == "production"
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of storage services"""
        health = {
            "strategy": self.strategy.value,
            "primary_storage": {"status": "unknown"},
            "fallback_storage": {"status": "not_configured"}
        }
        
        # Check primary storage
        try:
            if hasattr(self.primary_storage, 'health_check'):
                health["primary_storage"] = await self.primary_storage.health_check()
            else:
                health["primary_storage"] = {"status": "healthy", "type": "local"}
        except Exception as e:
            health["primary_storage"] = {"status": "unhealthy", "error": str(e)}
        
        # Check fallback storage if available
        if self.fallback_storage:
            try:
                if hasattr(self.fallback_storage, 'health_check'):
                    health["fallback_storage"] = await self.fallback_storage.health_check()
                else:
                    health["fallback_storage"] = {"status": "healthy", "type": "local"}
            except Exception as e:
                health["fallback_storage"] = {"status": "unhealthy", "error": str(e)}
        
        return health

class LocalStorageService:
    """Simple local storage service for development"""
    
    def __init__(self, upload_dir: str = "uploads/resumes"):
        from pathlib import Path
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_uploaded_file(self, file_content: bytes, filename: str, user_id: str) -> Tuple[str, Optional[str]]:
        """Save file locally"""
        import uuid
        from pathlib import Path
        
        file_extension = Path(filename).suffix
        unique_filename = f"{user_id}_{uuid.uuid4().hex}{file_extension}"
        file_path = self.upload_dir / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path), None
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete local file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception:
            return False