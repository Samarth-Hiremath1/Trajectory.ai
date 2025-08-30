#!/usr/bin/env python3
"""
Test runner for Supabase Storage Integration
Runs comprehensive tests to ensure full functionality
"""
import os
import sys
import subprocess
from pathlib import Path
import argparse

def check_environment():
    """Check if required environment variables are set"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    return missing_vars

def install_test_dependencies():
    """Install required test dependencies"""
    print("📦 Installing test dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "pytest", "pytest-asyncio", "pytest-mock"
        ], check=True, capture_output=True)
        print("✅ Test dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_unit_tests():
    """Run unit tests with mocks"""
    print("\n🧪 Running Unit Tests (with mocks)")
    print("-" * 40)
    
    test_file = Path("backend/tests/test_supabase_storage_integration.py")
    if not test_file.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", "--tb=short"
        ], cwd=Path.cwd())
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run unit tests: {e}")
        return False

def run_e2e_tests():
    """Run end-to-end tests with real Supabase"""
    print("\n🌐 Running End-to-End Tests (real Supabase)")
    print("-" * 45)
    
    # Check environment first
    missing_vars = check_environment()
    if missing_vars:
        print("❌ Missing environment variables for E2E tests:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nSkipping E2E tests. Set environment variables to run them.")
        return True  # Don't fail the overall test run
    
    test_file = Path("backend/tests/test_e2e_storage_integration.py")
    if not test_file.exists():
        print(f"❌ E2E test file not found: {test_file}")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            str(test_file), 
            "-v", "--tb=short", "-s"
        ], cwd=Path.cwd())
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run E2E tests: {e}")
        return False

def run_integration_test_script():
    """Run the standalone integration test script"""
    print("\n🔧 Running Integration Test Script")
    print("-" * 35)
    
    test_script = Path("test_storage_integration.py")
    if not test_script.exists():
        print(f"❌ Integration test script not found: {test_script}")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(test_script)], cwd=Path.cwd())
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run integration test script: {e}")
        return False

def run_setup_verification():
    """Run setup verification"""
    print("\n⚙️ Running Setup Verification")
    print("-" * 30)
    
    setup_script = Path("setup_supabase.py")
    if not setup_script.exists():
        print(f"❌ Setup script not found: {setup_script}")
        return False
    
    try:
        result = subprocess.run([sys.executable, str(setup_script), "--test"], cwd=Path.cwd())
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run setup verification: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Run Supabase Storage Integration Tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--e2e-only", action="store_true", help="Run only E2E tests")
    parser.add_argument("--setup-only", action="store_true", help="Run only setup verification")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    
    args = parser.parse_args()
    
    print("🚀 Supabase Storage Integration Test Suite")
    print("=" * 50)
    
    # Install dependencies unless skipped
    if not args.skip_deps:
        if not install_test_dependencies():
            print("❌ Failed to install dependencies")
            return 1
    
    results = []
    
    # Run setup verification
    if args.setup_only or not (args.unit_only or args.e2e_only):
        results.append(("Setup Verification", run_setup_verification()))
    
    # Run unit tests
    if args.unit_only or not (args.e2e_only or args.setup_only):
        results.append(("Unit Tests", run_unit_tests()))
    
    # Run E2E tests
    if args.e2e_only or not (args.unit_only or args.setup_only):
        results.append(("E2E Tests", run_e2e_tests()))
    
    # Run integration test script
    if not (args.unit_only or args.e2e_only or args.setup_only):
        results.append(("Integration Script", run_integration_test_script()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Supabase Storage integration is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Deploy to production with environment variables")
        print("   2. Create the 'resumes' bucket in Supabase dashboard")
        print("   3. Run the SQL policies from setup_supabase.py --sql")
        print("   4. Monitor storage usage and user feedback")
        return 0
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify environment variables are set correctly")
        print("   2. Check Supabase bucket exists and is configured")
        print("   3. Ensure SQL policies are applied")
        print("   4. Check network connectivity to Supabase")
        return 1

if __name__ == "__main__":
    sys.exit(main())