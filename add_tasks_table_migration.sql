-- Migration: Add tasks table for enhanced to-do functionality
-- This table supports both roadmap-generated tasks and manually created tasks

CREATE TABLE IF NOT EXISTS tasks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  roadmap_id UUID REFERENCES roadmaps(id) ON DELETE CASCADE,
  title TEXT NOT NULL CHECK (length(title) >= 1 AND length(title) <= 200),
  description TEXT CHECK (length(description) <= 1000),
  status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'cancelled')),
  priority TEXT DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
  task_type TEXT DEFAULT 'manual' CHECK (task_type IN ('milestone', 'learning', 'practice', 'skill', 'manual')),
  
  -- Roadmap-specific fields
  phase_number INTEGER,
  milestone_index INTEGER,
  skill_name TEXT,
  
  -- Scheduling and tracking
  due_date TIMESTAMP WITH TIME ZONE,
  estimated_hours INTEGER CHECK (estimated_hours >= 0 AND estimated_hours <= 1000),
  actual_hours INTEGER CHECK (actual_hours >= 0 AND actual_hours <= 1000),
  
  -- Metadata
  tags TEXT[] DEFAULT '{}',
  metadata JSONB DEFAULT '{}',
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS tasks_user_id_idx ON tasks(user_id);
CREATE INDEX IF NOT EXISTS tasks_roadmap_id_idx ON tasks(roadmap_id);
CREATE INDEX IF NOT EXISTS tasks_status_idx ON tasks(status);
CREATE INDEX IF NOT EXISTS tasks_priority_idx ON tasks(priority);
CREATE INDEX IF NOT EXISTS tasks_task_type_idx ON tasks(task_type);
CREATE INDEX IF NOT EXISTS tasks_due_date_idx ON tasks(due_date);
CREATE INDEX IF NOT EXISTS tasks_created_at_idx ON tasks(created_at);

-- Create composite indexes for common queries
CREATE INDEX IF NOT EXISTS tasks_user_status_idx ON tasks(user_id, status);
CREATE INDEX IF NOT EXISTS tasks_user_priority_idx ON tasks(user_id, priority);
CREATE INDEX IF NOT EXISTS tasks_user_roadmap_idx ON tasks(user_id, roadmap_id);

-- Create trigger to automatically update updated_at timestamp
CREATE TRIGGER update_tasks_updated_at
  BEFORE UPDATE ON tasks
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to automatically set completed_at when status changes to completed
CREATE OR REPLACE FUNCTION set_task_completed_at()
RETURNS TRIGGER AS $$
BEGIN
  -- Set completed_at when status changes to completed
  IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
    NEW.completed_at = NOW();
  -- Clear completed_at when status changes from completed to something else
  ELSIF NEW.status != 'completed' AND OLD.status = 'completed' THEN
    NEW.completed_at = NULL;
  END IF;
  
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER set_tasks_completed_at
  BEFORE UPDATE ON tasks
  FOR EACH ROW
  EXECUTE FUNCTION set_task_completed_at();

-- Add some helpful comments
COMMENT ON TABLE tasks IS 'Career development tasks and to-do items, supporting both roadmap-generated and manually created tasks';
COMMENT ON COLUMN tasks.roadmap_id IS 'Optional reference to roadmap - NULL for manually created tasks';
COMMENT ON COLUMN tasks.phase_number IS 'Phase number from roadmap (for roadmap-generated tasks)';
COMMENT ON COLUMN tasks.milestone_index IS 'Milestone index within phase (for milestone tasks)';
COMMENT ON COLUMN tasks.skill_name IS 'Skill name (for skill development tasks)';
COMMENT ON COLUMN tasks.tags IS 'Array of tags for categorization and filtering';
COMMENT ON COLUMN tasks.metadata IS 'Additional metadata in JSON format';