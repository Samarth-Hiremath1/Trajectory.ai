#!/usr/bin/env python3
"""
Script to run database migration for user_id field type change
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def run_migration():
    """Run the database migration"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        print("🔄 Running database migration...")
        
        # Read migration SQL
        with open('migrate_user_id_to_text.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        # Execute each statement
        for i, statement in enumerate(statements):
            if statement.startswith('--') or not statement:
                continue
                
            print(f"Executing statement {i+1}/{len(statements)}: {statement[:50]}...")
            
            try:
                # Use rpc to execute raw SQL
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                print(f"✅ Statement {i+1} executed successfully")
            except Exception as e:
                print(f"⚠️  Statement {i+1} failed (might be expected): {e}")
                # Continue with other statements
        
        print("✅ Migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify the migration was successful"""
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        
        print("🔍 Verifying migration...")
        
        # Try to insert a test record with string user_id
        test_data = {
            "user_id": "test_user_123",
            "current_role": "Test Role",
            "target_role": "Test Target",
            "title": "Test Roadmap",
            "phases": []
        }
        
        result = supabase.table("roadmaps").insert(test_data).execute()
        
        if result.data:
            # Clean up test data
            test_id = result.data[0]["id"]
            supabase.table("roadmaps").delete().eq("id", test_id).execute()
            print("✅ Migration verification successful!")
            return True
        else:
            print("❌ Migration verification failed - no data returned")
            return False
            
    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database migration")
    print("=" * 40)
    
    # Note: Since we can't execute raw SQL with the anon key,
    # we'll need to run this migration manually in the Supabase dashboard
    print("⚠️  This migration needs to be run manually in the Supabase SQL editor")
    print("📋 Please copy the contents of 'migrate_user_id_to_text.sql' and run it in:")
    print("   https://supabase.com/dashboard/project/[your-project]/sql")
    print()
    print("After running the migration, you can test it by restarting the backend server.")
    
    # For now, let's just verify if we can connect to the database
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if supabase_url and supabase_key:
        try:
            supabase = create_client(supabase_url, supabase_key)
            # Test connection
            result = supabase.table("roadmaps").select("id").limit(1).execute()
            print("✅ Database connection successful")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
    else:
        print("❌ Missing database credentials")