-- Add resumes table for storing resume metadata and content
CREATE TABLE IF NOT EXISTS resumes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  file_path TEXT,
  file_size INTEGER,
  content_type TEXT DEFAULT 'application/pdf',
  parsed_content JSONB DEFAULT '{}',
  text_chunks JSONB DEFAULT '[]',
  processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
  error_message TEXT,
  upload_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  processed_date TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id) -- Only one resume per user for now
);

-- Create indexes for resumes
CREATE INDEX IF NOT EXISTS resumes_user_id_idx ON resumes(user_id);
CREATE INDEX IF NOT EXISTS resumes_processing_status_idx ON resumes(processing_status);
CREATE INDEX IF NOT EXISTS resumes_upload_date_idx ON resumes(upload_date);

-- Create trigger to automatically update updated_at for resumes
CREATE TRIGGER update_resumes_updated_at
  BEFORE UPDATE ON resumes
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();