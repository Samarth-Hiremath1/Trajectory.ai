-- Row Level Security (RLS) Policies for Trajectory.AI
-- These policies ensure users can only access their own data

-- Enable RLS on existing tables only
-- Note: Only enable RLS on tables that exist in your database
-- Comment out or remove lines for tables that don't exist yet

-- Core tables (enable these first)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmaps ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_sessions ENABLE ROW LEVEL SECURITY;

-- Agent system tables (uncomment when these tables are created)
-- ALTER TABLE agent_requests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_responses ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_workflows ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agent_status ENABLE ROW LEVEL SECURITY;

-- Task management tables (uncomment when tasks table is created)
-- ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Profiles table policies
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own profile" ON profiles
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own profile" ON profiles
    FOR DELETE USING (auth.uid()::text = user_id);

-- Resumes table policies
CREATE POLICY "Users can view own resume" ON resumes
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own resume" ON resumes
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own resume" ON resumes
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own resume" ON resumes
    FOR DELETE USING (auth.uid()::text = user_id);

-- Roadmaps table policies
CREATE POLICY "Users can view own roadmaps" ON roadmaps
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own roadmaps" ON roadmaps
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own roadmaps" ON roadmaps
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own roadmaps" ON roadmaps
    FOR DELETE USING (auth.uid()::text = user_id);

-- Chat sessions table policies
CREATE POLICY "Users can view own chat sessions" ON chat_sessions
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own chat sessions" ON chat_sessions
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own chat sessions" ON chat_sessions
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own chat sessions" ON chat_sessions
    FOR DELETE USING (auth.uid()::text = user_id);

-- Tasks table policies (uncomment when tasks table is created)
/*
CREATE POLICY "Users can view own tasks" ON tasks
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own tasks" ON tasks
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own tasks" ON tasks
    FOR UPDATE USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete own tasks" ON tasks
    FOR DELETE USING (auth.uid()::text = user_id);
*/

-- Agent system table policies (uncomment when these tables are created)
/*
-- Agent requests table policies
CREATE POLICY "Users can view own agent requests" ON agent_requests
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert own agent requests" ON agent_requests
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update own agent requests" ON agent_requests
    FOR UPDATE USING (auth.uid()::text = user_id);

-- Agent responses table policies (users can view responses to their requests)
CREATE POLICY "Users can view responses to own requests" ON agent_responses
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_requests 
            WHERE agent_requests.id = agent_responses.request_id 
            AND agent_requests.user_id = auth.uid()::text
        )
    );

-- Agent workflows table policies (users can view workflows for their requests)
CREATE POLICY "Users can view workflows for own requests" ON agent_workflows
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_requests 
            WHERE agent_requests.id = agent_workflows.request_id 
            AND agent_requests.user_id = auth.uid()::text
        )
    );

-- Agent messages table policies
CREATE POLICY "Users can view messages for own requests" ON agent_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_workflows aw
            JOIN agent_requests ar ON aw.request_id = ar.id
            WHERE aw.id = agent_messages.workflow_id 
            AND ar.user_id = auth.uid()::text
        )
    );

-- Agent status table policies (admin-only, users can view status of their requests)
CREATE POLICY "Users can view agent status for own requests" ON agent_status
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM agent_requests 
            WHERE agent_requests.assigned_agents @> ARRAY[agent_status.agent_id]
            AND agent_requests.user_id = auth.uid()::text
        )
    );
*/

-- Storage bucket for resumes (create if it doesn't exist)
INSERT INTO storage.buckets (id, name, public) 
VALUES ('resumes', 'resumes', false)
ON CONFLICT (id) DO NOTHING;

-- Storage object policies
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