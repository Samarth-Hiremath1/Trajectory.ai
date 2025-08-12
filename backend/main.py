from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

from api.resume import router as resume_router
from api.chat import router as chat_router
from api.roadmap import router as roadmap_router
from api.roadmap_chat import router as roadmap_chat_router
from api.profile import router as profile_router
from api.task import router as task_router

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

# Include routers
app.include_router(resume_router)
app.include_router(chat_router)
app.include_router(roadmap_router)
app.include_router(roadmap_chat_router)
app.include_router(profile_router)
app.include_router(task_router)

@app.get("/")
async def root():
    return {"message": "Trajectory.AI Backend API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)