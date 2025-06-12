#!/usr/bin/env python3
"""
Quick Validation Script for Devin AI Integration
The HigherSelf Network Server - Fast Environment Validation

This script provides rapid validation of the development environment
for Devin's automated testing system.
"""

import importlib.util
import os
import sys
from pathlib import Path


def check_python_version():
    """Check Python version compatibility."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(
            f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+"
        )
        return False


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"✅ {description} - Found")
        return True
    else:
        print(f"❌ {description} - Missing")
        return False


def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if Path(dirpath).is_dir():
        print(f"✅ {description} - Found")
        return True
    else:
        print(f"❌ {description} - Missing")
        return False


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"✅ {description} - Available")
            return True
        else:
            print(f"❌ {description} - Not found")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False


def check_environment_variables():
    """Check critical environment variables."""
    critical_vars = [
        ("PYTHONPATH", "Python Path"),
    ]

    optional_vars = [
        ("TEST_MODE", "Test Mode"),
        ("DISABLE_WEBHOOKS", "Webhook Disable"),
        ("NOTION_API_TOKEN", "Notion API Token"),
    ]

    results = []

    print("\n🔍 Environment Variables Check:")
    for var, desc in critical_vars:
        if os.environ.get(var):
            print(f"✅ {desc} ({var}) - Set")
            results.append(True)
        else:
            print(f"⚠️  {desc} ({var}) - Not set (will be configured)")
            results.append(True)  # Not critical for basic validation

    for var, desc in optional_vars:
        if os.environ.get(var):
            print(f"✅ {desc} ({var}) - Set")
        else:
            print(f"ℹ️  {desc} ({var}) - Not set (optional)")

    return all(results)


def main():
    """Main validation function."""
    print("🚀 Devin Quick Validation - The HigherSelf Network Server")
    print("=" * 60)

    # Set PYTHONPATH to current directory
    current_dir = Path(__file__).parent
    os.environ["PYTHONPATH"] = str(current_dir)

    checks = []

    # Python version check
    print("\n🐍 Python Environment:")
    checks.append(check_python_version())

    # Core files check
    print("\n📁 Core Files:")
    checks.append(check_file_exists("main.py", "Main Application File"))
    checks.append(check_file_exists("requirements.txt", "Requirements File"))
    checks.append(check_file_exists("pyproject.toml", "Project Configuration"))
    checks.append(check_file_exists("run_tests.py", "Test Runner"))

    # Directory structure check
    print("\n📂 Directory Structure:")
    checks.append(check_directory_exists("agents", "Agents Directory"))
    checks.append(check_directory_exists("api", "API Directory"))
    checks.append(check_directory_exists("services", "Services Directory"))
    checks.append(check_directory_exists("models", "Models Directory"))
    checks.append(check_directory_exists("tests", "Tests Directory"))

    # Core imports check
    print("\n📦 Core Imports:")
    checks.append(check_import("pathlib", "Pathlib"))
    checks.append(check_import("json", "JSON"))
    checks.append(check_import("os", "OS"))
    checks.append(check_import("sys", "Sys"))

    # Project-specific imports (basic)
    print("\n🏗️  Project Imports (Basic):")
    try:
        # Test basic model imports
        from models.base import BaseModel

        print("✅ Base Models - Available")
        checks.append(True)
    except Exception as e:
        print(f"❌ Base Models - Error: {e}")
        checks.append(False)

    try:
        # Test settings import
        from config.settings import settings

        print("✅ Settings Configuration - Available")
        checks.append(True)
    except Exception as e:
        print(f"❌ Settings Configuration - Error: {e}")
        checks.append(False)

    # Environment variables check
    checks.append(check_environment_variables())

    # Test execution capability
    print("\n🧪 Test Execution Check:")
    try:
        import subprocess

        result = subprocess.run(
            ["python3", "-c", "print('Test execution works')"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print("✅ Test Execution - Working")
            checks.append(True)
        else:
            print(f"❌ Test Execution - Failed: {result.stderr}")
            checks.append(False)
    except Exception as e:
        print(f"❌ Test Execution - Error: {e}")
        checks.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(checks)
    total = len(checks)
    success_rate = (passed / total) * 100

    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("\n🎉 VALIDATION PASSED!")
        print("✅ Environment is ready for Devin integration")
        print("✅ You can proceed with automated testing")
        print("\n🚀 Next Steps:")
        print("   1. Run: python3 devin_automated_setup.py")
        print("   2. Or run: python3 run_tests.py")
        return 0
    elif success_rate >= 70:
        print("\n⚠️  VALIDATION PARTIALLY PASSED")
        print("🔧 Some issues detected but environment is mostly ready")
        print("📚 Check the failed items above and refer to documentation")
        return 1
    else:
        print("\n❌ VALIDATION FAILED")
        print("🚨 Critical issues detected - environment needs setup")
        print("📚 Refer to DEVIN_COMPREHENSIVE_SETUP_GUIDE.md")
        return 2


if __name__ == "__main__":
    sys.exit(main())
