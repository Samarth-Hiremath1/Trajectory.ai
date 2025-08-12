#!/usr/bin/env python3
"""
Migration runner for adding the tasks table to the database.
This script will provide instructions for running the SQL migration to create the tasks table.
"""

import os
import sys
from services.database_service import DatabaseService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_tasks_table_migration():
    """Run the migration to create the tasks table"""
    
    try:
        # Create database service to test connection
        db_service = DatabaseService()
        
        # Read the migration SQL
        migration_file = "../add_tasks_table_migration.sql"
        if not os.path.exists(migration_file):
            print(f"❌ Error: Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🚀 Tasks Table Migration")
        print("=" * 40)
        print("📄 Migration SQL:")
        print("-" * 50)
        print(migration_sql)
        print("-" * 50)
        
        print("\n⚠️  IMPORTANT: Please run this migration manually using one of these methods:")
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
            result = db_service.supabase.table("tasks").select("count", count="exact").limit(1).execute()
            print("\n✅ The 'tasks' table already exists!")
            print(f"Current task count: {result.count}")
            return True
        except Exception:
            print("\n❌ The 'tasks' table does not exist yet. Please run the migration SQL manually.")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Tasks Table Migration Runner")
    print("=" * 40)
    
    success = run_tasks_table_migration()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("🎉 You can now use the task management system.")
    else:
        print("\n❌ Migration needed. Please run the SQL manually as described above.")
        print("\n📝 After running the migration, you can test the task system with:")
        print("   python test_task_system.py")
        sys.exit(1)