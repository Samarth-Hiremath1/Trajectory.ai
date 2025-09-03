"""
Rate limiting middleware and utilities for API security
"""
import time
import asyncio
from typing import Dict, Optional, Callable
from collections import defaultdict, deque
from datetime import datetime, timedelta
import logging
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter using sliding window algorithm"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_storage = defaultdict(deque)  # Fallback for when Redis is not available
        
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed based on rate limit
        
        Args:
            key: Unique identifier for the client (IP, user ID, etc.)
            limit: Maximum number of requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        now = time.time()
        window_start = now - window_seconds
        
        if self.redis_client:
            return await self._check_redis_rate_limit(key, limit, window_seconds, now, window_start)
        else:
            return self._check_local_rate_limit(key, limit, window_seconds, now, window_start)
    
    async def _check_redis_rate_limit(self, key: str, limit: int, window_seconds: int, now: float, window_start: float) -> tuple[bool, Dict[str, int]]:
        """Check rate limit using Redis"""
        try:
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window_seconds)
            
            results = await pipe.execute()
            current_count = results[1] + 1  # +1 for the request we just added
            
            rate_limit_info = {
                "limit": limit,
                "remaining": max(0, limit - current_count),
                "reset_time": int(now + window_seconds),
                "window_seconds": window_seconds
            }
            
            return current_count <= limit, rate_limit_info
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            # Fall back to local storage
            return self._check_local_rate_limit(key, limit, window_seconds, now, window_start)
    
    def _check_local_rate_limit(self, key: str, limit: int, window_seconds: int, now: float, window_start: float) -> tuple[bool, Dict[str, int]]:
        """Check rate limit using local memory (fallback)"""
        requests = self.local_storage[key]
        
        # Remove old requests
        while requests and requests[0] < window_start:
            requests.popleft()
        
        # Add current request
        requests.append(now)
        
        current_count = len(requests)
        
        rate_limit_info = {
            "limit": limit,
            "remaining": max(0, limit - current_count),
            "reset_time": int(now + window_seconds),
            "window_seconds": window_seconds
        }
        
        return current_count <= limit, rate_limit_info

class RateLimitConfig:
    """Configuration for different rate limits"""
    
    # Default rate limits (requests per time window)
    DEFAULT_LIMITS = {
        "global": (1000, 3600),  # 1000 requests per hour
        "auth": (10, 300),       # 10 auth requests per 5 minutes
        "upload": (5, 300),      # 5 uploads per 5 minutes
        "ai_chat": (50, 3600),   # 50 AI chat requests per hour
        "roadmap": (10, 3600),   # 10 roadmap generations per hour
    }
    
    # Burst limits (short-term limits)
    BURST_LIMITS = {
        "global": (100, 60),     # 100 requests per minute
        "auth": (5, 60),         # 5 auth requests per minute
        "upload": (2, 60),       # 2 uploads per minute
        "ai_chat": (10, 60),     # 10 AI chat requests per minute
        "roadmap": (3, 60),      # 3 roadmap generations per minute
    }

def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    redis_client = None
    
    # Try to connect to Redis if available
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_client = redis.from_url(redis_url, decode_responses=True)
            redis_client.ping()  # Test connection
            logger.info("Connected to Redis for rate limiting")
        except Exception as e:
            logger.warning(f"Could not connect to Redis, using local rate limiting: {e}")
            redis_client = None
    
    return RateLimiter(redis_client)

def get_client_identifier(request: Request) -> str:
    """Get unique identifier for the client"""
    # Try to get user ID from headers first
    user_id = request.headers.get("x-user-id")
    if user_id:
        return f"user:{user_id}"
    
    # Fall back to IP address
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Get the first IP in the chain
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        client_ip = request.client.host if request.client else "unknown"
    
    return f"ip:{client_ip}"

def create_rate_limit_middleware(rate_limiter: RateLimiter):
    """Create rate limiting middleware"""
    
    async def rate_limit_middleware(request: Request, call_next: Callable):
        """Rate limiting middleware"""
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        client_id = get_client_identifier(request)
        
        # Determine rate limit type based on endpoint
        limit_type = "global"
        if "/auth" in request.url.path:
            limit_type = "auth"
        elif "/upload" in request.url.path:
            limit_type = "upload"
        elif "/chat" in request.url.path:
            limit_type = "ai_chat"
        elif "/roadmap" in request.url.path:
            limit_type = "roadmap"
        
        # Check both burst and default limits
        burst_limit, burst_window = RateLimitConfig.BURST_LIMITS[limit_type]
        default_limit, default_window = RateLimitConfig.DEFAULT_LIMITS[limit_type]
        
        # Check burst limit first
        burst_allowed, burst_info = await rate_limiter.is_allowed(
            f"{client_id}:burst:{limit_type}", burst_limit, burst_window
        )
        
        if not burst_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {burst_limit} per {burst_window} seconds",
                    "rate_limit": burst_info,
                    "retry_after": burst_info["reset_time"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(burst_limit),
                    "X-RateLimit-Remaining": str(burst_info["remaining"]),
                    "X-RateLimit-Reset": str(burst_info["reset_time"]),
                    "Retry-After": str(burst_info["reset_time"] - int(time.time()))
                }
            )
        
        # Check default limit
        default_allowed, default_info = await rate_limiter.is_allowed(
            f"{client_id}:default:{limit_type}", default_limit, default_window
        )
        
        if not default_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Daily/hourly limit exceeded. Limit: {default_limit} per {default_window} seconds",
                    "rate_limit": default_info,
                    "retry_after": default_info["reset_time"] - int(time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(default_limit),
                    "X-RateLimit-Remaining": str(default_info["remaining"]),
                    "X-RateLimit-Reset": str(default_info["reset_time"]),
                    "Retry-After": str(default_info["reset_time"] - int(time.time()))
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        
        # Use the more restrictive limit for headers
        if burst_info["remaining"] < default_info["remaining"]:
            response.headers["X-RateLimit-Limit"] = str(burst_limit)
            response.headers["X-RateLimit-Remaining"] = str(burst_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(burst_info["reset_time"])
        else:
            response.headers["X-RateLimit-Limit"] = str(default_limit)
            response.headers["X-RateLimit-Remaining"] = str(default_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(default_info["reset_time"])
        
        return response
    
    return rate_limit_middleware

class APIKeyRateLimiter:
    """Special rate limiter for API keys (like Hugging Face)"""
    
    def __init__(self):
        self.request_times = defaultdict(deque)
        self.lock = asyncio.Lock()
    
    async def wait_if_needed(self, api_key_hash: str, requests_per_minute: int = 30):
        """
        Wait if necessary to respect API rate limits
        
        Args:
            api_key_hash: Hash of the API key
            requests_per_minute: Maximum requests per minute
        """
        async with self.lock:
            now = time.time()
            minute_ago = now - 60
            
            # Remove old requests
            while (self.request_times[api_key_hash] and 
                   self.request_times[api_key_hash][0] < minute_ago):
                self.request_times[api_key_hash].popleft()
            
            # Check if we need to wait
            if len(self.request_times[api_key_hash]) >= requests_per_minute:
                # Calculate wait time
                oldest_request = self.request_times[api_key_hash][0]
                wait_time = 60 - (now - oldest_request)
                
                if wait_time > 0:
                    logger.info(f"Rate limiting API requests, waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
            
            # Record this request
            self.request_times[api_key_hash].append(now)

# Global API rate limiter instance
api_rate_limiter = APIKeyRateLimiter()