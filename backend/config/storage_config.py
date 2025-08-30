"""
Storage configuration for the application
"""
import os
from enum import Enum

class StorageProvider(Enum):
    LOCAL = "local"
    SUPABASE = "supabase"
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"

class StorageConfig:
    """Configuration for file storage"""
    
    # Default storage provider (can be overridden by environment variable)
    DEFAULT_PROVIDER = StorageProvider.SUPABASE
    
    @classmethod
    def get_storage_provider(cls) -> StorageProvider:
        """Get the configured storage provider"""
        provider_name = os.getenv("STORAGE_PROVIDER", cls.DEFAULT_PROVIDER.value).lower()
        
        try:
            return StorageProvider(provider_name)
        except ValueError:
            # Fallback to default if invalid provider specified
            return cls.DEFAULT_PROVIDER
    
    @classmethod
    def use_cloud_storage(cls) -> bool:
        """Check if cloud storage should be used"""
        return cls.get_storage_provider() != StorageProvider.LOCAL
    
    # Storage-specific configurations
    SUPABASE_CONFIG = {
        "bucket_name": "resumes",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_types": ["application/pdf"],
        "signed_url_expires": 3600  # 1 hour
    }
    
    AWS_S3_CONFIG = {
        "bucket_name": os.getenv("AWS_S3_BUCKET", "goaltrajectory-resumes"),
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_types": ["application/pdf"],
        "encryption": "AES256"
    }
    
    LOCAL_CONFIG = {
        "upload_dir": "uploads/resumes",
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "allowed_types": ["application/pdf"]
    }
    
    @classmethod
    def get_config(cls) -> dict:
        """Get configuration for the current storage provider"""
        provider = cls.get_storage_provider()
        
        if provider == StorageProvider.SUPABASE:
            return cls.SUPABASE_CONFIG
        elif provider == StorageProvider.AWS_S3:
            return cls.AWS_S3_CONFIG
        elif provider == StorageProvider.LOCAL:
            return cls.LOCAL_CONFIG
        else:
            return cls.LOCAL_CONFIG  # Fallback