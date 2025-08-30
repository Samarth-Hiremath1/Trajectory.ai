"""
Performance monitoring service for tracking system metrics and AI service performance
"""
import os
import time
import psutil
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_usage_percent: float = 0.0
    disk_free_gb: float = 0.0
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    process_count: int = 0
    timestamp: Optional[datetime] = None

@dataclass
class AIServiceMetrics:
    """AI service performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    total_tokens: int = 0
    provider_usage: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_query_time: float = 0.0
    active_connections: int = 0
    idle_connections: int = 0
    pool_size: int = 0
    timestamp: Optional[datetime] = None

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    total_gets: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    total_sets: int = 0
    key_count: int = 0
    memory_usage_mb: float = 0.0
    backend_type: str = "memory"
    timestamp: Optional[datetime] = None

class PerformanceMonitor:
    """
    Comprehensive performance monitoring service
    """
    
    def __init__(
        self,
        collection_interval: int = 60,  # seconds
        history_size: int = 1440,  # 24 hours of minute-by-minute data
        enable_detailed_logging: bool = False
    ):
        """
        Initialize performance monitor
        
        Args:
            collection_interval: How often to collect metrics (seconds)
            history_size: Number of historical data points to keep
            enable_detailed_logging: Enable detailed performance logging
        """
        self.collection_interval = collection_interval
        self.history_size = history_size
        self.enable_detailed_logging = enable_detailed_logging
        
        # Historical data storage
        self.system_history: deque = deque(maxlen=history_size)
        self.ai_service_history: deque = deque(maxlen=history_size)
        self.database_history: deque = deque(maxlen=history_size)
        self.cache_history: deque = deque(maxlen=history_size)
        
        # Current metrics
        self.current_system_metrics: Optional[SystemMetrics] = None
        self.current_ai_metrics: Optional[AIServiceMetrics] = None
        self.current_db_metrics: Optional[DatabaseMetrics] = None
        self.current_cache_metrics: Optional[CacheMetrics] = None
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Alert thresholds
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_usage_percent": 90.0,
            "ai_error_rate": 10.0,  # percentage
            "db_error_rate": 5.0,   # percentage
            "response_time_ms": 5000.0
        }
        
        logger.info("Performance monitor initialized")
    
    async def start_monitoring(self):
        """Start the performance monitoring task"""
        if self._running:
            logger.warning("Performance monitoring already running")
            return
        
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop the performance monitoring task"""
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Performance monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Collect all metrics
                await self._collect_system_metrics()
                await self._collect_ai_service_metrics()
                await self._collect_database_metrics()
                await self._collect_cache_metrics()
                
                # Check for alerts
                await self._check_alerts()
                
                # Log detailed metrics if enabled
                if self.enable_detailed_logging:
                    self._log_detailed_metrics()
                
                # Wait for next collection
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / (1024 * 1024)
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_free_gb = disk.free / (1024 * 1024 * 1024)
            
            # Network I/O
            network = psutil.net_io_counters()
            network_bytes_sent = network.bytes_sent
            network_bytes_recv = network.bytes_recv
            
            # Process count
            process_count = len(psutil.pids())
            
            # Create metrics object
            metrics = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                disk_free_gb=disk_free_gb,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                process_count=process_count,
                timestamp=datetime.utcnow()
            )
            
            self.current_system_metrics = metrics
            self.system_history.append(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
    
    async def _collect_ai_service_metrics(self):
        """Collect AI service performance metrics"""
        try:
            from services.ai_service import get_ai_service
            
            ai_service = await get_ai_service()
            service_metrics = ai_service.get_metrics()
            
            metrics = AIServiceMetrics(
                total_requests=service_metrics.get("total_requests", 0),
                successful_requests=service_metrics.get("successful_requests", 0),
                failed_requests=service_metrics.get("failed_requests", 0),
                average_response_time=service_metrics.get("average_response_time", 0.0),
                total_tokens=service_metrics.get("total_tokens", 0),
                provider_usage=service_metrics.get("provider_usage", {}),
                error_counts=service_metrics.get("error_counts", {}),
                timestamp=datetime.utcnow()
            )
            
            self.current_ai_metrics = metrics
            self.ai_service_history.append(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting AI service metrics: {str(e)}")
    
    async def _collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            from services.connection_pool import get_connection_pool
            
            pool = await get_connection_pool()
            pool_status = pool.get_pool_status()
            
            if pool_status.get("status") == "active":
                metrics = DatabaseMetrics(
                    total_queries=pool_status.get("total_queries", 0),
                    successful_queries=pool_status.get("successful_queries", 0),
                    failed_queries=pool_status.get("failed_queries", 0),
                    average_query_time=pool_status.get("average_query_time", 0.0),
                    active_connections=pool_status.get("active_connections", 0),
                    idle_connections=pool_status.get("idle_connections", 0),
                    pool_size=pool_status.get("pool_size", 0),
                    timestamp=datetime.utcnow()
                )
                
                self.current_db_metrics = metrics
                self.database_history.append(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting database metrics: {str(e)}")
    
    async def _collect_cache_metrics(self):
        """Collect cache performance metrics"""
        try:
            from services.cache_service import get_cache_service
            
            cache_service = await get_cache_service()
            cache_metrics = cache_service.get_metrics()
            
            metrics = CacheMetrics(
                total_gets=cache_metrics.get("total_gets", 0),
                cache_hits=cache_metrics.get("cache_hits", 0),
                cache_misses=cache_metrics.get("cache_misses", 0),
                hit_rate=cache_metrics.get("hit_rate_percentage", 0.0),
                total_sets=cache_metrics.get("total_sets", 0),
                key_count=cache_metrics.get("key_count", 0),
                memory_usage_mb=cache_metrics.get("memory_usage_bytes", 0) / (1024 * 1024),
                backend_type=cache_metrics.get("backend", "memory"),
                timestamp=datetime.utcnow()
            )
            
            self.current_cache_metrics = metrics
            self.cache_history.append(metrics)
            
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {str(e)}")
    
    async def _check_alerts(self):
        """Check for performance alerts"""
        alerts = []
        
        # System alerts
        if self.current_system_metrics:
            sys_metrics = self.current_system_metrics
            
            if sys_metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
                alerts.append(f"High CPU usage: {sys_metrics.cpu_percent:.1f}%")
            
            if sys_metrics.memory_percent > self.alert_thresholds["memory_percent"]:
                alerts.append(f"High memory usage: {sys_metrics.memory_percent:.1f}%")
            
            if sys_metrics.disk_usage_percent > self.alert_thresholds["disk_usage_percent"]:
                alerts.append(f"High disk usage: {sys_metrics.disk_usage_percent:.1f}%")
        
        # AI service alerts
        if self.current_ai_metrics:
            ai_metrics = self.current_ai_metrics
            
            if ai_metrics.total_requests > 0:
                error_rate = (ai_metrics.failed_requests / ai_metrics.total_requests) * 100
                if error_rate > self.alert_thresholds["ai_error_rate"]:
                    alerts.append(f"High AI service error rate: {error_rate:.1f}%")
            
            if ai_metrics.average_response_time > self.alert_thresholds["response_time_ms"]:
                alerts.append(f"Slow AI response time: {ai_metrics.average_response_time:.1f}ms")
        
        # Database alerts
        if self.current_db_metrics:
            db_metrics = self.current_db_metrics
            
            if db_metrics.total_queries > 0:
                error_rate = (db_metrics.failed_queries / db_metrics.total_queries) * 100
                if error_rate > self.alert_thresholds["db_error_rate"]:
                    alerts.append(f"High database error rate: {error_rate:.1f}%")
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"PERFORMANCE ALERT: {alert}")
    
    def _log_detailed_metrics(self):
        """Log detailed performance metrics"""
        metrics_summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": self.current_system_metrics.cpu_percent if self.current_system_metrics else None,
                "memory_percent": self.current_system_metrics.memory_percent if self.current_system_metrics else None,
                "disk_usage_percent": self.current_system_metrics.disk_usage_percent if self.current_system_metrics else None
            },
            "ai_service": {
                "total_requests": self.current_ai_metrics.total_requests if self.current_ai_metrics else None,
                "success_rate": (
                    (self.current_ai_metrics.successful_requests / max(self.current_ai_metrics.total_requests, 1)) * 100
                    if self.current_ai_metrics else None
                ),
                "avg_response_time": self.current_ai_metrics.average_response_time if self.current_ai_metrics else None
            },
            "database": {
                "total_queries": self.current_db_metrics.total_queries if self.current_db_metrics else None,
                "active_connections": self.current_db_metrics.active_connections if self.current_db_metrics else None,
                "avg_query_time": self.current_db_metrics.average_query_time if self.current_db_metrics else None
            },
            "cache": {
                "hit_rate": self.current_cache_metrics.hit_rate if self.current_cache_metrics else None,
                "key_count": self.current_cache_metrics.key_count if self.current_cache_metrics else None,
                "backend": self.current_cache_metrics.backend_type if self.current_cache_metrics else None
            }
        }
        
        logger.info(f"Performance metrics: {json.dumps(metrics_summary, indent=2)}")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": self.current_system_metrics.__dict__ if self.current_system_metrics else None,
            "ai_service": self.current_ai_metrics.__dict__ if self.current_ai_metrics else None,
            "database": self.current_db_metrics.__dict__ if self.current_db_metrics else None,
            "cache": self.current_cache_metrics.__dict__ if self.current_cache_metrics else None
        }
    
    def get_historical_metrics(
        self, 
        metric_type: str, 
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get historical metrics for a specific type
        
        Args:
            metric_type: Type of metrics ('system', 'ai_service', 'database', 'cache')
            hours: Number of hours of history to return
            
        Returns:
            List of historical metric dictionaries
        """
        # Calculate how many data points to return
        points_per_hour = 3600 // self.collection_interval
        max_points = hours * points_per_hour
        
        # Get the appropriate history
        if metric_type == "system":
            history = list(self.system_history)
        elif metric_type == "ai_service":
            history = list(self.ai_service_history)
        elif metric_type == "database":
            history = list(self.database_history)
        elif metric_type == "cache":
            history = list(self.cache_history)
        else:
            return []
        
        # Return recent history
        recent_history = history[-max_points:] if len(history) > max_points else history
        return [metric.__dict__ for metric in recent_history]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance"""
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_active": self._running,
            "collection_interval": self.collection_interval,
            "history_size": self.history_size
        }
        
        # System summary
        if self.current_system_metrics:
            summary["system"] = {
                "cpu_usage": f"{self.current_system_metrics.cpu_percent:.1f}%",
                "memory_usage": f"{self.current_system_metrics.memory_percent:.1f}%",
                "disk_usage": f"{self.current_system_metrics.disk_usage_percent:.1f}%",
                "status": "healthy" if (
                    self.current_system_metrics.cpu_percent < self.alert_thresholds["cpu_percent"] and
                    self.current_system_metrics.memory_percent < self.alert_thresholds["memory_percent"]
                ) else "warning"
            }
        
        # AI service summary
        if self.current_ai_metrics:
            success_rate = 0.0
            if self.current_ai_metrics.total_requests > 0:
                success_rate = (self.current_ai_metrics.successful_requests / self.current_ai_metrics.total_requests) * 100
            
            summary["ai_service"] = {
                "total_requests": self.current_ai_metrics.total_requests,
                "success_rate": f"{success_rate:.1f}%",
                "avg_response_time": f"{self.current_ai_metrics.average_response_time:.2f}s",
                "total_tokens": self.current_ai_metrics.total_tokens,
                "status": "healthy" if success_rate >= (100 - self.alert_thresholds["ai_error_rate"]) else "warning"
            }
        
        # Database summary
        if self.current_db_metrics:
            success_rate = 0.0
            if self.current_db_metrics.total_queries > 0:
                success_rate = (self.current_db_metrics.successful_queries / self.current_db_metrics.total_queries) * 100
            
            summary["database"] = {
                "total_queries": self.current_db_metrics.total_queries,
                "success_rate": f"{success_rate:.1f}%",
                "active_connections": self.current_db_metrics.active_connections,
                "pool_size": self.current_db_metrics.pool_size,
                "status": "healthy" if success_rate >= (100 - self.alert_thresholds["db_error_rate"]) else "warning"
            }
        
        # Cache summary
        if self.current_cache_metrics:
            summary["cache"] = {
                "hit_rate": f"{self.current_cache_metrics.hit_rate:.1f}%",
                "key_count": self.current_cache_metrics.key_count,
                "backend": self.current_cache_metrics.backend_type,
                "memory_usage_mb": f"{self.current_cache_metrics.memory_usage_mb:.1f}MB",
                "status": "healthy"
            }
        
        return summary

# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None

async def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor"""
    global _performance_monitor
    
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
        await _performance_monitor.start_monitoring()
    
    return _performance_monitor

async def cleanup_performance_monitor():
    """Cleanup the global performance monitor"""
    global _performance_monitor
    
    if _performance_monitor:
        await _performance_monitor.stop_monitoring()
        _performance_monitor = None