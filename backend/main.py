from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from dotenv import load_dotenv

# Load environment variables from multiple possible locations
import os
from pathlib import Path

# Try to load .env from current directory, then from backend directory
env_paths = ['.env', 'backend/.env', '../.env']
for env_path in env_paths:
    if Path(env_path).exists():
        load_dotenv(env_path)
        break

# Import security modules
from security.rate_limiting import get_rate_limiter, create_rate_limit_middleware
from security.input_validation import ValidationError
from security.auth import AuthenticationError, AuthorizationError

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
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)