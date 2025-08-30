#!/usr/bin/env python3
"""
Quick test status checker for Supabase Storage Integration
Provides a fast overview of system readiness
"""
import os
import sys
from pathlib import Path

def check_environment_variables():
    """Check if required environment variables are set"""
    required_vars = {
        "SUPABASE_URL": "Supabase project URL",
        "SUPABASE_ANON_KEY": "Supabase anonymous key", 
        "SUPABASE_SERVICE_ROLE_KEY": "Supabase service role key",
        "STORAGE_PROVIDER": "Storage provider setting"
    }
    
    print("🔧 Environment Variables")
    print("-" * 25)
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Show partial value for security
            display_value = value[:20] + "..." if len(value) > 20 else value
            if var == "STORAGE_PROVIDER":
                display_value = value  # Show full value for this one
            print(f"✅ {var:<25} {display_value}")
        else:
            print(f"❌ {var:<25} Not set")
            all_set = False
    
    return all_set

def check_test_files():
    """Check if test files exist"""
    test_files = {
        "backend/tests/test_supabase_storage_integration.py": "Unit tests",
        "backend/tests/test_e2e_storage_integration.py": "E2E tests",
        "test_storage_integration.py": "Integration script",
        "setup_supabase.py": "Setup script",
        "run_storage_tests.py": "Test runner"
    }
    
    print("\n📁 Test Files")
    print("-" * 15)
    
    all_exist = True
    for file_path, description in test_files.items():
        if Path(file_path).exists():
            print(f"✅ {description:<20} {file_path}")
        else:
            print(f"❌ {description:<20} {file_path} (missing)")
            all_exist = False
    
    return all_exist

def check_dependencies():
    """Check if required dependencies are available"""
    dependencies = {
        "pytest": "Testing framework",
        "pytest-asyncio": "Async test support",
        "supabase": "Supabase client",
        "pdfplumber": "PDF processing",
        "chromadb": "Vector database"
    }
    
    print("\n📦 Dependencies")
    print("-" * 15)
    
    all_available = True
    for package, description in dependencies.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {description:<20} {package}")
        except ImportError:
            print(f"❌ {description:<20} {package} (not installed)")
            all_available = False
    
    return all_available

def check_backend_services():
    """Check if backend services can be imported"""
    services = {
        "services.supabase_storage_service": "Supabase Storage Service",
        "services.storage_quota_manager": "Storage Quota Manager", 
        "services.resume_service": "Resume Processing Service"
    }
    
    print("\n🔧 Backend Services")
    print("-" * 20)
    
    # Add backend to path
    backend_path = Path("backend")
    if backend_path.exists():
        sys.path.insert(0, str(backend_path))
    
    all_importable = True
    for module, description in services.items():
        try:
            __import__(module)
            print(f"✅ {description:<25} {module}")
        except ImportError as e:
            print(f"❌ {description:<25} {module} ({e})")
            all_importable = False
    
    return all_importable

def get_quick_recommendations():
    """Get quick recommendations based on status"""
    recommendations = []
    
    # Check environment
    if not check_environment_variables():
        recommendations.append("Set missing environment variables in backend/.env")
    
    # Check if we can run basic tests
    if not Path("backend/tests/test_supabase_storage_integration.py").exists():
        recommendations.append("Run the integration setup to create test files")
    
    # Check if we can run E2E tests
    if not os.getenv("SUPABASE_URL"):
        recommendations.append("Set up Supabase project and add credentials for E2E tests")
    
    return recommendations

def main():
    print("🚀 Supabase Storage Integration - Test Status Check")
    print("=" * 55)
    
    # Run all checks
    env_ok = check_environment_variables()
    files_ok = check_test_files()
    deps_ok = check_dependencies()
    services_ok = check_backend_services()
    
    # Overall status
    print("\n" + "=" * 55)
    print("📊 Overall Status")
    print("=" * 55)
    
    if env_ok and files_ok and deps_ok and services_ok:
        print("🎉 ALL SYSTEMS GO! Ready to run comprehensive tests.")
        print("\n🚀 Next steps:")
        print("   python run_storage_tests.py")
        return 0
    else:
        print("⚠️ Some components need attention before running tests.")
        
        recommendations = get_quick_recommendations()
        if recommendations:
            print("\n💡 Quick fixes:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n🔧 Detailed setup:")
        print("   python setup_supabase.py")
        print("   python run_storage_tests.py --setup-only")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())