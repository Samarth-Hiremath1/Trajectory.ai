"""
Database connection pooling service for improved performance
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import asyncpg
from asyncpg import Pool
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class PoolMetrics:
    """Metrics for connection pool monitoring"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    successful_queries: int = 0
    failed_queries: int = 0
    average_query_time: float = 0.0
    peak_connections: int = 0
    pool_created_at: Optional[datetime] = None
    last_query_time: Optional[datetime] = None
    query_times: list = field(default_factory=list)

class DatabaseConnectionPool:
    """
    High-performance database connection pool with monitoring
    """
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        min_size: int = 5,
        max_size: int = 20,
        command_timeout: int = 30,
        server_settings: Optional[Dict[str, str]] = None
    ):
        """
        Initialize database connection pool
        
        Args:
            database_url: PostgreSQL connection URL
            min_size: Minimum number of connections in pool
            max_size: Maximum number of connections in pool
            command_timeout: Command timeout in seconds
            server_settings: Additional server settings
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            logger.warning("DATABASE_URL not provided - database features will be disabled")
            self.database_url = None
        
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self.server_settings = server_settings or {
            'application_name': 'trajectory_ai',
            'timezone': 'UTC'
        }
        
        self.pool: Optional[Pool] = None
        self.metrics = PoolMetrics()
        self._lock = asyncio.Lock()
        
        logger.info(f"Database pool configured: min={min_size}, max={max_size}")
    
    async def initialize(self) -> bool:
        """Initialize the connection pool"""
        if not self.database_url:
            logger.info("Skipping database connection pool initialization - no DATABASE_URL provided")
            return True
            
        try:
            async with self._lock:
                if self.pool is not None:
                    logger.warning("Pool already initialized")
                    return True
                
                self.pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    command_timeout=self.command_timeout,
                    server_settings=self.server_settings
                )
                
                self.metrics.pool_created_at = datetime.utcnow()
                self.metrics.total_connections = self.max_size
                
                logger.info("Database connection pool initialized successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            return False
    
    async def close(self):
        """Close the connection pool"""
        try:
            async with self._lock:
                if self.pool:
                    await self.pool.close()
                    self.pool = None
                    logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Error closing database pool: {str(e)}")
    
    @asynccontextmanager
    async def acquire_connection(self):
        """
        Acquire a connection from the pool
        
        Usage:
            async with pool.acquire_connection() as conn:
                result = await conn.fetch("SELECT * FROM table")
        """
        if not self.database_url:
            raise RuntimeError("Database not configured - DATABASE_URL not provided")
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        start_time = datetime.utcnow()
        connection = None
        
        try:
            connection = await self.pool.acquire()
            self.metrics.active_connections += 1
            self.metrics.peak_connections = max(
                self.metrics.peak_connections, 
                self.metrics.active_connections
            )
            
            yield connection
            
        except Exception as e:
            self.metrics.failed_queries += 1
            logger.error(f"Database connection error: {str(e)}")
            raise
        finally:
            if connection:
                try:
                    await self.pool.release(connection)
                    self.metrics.active_connections -= 1
                    
                    # Update query metrics
                    query_time = (datetime.utcnow() - start_time).total_seconds()
                    self._update_query_metrics(query_time)
                    
                except Exception as e:
                    logger.error(f"Error releasing connection: {str(e)}")
    
    async def execute_query(
        self, 
        query: str, 
        *args, 
        fetch_type: str = "fetch"
    ) -> Any:
        """
        Execute a query with automatic connection management
        
        Args:
            query: SQL query to execute
            *args: Query parameters
            fetch_type: Type of fetch operation ('fetch', 'fetchrow', 'execute')
            
        Returns:
            Query result based on fetch_type
        """
        async with self.acquire_connection() as conn:
            self.metrics.total_queries += 1
            
            try:
                if fetch_type == "fetch":
                    result = await conn.fetch(query, *args)
                elif fetch_type == "fetchrow":
                    result = await conn.fetchrow(query, *args)
                elif fetch_type == "execute":
                    result = await conn.execute(query, *args)
                else:
                    raise ValueError(f"Invalid fetch_type: {fetch_type}")
                
                self.metrics.successful_queries += 1
                self.metrics.last_query_time = datetime.utcnow()
                
                return result
                
            except Exception as e:
                self.metrics.failed_queries += 1
                logger.error(f"Query execution failed: {str(e)}")
                raise
    
    async def execute_transaction(self, queries: list) -> list:
        """
        Execute multiple queries in a transaction
        
        Args:
            queries: List of (query, args, fetch_type) tuples
            
        Returns:
            List of query results
        """
        async with self.acquire_connection() as conn:
            async with conn.transaction():
                results = []
                
                for query_info in queries:
                    if len(query_info) == 3:
                        query, args, fetch_type = query_info
                    elif len(query_info) == 2:
                        query, args = query_info
                        fetch_type = "fetch"
                    else:
                        query = query_info[0]
                        args = []
                        fetch_type = "fetch"
                    
                    self.metrics.total_queries += 1
                    
                    try:
                        if fetch_type == "fetch":
                            result = await conn.fetch(query, *args)
                        elif fetch_type == "fetchrow":
                            result = await conn.fetchrow(query, *args)
                        elif fetch_type == "execute":
                            result = await conn.execute(query, *args)
                        else:
                            raise ValueError(f"Invalid fetch_type: {fetch_type}")
                        
                        results.append(result)
                        self.metrics.successful_queries += 1
                        
                    except Exception as e:
                        self.metrics.failed_queries += 1
                        logger.error(f"Transaction query failed: {str(e)}")
                        raise
                
                self.metrics.last_query_time = datetime.utcnow()
                return results
    
    def _update_query_metrics(self, query_time: float):
        """Update query performance metrics"""
        self.metrics.query_times.append(query_time)
        
        # Keep only last 1000 query times for memory efficiency
        if len(self.metrics.query_times) > 1000:
            self.metrics.query_times = self.metrics.query_times[-1000:]
        
        # Calculate average query time
        if self.metrics.query_times:
            self.metrics.average_query_time = sum(self.metrics.query_times) / len(self.metrics.query_times)
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics"""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "pool_size": self.pool.get_size(),
            "idle_connections": self.pool.get_idle_size(),
            "active_connections": self.metrics.active_connections,
            "total_connections": self.metrics.total_connections,
            "peak_connections": self.metrics.peak_connections,
            "total_queries": self.metrics.total_queries,
            "successful_queries": self.metrics.successful_queries,
            "failed_queries": self.metrics.failed_queries,
            "success_rate": (
                self.metrics.successful_queries / max(self.metrics.total_queries, 1)
            ) * 100,
            "average_query_time": self.metrics.average_query_time,
            "last_query_time": self.metrics.last_query_time.isoformat() if self.metrics.last_query_time else None,
            "pool_created_at": self.metrics.pool_created_at.isoformat() if self.metrics.pool_created_at else None,
            "configuration": {
                "min_size": self.min_size,
                "max_size": self.max_size,
                "command_timeout": self.command_timeout
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the connection pool"""
        try:
            if not self.pool:
                return {
                    "healthy": False,
                    "error": "Pool not initialized"
                }
            
            # Test connection with simple query
            start_time = datetime.utcnow()
            result = await self.execute_query("SELECT 1 as test", fetch_type="fetchrow")
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "healthy": True,
                "response_time": response_time,
                "test_query_result": dict(result) if result else None,
                "pool_status": self.get_pool_status()
            }
            
        except Exception as e:
            logger.error(f"Pool health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "pool_status": self.get_pool_status()
            }

# Global connection pool instance
_connection_pool: Optional[DatabaseConnectionPool] = None

async def get_connection_pool() -> DatabaseConnectionPool:
    """Get or create the global connection pool"""
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = DatabaseConnectionPool()
        await _connection_pool.initialize()
    
    return _connection_pool

async def cleanup_connection_pool():
    """Cleanup the global connection pool"""
    global _connection_pool
    
    if _connection_pool:
        await _connection_pool.close()
        _connection_pool = None