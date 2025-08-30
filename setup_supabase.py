#!/usr/bin/env python3
"""
Quick setup script for Supabase Storage integration
"""
import os
import sys
from pathlib import Path

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars

def print_setup_instructions():
    """Print setup instructions"""
    print("🚀 GoalTrajectory.ai - Supabase Storage Setup")
    print("=" * 50)
    
    missing_vars = check_environment()
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        
        print("\n📝 Add these to your backend/.env file:")
        print("\n# Storage Configuration")
        print("STORAGE_PROVIDER=supabase")
        print("\n# Supabase Configuration")
        print("SUPABASE_URL=https://your-project.supabase.co")
        print("SUPABASE_ANON_KEY=your-anon-key")
        print("SUPABASE_SERVICE_ROLE_KEY=your-service-role-key")
        
        print("\n🔧 Setup Steps:")
        print("1. Create a Supabase project at https://supabase.com")
        print("2. Go to Settings > API to get your keys")
        print("3. Create a 'resumes' bucket in Storage section")
        print("4. Set bucket to Private (not public)")
        print("5. Run the SQL policies (see SUPABASE_STORAGE_INTEGRATION.md)")
        
        return False
    else:
        print("✅ All environment variables are set!")
        print("\n🎯 Next steps:")
        print("1. Make sure you've created the 'resumes' bucket in Supabase")
        print("2. Set up the SQL policies (see documentation)")
        print("3. Test the integration by uploading a resume")
        
        return True

def test_connection():
    """Test Supabase connection"""
    try:
        # Add backend to path
        sys.path.append(str(Path(__file__).parent / "backend"))
        
        from services.supabase_storage_service import SupabaseStorageService
        
        print("\n🔗 Testing Supabase connection...")
        storage_service = SupabaseStorageService()
        health = storage_service.health_check()
        
        if health["status"] == "healthy":
            print(f"✅ Connected successfully to bucket: {health['bucket_name']}")
            return True
        else:
            print(f"❌ Connection failed: {health.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def print_sql_policies():
    """Print SQL policies for setup"""
    print("\n📋 SQL Policies to run in Supabase SQL Editor:")
    print("-" * 50)
    
    sql_policies = '''
-- Create the resumes bucket (if not exists)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('resumes', 'resumes', false, 10485760, '{"application/pdf"}')
ON CONFLICT (id) DO NOTHING;

-- Allow users to upload their own resumes
CREATE POLICY "Users can upload their own resumes" ON storage.objects
FOR INSERT WITH CHECK (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to view their own resumes
CREATE POLICY "Users can view their own resumes" ON storage.objects
FOR SELECT USING (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to delete their own resumes
CREATE POLICY "Users can delete their own resumes" ON storage.objects
FOR DELETE USING (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);

-- Allow users to update their own resumes
CREATE POLICY "Users can update their own resumes" ON storage.objects
FOR UPDATE USING (
  bucket_id = 'resumes' AND
  auth.uid()::text = (storage.foldername(name))[1]
);
'''
    
    print(sql_policies)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--sql":
        print_sql_policies()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        env_ok = print_setup_instructions()
        if env_ok:
            test_connection()
    else:
        env_ok = print_setup_instructions()
        
        if env_ok:
            print("\n🧪 Run 'python setup_supabase.py --test' to test connection")
            print("🔧 Run 'python setup_supabase.py --sql' to see SQL policies")
        
        sys.exit(0 if env_ok else 1)