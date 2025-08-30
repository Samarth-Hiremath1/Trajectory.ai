from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

from api.resume import router as resume_router
from api.chat import router as chat_router
from api.roadmap import router as roadmap_router
from api.roadmap_chat import router as roadmap_chat_router
from api.profile import router as profile_router
from api.task import router as task_router
from api.learning_resources import router as learning_resources_router
from api.langgraph_workflows import router as langgraph_workflows_router
from api.agents import router as agents_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Trajectory.AI Backend", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
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
            
    except Exception as e:
        logger.error(f"Failed to initialize multi-agent service: {str(e)}")
        import traceback
        logger.error(f"Startup error traceback: {traceback.format_exc()}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    try:
        from services.multi_agent_service import cleanup_multi_agent_service
        await cleanup_multi_agent_service()
        logger.info("Multi-agent service cleaned up")
    except Exception as e:
        logger.error(f"Failed to cleanup multi-agent service: {str(e)}")

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

@app.get("/")
async def root():
    return {"message": "Trajectory.AI Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)