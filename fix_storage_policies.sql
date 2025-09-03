-- Fix Storage Policies for Resume Upload Issue
-- Run this in your Supabase SQL Editor

-- Step 1: Ensure storage bucket exists with correct settings
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('resumes', 'resumes', false, 10485760, '{"application/pdf","image/jpeg","image/png","text/plain"}')
ON CONFLICT (id) DO UPDATE SET
  file_size_limit = 10485760,
  allowed_mime_types = '{"application/pdf","image/jpeg","image/png","text/plain"}';

-- Step 2: Drop ALL existing storage policies to start fresh
DROP POLICY IF EXISTS "Users can upload own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated uploads" ON storage.objects;
DROP POLICY IF EXISTS "Allow authenticated reads" ON storage.objects;
DROP POLICY IF EXISTS "Allow service role access" ON storage.objects;

-- Step 3: Create comprehensive storage policies
-- Allow service role to do everything (for server-side operations)
CREATE POLICY "Service role full access" ON storage.objects
    FOR ALL USING (
        auth.role() = 'service_role'
    );

-- Allow authenticated users to upload to their own folder
CREATE POLICY "Users can upload to own folder" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'resumes' AND 
        auth.uid() IS NOT NULL AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to read their own files
CREATE POLICY "Users can read own files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'resumes' AND 
        auth.uid() IS NOT NULL AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to update their own files
CREATE POLICY "Users can update own files" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'resumes' AND 
        auth.uid() IS NOT NULL AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Allow authenticated users to delete their own files
CREATE POLICY "Users can delete own files" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'resumes' AND 
        auth.uid() IS NOT NULL AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Step 4: Verify bucket settings
SELECT 
    id, 
    name, 
    public, 
    file_size_limit, 
    allowed_mime_types 
FROM storage.buckets 
WHERE id = 'resumes';

-- Step 5: List all storage policies for verification
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'storage' AND tablename = 'objects'
ORDER BY policyname;