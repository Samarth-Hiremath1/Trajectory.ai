#!/usr/bin/env python3
"""
Security setup script for Trajectory.AI backend
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from security.config import SecurityConfig
from security.auth import supabase_auth

logger = logging.getLogger(__name__)

async def setup_rls_policies():
    """Set up Row Level Security policies in Supabase"""
    print("🔒 Setting up Row Level Security policies...")
    
    try:
        # Read RLS policies from file
        rls_file = Path(__file__).parent / "security" / "rls_policies.sql"
        
        if not rls_file.exists():
            print("❌ RLS policies file not found")
            return False
        
        with open(rls_file, 'r') as f:
            rls_sql = f.read()
        
        print("📋 RLS Policies to apply:")
        print("-" * 50)
        print(rls_sql)
        print("-" * 50)
        
        print("\n⚠️  Please apply these policies manually in your Supabase SQL Editor:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the above SQL")
        print("4. Run the queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading RLS policies: {e}")
        return False

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    config_errors = SecurityConfig.validate_config()
    
    if config_errors:
        print("❌ Configuration errors found:")
        for error in config_errors:
            print(f"   - {error}")
        return False
    else:
        print("✅ All required environment variables are set")
        return True

def check_security_dependencies():
    """Check if security dependencies are installed"""
    print("📦 Checking security dependencies...")
    
    required_packages = [
        'bleach',
        'python-magic',
        'yara-python',
        'PyJWT',
        'cryptography',
        'redis'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing security dependencies:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    else:
        print("✅ All security dependencies are installed")
        return True

async def test_supabase_connection():
    """Test Supabase connection and authentication"""
    print("🔗 Testing Supabase connection...")
    
    try:
        # Test basic connection
        test_user_id = "test-user-id"
        user_info = await supabase_auth.get_user_by_id(test_user_id)
        
        # This should return None for non-existent user, but not throw an error
        print("✅ Supabase connection successful")
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def check_file_permissions():
    """Check file permissions for security"""
    print("📁 Checking file permissions...")
    
    security_files = [
        "security/rls_policies.sql",
        "security/auth.py",
        "security/input_validation.py",
        "security/rate_limiting.py",
        "security/file_security.py"
    ]
    
    issues = []
    
    for file_path in security_files:
        full_path = Path(__file__).parent / file_path
        
        if not full_path.exists():
            issues.append(f"Missing file: {file_path}")
            continue
        
        # Check if file is readable
        if not os.access(full_path, os.R_OK):
            issues.append(f"File not readable: {file_path}")
        
        # Check if file is not world-writable (security risk)
        stat_info = full_path.stat()
        if stat_info.st_mode & 0o002:  # World writable
            issues.append(f"File is world-writable (security risk): {file_path}")
    
    if issues:
        print("❌ File permission issues:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ File permissions are secure")
        return True

def print_security_summary():
    """Print security configuration summary"""
    print("\n📊 Security Configuration Summary:")
    print("=" * 50)
    
    summary = SecurityConfig.get_security_summary()
    
    for key, value in summary.items():
        if key == "validation_errors" and value:
            print(f"❌ {key}: {len(value)} errors")
        else:
            print(f"✅ {key}: {value}")

def print_next_steps():
    """Print next steps for security setup"""
    print("\n🚀 Next Steps:")
    print("=" * 30)
    print("1. Apply RLS policies in Supabase SQL Editor")
    print("2. Configure environment variables for production")
    print("3. Set up Redis for rate limiting (optional)")
    print("4. Install ClamAV for virus scanning (optional)")
    print("5. Configure monitoring and alerting")
    print("6. Review and test all security measures")
    print("\n💡 Security Best Practices:")
    print("- Regularly update dependencies")
    print("- Monitor security logs")
    print("- Conduct security audits")
    print("- Keep environment variables secure")
    print("- Use HTTPS in production")

async def main():
    """Main setup function"""
    print("🛡️  Trajectory.AI Security Setup")
    print("=" * 40)
    
    checks = [
        ("Environment Variables", check_environment_variables()),
        ("Security Dependencies", check_security_dependencies()),
        ("File Permissions", check_file_permissions()),
        ("Supabase Connection", await test_supabase_connection()),
        ("RLS Policies", await setup_rls_policies())
    ]
    
    all_passed = True
    
    for check_name, result in checks:
        if not result:
            all_passed = False
    
    print_security_summary()
    
    if all_passed:
        print("\n🎉 Security setup completed successfully!")
        print("✅ All security checks passed")
    else:
        print("\n⚠️  Security setup needs attention")
        print("❌ Some checks failed - please review above")
    
    print_next_steps()
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run setup
    exit_code = asyncio.run(main())
    sys.exit(exit_code)