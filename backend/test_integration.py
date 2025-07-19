#!/usr/bin/env python3
"""
Integration test for resume upload and parsing functionality
"""

import tempfile
import os
from pathlib import Path

# Test the complete flow
def test_complete_resume_flow():
    """Test the complete resume processing flow"""
    print("Testing Complete Resume Processing Flow...")
    
    from services.resume_service import ResumeProcessingService
    
    # Initialize service
    service = ResumeProcessingService(upload_dir="integration_test_uploads")
    
    # Create a more realistic test PDF content
    realistic_pdf = b"""%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(JOHN DOE) Tj
0 -20 Td
(Software Engineer) Tj
0 -20 Td
(john.doe@email.com | (555) 123-4567) Tj
0 -40 Td
(EXPERIENCE) Tj
0 -20 Td
(Senior Software Engineer at TechCorp (2020-2023)) Tj
0 -15 Td
(- Developed scalable web applications using React and Node.js) Tj
0 -15 Td
(- Led a team of 5 developers on multiple projects) Tj
0 -40 Td
(EDUCATION) Tj
0 -20 Td
(BS Computer Science, University of Technology (2016-2020)) Tj
0 -40 Td
(SKILLS) Tj
0 -20 Td
(JavaScript, Python, React, Node.js, AWS, Docker) Tj
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
0000000525 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
622
%%EOF"""
    
    print("1. Testing file validation...")
    is_valid, error = service.validate_pdf_file(realistic_pdf, "john_doe_resume.pdf")
    assert is_valid, f"Validation failed: {error}"
    print("   ✅ File validation passed")
    
    print("2. Testing file upload...")
    file_path = None
    try:
        import asyncio
        file_path = asyncio.run(service.save_uploaded_file(
            realistic_pdf, "john_doe_resume.pdf", "integration_test_user"
        ))
        assert os.path.exists(file_path), "File was not saved"
        print(f"   ✅ File saved to: {file_path}")
    except Exception as e:
        print(f"   ❌ File upload failed: {e}")
        return False
    
    print("3. Testing PDF parsing...")
    try:
        parse_result = service.parse_pdf_content(file_path)
        assert parse_result.success, f"Parsing failed: {parse_result.error_message}"
        
        print(f"   Text content preview: {parse_result.text_content[:100]}...")
        print(f"   Number of chunks: {len(parse_result.chunks)}")
        print(f"   Metadata: {parse_result.metadata}")
        
        # Verify content contains expected information
        content = parse_result.text_content.lower()
        assert "john doe" in content, "Name not found in parsed content"
        assert "software engineer" in content, "Job title not found"
        assert "experience" in content, "Experience section not found"
        assert "education" in content, "Education section not found"
        
        print("   ✅ PDF parsing successful with expected content")
    except Exception as e:
        print(f"   ❌ PDF parsing failed: {e}")
        return False
    
    print("4. Testing text chunking...")
    try:
        chunks = parse_result.chunks
        assert len(chunks) > 0, "No chunks created"
        
        for i, chunk in enumerate(chunks):
            print(f"   Chunk {i+1}: {len(chunk.content)} chars")
            assert chunk.chunk_id, "Chunk missing ID"
            assert chunk.content.strip(), "Chunk has no content"
            assert chunk.chunk_index == i, "Chunk index mismatch"
        
        print("   ✅ Text chunking successful")
    except Exception as e:
        print(f"   ❌ Text chunking failed: {e}")
        return False
    
    print("5. Testing cleanup...")
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove test directory if empty
        test_dir = Path("integration_test_uploads")
        if test_dir.exists() and not any(test_dir.iterdir()):
            test_dir.rmdir()
        
        print("   ✅ Cleanup successful")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")
    
    return True

def test_error_handling():
    """Test error handling scenarios"""
    print("\nTesting Error Handling...")
    
    from services.resume_service import ResumeProcessingService
    service = ResumeProcessingService()
    
    # Test parsing non-existent file
    print("1. Testing non-existent file parsing...")
    result = service.parse_pdf_content("non_existent_file.pdf")
    assert not result.success, "Should fail for non-existent file"
    assert result.error_message, "Should have error message"
    print("   ✅ Non-existent file properly handled")
    
    # Test various validation scenarios
    print("2. Testing validation edge cases...")
    test_cases = [
        (b"", "empty.pdf", "empty file"),
        (b"not a pdf", "fake.pdf", "invalid content"),
        (b"%PDF-1.4\nvalid", "test.txt", "wrong extension"),
    ]
    
    for content, filename, description in test_cases:
        is_valid, error = service.validate_pdf_file(content, filename)
        assert not is_valid, f"Should reject {description}"
        assert error, f"Should have error message for {description}"
        print(f"   ✅ {description.title()} properly rejected")

if __name__ == "__main__":
    print("=" * 60)
    print("Resume Processing Integration Test")
    print("=" * 60)
    
    try:
        # Test complete flow
        success = test_complete_resume_flow()
        
        if success:
            # Test error handling
            test_error_handling()
            
            print("\n" + "=" * 60)
            print("🎉 ALL INTEGRATION TESTS PASSED!")
            print("Resume upload and parsing service is working correctly!")
            print("=" * 60)
        else:
            print("\n❌ Integration test failed")
            
    except Exception as e:
        print(f"\n❌ Integration test failed with exception: {e}")
        import traceback
        traceback.print_exc()