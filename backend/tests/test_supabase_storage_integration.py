#!/usr/bin/env python3
"""
Comprehensive test suite for Supabase Storage integration
"""
import pytest
import asyncio
import os
import tempfile
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from services.supabase_storage_service import SupabaseStorageService
from services.storage_quota_manager import StorageQuotaManager, StorageMode
from services.resume_service import ResumeProcessingService
from models.resume import ProcessingStatus


class TestSupabaseStorageService:
    """Test the Supabase Storage Service"""
    
    @pytest.fixture
    def storage_service(self):
        """Create a storage service instance for testing"""
        return SupabaseStorageService()
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing"""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
    
    def test_health_check(self, storage_service):
        """Test storage service health check"""
        health = storage_service.health_check()
        
        assert "status" in health
        assert "bucket_name" in health
        assert health["bucket_name"] == "resumes"
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_permanent(self, storage_service, sample_pdf_content):
        """Test saving file permanently"""
        user_id = "test-user-123"
        filename = "test-resume.pdf"
        
        with patch.object(storage_service.supabase.storage, 'from_') as mock_storage:
            mock_bucket = Mock()
            mock_storage.return_value = mock_bucket
            mock_bucket.upload.return_value = Mock(data={"path": f"users/{user_id}/test.pdf"})
            mock_bucket.get_public_url.return_value = Mock(data={"publicUrl": "https://test.url"})
            
            file_path, public_url = await storage_service.save_uploaded_file(
                sample_pdf_content, filename, user_id, temporary=False
            )
            
            assert file_path.startswith(f"users/{user_id}/")
            assert file_path.endswith(".pdf")
            assert public_url == "https://test.url"
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_temporary(self, storage_service, sample_pdf_content):
        """Test saving file temporarily"""
        user_id = "test-user-456"
        filename = "test-resume.pdf"
        
        with patch.object(storage_service.supabase.storage, 'from_') as mock_storage:
            mock_bucket = Mock()
            mock_storage.return_value = mock_bucket
            mock_bucket.upload.return_value = Mock(data={"path": f"temp/{user_id}/test.pdf"})
            mock_bucket.get_public_url.return_value = Mock(data={"publicUrl": "https://test.url"})
            
            file_path, public_url = await storage_service.save_uploaded_file(
                sample_pdf_content, filename, user_id, temporary=True
            )
            
            assert file_path.startswith(f"temp/{user_id}/")
            assert file_path.endswith(".pdf")
    
    @pytest.mark.asyncio
    async def test_delete_file(self, storage_service):
        """Test file deletion"""
        file_path = "users/test-user/test-file.pdf"
        
        with patch.object(storage_service.supabase.storage, 'from_') as mock_storage:
            mock_bucket = Mock()
            mock_storage.return_value = mock_bucket
            mock_bucket.remove.return_value = Mock(data={"message": "deleted"})
            
            result = await storage_service.delete_file(file_path)
            
            assert result is True
            mock_bucket.remove.assert_called_once_with([file_path])
    
    def test_get_file_url(self, storage_service):
        """Test getting secure file URL"""
        file_path = "users/test-user/test-file.pdf"
        
        with patch.object(storage_service.supabase.storage, 'from_') as mock_storage:
            mock_bucket = Mock()
            mock_storage.return_value = mock_bucket
            mock_bucket.create_signed_url.return_value = Mock(
                data={"signedUrl": "https://signed.url"}
            )
            
            url = storage_service.get_file_url(file_path, expires_in=3600)
            
            assert url == "https://signed.url"
            mock_bucket.create_signed_url.assert_called_once_with(file_path, 3600)


class TestStorageQuotaManager:
    """Test the Storage Quota Manager"""
    
    @pytest.fixture
    def mock_storage_service(self):
        """Create a mock storage service"""
        return Mock(spec=SupabaseStorageService)
    
    @pytest.fixture
    def quota_manager(self, mock_storage_service):
        """Create a quota manager instance"""
        return StorageQuotaManager(mock_storage_service)
    
    @pytest.mark.asyncio
    async def test_check_storage_status_persistent(self, quota_manager, mock_storage_service):
        """Test storage status check in persistent mode"""
        # Mock low storage usage
        mock_storage_service.get_storage_usage.return_value = {
            "total_size_bytes": 100 * 1024 * 1024,  # 100MB
            "file_count": 10
        }
        
        with patch.object(quota_manager, '_get_bucket_statistics', return_value={
            "storage_used": 100 * 1024 * 1024,
            "file_count": 10
        }):
            status = await quota_manager.check_storage_status()
            
            assert status["mode"] == StorageMode.PERSISTENT
            assert status["storage_usage_percent"] < 0.8
            assert status["can_store_files"] is True
    
    @pytest.mark.asyncio
    async def test_check_storage_status_warning(self, quota_manager):
        """Test storage status check in warning mode"""
        # Mock high storage usage (85%)
        with patch.object(quota_manager, '_get_bucket_statistics', return_value={
            "storage_used": int(0.85 * quota_manager.FREE_TIER_STORAGE_BYTES),
            "file_count": 100
        }):
            status = await quota_manager.check_storage_status()
            
            assert status["mode"] == StorageMode.WARNING
            assert 0.8 <= status["storage_usage_percent"] < 0.9
            assert status["can_store_files"] is True
    
    @pytest.mark.asyncio
    async def test_check_storage_status_temporary(self, quota_manager):
        """Test storage status check in temporary mode"""
        # Mock very high storage usage (95%)
        with patch.object(quota_manager, '_get_bucket_statistics', return_value={
            "storage_used": int(0.95 * quota_manager.FREE_TIER_STORAGE_BYTES),
            "file_count": 200
        }):
            status = await quota_manager.check_storage_status()
            
            assert status["mode"] == StorageMode.TEMPORARY
            assert status["storage_usage_percent"] >= 0.9
            assert status["can_store_files"] is False
    
    def test_get_user_notification_message_temporary(self, quota_manager):
        """Test user notification for temporary mode"""
        storage_status = {
            "mode": StorageMode.TEMPORARY,
            "storage_usage_percent": 0.95
        }
        
        notification = quota_manager.get_user_notification_message(storage_status)
        
        assert notification is not None
        assert notification["type"] == "warning"
        assert notification["title"] == "Storage Limit Reached"
        assert "deleted for space" in notification["message"]
        assert "email me" in notification["message"]
    
    def test_get_user_notification_message_warning(self, quota_manager):
        """Test user notification for warning mode"""
        storage_status = {
            "mode": StorageMode.WARNING,
            "storage_usage_percent": 0.85
        }
        
        notification = quota_manager.get_user_notification_message(storage_status)
        
        assert notification is not None
        assert notification["type"] == "info"
        assert notification["title"] == "Storage Usage Notice"
        assert "85.0%" in notification["message"]
    
    def test_get_user_notification_message_persistent(self, quota_manager):
        """Test no notification for persistent mode"""
        storage_status = {
            "mode": StorageMode.PERSISTENT,
            "storage_usage_percent": 0.5
        }
        
        notification = quota_manager.get_user_notification_message(storage_status)
        
        assert notification is None
    
    @pytest.mark.asyncio
    async def test_should_delete_after_processing(self, quota_manager):
        """Test should delete after processing logic"""
        # Mock temporary mode
        with patch.object(quota_manager, 'check_storage_status', return_value={
            "mode": StorageMode.TEMPORARY
        }):
            should_delete = await quota_manager.should_delete_after_processing()
            assert should_delete is True
        
        # Mock persistent mode
        with patch.object(quota_manager, 'check_storage_status', return_value={
            "mode": StorageMode.PERSISTENT
        }):
            should_delete = await quota_manager.should_delete_after_processing()
            assert should_delete is False


class TestResumeProcessingService:
    """Test the Resume Processing Service with Supabase integration"""
    
    @pytest.fixture
    def resume_service(self):
        """Create a resume service instance"""
        return ResumeProcessingService(use_cloud_storage=True)
    
    @pytest.fixture
    def sample_pdf_content(self):
        """Create sample PDF content for testing"""
        return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Resources <<\n/Font <<\n/F1 4 0 R\n>>\n>>\n/Contents 5 0 R\n>>\nendobj\n4 0 obj\n<<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\nendobj\n5 0 obj\n<<\n/Length 44\n>>\nstream\nBT\n/F1 12 Tf\n72 720 Td\n(John Doe Resume) Tj\nET\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \n0000000179 00000 n \n0000000364 00000 n \ntrailer\n<<\n/Size 6\n/Root 1 0 R\n>>\nstartxref\n456\n%%EOF"
    
    def test_validate_pdf_file_valid(self, resume_service, sample_pdf_content):
        """Test PDF validation with valid file"""
        is_valid, error = resume_service.validate_pdf_file(sample_pdf_content, "test.pdf")
        
        assert is_valid is True
        assert error is None
    
    def test_validate_pdf_file_invalid_extension(self, resume_service, sample_pdf_content):
        """Test PDF validation with invalid extension"""
        is_valid, error = resume_service.validate_pdf_file(sample_pdf_content, "test.txt")
        
        assert is_valid is False
        assert "must be a PDF" in error
    
    def test_validate_pdf_file_too_large(self, resume_service):
        """Test PDF validation with file too large"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        is_valid, error = resume_service.validate_pdf_file(large_content, "test.pdf")
        
        assert is_valid is False
        assert "less than 10MB" in error
    
    def test_validate_pdf_file_empty(self, resume_service):
        """Test PDF validation with empty file"""
        is_valid, error = resume_service.validate_pdf_file(b"", "test.pdf")
        
        assert is_valid is False
        assert "cannot be empty" in error
    
    def test_validate_pdf_file_invalid_format(self, resume_service):
        """Test PDF validation with invalid PDF format"""
        is_valid, error = resume_service.validate_pdf_file(b"not a pdf", "test.pdf")
        
        assert is_valid is False
        assert "Invalid PDF file format" in error
    
    @pytest.mark.asyncio
    async def test_save_uploaded_file_cloud_storage(self, resume_service, sample_pdf_content):
        """Test file saving with cloud storage"""
        user_id = "test-user-789"
        filename = "test-resume.pdf"
        
        with patch.object(resume_service.storage_service, 'save_uploaded_file') as mock_save:
            mock_save.return_value = (f"users/{user_id}/test.pdf", "https://test.url")
            
            with patch.object(resume_service.quota_manager, 'check_storage_status') as mock_quota:
                mock_quota.return_value = {
                    "mode": StorageMode.PERSISTENT,
                    "storage_usage_percent": 0.5
                }
                
                file_path, public_url, storage_info = await resume_service.save_uploaded_file(
                    sample_pdf_content, filename, user_id
                )
                
                assert file_path.startswith(f"users/{user_id}/")
                assert public_url == "https://test.url"
                assert storage_info["temporary"] is False
                assert storage_info["quota_status"]["mode"] == StorageMode.PERSISTENT
    
    @pytest.mark.asyncio
    async def test_process_resume_with_embeddings_success(self, resume_service, sample_pdf_content):
        """Test complete resume processing pipeline"""
        user_id = "test-user-complete"
        filename = "complete-test.pdf"
        
        # Mock all dependencies
        with patch.object(resume_service, 'save_uploaded_file') as mock_save, \
             patch.object(resume_service, 'parse_pdf_content') as mock_parse, \
             patch.object(resume_service.embedding_service, 'store_resume_embeddings') as mock_embed, \
             patch.object(resume_service, '_refresh_chat_service_context') as mock_refresh:
            
            # Setup mocks
            mock_save.return_value = (
                f"users/{user_id}/test.pdf", 
                "https://test.url",
                {"temporary": False, "quota_status": {"mode": StorageMode.PERSISTENT}}
            )
            
            mock_parse_result = Mock()
            mock_parse_result.success = True
            mock_parse_result.text_content = "John Doe Resume Content"
            mock_parse_result.chunks = [Mock(chunk_id="1", content="chunk1")]
            mock_parse_result.metadata = {"page_count": 1}
            mock_parse_result.error_message = None
            mock_parse.return_value = mock_parse_result
            
            mock_embed.return_value = True
            mock_refresh.return_value = None
            
            # Test processing
            result = await resume_service.process_resume_with_embeddings(
                user_id, sample_pdf_content, filename
            )
            
            # Verify results
            assert result["success"] is True
            assert result["file_path"] == f"users/{user_id}/test.pdf"
            assert result["public_url"] == "https://test.url"
            assert result["text_content"] == "John Doe Resume Content"
            assert result["chunk_count"] == 1
            assert result["embeddings_stored"] is True
            assert result["processing_status"] == ProcessingStatus.COMPLETED
            assert "user_notification" not in result  # No notification for persistent mode
    
    @pytest.mark.asyncio
    async def test_process_resume_temporary_mode_with_cleanup(self, resume_service, sample_pdf_content):
        """Test resume processing in temporary mode with file cleanup"""
        user_id = "test-user-temp"
        filename = "temp-test.pdf"
        
        with patch.object(resume_service, 'save_uploaded_file') as mock_save, \
             patch.object(resume_service, 'parse_pdf_content') as mock_parse, \
             patch.object(resume_service.embedding_service, 'store_resume_embeddings') as mock_embed, \
             patch.object(resume_service, 'delete_resume_file') as mock_delete, \
             patch.object(resume_service, '_refresh_chat_service_context') as mock_refresh:
            
            # Setup mocks for temporary mode
            quota_status = {
                "mode": StorageMode.TEMPORARY,
                "storage_usage_percent": 0.95
            }
            
            mock_save.return_value = (
                f"temp/{user_id}/test.pdf", 
                "https://test.url",
                {"temporary": True, "quota_status": quota_status}
            )
            
            mock_parse_result = Mock()
            mock_parse_result.success = True
            mock_parse_result.text_content = "Resume Content"
            mock_parse_result.chunks = [Mock(chunk_id="1")]
            mock_parse_result.metadata = {"page_count": 1}
            mock_parse.return_value = mock_parse_result
            
            mock_embed.return_value = True
            mock_delete.return_value = True
            mock_refresh.return_value = None
            
            # Mock quota manager notification
            with patch.object(resume_service.quota_manager, 'get_user_notification_message') as mock_notification:
                mock_notification.return_value = {
                    "type": "warning",
                    "title": "Storage Limit Reached",
                    "message": "File will be deleted after processing"
                }
                
                # Test processing
                result = await resume_service.process_resume_with_embeddings(
                    user_id, sample_pdf_content, filename
                )
                
                # Verify results
                assert result["success"] is True
                assert result["storage_info"]["temporary"] is True
                assert result["cleanup_info"]["file_deleted"] is True
                assert result["user_notification"]["type"] == "warning"
                assert "Storage Limit Reached" in result["user_notification"]["title"]
                
                # Verify file was deleted
                mock_delete.assert_called_once_with(f"temp/{user_id}/test.pdf")
    
    @pytest.mark.asyncio
    async def test_process_resume_validation_failure(self, resume_service):
        """Test resume processing with validation failure"""
        user_id = "test-user-invalid"
        invalid_content = b"not a pdf"
        filename = "invalid.pdf"
        
        result = await resume_service.process_resume_with_embeddings(
            user_id, invalid_content, filename
        )
        
        assert result["success"] is False
        assert "Invalid PDF file format" in result["error"]
        assert result["processing_status"] == ProcessingStatus.FAILED
    
    def test_search_resume_content(self, resume_service):
        """Test resume content search"""
        user_id = "test-user-search"
        query = "python developer"
        
        with patch.object(resume_service.embedding_service, 'search_resume_embeddings') as mock_search:
            mock_search.return_value = [
                {"content": "Python developer with 5 years experience", "score": 0.9}
            ]
            
            results = resume_service.search_resume_content(user_id, query, n_results=5)
            
            assert len(results) == 1
            assert results[0]["content"] == "Python developer with 5 years experience"
            assert results[0]["score"] == 0.9
            mock_search.assert_called_once_with(user_id, query, 5)


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_upload_flow_persistent_mode(self):
        """Test complete upload flow in persistent mode"""
        # This would be an integration test that tests the full flow
        # from API endpoint to storage, including all services
        pass
    
    @pytest.mark.asyncio
    async def test_full_upload_flow_temporary_mode(self):
        """Test complete upload flow in temporary mode with cleanup"""
        # This would test the full flow when storage limits are reached
        pass
    
    @pytest.mark.asyncio
    async def test_quota_threshold_transitions(self):
        """Test transitions between storage modes as usage increases"""
        # This would test the behavior as storage usage crosses thresholds
        pass


# Test configuration and fixtures
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])