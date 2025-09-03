#!/usr/bin/env python3
"""
Fix Resume Upload Issue

This script addresses the RLS policy violation for the resumes table by:
1. Creating the resumes table if it doesn't exist
2. Setting up proper RLS policies
3. Testing the connection

Run this script to fix the resume upload issue.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def print_sql_to_run():
    """Print the SQL that needs to be run in Supabase"""
    print("🔧 Resume Upload Fix - SQL to run in Supabase SQL Editor")
    print("=" * 60)
    
    sql_script = '''
-- Step 1: Create the resumes table if it doesn't exist
CREATE TABLE IF NOT EXISTS resumes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  file_path TEXT,
  file_size INTEGER,
  content_type TEXT DEFAULT 'application/pdf',
  parsed_content JSONB DEFAULT '{}',
  text_chunks TEXT[] DEFAULT '{}',
  processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  processed_date TIMESTAMP WITH TIME ZONE,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Step 2: Create indexes for performance
CREATE INDEX IF NOT EXISTS resumes_user_id_idx ON resumes(user_id);
CREATE INDEX IF NOT EXISTS resumes_processing_status_idx ON resumes(processing_status);
CREATE INDEX IF NOT EXISTS resumes_upload_date_idx ON resumes(upload_date);

-- Step 3: Create update trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 4: Create trigger for automatic updated_at
DROP TRIGGER IF EXISTS update_resumes_updated_at ON resumes;
CREATE TRIGGER update_resumes_updated_at
  BEFORE UPDATE ON resumes
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Step 5: Enable RLS on resumes table
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

-- Step 6: Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can view own resume" ON resumes;
DROP POLICY IF EXISTS "Users can insert own resume" ON resumes;
DROP POLICY IF EXISTS "Users can update own resume" ON resumes;
DROP POLICY IF EXISTS "Users can delete own resume" ON resumes;

-- Step 7: Create RLS policies for resumes table
CREATE POLICY "Users can view own resume" ON resumes
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own resume" ON resumes
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own resume" ON resumes
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own resume" ON resumes
    FOR DELETE USING (auth.uid()::text = user_id);

-- Step 8: Ensure storage bucket exists
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('resumes', 'resumes', false, 10485760, '{"application/pdf"}')
ON CONFLICT (id) DO NOTHING;

-- Step 9: Drop existing storage policies if they exist
DROP POLICY IF EXISTS "Users can upload own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own resumes" ON storage.objects;

-- Step 10: Create storage policies
CREATE POLICY "Users can upload own resumes" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can view own resumes" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can update own resumes" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = auth.uid()::text
    );

CREATE POLICY "Users can delete own resumes" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = auth.uid()::text
    );
'''
    
    print(sql_script)
    print("\n" + "=" * 60)
    print("📋 Instructions:")
    print("1. Copy the SQL above")
    print("2. Go to your Supabase Dashboard > SQL Editor")
    print("3. Paste and run the SQL script")
    print("4. Test resume upload again")

def test_connection():
    """Test if we can connect to Supabase"""
    try:
        # Add backend to path
        sys.path.append(str(Path(__file__).parent / "backend"))
        
        from supabase import create_client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing Supabase credentials in environment variables")
            return False
        
        print("\n🔗 Testing Supabase connection...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Test if resumes table exists
        try:
            result = supabase.table("resumes").select("count", count="exact").limit(1).execute()
            print("✅ Resumes table exists and is accessible")
            return True
        except Exception as e:
            print(f"❌ Resumes table issue: {e}")
            print("   This confirms the table needs to be created/fixed")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def main():
    print("🚀 Resume Upload Issue Fix")
    print("=" * 40)
    
    # Check environment
    missing_vars = []
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nMake sure these are set in your backend/.env file")
        return
    
    # Test connection
    connection_ok = test_connection()
    
    # Always show the SQL to run
    print_sql_to_run()
    
    if connection_ok:
        print("\n✅ After running the SQL, your resume upload should work!")
    else:
        print("\n⚠️  Run the SQL above to create the missing resumes table and policies")

if __name__ == "__main__":
    main()