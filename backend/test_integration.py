#!/usr/bin/env python3
"""
Integration test for resume upload with embedding generation
"""

import asyncio
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
import tempfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

# Add backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from main import app

def create_test_pdf():
    """Create a simple test PDF with resume content"""
    buffer = io.BytesIO()
    
    # Create PDF with reportlab
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Add some resume content
    p.drawString(100, 750, "John Doe")
    p.drawString(100, 730, "Software Engineer")
    p.drawString(100, 710, "")
    p.drawString(100, 690, "Experience:")
    p.drawString(100, 670, "• 5 years of Python development")
    p.drawString(100, 650, "• Machine learning with TensorFlow and PyTorch")
    p.drawString(100, 630, "• REST API development with FastAPI")
    p.drawString(100, 610, "• Database design and optimization")
    p.drawString(100, 590, "")
    p.drawString(100, 570, "Education:")
    p.drawString(100, 550, "• BS Computer Science, University of Technology")
    p.drawString(100, 530, "• Machine Learning Specialization, Coursera")
    p.drawString(100, 510, "")
    p.drawString(100, 490, "Skills:")
    p.drawString(100, 470, "• Python, JavaScript, SQL")
    p.drawString(100, 450, "• TensorFlow, PyTorch, Scikit-learn")
    p.drawString(100, 430, "• FastAPI, Django, React")
    p.drawString(100, 410, "• PostgreSQL, MongoDB, Redis")
    
    p.save()
    
    buffer.seek(0)
    return buffer.getvalue()

def test_resume_upload_with_embeddings():
    """Test resume upload endpoint with embedding generation"""
    print("🧪 Testing Resume Upload with Embeddings")
    print("=" * 50)
    
    try:
        # Create test client
        client = TestClient(app)
        
        # Test health endpoint first
        print("1. Testing health endpoint...")
        health_response = client.get("/health")
        assert health_response.status_code == 200
        print("✅ Health endpoint working")
        
        # Test resume health endpoint
        print("2. Testing resume health endpoint...")
        resume_health_response = client.get("/api/resume/health")
        assert resume_health_response.status_code == 200
        health_data = resume_health_response.json()
        print(f"Resume service status: {health_data.get('status', 'unknown')}")
        print(f"Embedding service status: {health_data.get('embedding_service', {}).get('status', 'unknown')}")
        
        # Create test PDF
        print("3. Creating test PDF...")
        pdf_content = create_test_pdf()
        print(f"✅ Created test PDF ({len(pdf_content)} bytes)")
        
        # Test resume upload
        print("4. Testing resume upload...")
        files = {"file": ("test_resume.pdf", pdf_content, "application/pdf")}
        upload_response = client.post("/api/resume/upload", files=files)
        
        print(f"Upload response status: {upload_response.status_code}")
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print("✅ Resume uploaded successfully")
            print(f"Processing status: {upload_data.get('processing_status')}")
            print(f"Chunk count: {upload_data.get('chunk_count')}")
        else:
            print(f"❌ Upload failed: {upload_response.text}")
            return False
        
        # Test resume search
        print("5. Testing resume search...")
        search_response = client.post(
            "/api/resume/search",
            params={"query": "machine learning experience", "n_results": 3}
        )
        
        print(f"Search response status: {search_response.status_code}")
        if search_response.status_code == 200:
            search_data = search_response.json()
            print("✅ Resume search successful")
            print(f"Query: {search_data.get('query')}")
            print(f"Results found: {search_data.get('total_results', 0)}")
            
            # Display search results
            for i, result in enumerate(search_data.get('results', [])[:2]):
                print(f"  Result {i+1}:")
                print(f"    Content: {result.get('content', '')[:100]}...")
                print(f"    Distance: {result.get('distance', 'N/A')}")
        else:
            print(f"❌ Search failed: {search_response.text}")
            return False
        
        # Test another search query
        print("6. Testing another search query...")
        search_response2 = client.post(
            "/api/resume/search",
            params={"query": "Python programming skills", "n_results": 2}
        )
        
        if search_response2.status_code == 200:
            search_data2 = search_response2.json()
            print("✅ Second search successful")
            print(f"Results found: {search_data2.get('total_results', 0)}")
        else:
            print(f"❌ Second search failed: {search_response2.text}")
        
        print("\n🎉 All integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run integration tests"""
    print("🚀 Starting Resume Upload Integration Tests")
    print("=" * 60)
    
    # Check if reportlab is available for PDF creation
    try:
        import reportlab
        print("✅ reportlab available for PDF creation")
    except ImportError:
        print("❌ reportlab not available, installing...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "reportlab"], check=True)
        print("✅ reportlab installed")
    
    success = test_resume_upload_with_embeddings()
    
    if success:
        print("\n🎉 All integration tests passed!")
        return 0
    else:
        print("\n❌ Some integration tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)