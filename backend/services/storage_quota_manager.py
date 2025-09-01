"""
Storage Quota Manager for handling storage limits and cleanup
"""
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class StorageMode(Enum):
    PERSISTENT = "persistent"  # Keep files permanently
    TEMPORARY = "temporary"    # Delete after processing

class StorageQuotaManager:
    """Manages storage quotas and automatic cleanup"""
    
    def __init__(self, supabase_storage_service):
        self.storage_service = supabase_storage_service
        
        # Supabase free tier limits
        self.FREE_TIER_STORAGE_GB = 1.0  # 1GB free storage
        self.FREE_TIER_BANDWIDTH_GB = 2.0  # 2GB free bandwidth per month
        
        # Convert to bytes
        self.FREE_TIER_STORAGE_BYTES = int(self.FREE_TIER_STORAGE_GB * 1024 * 1024 * 1024)
        self.FREE_TIER_BANDWIDTH_BYTES = int(self.FREE_TIER_BANDWIDTH_GB * 1024 * 1024 * 1024)
        
        # Storage thresholds
        self.WARNING_THRESHOLD = 0.8  # Warn at 80%
        self.CLEANUP_THRESHOLD = 0.9  # Start cleanup at 90%
        
        logger.info(f"Storage quota manager initialized - Free tier: {self.FREE_TIER_STORAGE_GB}GB storage")
    
    async def check_storage_status(self) -> Dict:
        """Check current storage usage and determine mode"""
        try:
            # Get bucket statistics (this would need to be implemented in Supabase)
            # For now, we'll simulate this check
            bucket_stats = await self._get_bucket_statistics()
            
            storage_used_bytes = bucket_stats.get("storage_used", 0)
            bandwidth_used_bytes = bucket_stats.get("bandwidth_used", 0)
            
            storage_usage_percent = storage_used_bytes / self.FREE_TIER_STORAGE_BYTES
            bandwidth_usage_percent = bandwidth_used_bytes / self.FREE_TIER_BANDWIDTH_BYTES
            
            # Determine storage mode
            if storage_usage_percent >= self.CLEANUP_THRESHOLD:
                mode = StorageMode.TEMPORARY
                message = "Storage limit reached. Files will be processed and then deleted."
            elif storage_usage_percent >= self.WARNING_THRESHOLD:
                mode = StorageMode.PERSISTENT
                message = f"Storage usage at {storage_usage_percent:.1%}. Approaching limit."
            else:
                mode = StorageMode.PERSISTENT
                message = "Storage usage normal."
            
            return {
                "mode": mode,
                "storage_used_bytes": storage_used_bytes,
                "storage_used_gb": storage_used_bytes / (1024**3),
                "storage_usage_percent": storage_usage_percent,
                "bandwidth_used_bytes": bandwidth_used_bytes,
                "bandwidth_used_gb": bandwidth_used_bytes / (1024**3),
                "bandwidth_usage_percent": bandwidth_usage_percent,
                "message": message,
                "needs_cleanup": storage_usage_percent >= self.CLEANUP_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Failed to check storage status: {e}")
            # Default to persistent mode if we can't check
            return {
                "mode": StorageMode.PERSISTENT,
                "message": "Could not check storage status. Using persistent mode.",
                "needs_cleanup": False
            }
    
    async def _get_bucket_statistics(self) -> Dict:
        """Get bucket usage statistics"""
        try:
            # This is a placeholder - Supabase doesn't provide direct API for usage stats
            # In a real implementation, you might:
            # 1. Track usage in your own database
            # 2. Use Supabase dashboard API (if available)
            # 3. Estimate based on file counts and sizes
            
            # For now, we'll use the storage service's get_storage_usage method
            usage_stats = await self.storage_service.get_storage_usage()
            
            return {
                "storage_used": usage_stats.get("total_size_bytes", 0),
                "bandwidth_used": 0,  # Would need to track this separately
                "file_count": usage_stats.get("file_count", 0)
            }
            
        except Exception as e:
            logger.warning(f"Could not get bucket statistics: {e}")
            return {"storage_used": 0, "bandwidth_used": 0, "file_count": 0}
    
    async def cleanup_old_files(self, days_old: int = 7) -> Dict:
        """Clean up old files to free storage space"""
        try:
            cleanup_count = 0
            freed_bytes = 0
            
            # This would need to be implemented to find and delete old files
            # For now, it's a placeholder
            
            logger.info(f"Cleanup completed: {cleanup_count} files deleted, {freed_bytes} bytes freed")
            
            return {
                "files_deleted": cleanup_count,
                "bytes_freed": freed_bytes,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {
                "files_deleted": 0,
                "bytes_freed": 0,
                "success": False,
                "error": str(e)
            }
    
    def get_user_notification_message(self, storage_status: Dict) -> Optional[str]:
        """Get user notification message based on storage status"""
        mode = storage_status["mode"]
        usage_percent = storage_status.get("storage_usage_percent", 0)
        
        if mode == StorageMode.TEMPORARY:
            return {
                "type": "warning",
                "title": "Storage Limit Reached",
                "message": (
                    "I've reached my storage limit, so your resume will be processed and then deleted for space. "
                    "You'll need to re-upload it if you want to make changes later. "
                    "If you'd like me to keep your resume permanently, please email me at [your-email] - "
                    "if I get enough requests, I'll upgrade the storage!"
                ),
                "action_required": False
            }
        elif usage_percent >= self.WARNING_THRESHOLD:
            return {
                "type": "info",
                "title": "Storage Usage Notice",
                "message": (
                    f"Storage usage is at {usage_percent:.1%}. "
                    "Your resume will be kept, but I may need to implement temporary storage soon."
                ),
                "action_required": False
            }
        
        return None
    
    async def should_delete_after_processing(self) -> bool:
        """Check if files should be deleted after processing"""
        storage_status = await self.check_storage_status()
        return storage_status["mode"] == StorageMode.TEMPORARY
    
    async def process_with_cleanup(self, user_id: str, file_content: bytes, filename: str) -> Dict:
        """Process file and clean up if necessary"""
        try:
            # Check storage status
            storage_status = await self.check_storage_status()
            should_cleanup = storage_status["mode"] == StorageMode.TEMPORARY
            
            # Get user notification
            notification = self.get_user_notification_message(storage_status)
            
            return {
                "should_cleanup_after_processing": should_cleanup,
                "storage_status": storage_status,
                "user_notification": notification,
                "storage_mode": storage_status["mode"].value
            }
            
        except Exception as e:
            logger.error(f"Error in process_with_cleanup: {e}")
            return {
                "should_cleanup_after_processing": False,
                "storage_status": {"mode": StorageMode.PERSISTENT},
                "user_notification": None,
                "storage_mode": "persistent"
            }