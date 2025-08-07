-- Create profiles table for user career information
-- Updated to work with NextAuth instead of Supabase auth
CREATE TABLE IF NOT EXISTS profiles (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  education JSONB DEFAULT '{}',
  career_background TEXT,
  "current_role" TEXT,
  target_roles TEXT[] DEFAULT '{}',
  additional_details TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id)
);

-- Create an index on user_id for faster lookups
CREATE INDEX IF NOT EXISTS profiles_user_id_idx ON profiles(user_id);

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Create roadmaps table for career roadmap data
CREATE TABLE IF NOT EXISTS roadmaps (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  "current_role" TEXT NOT NULL,
  "target_role" TEXT NOT NULL,
  status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'completed', 'archived')),
  phases JSONB DEFAULT '[]',
  total_estimated_weeks INTEGER DEFAULT 1,
  overall_progress_percentage DECIMAL(5,2) DEFAULT 0.0 CHECK (overall_progress_percentage >= 0 AND overall_progress_percentage <= 100),
  current_phase INTEGER,
  generated_with_model TEXT,
  generation_prompt TEXT,
  user_context_used JSONB DEFAULT '{}',
  created_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_accessed_date TIMESTAMP WITH TIME ZONE
);

-- Create indexes for roadmaps
CREATE INDEX IF NOT EXISTS roadmaps_user_id_idx ON roadmaps(user_id);
CREATE INDEX IF NOT EXISTS roadmaps_status_idx ON roadmaps(status);
CREATE INDEX IF NOT EXISTS roadmaps_created_date_idx ON roadmaps(created_date);

-- Create chat_sessions table for AI chat conversations
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  title TEXT,
  messages JSONB DEFAULT '[]',
  context_version TEXT DEFAULT '1.0',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  metadata JSONB DEFAULT '{}'
);

-- Create indexes for chat_sessions
CREATE INDEX IF NOT EXISTS chat_sessions_user_id_idx ON chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS chat_sessions_is_active_idx ON chat_sessions(is_active);
CREATE INDEX IF NOT EXISTS chat_sessions_updated_at_idx ON chat_sessions(updated_at);

-- Create trigger to automatically update updated_at for roadmaps
CREATE TRIGGER update_roadmaps_updated_at
  BEFORE UPDATE ON roadmaps
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to automatically update updated_at for chat_sessions
CREATE TRIGGER update_chat_sessions_updated_at
  BEFORE UPDATE ON chat_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Note: RLS policies and automatic profile creation removed 
-- since we're using NextAuth instead of Supabase auth
-- Security will be handled at the application level
-- Profiles will be created manually through the onboarding flow