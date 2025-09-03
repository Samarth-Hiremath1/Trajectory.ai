-- Fix Supabase Security and Performance Issues
-- This script addresses all the warnings from Supabase security advisor

-- 1. CRITICAL: Enable RLS on tasks table
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- 2. Create optimized RLS policies for tasks table
-- Using (select auth.uid()) instead of auth.uid() for better performance
CREATE POLICY "Users can view own tasks" ON tasks
    FOR SELECT USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can insert own tasks" ON tasks
    FOR INSERT WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update own tasks" ON tasks
    FOR UPDATE USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete own tasks" ON tasks
    FOR DELETE USING ((select auth.uid())::text = user_id);

-- 3. Fix function search path issues by recreating functions with SECURITY DEFINER and SET search_path
-- Drop and recreate the update_updated_at_column function with proper security
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

-- Create a function specifically for tasks completion timestamp
CREATE OR REPLACE FUNCTION set_task_completed_at()
RETURNS TRIGGER 
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
    NEW.completed_at = NOW();
  ELSIF NEW.status != 'completed' THEN
    NEW.completed_at = NULL;
  END IF;
  RETURN NEW;
END;
$$;

-- Recreate all the triggers that were dropped when we dropped the function
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_roadmaps_updated_date
  BEFORE UPDATE ON roadmaps
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Add trigger for tasks table if it has an updated_at column
-- This will only work if the tasks table has an updated_at column
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'tasks' AND column_name = 'updated_at'
  ) THEN
    EXECUTE 'CREATE TRIGGER update_tasks_updated_at
      BEFORE UPDATE ON tasks
      FOR EACH ROW
      EXECUTE FUNCTION update_updated_at_column()';
  END IF;
END $$;

-- Add trigger for task completion if tasks table has completed_at column
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_name = 'tasks' AND column_name = 'completed_at'
  ) THEN
    EXECUTE 'CREATE TRIGGER set_task_completed_at_trigger
      BEFORE UPDATE ON tasks
      FOR EACH ROW
      EXECUTE FUNCTION set_task_completed_at()';
  END IF;
END $$;

-- 4. Drop and recreate existing RLS policies with optimized auth function calls
-- This fixes the performance warnings about re-evaluating auth functions

-- Drop existing policies first
DROP POLICY IF EXISTS "test_policy" ON profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
DROP POLICY IF EXISTS "Users can delete own profile" ON profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;

DROP POLICY IF EXISTS "Users can view own resume" ON resumes;
DROP POLICY IF EXISTS "Users can insert own resume" ON resumes;
DROP POLICY IF EXISTS "Users can update own resume" ON resumes;
DROP POLICY IF EXISTS "Users can delete own resume" ON resumes;

DROP POLICY IF EXISTS "Users can view own roadmaps" ON roadmaps;
DROP POLICY IF EXISTS "Users can insert own roadmaps" ON roadmaps;
DROP POLICY IF EXISTS "Users can update own roadmaps" ON roadmaps;
DROP POLICY IF EXISTS "Users can delete own roadmaps" ON roadmaps;

DROP POLICY IF EXISTS "Users can view own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can insert own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can update own chat sessions" ON chat_sessions;
DROP POLICY IF EXISTS "Users can delete own chat sessions" ON chat_sessions;

-- Create optimized policies for profiles
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete own profile" ON profiles
    FOR DELETE USING ((select auth.uid())::text = user_id);

-- Create optimized policies for resumes
CREATE POLICY "Users can view own resume" ON resumes
    FOR SELECT USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can insert own resume" ON resumes
    FOR INSERT WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update own resume" ON resumes
    FOR UPDATE USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete own resume" ON resumes
    FOR DELETE USING ((select auth.uid())::text = user_id);

-- Create optimized policies for roadmaps
CREATE POLICY "Users can view own roadmaps" ON roadmaps
    FOR SELECT USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can insert own roadmaps" ON roadmaps
    FOR INSERT WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update own roadmaps" ON roadmaps
    FOR UPDATE USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete own roadmaps" ON roadmaps
    FOR DELETE USING ((select auth.uid())::text = user_id);

-- Create optimized policies for chat_sessions
CREATE POLICY "Users can view own chat sessions" ON chat_sessions
    FOR SELECT USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can insert own chat sessions" ON chat_sessions
    FOR INSERT WITH CHECK ((select auth.uid())::text = user_id);

CREATE POLICY "Users can update own chat sessions" ON chat_sessions
    FOR UPDATE USING ((select auth.uid())::text = user_id);

CREATE POLICY "Users can delete own chat sessions" ON chat_sessions
    FOR DELETE USING ((select auth.uid())::text = user_id);

-- 5. Update storage policies to use optimized auth function calls
DROP POLICY IF EXISTS "Users can upload own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can update own resumes" ON storage.objects;
DROP POLICY IF EXISTS "Users can delete own resumes" ON storage.objects;

CREATE POLICY "Users can upload own resumes" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = (select auth.uid())::text
    );

CREATE POLICY "Users can view own resumes" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = (select auth.uid())::text
    );

CREATE POLICY "Users can update own resumes" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = (select auth.uid())::text
    );

CREATE POLICY "Users can delete own resumes" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'resumes' AND 
        (storage.foldername(name))[1] = (select auth.uid())::text
    );

-- 6. Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'Security fixes applied successfully!';
  RAISE NOTICE '1. RLS enabled on tasks table';
  RAISE NOTICE '2. Functions recreated with proper search_path';
  RAISE NOTICE '3. RLS policies optimized for performance';
  RAISE NOTICE '4. Storage policies updated';
END $$;