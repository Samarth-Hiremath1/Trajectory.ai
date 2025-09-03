-- Auth Security Configuration
-- This script configures additional security settings for Supabase Auth

-- Note: Some of these settings need to be configured through the Supabase Dashboard
-- or using the Management API, not through SQL

-- This is a reference for the settings that should be enabled:

/*
LEAKED PASSWORD PROTECTION:
- Go to Supabase Dashboard > Authentication > Settings
- Enable "Leaked Password Protection"
- This will check passwords against HaveIBeenPwned.org

ADDITIONAL RECOMMENDED AUTH SETTINGS:
1. Password Requirements:
   - Minimum length: 8 characters
   - Require uppercase letters
   - Require lowercase letters  
   - Require numbers
   - Require special characters

2. Session Settings:
   - JWT expiry: 3600 seconds (1 hour)
   - Refresh token rotation: Enabled
   - Refresh token reuse interval: 10 seconds

3. Rate Limiting:
   - Enable rate limiting for auth endpoints
   - Max requests per hour: 30 for signup/signin

4. Email Settings:
   - Enable email confirmations
   - Enable secure email change flow
   - Set appropriate email templates

5. Security Headers:
   - Enable CORS for your domain only
   - Set appropriate CSP headers
*/

-- SQL-configurable security settings:

-- Ensure auth schema has proper permissions
GRANT USAGE ON SCHEMA auth TO authenticated;

-- Create a function to validate password strength (if needed for custom validation)
CREATE OR REPLACE FUNCTION validate_password_strength(password TEXT)
RETURNS BOOLEAN
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
BEGIN
  -- Check minimum length
  IF LENGTH(password) < 8 THEN
    RETURN FALSE;
  END IF;
  
  -- Check for uppercase letter
  IF password !~ '[A-Z]' THEN
    RETURN FALSE;
  END IF;
  
  -- Check for lowercase letter
  IF password !~ '[a-z]' THEN
    RETURN FALSE;
  END IF;
  
  -- Check for number
  IF password !~ '[0-9]' THEN
    RETURN FALSE;
  END IF;
  
  -- Check for special character
  IF password !~ '[^A-Za-z0-9]' THEN
    RETURN FALSE;
  END IF;
  
  RETURN TRUE;
END;
$$;

-- Create audit log table for security events (optional)
CREATE TABLE IF NOT EXISTS security_audit_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id TEXT,
  event_type TEXT NOT NULL,
  event_details JSONB DEFAULT '{}',
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for audit log
CREATE INDEX IF NOT EXISTS security_audit_log_user_id_idx ON security_audit_log(user_id);
CREATE INDEX IF NOT EXISTS security_audit_log_event_type_idx ON security_audit_log(event_type);
CREATE INDEX IF NOT EXISTS security_audit_log_created_at_idx ON security_audit_log(created_at);

-- Enable RLS on audit log
ALTER TABLE security_audit_log ENABLE ROW LEVEL SECURITY;

-- Only allow users to view their own audit logs
CREATE POLICY "Users can view own audit logs" ON security_audit_log
    FOR SELECT USING ((select auth.uid())::text = user_id);

-- Function to log security events
CREATE OR REPLACE FUNCTION log_security_event(
  p_user_id TEXT,
  p_event_type TEXT,
  p_event_details JSONB DEFAULT '{}',
  p_ip_address INET DEFAULT NULL,
  p_user_agent TEXT DEFAULT NULL
)
RETURNS UUID
SECURITY DEFINER
SET search_path = public
LANGUAGE plpgsql AS $$
DECLARE
  log_id UUID;
BEGIN
  INSERT INTO security_audit_log (user_id, event_type, event_details, ip_address, user_agent)
  VALUES (p_user_id, p_event_type, p_event_details, p_ip_address, p_user_agent)
  RETURNING id INTO log_id;
  
  RETURN log_id;
END;
$$;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'Auth security configuration completed!';
  RAISE NOTICE 'Remember to enable leaked password protection in Supabase Dashboard';
  RAISE NOTICE 'Security audit logging is now available';
END $$;