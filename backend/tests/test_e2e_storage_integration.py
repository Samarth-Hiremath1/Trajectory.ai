#!/usr/bin/env python3
"""
End-to-End Integration Tests for Supabase Storage
Tests real functionality with actual Supabase connection (requires environment setup)
"""
import pytest
import asyncio
import os
import tempfile
from pathlib import Path
import sys
import uuid
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from services.supabase_storage_service import SupabaseStorageService
from services.storage_quota_manager import StorageQuotaManager, StorageMode
from services.resume_service import ResumeProcessingService


# Skip tests if environment variables are not set
pytestmark = pytest.mark.skipif(
    not all([
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    ]),
    reason="Supabase environment variables not set"
)


class TestE2EStorageIntegration:
    """End-to-end tests with real Supabase connection"""
    
    @pytest.fixture(scope="class")
    def storage_service(self):
        """Create real storage service instance"""
        return SupabaseStorageService()
    
    @pytest.fixture(scope="class")
    def quota_manager(self, storage_service):
        """Create real quota manager instance"""
        return StorageQuotaManager(storage_service)
    
    @pytest.fixture(scope="class")
    def resume_service(self):
        """Create real resume service instance"""
        return ResumeProcessingService(use_cloud_storage=True)
    
    @pytest.fixture
    def test_user_id(self):
        """Generate unique test user ID"""
        return f"test-user-{uuid.uuid4().hex[:8]}"
    
    @pytest.fixture
    def sample_resume_pdf(self):
        """Create a realistic PDF resume for testing"""
        # This creates a more realistic PDF with actual text content
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
/Resources <<
/Font <<
/F1 4 0 R
>>
>>
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
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
(john.doe@email.com) Tj
0 -40 Td
(EXPERIENCE) Tj
0 -20 Td
(Senior Python Developer - 5 years) Tj
0 -20 Td
(Machine Learning Engineer - 3 years) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
0000000179 00000 n 
0000000364 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
456
%%EOF"""
        return pdf_content
    
    def test_storage_service_health_check(self, storage_service):
        """Test real storage service health check"""
        health = storage_service.health_check()
        
        assert health["status"] in ["healthy", "degraded"]
        assert health["bucket_name"] == "resumes"
        
        if health["status"] == "healthy":
            print(f"✅ Storage service healthy: {health}")
        else:
            print(f"⚠️ Storage service degraded: {health}")
    
    @pytest.mark.asyncio
    async def test_file_upload_and_delete_cycle(self, storage_service, test_user_id, sample_resume_pdf):
        """Test complete file upload and delete cycle"""
        filename = "test-resume-e2e.pdf"
        
        try:
            # Test upload
            file_path, public_url = await storage_service.save_uploaded_file(
                sample_resume_pdf, filename, test_user_id, temporary=False
            )
            
            assert file_path.startswith(f"users/{test_user_id}/")
            assert file_path.endswith(".pdf")
            assert public_url is not None
            
            print(f"✅ File uploaded: {file_path}")
            
            # Test file URL generation
            signed_url = storage_service.get_file_url(file_path, expires_in=3600)
            assert signed_url is not None
            assert "sign" in signed_url.lower()  # Should be a signed URL
            
            print(f"✅ Signed URL generated: {signed_url[:50]}...")
            
        finally:
            # Clean up - delete the test file
            deleted = await storage_service.delete_file(file_path)
            assert deleted is True
            print(f"✅ Test file cleaned up: {file_path}")
    
    @pytest.mark.asyncio
    async def test_temporary_file_handling(self, storage_service, test_user_id, sample_resume_pdf):
        """Test temporary file upload and handling"""
        filename = "temp-test-resume.pdf"
        
        try:
            # Upload as temporary file
            file_path, public_url = await storage_service.save_uploaded_file(
                sample_resume_pdf, filename, test_user_id, temporary=True
            )
            
            assert file_path.startswith(f"temp/{test_user_id}/")
            assert file_path.endswith(".pdf")
            
            print(f"✅ Temporary file uploaded: {file_path}")
            
        finally:
            # Clean up
            await storage_service.delete_file(file_path)
    
    @pytest.mark.asyncio
    async def test_quota_manager_functionality(self, quota_manager):
        """Test quota manager with real storage"""
        # Check current storage status
        storage_status = await quota_manager.check_storage_status()
        
        assert "mode" in storage_status
        assert "storage_usage_percent" in storage_status
        assert "can_store_files" in storage_status
        
        print(f"✅ Current storage mode: {storage_status['mode'].value}")
        print(f"✅ Storage usage: {storage_status['storage_usage_percent']:.1%}")
        
        # Test notification generation
        notification = quota_manager.get_user_notification_message(storage_status)
        
        if notification:
            print(f"✅ Notification generated: {notification['title']}")
            assert "type" in notification
            assert "title" in notification
            assert "message" in notification
        else:
            print("✅ No notification needed (storage available)")
    
    @pytest.mark.asyncio
    async def test_complete_resume_processing_flow(self, resume_service, test_user_id, sample_resume_pdf):
        """Test complete resume processing with real services"""
        filename = "complete-flow-test.pdf"
        
        try:
            # Process resume with full pipeline
            result = await resume_service.process_resume_with_embeddings(
                test_user_id, sample_resume_pdf, filename
            )
            
            # Verify successful processing
            assert result["success"] is True
            assert result["file_path"] is not None
            assert result["text_content"] is not None
            assert len(result["chunks"]) > 0
            assert result["processing_status"].value == "completed"
            
            print(f"✅ Resume processed successfully")
            print(f"   - File path: {result['file_path']}")
            print(f"   - Text length: {len(result['text_content'])} chars")
            print(f"   - Chunks: {result['chunk_count']}")
            print(f"   - Embeddings stored: {result['embeddings_stored']}")
            
            # Test if storage info is included
            if "storage_info" in result:
                print(f"   - Storage mode: {result['storage_info']['quota_status']['mode'].value}")
                print(f"   - Temporary: {result['storage_info']['temporary']}")
            
            # Test if notification is included
            if "user_notification" in result:
                print(f"   - User notification: {result['user_notification']['title']}")
            
            # Test if cleanup happened
            if "cleanup_info" in result:
                print(f"   - File deleted: {result['cleanup_info']['file_deleted']}")
            
            # Test resume search functionality
            search_results = resume_service.search_resume_content(
                test_user_id, "python developer", n_results=3
            )
            
            print(f"✅ Search results: {len(search_results)} matches")
            for i, result_item in enumerate(search_results[:2]):  # Show first 2
                print(f"   - Match {i+1}: {result_item.get('content', '')[:50]}...")
            
        finally:
            # Clean up test data
            try:
                if result.get("success") and result.get("file_path"):
                    # Only try to delete if file wasn't already deleted by cleanup
                    if not result.get("cleanup_info", {}).get("file_deleted", False):
                        await resume_service.delete_resume_file(result["file_path"])
                
                # Clean up embeddings
                resume_service.delete_user_resume_data(test_user_id)
                print(f"✅ Test data cleaned up for user: {test_user_id}")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup warning: {cleanup_error}")
    
    @pytest.mark.asyncio
    async def test_pdf_validation_edge_cases(self, resume_service):
        """Test PDF validation with various edge cases"""
        # Test valid PDF
        valid_pdf = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\n0000000000 65535 f \ntrailer\n<<\n/Size 1\n>>\nstartxref\n9\n%%EOF"
        is_valid, error = resume_service.validate_pdf_file(valid_pdf, "test.pdf")
        assert is_valid is True
        assert error is None
        
        # Test invalid extension
        is_valid, error = resume_service.validate_pdf_file(valid_pdf, "test.doc")
        assert is_valid is False
        assert "must be a PDF" in error
        
        # Test empty file
        is_valid, error = resume_service.validate_pdf_file(b"", "test.pdf")
        assert is_valid is False
        assert "cannot be empty" in error
        
        # Test non-PDF content
        is_valid, error = resume_service.validate_pdf_file(b"This is not a PDF", "test.pdf")
        assert is_valid is False
        assert "Invalid PDF file format" in error
        
        # Test file too large (simulate 11MB file)
        large_content = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
        is_valid, error = resume_service.validate_pdf_file(large_content, "test.pdf")
        assert is_valid is False
        assert "less than 10MB" in error
        
        print("✅ All PDF validation edge cases passed")
    
    @pytest.mark.asyncio
    async def test_storage_mode_simulation(self, quota_manager):
        """Test storage mode behavior by simulating different usage levels"""
        # This test simulates different storage usage levels
        # In a real scenario, you might temporarily modify the quota thresholds
        
        original_free_tier = quota_manager.FREE_TIER_STORAGE_BYTES
        original_warning = quota_manager.WARNING_THRESHOLD
        original_cleanup = quota_manager.CLEANUP_THRESHOLD
        
        try:
            # Simulate small storage limit for testing
            quota_manager.FREE_TIER_STORAGE_BYTES = 1024 * 1024  # 1MB
            quota_manager.WARNING_THRESHOLD = 0.5  # 50%
            quota_manager.CLEANUP_THRESHOLD = 0.8  # 80%
            
            # Test with simulated low usage
            with pytest.MonkeyPatch().context() as m:
                async def mock_low_usage():
                    return {"storage_used": 100 * 1024, "file_count": 1}  # 100KB
                
                m.setattr(quota_manager, '_get_bucket_statistics', mock_low_usage)
                status = await quota_manager.check_storage_status()
                
                assert status["mode"] == StorageMode.PERSISTENT
                print(f"✅ Low usage mode: {status['mode'].value}")
            
            # Test with simulated high usage
            with pytest.MonkeyPatch().context() as m:
                async def mock_high_usage():
                    return {"storage_used": 900 * 1024, "file_count": 10}  # 900KB (90%)
                
                m.setattr(quota_manager, '_get_bucket_statistics', mock_high_usage)
                status = await quota_manager.check_storage_status()
                
                assert status["mode"] == StorageMode.TEMPORARY
                print(f"✅ High usage mode: {status['mode'].value}")
                
                # Test notification generation
                notification = quota_manager.get_user_notification_message(status)
                assert notification is not None
                assert notification["type"] == "warning"
                print(f"✅ Notification: {notification['title']}")
        
        finally:
            # Restore original values
            quota_manager.FREE_TIER_STORAGE_BYTES = original_free_tier
            quota_manager.WARNING_THRESHOLD = original_warning
            quota_manager.CLEANUP_THRESHOLD = original_cleanup


class TestPerformanceAndReliability:
    """Test performance and reliability aspects"""
    
    @pytest.mark.asyncio
    async def test_concurrent_uploads(self, sample_resume_pdf):
        """Test handling multiple concurrent uploads"""
        storage_service = SupabaseStorageService()
        test_users = [f"concurrent-user-{i}" for i in range(3)]
        
        async def upload_for_user(user_id):
            try:
                file_path, _ = await storage_service.save_uploaded_file(
                    sample_resume_pdf, f"concurrent-test-{user_id}.pdf", user_id
                )
                return file_path
            except Exception as e:
                return f"Error: {e}"
        
        # Run concurrent uploads
        tasks = [upload_for_user(user_id) for user_id in test_users]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify results
        successful_uploads = [r for r in results if isinstance(r, str) and r.startswith("users/")]
        print(f"✅ Concurrent uploads: {len(successful_uploads)}/{len(test_users)} successful")
        
        # Clean up
        for file_path in successful_uploads:
            try:
                await storage_service.delete_file(file_path)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and recovery scenarios"""
        storage_service = SupabaseStorageService()
        
        # Test with invalid file path
        result = await storage_service.delete_file("nonexistent/path/file.pdf")
        # Should handle gracefully without throwing
        print(f"✅ Invalid file deletion handled: {result}")
        
        # Test with malformed user ID
        try:
            file_path, _ = await storage_service.save_uploaded_file(
                b"test", "test.pdf", "invalid/user/id"
            )
            print(f"⚠️ Malformed user ID accepted: {file_path}")
        except Exception as e:
            print(f"✅ Malformed user ID rejected: {type(e).__name__}")


# Test fixtures and configuration
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Check environment before running
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY", "SUPABASE_SERVICE_ROLE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nSet these in your .env file before running E2E tests")
        sys.exit(1)
    
    print("🧪 Running End-to-End Supabase Storage Integration Tests")
    print("=" * 60)
    
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])