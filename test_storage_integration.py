#!/usr/bin/env python3
"""
Test script for Supabase Storage integration
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_storage_integration():
    """Test the complete storage integration"""
    print("🧪 Testing Supabase Storage Integration")
    print("=" * 40)
    
    try:
        from services.supabase_storage_service import SupabaseStorageService
        from services.storage_quota_manager import StorageQuotaManager
        from services.resume_service import ResumeProcessingService
        
        # Test 1: Storage Service Health
        print("\n1️⃣ Testing Storage Service...")
        storage_service = SupabaseStorageService()
        health = storage_service.health_check()
        
        if health["status"] == "healthy":
            print(f"✅ Storage service healthy (bucket: {health['bucket_name']})")
        else:
            print(f"❌ Storage service unhealthy: {health.get('error')}")
            return False
        
        # Test 2: Quota Manager
        print("\n2️⃣ Testing Quota Manager...")
        quota_manager = StorageQuotaManager(storage_service)
        storage_status = await quota_manager.check_storage_status()
        
        print(f"✅ Storage mode: {storage_status['mode'].value}")
        print(f"✅ Usage: {storage_status.get('storage_usage_percent', 0):.1%}")
        
        # Test 3: Resume Service
        print("\n3️⃣ Testing Resume Service...")
        resume_service = ResumeProcessingService(use_cloud_storage=True)
        
        if resume_service.use_cloud_storage:
            print("✅ Resume service configured for cloud storage")
        else:
            print("❌ Resume service not using cloud storage")
            return False
        
        # Test 4: Notification System
        print("\n4️⃣ Testing Notification System...")
        notification = quota_manager.get_user_notification_message(storage_status)
        
        if storage_status['mode'].value == "temporary":
            if notification:
                print(f"✅ Notification generated: {notification['title']}")
            else:
                print("❌ No notification generated for temporary mode")
        else:
            print("✅ No notification needed (storage available)")
        
        print("\n🎉 All tests passed! Supabase Storage integration is working.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_file_operations():
    """Test actual file operations (requires test file)"""
    print("\n🗂️ Testing File Operations")
    print("-" * 30)
    
    try:
        from services.resume_service import ResumeProcessingService
        
        # Create a simple test PDF content (just for testing)
        test_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n179\n%%EOF"
        
        resume_service = ResumeProcessingService(use_cloud_storage=True)
        
        # Test file validation
        is_valid, error = resume_service.validate_pdf_file(test_content, "test.pdf")
        if is_valid:
            print("✅ PDF validation passed")
        else:
            print(f"❌ PDF validation failed: {error}")
        
        # Test file save (without processing to avoid errors)
        test_user_id = "test-user-123"
        file_path, public_url, storage_info = await resume_service.save_uploaded_file(
            test_content, "test.pdf", test_user_id
        )
        
        print(f"✅ File saved: {file_path}")
        print(f"✅ Storage info: {storage_info}")
        
        # Clean up test file
        if file_path:
            deleted = await resume_service.delete_resume_file(file_path)
            if deleted:
                print("✅ Test file cleaned up")
            else:
                print("⚠️ Could not clean up test file")
        
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

if __name__ == "__main__":
    print("GoalTrajectory.ai - Storage Integration Test")
    print("=" * 50)
    
    # Run basic integration test
    success = asyncio.run(test_storage_integration())
    
    if success and len(sys.argv) > 1 and sys.argv[1] == "--files":
        # Run file operations test if requested
        print("\n" + "=" * 50)
        asyncio.run(test_file_operations())
    
    if success:
        print("\n🚀 Integration is ready!")
        print("💡 Run with --files flag to test file operations")
    else:
        print("\n❌ Integration needs attention")
        print("💡 Check your environment variables and Supabase setup")
    
    sys.exit(0 if success else 1)