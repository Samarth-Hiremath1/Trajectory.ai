-- Disable RLS for Storage Objects to Fix Resume Upload
-- This is a temporary fix to get resume uploads working
-- Run this in your Supabase SQL Editor

-- Disable RLS on storage.objects table entirely
ALTER TABLE storage.objects DISABLE ROW LEVEL SECURITY;

-- Verify RLS is disabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'storage' AND tablename = 'objects';