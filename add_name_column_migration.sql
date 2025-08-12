-- Migration to add name column to profiles table
-- Run this against your Supabase database

ALTER TABLE profiles ADD COLUMN IF NOT EXISTS name TEXT;

-- Update any existing profiles to have a default name if needed
-- (This is optional - you can remove this if you want existing profiles to have NULL names)
UPDATE profiles SET name = 'User' WHERE name IS NULL;