#!/usr/bin/env python3
"""
Test Supabase Authentication
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv("backend/.env.development")

def test_supabase_keys():
    """Test both anon and service role keys"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_ANON_KEY")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    print("🔑 Supabase Key Test")
    print("=" * 40)
    print(f"URL: {supabase_url}")
    print(f"Anon Key: {anon_key[:20]}..." if anon_key else "❌ Missing")
    print(f"Service Key: {service_key[:20]}..." if service_key else "❌ Missing")
    
    if not all([supabase_url, anon_key, service_key]):
        print("\n❌ Missing required keys!")
        return False
    
    try:
        # Add backend to path
        sys.path.append(str(Path(__file__).parent / "backend"))
        
        from supabase import create_client
        
        print("\n🧪 Testing Anon Key...")
        anon_client = create_client(supabase_url, anon_key)
        
        print("🧪 Testing Service Role Key...")
        service_client = create_client(supabase_url, service_key)
        
        # Test storage access with service key
        print("🧪 Testing Storage Access with Service Key...")
        buckets = service_client.storage.list_buckets()
        print(f"✅ Service key can access storage: {len(buckets)} buckets found")
        
        # Test if resumes bucket exists
        resume_bucket_exists = any(bucket.name == 'resumes' for bucket in buckets)
        print(f"✅ Resumes bucket exists: {resume_bucket_exists}")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

if __name__ == "__main__":
    test_supabase_keys()