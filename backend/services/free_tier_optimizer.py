"""
Free Tier Optimizer - Maximizes usage of free tiers across services
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

class FreeTierOptimizer:
    """Optimizes resource usage to stay within free tier limits"""
    
    def __init__(self):
        self.supabase_limits = {
            "storage_gb": 1.0,
            "bandwidth_gb": 2.0,
            "database_mb": 500,
            "auth_users": 50000
        }
        
        self.railway_limits = {
            "credit_dollars": 5.0,
            "hours_per_month": 500  # Approximate
        }
        
        self.vercel_limits = {
            "bandwidth_gb": 100,
            "build_minutes": 6000,
            "serverless_executions": 100000
        }
    
    async def check_storage_usage(self) -> Dict[str, Any]:
        """Check current storage usage against limits"""
        try:
            from services.supabase_storage_service import SupabaseStorageService
            storage_service = SupabaseStorageService()
            
            # This would need to be implemented in Supabase service
            # For now, return estimated usage
            return {
                "storage_used_gb": 0.1,  # Placeholder
                "storage_limit_gb": self.supabase_limits["storage_gb"],
                "storage_percentage": 10.0,
                "bandwidth_used_gb": 0.05,
                "bandwidth_limit_gb": self.supabase_limits["bandwidth_gb"],
                "bandwidth_percentage": 2.5,
                "status": "healthy"
            }
        except Exception as e:
            logger.error(f"Failed to check storage usage: {e}")
            return {"status": "error", "error": str(e)}
    
    async def optimize_file_storage(self, file_content: bytes, filename: str) -> bytes:
        """Optimize file to reduce storage usage"""
        try:
            # For PDFs, we can compress them
            if filename.lower().endswith('.pdf'):
                return await self._compress_pdf(file_content)
            return file_content
        except Exception as e:
            logger.warning(f"File optimization failed: {e}")
            return file_content
    
    async def _compress_pdf(self, pdf_content: bytes) -> bytes:
        """Compress PDF to reduce file size"""
        try:
            # Simple compression - in production, use proper PDF compression
            # For now, just return original content
            # TODO: Implement PDF compression using PyPDF2 or similar
            return pdf_content
        except Exception:
            return pdf_content
    
    async def cleanup_old_files(self, days_old: int = 30) -> Dict[str, Any]:
        """Clean up old files to free space"""
        try:
            # This would implement cleanup logic
            # For now, return placeholder
            return {
                "files_cleaned": 0,
                "space_freed_mb": 0,
                "status": "completed"
            }
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def should_compress_response(self, response_size: int) -> bool:
        """Determine if response should be compressed to save bandwidth"""
        # Compress responses larger than 1KB
        return response_size > 1024
    
    def get_optimization_recommendations(self, usage_stats: Dict[str, Any]) -> list:
        """Get recommendations for staying within free tiers"""
        recommendations = []
        
        # Storage recommendations
        if usage_stats.get("storage_percentage", 0) > 80:
            recommendations.append({
                "type": "storage",
                "priority": "high",
                "message": "Storage usage is high. Consider cleaning up old files.",
                "action": "cleanup_old_files"
            })
        
        # Bandwidth recommendations
        if usage_stats.get("bandwidth_percentage", 0) > 80:
            recommendations.append({
                "type": "bandwidth",
                "priority": "high", 
                "message": "Bandwidth usage is high. Enable response compression.",
                "action": "enable_compression"
            })
        
        return recommendations
    
    async def monitor_free_tier_health(self) -> Dict[str, Any]:
        """Monitor overall free tier health"""
        storage_usage = await self.check_storage_usage()
        
        health_score = 100
        issues = []
        
        # Check storage health
        if storage_usage.get("storage_percentage", 0) > 90:
            health_score -= 30
            issues.append("Storage nearly full")
        
        if storage_usage.get("bandwidth_percentage", 0) > 90:
            health_score -= 30
            issues.append("Bandwidth nearly exhausted")
        
        status = "healthy"
        if health_score < 70:
            status = "warning"
        if health_score < 40:
            status = "critical"
        
        return {
            "health_score": health_score,
            "status": status,
            "issues": issues,
            "usage_stats": storage_usage,
            "recommendations": self.get_optimization_recommendations(storage_usage)
        }