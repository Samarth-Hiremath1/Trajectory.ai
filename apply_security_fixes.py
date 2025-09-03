#!/usr/bin/env python3
"""
Apply Supabase Security Fixes

This script applies the security fixes to address Supabase security advisor warnings.
Run this script to fix:
1. RLS not enabled on tasks table
2. Function search path issues
3. Performance issues with RLS policies
"""

import os
import sys
from pathlib import Path

def main():
    """Apply security fixes to Supabase database."""
    
    print("🔒 Applying Supabase Security Fixes...")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend/security/fix_security_issues.sql").exists():
        print("❌ Error: Security fix file not found!")
        print("Make sure you're running this from the project root directory.")
        sys.exit(1)
    
    print("📋 Security issues to be fixed:")
    print("1. ✅ Enable RLS on tasks table")
    print("2. ✅ Fix function search path issues")
    print("3. ✅ Optimize RLS policies for performance")
    print("4. ✅ Update storage policies")
    print("5. ⚠️  Enable leaked password protection (manual)")
    print()
    
    print("🚀 To apply these fixes:")
    print("1. Copy the contents of 'backend/security/fix_security_issues.sql'")
    print("2. Go to your Supabase Dashboard > SQL Editor")
    print("3. Paste and run the SQL script")
    print()
    
    print("📖 Additional manual steps:")
    print("1. Go to Supabase Dashboard > Authentication > Settings")
    print("2. Enable 'Leaked Password Protection'")
    print("3. Review and adjust other auth security settings as needed")
    print()
    
    # Show the SQL file path
    sql_file = Path("backend/security/fix_security_issues.sql").resolve()
    print(f"📄 SQL file location: {sql_file}")
    
    # Optionally show the SQL content
    response = input("\n🤔 Would you like to see the SQL content? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        print("\n" + "=" * 60)
        print("SQL CONTENT:")
        print("=" * 60)
        with open(sql_file, 'r') as f:
            print(f.read())
    
    print("\n✅ Security fix script is ready!")
    print("Apply it in your Supabase Dashboard SQL Editor.")

if __name__ == "__main__":
    main()