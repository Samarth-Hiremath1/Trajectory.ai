#!/usr/bin/env python3
"""
Simple test script to verify resume upload and parsing functionality
"""

import asyncio
import tempfile
import os
from pathlib import Path

from services.resume_service import ResumeProcessingService


def create_test_pdf():
    """Create a simple test PDF file for testing"""
    # This creates a minimal PDF with some text content
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


async def test_resume_service():
    """Test the resume processing service"""
    print("Testing Resume Processing Service...")
    
    # Initialize service
    service = ResumeProcessingService(upload_dir="test_uploads")
    
    # Create test PDF
    test_pdf_content = create_test_pdf()
    test_filename = "test_resume.pdf"
    
    print(f"1. Testing PDF validation...")
    is_valid, error = service.validate_pdf_file(test_pdf_content, test_filename)
    print(f"   Validation result: {is_valid}, Error: {error}")
    
    if not is_valid:
        print("   ❌ PDF validation failed")
        return
    
    print("   ✅ PDF validation passed")
    
    print(f"2. Testing file upload...")
    try:
        file_path = await service.save_uploaded_file(
            test_pdf_content, test_filename, "test_user"
        )
        print(f"   File saved to: {file_path}")
        print("   ✅ File upload successful")
    except Exception as e:
        print(f"   ❌ File upload failed: {e}")
        return
    
    print(f"3. Testing PDF parsing...")
    try:
        parse_result = service.parse_pdf_content(file_path)
        print(f"   Parse success: {parse_result.success}")
        if parse_result.success:
            print(f"   Text content length: {len(parse_result.text_content)}")
            print(f"   Number of chunks: {len(parse_result.chunks)}")
            print(f"   Metadata: {parse_result.metadata}")
            print("   ✅ PDF parsing successful")
        else:
            print(f"   ❌ PDF parsing failed: {parse_result.error_message}")
    except Exception as e:
        print(f"   ❌ PDF parsing failed with exception: {e}")
    
    # Cleanup
    print(f"4. Cleaning up test files...")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
        # Remove test directory if empty
        test_dir = Path("test_uploads")
        if test_dir.exists() and not any(test_dir.iterdir()):
            test_dir.rmdir()
        print("   ✅ Cleanup successful")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")


def test_validation_edge_cases():
    """Test validation with various edge cases"""
    print("\nTesting validation edge cases...")
    
    service = ResumeProcessingService()
    
    # Test cases
    test_cases = [
        (b"", "empty.pdf", "Empty file"),
        (b"not a pdf", "fake.pdf", "Invalid PDF content"),
        (b"%PDF-1.4\nvalid pdf", "test.txt", "Wrong extension"),
        (b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024), "large.pdf", "File too large"),
    ]
    
    for content, filename, description in test_cases:
        is_valid, error = service.validate_pdf_file(content, filename)
        status = "✅" if not is_valid else "❌"
        print(f"   {status} {description}: Valid={is_valid}, Error={error}")


if __name__ == "__main__":
    print("=" * 50)
    print("Resume Service Test Suite")
    print("=" * 50)
    
    # Run async test
    asyncio.run(test_resume_service())
    
    # Run validation tests
    test_validation_edge_cases()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("=" * 50)