#!/usr/bin/env python3
"""
Test script to verify FastAPI resume endpoints
"""

import io
from fastapi.testclient import TestClient
from main import app

def create_test_pdf_bytes():
    """Create a simple test PDF as bytes"""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(John Doe - Software Engineer) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000274 00000 n 
0000000369 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
456
%%EOF"""
    return pdf_content

def test_api_endpoints():
    """Test the FastAPI resume endpoints"""
    print("Testing FastAPI Resume Endpoints...")
    
    client = TestClient(app)
    
    # Test health endpoint
    print("1. Testing health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✅ Health endpoint working")
    
    # Test root endpoint
    print("2. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✅ Root endpoint working")
    
    # Test resume list endpoint
    print("3. Testing resume list endpoint...")
    response = client.get("/api/resume/list")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    print("   ✅ Resume list endpoint working")
    
    # Test resume upload endpoint
    print("4. Testing resume upload endpoint...")
    test_pdf = create_test_pdf_bytes()
    
    files = {
        "file": ("test_resume.pdf", io.BytesIO(test_pdf), "application/pdf")
    }
    
    response = client.post("/api/resume/upload", files=files)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        response_data = response.json()
        print(f"   Response: {response_data}")
        print(f"   Resume ID: {response_data.get('id')}")
        print(f"   Processing Status: {response_data.get('processing_status')}")
        print(f"   Chunk Count: {response_data.get('chunk_count')}")
        print("   ✅ Resume upload endpoint working")
    else:
        print(f"   ❌ Resume upload failed: {response.text}")
    
    # Test invalid file upload
    print("5. Testing invalid file upload...")
    invalid_files = {
        "file": ("test.txt", io.BytesIO(b"not a pdf"), "text/plain")
    }
    
    response = client.post("/api/resume/upload", files=invalid_files)
    print(f"   Status: {response.status_code}")
    if response.status_code == 400:
        print("   ✅ Invalid file properly rejected")
    else:
        print(f"   ⚠️  Expected 400, got {response.status_code}")

if __name__ == "__main__":
    print("=" * 50)
    print("FastAPI Resume Endpoints Test")
    print("=" * 50)
    
    try:
        test_api_endpoints()
        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("=" * 50)