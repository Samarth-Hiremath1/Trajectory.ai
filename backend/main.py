from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from multiple possible locations
import os
from pathlib import Path

# Try to load .env files in order of priority (local overrides main)
env_paths = [
    ('.env.local', 'backend/.env.local', '../.env.local'),  # Local files first (highest priority)
    ('.env', 'backend/.env', '../.env')  # Main files second
]

for env_group in env_paths:
    for env_path in env_group:
        if Path(env_path).exists():
            load_dotenv(env_path, override=True)  # Allow override for local files

# Import security modules
from security.rate_limiting import get_rate_limiter, create_rate_limit_middleware
from security.input_validation import ValidationError
from security.auth import AuthenticationError, AuthorizationError, get_supabase_auth

from api.resume import router as resume_router
from api.chat import router as chat_router
from api.roadmap import router as roadmap_router
from api.roadmap_chat import router as roadmap_chat_router
from api.profile import router as profile_router
from api.task import router as task_router
from api.learning_resources import router as learning_resources_router
from api.langgraph_workflows import router as langgraph_workflows_router
from api.agents import router as agents_router
from api.performance import router as performance_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    try:
        # Initialize performance monitoring services
        logger.info("Initializing performance services...")
        
        # Initialize connection pool
        from services.connection_pool import get_connection_pool
        pool = await get_connection_pool()
        logger.info("Database connection pool initialized")
        
        # Initialize cache service
        from services.cache_service import get_cache_service
        cache = await get_cache_service()
        logger.info(f"Cache service initialized with backend: {cache.backend.value}")
        
        # Initialize performance monitor
        from services.performance_monitor import get_performance_monitor
        monitor = await get_performance_monitor()
        logger.info("Performance monitoring started")
        
        # Initialize multi-agent service
        from services.multi_agent_service import get_multi_agent_service
        multi_agent_service = await get_multi_agent_service()
        logger.info(f"Multi-agent service initialized: {multi_agent_service.is_initialized}")
        logger.info(f"Multi-agent service running: {multi_agent_service.is_running}")
        logger.info(f"Multi-agent service agents: {len(multi_agent_service.agents)}")
        
        if multi_agent_service.orchestrator:
            logger.info(f"Orchestrator agents: {len(multi_agent_service.orchestrator.agents)}")
            for agent_id, agent in multi_agent_service.orchestrator.agents.items():
                logger.info(f"  - {agent.agent_type.value}: {agent_id}")
        else:
            logger.warning("No orchestrator found in multi-agent service")
            
        logger.info("All services initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        import traceback
        logger.error(f"Startup error traceback: {traceback.format_exc()}")
    
    yield
    
    # Shutdown
    try:
        logger.info("Shutting down services...")
        
        # Cleanup performance monitor
        from services.performance_monitor import cleanup_performance_monitor
        await cleanup_performance_monitor()
        logger.info("Performance monitor cleaned up")
        
        # Cleanup cache service
        from services.cache_service import cleanup_cache_service
        await cleanup_cache_service()
        logger.info("Cache service cleaned up")
        
        # Cleanup connection pool
        from services.connection_pool import cleanup_connection_pool
        await cleanup_connection_pool()
        logger.info("Database connection pool cleaned up")
        
        # Cleanup multi-agent service
        from services.multi_agent_service import cleanup_multi_agent_service
        await cleanup_multi_agent_service()
        logger.info("Multi-agent service cleaned up")
        
        logger.info("All services cleaned up successfully")
        
    except Exception as e:
        logger.error(f"Failed to cleanup services: {str(e)}")

app = FastAPI(
    title="Trajectory.AI Backend", 
    version="1.0.0", 
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None
)

# Security middleware - order matters!

# 1. Trusted Host middleware (prevent host header attacks)
allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,*.vercel.app").split(",")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# 2. Rate limiting middleware
rate_limiter = get_rate_limiter()
rate_limit_middleware = create_rate_limit_middleware(rate_limiter)
app.middleware("http")(rate_limit_middleware)

# 3. CORS middleware with strict configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type", 
        "X-User-ID",
        "X-Request-ID",
        "Accept",
        "Origin",
        "User-Agent"
    ],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
)

# 4. Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    # Content Security Policy
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' https://api.huggingface.co https://*.supabase.co; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp
    
    # HSTS (only in production with HTTPS)
    if os.getenv("ENVIRONMENT") == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# 5. Global exception handlers for security errors
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error from {request.client.host}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "type": "validation_error"
        }
    )

@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    logger.warning(f"Authentication error from {request.client.host}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Authentication Error",
            "message": str(exc),
            "type": "authentication_error"
        },
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request: Request, exc: AuthorizationError):
    """Handle authorization errors"""
    logger.warning(f"Authorization error from {request.client.host}: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Authorization Error",
            "message": str(exc),
            "type": "authorization_error"
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with security logging"""
    if exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code} from {request.client.host}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": f"HTTP {exc.status_code}",
            "message": exc.detail,
            "type": "http_error"
        }
    )



# Include routers
app.include_router(resume_router)
app.include_router(chat_router)
app.include_router(roadmap_router)
app.include_router(roadmap_chat_router)
app.include_router(profile_router)
app.include_router(task_router)
app.include_router(learning_resources_router)
app.include_router(langgraph_workflows_router)
app.include_router(agents_router)
app.include_router(performance_router)

@app.get("/")
async def root():
    return {"message": "Trajectory.AI Backend API"}

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with service dependency checks"""
    from datetime import datetime
    from fastapi import status
    import asyncio
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0",
        "uptime": None,
        "services": {},
        "components": {}
    }
    
    # Calculate uptime if performance monitor is available
    try:
        from services.performance_monitor import get_performance_monitor
        monitor = await get_performance_monitor()
        if monitor.current_system_metrics and monitor.current_system_metrics.timestamp:
            uptime_seconds = (datetime.utcnow() - monitor.current_system_metrics.timestamp).total_seconds()
            health_status["uptime"] = f"{uptime_seconds:.0f}s"
    except Exception:
        pass
    
    overall_status = "healthy"
    
    # Check database connectivity with detailed status
    try:
        from services.connection_pool import get_connection_pool
        pool = await get_connection_pool()
        pool_status = pool.get_pool_status()
        
        if pool_status.get("status") == "active":
            health_status["services"]["database"] = {
                "status": "healthy",
                "details": {
                    "pool_size": pool_status.get("pool_size", 0),
                    "active_connections": pool_status.get("active_connections", 0),
                    "idle_connections": pool_status.get("idle_connections", 0),
                    "total_queries": pool_status.get("total_queries", 0),
                    "success_rate": f"{pool_status.get('success_rate', 0):.1f}%"
                }
            }
        else:
            health_status["services"]["database"] = {
                "status": "degraded",
                "details": {"message": "Pool not active"}
            }
            overall_status = "degraded"
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "details": {"error": str(e)[:100]}
        }
        overall_status = "degraded"
    
    # Check cache service with detailed status
    try:
        from services.cache_service import get_cache_service
        cache_service = await get_cache_service()
        cache_metrics = cache_service.get_metrics()
        
        health_status["services"]["cache"] = {
            "status": "healthy",
            "details": {
                "backend": cache_metrics.get("backend", "unknown"),
                "key_count": cache_metrics.get("key_count", 0),
                "hit_rate": f"{cache_metrics.get('hit_rate_percentage', 0):.1f}%",
                "memory_usage_mb": f"{cache_metrics.get('memory_usage_bytes', 0) / (1024 * 1024):.1f}"
            }
        }
    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "degraded",
            "details": {"error": str(e)[:100]}
        }
    
    # Check ChromaDB connectivity with actual connection test
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Try to create a client and test connection
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        # Use a timeout for the connection test
        async def test_chroma_connection():
            try:
                client = chromadb.HttpClient(
                    host=chroma_host,
                    port=chroma_port,
                    settings=Settings(allow_reset=True)
                )
                # Test with a simple heartbeat operation
                client.heartbeat()
                return True
            except Exception:
                return False
        
        # Run with timeout
        chroma_healthy = await asyncio.wait_for(
            asyncio.to_thread(test_chroma_connection), 
            timeout=2.0
        )
        
        if chroma_healthy:
            health_status["services"]["chromadb"] = {
                "status": "healthy",
                "details": {
                    "host": chroma_host,
                    "port": chroma_port,
                    "connection": "active"
                }
            }
        else:
            health_status["services"]["chromadb"] = {
                "status": "unhealthy",
                "details": {
                    "host": chroma_host,
                    "port": chroma_port,
                    "connection": "failed"
                }
            }
            overall_status = "degraded"
            
    except asyncio.TimeoutError:
        health_status["services"]["chromadb"] = {
            "status": "unhealthy",
            "details": {"error": "Connection timeout"}
        }
        overall_status = "degraded"
    except Exception as e:
        health_status["services"]["chromadb"] = {
            "status": "unhealthy",
            "details": {"error": str(e)[:100]}
        }
        overall_status = "degraded"
    
    # Check AI service status
    try:
        from services.ai_service import get_ai_service
        ai_service = await get_ai_service()
        ai_metrics = ai_service.get_metrics()
        
        total_requests = ai_metrics.get("total_requests", 0)
        successful_requests = ai_metrics.get("successful_requests", 0)
        success_rate = (successful_requests / max(total_requests, 1)) * 100
        
        health_status["services"]["ai_service"] = {
            "status": "healthy" if success_rate >= 90 else "degraded",
            "details": {
                "total_requests": total_requests,
                "success_rate": f"{success_rate:.1f}%",
                "avg_response_time": f"{ai_metrics.get('average_response_time', 0):.2f}s",
                "providers": list(ai_metrics.get("provider_usage", {}).keys())
            }
        }
        
        if success_rate < 90:
            overall_status = "degraded"
            
    except Exception as e:
        health_status["services"]["ai_service"] = {
            "status": "degraded",
            "details": {"error": str(e)[:100]}
        }
    
    # Check multi-agent system
    try:
        from services.multi_agent_service import get_multi_agent_service
        multi_agent_service = await get_multi_agent_service()
        
        agent_count = len(multi_agent_service.agents) if multi_agent_service.agents else 0
        orchestrator_agents = 0
        if multi_agent_service.orchestrator and multi_agent_service.orchestrator.agents:
            orchestrator_agents = len(multi_agent_service.orchestrator.agents)
        
        health_status["services"]["multi_agent"] = {
            "status": "healthy" if multi_agent_service.is_running else "degraded",
            "details": {
                "initialized": multi_agent_service.is_initialized,
                "running": multi_agent_service.is_running,
                "agent_count": agent_count,
                "orchestrator_agents": orchestrator_agents
            }
        }
        
        if not multi_agent_service.is_running:
            overall_status = "degraded"
            
    except Exception as e:
        health_status["services"]["multi_agent"] = {
            "status": "degraded",
            "details": {"error": str(e)[:100]}
        }
    
    # System resource checks
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        health_status["components"]["system"] = {
            "status": "healthy",
            "details": {
                "cpu_usage": f"{cpu_percent:.1f}%",
                "memory_usage": f"{memory.percent:.1f}%",
                "disk_usage": f"{(disk.used / disk.total) * 100:.1f}%",
                "available_memory_mb": f"{memory.available / (1024 * 1024):.0f}",
                "free_disk_gb": f"{disk.free / (1024 * 1024 * 1024):.1f}"
            }
        }
        
        # Mark as degraded if resources are critically low
        if cpu_percent > 90 or memory.percent > 95 or (disk.used / disk.total) * 100 > 95:
            health_status["components"]["system"]["status"] = "degraded"
            overall_status = "degraded"
            
    except Exception as e:
        health_status["components"]["system"] = {
            "status": "unknown",
            "details": {"error": str(e)[:100]}
        }
    
    # Application-level health
    health_status["components"]["application"] = {
        "status": "healthy",
        "details": {
            "fastapi_version": "running",
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    }
    
    # Set overall status
    health_status["status"] = overall_status
    
    # Return appropriate HTTP status code
    if overall_status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )
    elif overall_status == "degraded":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=health_status
        )
    else:
        return health_status

@app.get("/health/ready")
async def readiness_check():
    """Kubernetes readiness probe - checks if app is ready to serve traffic"""
    return {"status": "ready", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/health/live")
async def liveness_check():
    """Kubernetes liveness probe - checks if app is alive"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from datetime import datetime
    import psutil
    
    metrics_lines = []
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    
    # Add help and type information for Prometheus
    metrics_lines.extend([
        "# HELP http_requests_total Total number of HTTP requests",
        "# TYPE http_requests_total counter",
        "# HELP http_request_duration_seconds HTTP request duration in seconds",
        "# TYPE http_request_duration_seconds histogram",
        "# HELP system_cpu_usage_percent System CPU usage percentage",
        "# TYPE system_cpu_usage_percent gauge",
        "# HELP system_memory_usage_percent System memory usage percentage", 
        "# TYPE system_memory_usage_percent gauge",
        "# HELP database_connections_active Active database connections",
        "# TYPE database_connections_active gauge",
        "# HELP database_queries_total Total database queries executed",
        "# TYPE database_queries_total counter",
        "# HELP ai_service_requests_total Total AI service requests",
        "# TYPE ai_service_requests_total counter",
        "# HELP cache_hits_total Total cache hits",
        "# TYPE cache_hits_total counter",
        ""
    ])
    
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        metrics_lines.extend([
            f"system_cpu_usage_percent {cpu_percent} {timestamp}",
            f"system_memory_usage_percent {memory.percent} {timestamp}",
            f"system_memory_available_bytes {memory.available} {timestamp}",
            f"system_memory_used_bytes {memory.used} {timestamp}",
        ])
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        metrics_lines.extend([
            f"system_disk_usage_percent {disk_usage_percent} {timestamp}",
            f"system_disk_free_bytes {disk.free} {timestamp}",
            f"system_disk_used_bytes {disk.used} {timestamp}",
        ])
        
    except Exception as e:
        logger.error(f"Error collecting system metrics for Prometheus: {str(e)}")
    
    try:
        # Database metrics
        from services.connection_pool import get_connection_pool
        pool = await get_connection_pool()
        pool_status = pool.get_pool_status()
        
        if pool_status.get("status") == "active":
            metrics_lines.extend([
                f"database_connections_active {pool_status.get('active_connections', 0)} {timestamp}",
                f"database_connections_idle {pool_status.get('idle_connections', 0)} {timestamp}",
                f"database_connections_total {pool_status.get('pool_size', 0)} {timestamp}",
                f"database_queries_total {pool_status.get('total_queries', 0)} {timestamp}",
                f"database_queries_successful_total {pool_status.get('successful_queries', 0)} {timestamp}",
                f"database_queries_failed_total {pool_status.get('failed_queries', 0)} {timestamp}",
                f"database_query_duration_seconds {pool_status.get('average_query_time', 0)} {timestamp}",
            ])
        
    except Exception as e:
        logger.error(f"Error collecting database metrics for Prometheus: {str(e)}")
    
    try:
        # AI Service metrics
        from services.ai_service import get_ai_service
        ai_service = await get_ai_service()
        ai_metrics = ai_service.get_metrics()
        
        metrics_lines.extend([
            f"ai_service_requests_total {ai_metrics.get('total_requests', 0)} {timestamp}",
            f"ai_service_requests_successful_total {ai_metrics.get('successful_requests', 0)} {timestamp}",
            f"ai_service_requests_failed_total {ai_metrics.get('failed_requests', 0)} {timestamp}",
            f"ai_service_response_duration_seconds {ai_metrics.get('average_response_time', 0)} {timestamp}",
            f"ai_service_tokens_total {ai_metrics.get('total_tokens', 0)} {timestamp}",
        ])
        
        # Provider-specific metrics
        for provider, count in ai_metrics.get("provider_usage", {}).items():
            safe_provider = provider.replace("-", "_").replace(".", "_")
            metrics_lines.append(f"ai_service_provider_requests_total{{provider=\"{provider}\"}} {count} {timestamp}")
        
    except Exception as e:
        logger.error(f"Error collecting AI service metrics for Prometheus: {str(e)}")
    
    try:
        # Cache metrics
        from services.cache_service import get_cache_service
        cache_service = await get_cache_service()
        cache_metrics = cache_service.get_metrics()
        
        metrics_lines.extend([
            f"cache_hits_total {cache_metrics.get('cache_hits', 0)} {timestamp}",
            f"cache_misses_total {cache_metrics.get('cache_misses', 0)} {timestamp}",
            f"cache_gets_total {cache_metrics.get('total_gets', 0)} {timestamp}",
            f"cache_sets_total {cache_metrics.get('total_sets', 0)} {timestamp}",
            f"cache_keys_count {cache_metrics.get('key_count', 0)} {timestamp}",
            f"cache_memory_usage_bytes {cache_metrics.get('memory_usage_bytes', 0)} {timestamp}",
            f"cache_hit_rate_percent {cache_metrics.get('hit_rate_percentage', 0)} {timestamp}",
        ])
        
    except Exception as e:
        logger.error(f"Error collecting cache metrics for Prometheus: {str(e)}")
    
    try:
        # Multi-agent system metrics
        from services.multi_agent_service import get_multi_agent_service
        multi_agent_service = await get_multi_agent_service()
        
        agent_count = len(multi_agent_service.agents) if multi_agent_service.agents else 0
        orchestrator_agents = 0
        if multi_agent_service.orchestrator and multi_agent_service.orchestrator.agents:
            orchestrator_agents = len(multi_agent_service.orchestrator.agents)
        
        metrics_lines.extend([
            f"multi_agent_system_initialized {1 if multi_agent_service.is_initialized else 0} {timestamp}",
            f"multi_agent_system_running {1 if multi_agent_service.is_running else 0} {timestamp}",
            f"multi_agent_agents_count {agent_count} {timestamp}",
            f"multi_agent_orchestrator_agents_count {orchestrator_agents} {timestamp}",
        ])
        
    except Exception as e:
        logger.error(f"Error collecting multi-agent metrics for Prometheus: {str(e)}")
    
    # Application uptime metric
    try:
        from services.performance_monitor import get_performance_monitor
        monitor = await get_performance_monitor()
        uptime_seconds = 0
        if monitor.current_system_metrics and monitor.current_system_metrics.timestamp:
            uptime_seconds = (datetime.utcnow() - monitor.current_system_metrics.timestamp).total_seconds()
        
        metrics_lines.append(f"application_uptime_seconds {uptime_seconds} {timestamp}")
        
    except Exception as e:
        logger.error(f"Error collecting uptime metrics for Prometheus: {str(e)}")
    
    # Return metrics in Prometheus format
    metrics_content = "\n".join(metrics_lines) + "\n"
    
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=metrics_content,
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)