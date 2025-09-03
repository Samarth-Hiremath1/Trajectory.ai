-- Fix RLS Policies for Resume Upload Issue
-- Run this in your Supabase SQL Editor

-- Step 1: Enable RLS on resumes table (if not already enabled)
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;

-- Step 2: Drop existing policies if they exist (to avoid conflicts)
DROP POLICY IF EXISTS "Users can view own resume" ON resumes;
DROP POLICY IF EXISTS "Users can insert own resume" ON resumes;
DROP POLICY IF EXISTS "Users can update own resume" ON resumes;
DROP POLICY IF EXISTS "Users can delete own resume" ON resumes;

-- Step 3: Create RLS policies for resumes table
CREATE POLICY "Users can view own resume" ON resumes
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own resume" ON resumes
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own resume" ON resumes
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own resume" ON resumes
    FOR DELETE USING (auth.uid()::text = user_id);

-- Step 4: Ensure storage bucket exists
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('resumes', 'resumes', false, 10485760, '{"application/pdf"}')
ON CONFLICT (id) DO NOTHING;

-- Step 5: Drop existing storage policies if they exist
DROP POLICY IF EXISTS "Users can upload own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own resumes" ON storage.objects;

-- Step 6: Create storage policies
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