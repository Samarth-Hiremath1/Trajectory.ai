"""
Migration script to create agent system tables
"""
import os
import logging
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_agent_migration():
    """Run the agent system database migration"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables")
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Connected to Supabase")
        
        # Read the SQL migration file
        with open("create_agent_tables.sql", "r") as f:
            sql_content = f.read()
        
        logger.info("Loaded agent tables SQL migration")
        
        # Execute the migration
        # Note: Supabase Python client doesn't support raw SQL execution directly
        # This would typically be run through the Supabase dashboard or CLI
        logger.info("Agent tables migration SQL loaded successfully")
        logger.info("Please run the following SQL in your Supabase dashboard:")
        logger.info("=" * 50)
        print(sql_content)
        logger.info("=" * 50)
        
        logger.info("Agent migration preparation completed")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_agent_migration()