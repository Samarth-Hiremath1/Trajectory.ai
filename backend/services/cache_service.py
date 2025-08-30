"""
Caching service with Redis support and fallback to in-memory caching
"""
import os
import json
import pickle
import logging
import asyncio
from typing import Any, Optional, Dict, Union, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

# Optional Redis imports
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

class CacheBackend(Enum):
    """Available cache backends"""
    MEMORY = "memory"
    REDIS = "redis"

@dataclass
class CacheMetrics:
    """Metrics for cache performance monitoring"""
    total_gets: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_sets: int = 0
    total_deletes: int = 0
    total_flushes: int = 0
    backend_type: str = "memory"
    created_at: Optional[datetime] = None
    last_access: Optional[datetime] = None
    memory_usage_bytes: int = 0
    key_count: int = 0

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

class CacheService:
    """
    High-performance caching service with Redis and in-memory fallback
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 3600,  # 1 hour
        max_memory_items: int = 1000,
        enable_metrics: bool = True
    ):
        """
        Initialize cache service
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
            max_memory_items: Maximum items in memory cache
            enable_metrics: Enable performance metrics
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.default_ttl = default_ttl
        self.max_memory_items = max_memory_items
        self.enable_metrics = enable_metrics
        
        # Cache backends
        self.redis_client: Optional[redis.Redis] = None
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.backend = CacheBackend.MEMORY
        
        # Metrics
        self.metrics = CacheMetrics()
        if enable_metrics:
            self.metrics.created_at = datetime.utcnow()
        
        # Cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(f"Cache service initialized with backend: {self.backend.value}")
    
    async def initialize(self) -> bool:
        """Initialize cache backends"""
        try:
            # Try to initialize Redis first
            if REDIS_AVAILABLE:
                await self._init_redis()
            
            # Start cleanup task for memory cache
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
            
            logger.info(f"Cache service initialized with backend: {self.backend.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize cache service: {str(e)}")
            return False
    
    async def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis_client.ping()
            self.backend = CacheBackend.REDIS
            self.metrics.backend_type = "redis"
            
            logger.info("Redis cache backend initialized successfully")
            
        except Exception as e:
            logger.warning(f"Redis initialization failed, falling back to memory: {str(e)}")
            self.redis_client = None
            self.backend = CacheBackend.MEMORY
            self.metrics.backend_type = "memory"
    
    async def close(self):
        """Close cache connections and cleanup"""
        try:
            # Cancel cleanup task
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
                self.redis_client = None
            
            # Clear memory cache
            self.memory_cache.clear()
            
            logger.info("Cache service closed")
            
        except Exception as e:
            logger.error(f"Error closing cache service: {str(e)}")
    
    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        if self.enable_metrics:
            self.metrics.total_gets += 1
            self.metrics.last_access = datetime.utcnow()
        
        try:
            if self.backend == CacheBackend.REDIS and self.redis_client:
                return await self._get_from_redis(key, default)
            else:
                return await self._get_from_memory(key, default)
                
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {str(e)}")
            if self.enable_metrics:
                self.metrics.cache_misses += 1
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        namespace: Optional[str] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (None for default)
            namespace: Optional namespace prefix
            
        Returns:
            True if successful, False otherwise
        """
        if namespace:
            key = f"{namespace}:{key}"
        
        if self.enable_metrics:
            self.metrics.total_sets += 1
        
        try:
            if self.backend == CacheBackend.REDIS and self.redis_client:
                return await self._set_in_redis(key, value, ttl)
            else:
                return await self._set_in_memory(key, value, ttl)
                
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {str(e)}")
            return False
    
    async def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key to delete
            namespace: Optional namespace prefix
            
        Returns:
            True if key was deleted, False otherwise
        """
        if namespace:
            key = f"{namespace}:{key}"
        
        if self.enable_metrics:
            self.metrics.total_deletes += 1
        
        try:
            if self.backend == CacheBackend.REDIS and self.redis_client:
                result = await self.redis_client.delete(key)
                return bool(result)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    self._update_memory_metrics()
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {str(e)}")
            return False
    
    async def exists(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key to check
            namespace: Optional namespace prefix
            
        Returns:
            True if key exists, False otherwise
        """
        if namespace:
            key = f"{namespace}:{key}"
        
        try:
            if self.backend == CacheBackend.REDIS and self.redis_client:
                return bool(await self.redis_client.exists(key))
            else:
                if key in self.memory_cache:
                    entry = self.memory_cache[key]
                    # Check if expired
                    if entry.expires_at and datetime.utcnow() > entry.expires_at:
                        del self.memory_cache[key]
                        self._update_memory_metrics()
                        return False
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {str(e)}")
            return False
    
    async def flush(self, namespace: Optional[str] = None) -> bool:
        """
        Flush cache (all keys or namespace)
        
        Args:
            namespace: Optional namespace to flush (None for all)
            
        Returns:
            True if successful, False otherwise
        """
        if self.enable_metrics:
            self.metrics.total_flushes += 1
        
        try:
            if self.backend == CacheBackend.REDIS and self.redis_client:
                if namespace:
                    # Delete keys with namespace prefix
                    pattern = f"{namespace}:*"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                else:
                    await self.redis_client.flushdb()
                return True
            else:
                if namespace:
                    # Delete keys with namespace prefix
                    keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{namespace}:")]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                else:
                    self.memory_cache.clear()
                self._update_memory_metrics()
                return True
                
        except Exception as e:
            logger.error(f"Cache flush error: {str(e)}")
            return False
    
    async def _get_from_redis(self, key: str, default: Any = None) -> Any:
        """Get value from Redis"""
        try:
            data = await self.redis_client.get(key)
            if data is None:
                if self.enable_metrics:
                    self.metrics.cache_misses += 1
                return default
            
            # Deserialize data
            value = pickle.loads(data)
            if self.enable_metrics:
                self.metrics.cache_hits += 1
            
            return value
            
        except Exception as e:
            logger.error(f"Redis get error: {str(e)}")
            if self.enable_metrics:
                self.metrics.cache_misses += 1
            return default
    
    async def _set_in_redis(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis"""
        try:
            # Serialize data
            data = pickle.dumps(value)
            
            # Set with TTL
            ttl = ttl or self.default_ttl
            await self.redis_client.setex(key, ttl, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis set error: {str(e)}")
            return False
    
    async def _get_from_memory(self, key: str, default: Any = None) -> Any:
        """Get value from memory cache"""
        if key not in self.memory_cache:
            if self.enable_metrics:
                self.metrics.cache_misses += 1
            return default
        
        entry = self.memory_cache[key]
        
        # Check if expired
        if entry.expires_at and datetime.utcnow() > entry.expires_at:
            del self.memory_cache[key]
            self._update_memory_metrics()
            if self.enable_metrics:
                self.metrics.cache_misses += 1
            return default
        
        # Update access info
        entry.access_count += 1
        entry.last_accessed = datetime.utcnow()
        
        if self.enable_metrics:
            self.metrics.cache_hits += 1
        
        return entry.value
    
    async def _set_in_memory(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        try:
            # Calculate expiration
            expires_at = None
            if ttl or self.default_ttl:
                expires_at = datetime.utcnow() + timedelta(seconds=ttl or self.default_ttl)
            
            # Create cache entry
            entry = CacheEntry(
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at
            )
            
            # Check if we need to evict items
            if len(self.memory_cache) >= self.max_memory_items:
                await self._evict_lru_items()
            
            self.memory_cache[key] = entry
            self._update_memory_metrics()
            
            return True
            
        except Exception as e:
            logger.error(f"Memory cache set error: {str(e)}")
            return False
    
    async def _evict_lru_items(self, count: int = 100):
        """Evict least recently used items from memory cache"""
        if not self.memory_cache:
            return
        
        # Sort by last accessed time (oldest first)
        sorted_items = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )
        
        # Remove oldest items
        for i in range(min(count, len(sorted_items))):
            key = sorted_items[i][0]
            del self.memory_cache[key]
        
        self._update_memory_metrics()
        logger.info(f"Evicted {min(count, len(sorted_items))} items from memory cache")
    
    async def _cleanup_expired_entries(self):
        """Background task to cleanup expired entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                if self.backend == CacheBackend.MEMORY:
                    current_time = datetime.utcnow()
                    expired_keys = []
                    
                    for key, entry in self.memory_cache.items():
                        if entry.expires_at and current_time > entry.expires_at:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self.memory_cache[key]
                    
                    if expired_keys:
                        self._update_memory_metrics()
                        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cache cleanup error: {str(e)}")
    
    def _update_memory_metrics(self):
        """Update memory cache metrics"""
        if self.enable_metrics:
            self.metrics.key_count = len(self.memory_cache)
            # Rough estimate of memory usage
            self.metrics.memory_usage_bytes = sum(
                len(pickle.dumps(entry.value)) for entry in self.memory_cache.values()
            )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        hit_rate = 0.0
        if self.metrics.total_gets > 0:
            hit_rate = (self.metrics.cache_hits / self.metrics.total_gets) * 100
        
        return {
            "backend": self.metrics.backend_type,
            "total_gets": self.metrics.total_gets,
            "cache_hits": self.metrics.cache_hits,
            "cache_misses": self.metrics.cache_misses,
            "hit_rate_percentage": hit_rate,
            "total_sets": self.metrics.total_sets,
            "total_deletes": self.metrics.total_deletes,
            "total_flushes": self.metrics.total_flushes,
            "key_count": self.metrics.key_count,
            "memory_usage_bytes": self.metrics.memory_usage_bytes,
            "created_at": self.metrics.created_at.isoformat() if self.metrics.created_at else None,
            "last_access": self.metrics.last_access.isoformat() if self.metrics.last_access else None,
            "redis_available": REDIS_AVAILABLE,
            "redis_connected": bool(self.redis_client)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on cache service"""
        try:
            # Test cache operations
            test_key = "health_check_test"
            test_value = {"timestamp": datetime.utcnow().isoformat()}
            
            # Test set
            set_success = await self.set(test_key, test_value, ttl=60)
            
            # Test get
            retrieved_value = await self.get(test_key)
            get_success = retrieved_value is not None
            
            # Test delete
            delete_success = await self.delete(test_key)
            
            return {
                "healthy": set_success and get_success and delete_success,
                "backend": self.backend.value,
                "operations": {
                    "set": set_success,
                    "get": get_success,
                    "delete": delete_success
                },
                "metrics": self.get_metrics()
            }
            
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "backend": self.backend.value,
                "metrics": self.get_metrics()
            }

# Global cache service instance
_cache_service: Optional[CacheService] = None

async def get_cache_service() -> CacheService:
    """Get or create the global cache service"""
    global _cache_service
    
    if _cache_service is None:
        _cache_service = CacheService()
        await _cache_service.initialize()
    
    return _cache_service

async def cleanup_cache_service():
    """Cleanup the global cache service"""
    global _cache_service
    
    if _cache_service:
        await _cache_service.close()
        _cache_service = None