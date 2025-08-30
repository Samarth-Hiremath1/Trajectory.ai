"""
Performance monitoring API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/performance", tags=["performance"])

@router.get("/metrics")
async def get_current_metrics() -> Dict[str, Any]:
    """Get current performance metrics for all services"""
    try:
        from services.performance_monitor import get_performance_monitor
        
        monitor = await get_performance_monitor()
        metrics = monitor.get_current_metrics()
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary")
async def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary with health status"""
    try:
        from services.performance_monitor import get_performance_monitor
        
        monitor = await get_performance_monitor()
        summary = monitor.get_performance_summary()
        
        return {
            "status": "success",
            "data": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{metric_type}")
async def get_historical_metrics(
    metric_type: str,
    hours: int = Query(default=1, ge=1, le=24, description="Hours of history to return")
) -> Dict[str, Any]:
    """
    Get historical metrics for a specific service
    
    Args:
        metric_type: Type of metrics ('system', 'ai_service', 'database', 'cache')
        hours: Number of hours of history to return (1-24)
    """
    try:
        from services.performance_monitor import get_performance_monitor
        
        valid_types = ["system", "ai_service", "database", "cache"]
        if metric_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid metric_type. Must be one of: {valid_types}"
            )
        
        monitor = await get_performance_monitor()
        history = monitor.get_historical_metrics(metric_type, hours)
        
        return {
            "status": "success",
            "data": {
                "metric_type": metric_type,
                "hours": hours,
                "data_points": len(history),
                "history": history
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting historical metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def get_service_health() -> Dict[str, Any]:
    """Get health status of all monitored services"""
    try:
        health_status = {}
        
        # AI Service health
        try:
            from services.ai_service import get_ai_service
            ai_service = await get_ai_service()
            ai_health = await ai_service.health_check()
            health_status["ai_service"] = ai_health
        except Exception as e:
            health_status["ai_service"] = {"status": "unhealthy", "error": str(e)}
        
        # Database health
        try:
            from services.connection_pool import get_connection_pool
            pool = await get_connection_pool()
            db_health = await pool.health_check()
            health_status["database"] = db_health
        except Exception as e:
            health_status["database"] = {"healthy": False, "error": str(e)}
        
        # Cache health
        try:
            from services.cache_service import get_cache_service
            cache_service = await get_cache_service()
            cache_health = await cache_service.health_check()
            health_status["cache"] = cache_health
        except Exception as e:
            health_status["cache"] = {"healthy": False, "error": str(e)}
        
        # Performance monitor health
        try:
            from services.performance_monitor import get_performance_monitor
            monitor = await get_performance_monitor()
            health_status["performance_monitor"] = {
                "healthy": monitor._running,
                "collection_interval": monitor.collection_interval,
                "history_size": monitor.history_size
            }
        except Exception as e:
            health_status["performance_monitor"] = {"healthy": False, "error": str(e)}
        
        # Overall health
        all_healthy = all(
            service.get("healthy", service.get("status") == "healthy")
            for service in health_status.values()
        )
        
        return {
            "status": "success",
            "data": {
                "overall_health": "healthy" if all_healthy else "degraded",
                "services": health_status,
                "timestamp": health_status.get("performance_monitor", {}).get("timestamp")
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting service health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-service/metrics")
async def get_ai_service_metrics() -> Dict[str, Any]:
    """Get detailed AI service metrics"""
    try:
        from services.ai_service import get_ai_service
        
        ai_service = await get_ai_service()
        metrics = ai_service.get_metrics()
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting AI service metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/database/status")
async def get_database_status() -> Dict[str, Any]:
    """Get database connection pool status"""
    try:
        from services.connection_pool import get_connection_pool
        
        pool = await get_connection_pool()
        status = pool.get_pool_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Error getting database status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/metrics")
async def get_cache_metrics() -> Dict[str, Any]:
    """Get cache service metrics"""
    try:
        from services.cache_service import get_cache_service
        
        cache_service = await get_cache_service()
        metrics = cache_service.get_metrics()
        
        return {
            "status": "success",
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting cache metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/flush")
async def flush_cache(namespace: Optional[str] = None) -> Dict[str, Any]:
    """
    Flush cache entries
    
    Args:
        namespace: Optional namespace to flush (None for all)
    """
    try:
        from services.cache_service import get_cache_service
        
        cache_service = await get_cache_service()
        success = await cache_service.flush(namespace)
        
        return {
            "status": "success",
            "data": {
                "flushed": success,
                "namespace": namespace or "all"
            }
        }
        
    except Exception as e:
        logger.error(f"Error flushing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-service/reset-metrics")
async def reset_ai_service_metrics() -> Dict[str, Any]:
    """Reset AI service metrics"""
    try:
        from services.ai_service import get_ai_service
        
        ai_service = await get_ai_service()
        ai_service.reset_metrics()
        
        return {
            "status": "success",
            "data": {
                "message": "AI service metrics reset successfully"
            }
        }
        
    except Exception as e:
        logger.error(f"Error resetting AI service metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))