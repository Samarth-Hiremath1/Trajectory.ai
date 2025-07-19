#!/usr/bin/env python3
"""
Script to start and test ChromaDB service
"""

import subprocess
import time
import requests
import sys
from pathlib import Path

def check_chromadb_health(host="localhost", port=8001, max_retries=30):
    """Check if ChromaDB is healthy and responding"""
    print(f"Checking ChromaDB health at {host}:{port}...")
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"http://{host}:{port}/api/v1/heartbeat", timeout=5)
            if response.status_code == 200:
                print("✅ ChromaDB is healthy and responding")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if attempt < max_retries - 1:
            print(f"Attempt {attempt + 1}/{max_retries} failed, retrying in 2 seconds...")
            time.sleep(2)
    
    print("❌ ChromaDB is not responding after maximum retries")
    return False

def start_docker_compose():
    """Start Docker Compose services"""
    print("Starting Docker Compose services...")
    
    try:
        # Check if docker-compose.yml exists
        compose_file = Path("../docker-compose.yml")
        if not compose_file.exists():
            print("❌ docker-compose.yml not found in parent directory")
            return False
        
        # Start services (try both docker-compose and docker compose)
        commands_to_try = [
            ["docker", "compose", "-f", str(compose_file), "up", "-d", "chromadb"],
            ["docker-compose", "-f", str(compose_file), "up", "-d", "chromadb"]
        ]
        
        for cmd in commands_to_try:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=Path(__file__).parent
                )
                
                if result.returncode == 0:
                    print("✅ Docker Compose services started")
                    return True
                    
            except FileNotFoundError:
                continue
        
        if result.returncode == 0:
            print("✅ Docker Compose services started")
            return True
        else:
            print(f"❌ Failed to start Docker Compose services: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ docker-compose command not found. Please install Docker Compose.")
        return False
    except Exception as e:
        print(f"❌ Error starting Docker Compose: {e}")
        return False

def main():
    """Main function to start services and run tests"""
    print("🚀 Starting ChromaDB Service Setup")
    print("=" * 40)
    
    # Start Docker Compose services
    if not start_docker_compose():
        print("Failed to start Docker services")
        return 1
    
    # Wait for ChromaDB to be ready
    print("\nWaiting for ChromaDB to be ready...")
    if not check_chromadb_health():
        print("ChromaDB failed to start properly")
        return 1
    
    print("\n🎉 ChromaDB service is ready!")
    print("\nYou can now:")
    print("1. Run the embedding service tests: python test_embedding_service.py")
    print("2. Start the FastAPI server: uvicorn main:app --reload")
    print("3. Test the resume upload endpoint at: http://localhost:8000/docs")
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)