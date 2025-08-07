-- Migration script to change user_id from UUID to TEXT
-- This is needed because we're using NextAuth which uses string IDs

-- First, let's check if we have any existing data
-- If there's existing data, we'll need to handle it carefully

-- Drop existing foreign key constraints if any exist
-- (There shouldn't be any based on our schema, but just in case)

-- Alter profiles table
ALTER TABLE profiles 
ALTER COLUMN user_id TYPE TEXT;

-- Alter roadmaps table  
ALTER TABLE roadmaps
ALTER COLUMN user_id TYPE TEXT;

-- Alter chat_sessions table
ALTER TABLE chat_sessions
ALTER COLUMN user_id TYPE TEXT;

-- Recreate indexes (they should be automatically updated, but let's be explicit)
DROP INDEX IF EXISTS profiles_user_id_idx;
CREATE INDEX profiles_user_id_idx ON profiles(user_id);

DROP INDEX IF EXISTS roadmaps_user_id_idx;
CREATE INDEX roadmaps_user_id_idx ON roadmaps(user_id);

DROP INDEX IF EXISTS chat_sessions_user_id_idx;
CREATE INDEX chat_sessions_user_id_idx ON chat_sessions(user_id);

-- Verify the changes
SELECT 
    table_name, 
    column_name, 
    data_type 
FROM information_schema.columns 
WHERE table_name IN ('profiles', 'roadmaps', 'chat_sessions') 
    AND column_name = 'user_id';