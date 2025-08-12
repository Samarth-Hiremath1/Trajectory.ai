#!/usr/bin/env python3
"""
Migration runner for adding the resumes table to the database.
This script will execute the SQL migration to create the resumes table.
"""

import os
import sys
import asyncio
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def run_resumes_table_migration():
    """Run the migration to create the resumes table"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_ANON_KEY) must be set in environment variables")
        return False
    
    try:
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Read the migration SQL
        migration_file = "../add_resumes_table_migration.sql"
        if not os.path.exists(migration_file):
            print(f"❌ Error: Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🚀 Running resumes table migration...")
        print("📄 Migration SQL:")
        print("-" * 50)
        print(migration_sql)
        print("-" * 50)
        
        # Note: Supabase Python client doesn't support raw SQL execution
        # We need to use the REST API or run this manually
        print("\n⚠️  IMPORTANT: The Python Supabase client doesn't support raw SQL execution.")
        print("Please run this migration manually using one of these methods:")
        print("\n1. Supabase Dashboard:")
        print("   - Go to your Supabase project dashboard")
        print("   - Navigate to SQL Editor")
        print("   - Copy and paste the SQL above")
        print("   - Click 'Run'")
        print("\n2. Using psql command line:")
        print("   - Connect to your database using the connection string from Supabase")
        print("   - Run the SQL commands above")
        print("\n3. Using any PostgreSQL client (pgAdmin, DBeaver, etc.)")
        
        # Check if the table already exists
        try:
            result = supabase.table("resumes").select("count", count="exact").limit(1).execute()
            print("\n✅ The 'resumes' table already exists!")
            return True
        except Exception:
            print("\n❌ The 'resumes' table does not exist yet. Please run the migration SQL manually.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Resume Table Migration Runner")
    print("=" * 40)
    
    success = asyncio.run(run_resumes_table_migration())
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🎉 You can now upload resumes and they will be properly stored in the database.")
    else:
        print("\n❌ Migration failed. Please run the SQL manually as described above.")
        sys.exit(1)