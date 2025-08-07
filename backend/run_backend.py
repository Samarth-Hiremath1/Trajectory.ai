#!/usr/bin/env python3
"""
Simple script to run the backend without Docker dependencies
"""

import os
import sys
import uvicorn
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up environment variables and directories"""
    
    # Create necessary directories
    chroma_db_dir = backend_dir / "chroma_db"
    chroma_db_dir.mkdir(exist_ok=True)
    
    uploads_dir = backend_dir / "uploads" / "resumes"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Created ChromaDB directory: {chroma_db_dir}")
    logger.info(f"Created uploads directory: {uploads_dir}")
    
    # Set environment variables for local development
    os.environ.setdefault("CHROMADB_HOST", "localhost")
    os.environ.setdefault("CHROMADB_PORT", "8001")
    os.environ.setdefault("USE_PERSISTENT_CHROMADB", "true")
    
    logger.info("Environment setup complete")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import fastapi
        import uvicorn
        import chromadb
        import sentence_transformers
        import supabase
        logger.info("✅ All required dependencies are available")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        return False

def main():
    """Main function to start the backend server"""
    logger.info("🚀 Starting Trajectory.AI Backend Server")
    logger.info("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup environment
    setup_environment()
    
    # Import the FastAPI app
    try:
        from main import app
        logger.info("✅ FastAPI app imported successfully")
    except Exception as e:
        logger.error(f"❌ Failed to import FastAPI app: {e}")
        sys.exit(1)
    
    # Start the server
    logger.info("🌟 Starting server on http://localhost:8000")
    logger.info("📚 API documentation available at http://localhost:8000/docs")
    logger.info("🔄 Press Ctrl+C to stop the server")
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()