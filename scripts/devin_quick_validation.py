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
        print(
            f"PASS: Python {version.major}.{version.minor}.{version.micro} - Compatible"
        )
        return True
    else:
        print(
            f"FAIL: Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+"
        )
        return False


def check_file_exists(filepath, description):
    """Check if a file exists."""
    if Path(filepath).exists():
        print(f"PASS: {description} - Found")
        return True
    else:
        print(f"FAIL: {description} - Missing")
        return False


def check_directory_exists(dirpath, description):
    """Check if a directory exists."""
    if Path(dirpath).is_dir():
        print(f"PASS: {description} - Found")
        return True
    else:
        print(f"FAIL: {description} - Missing")
        return False


def check_import(module_name, description):
    """Check if a module can be imported."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"PASS: {description} - Available")
            return True
        else:
            print(f"FAIL: {description} - Not found")
            return False
    except Exception as e:
        print(f"FAIL: {description} - Error: {e}")
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

    print("\nEnvironment Variables Check:")
    for var, desc in critical_vars:
        if os.environ.get(var):
            print(f"PASS: {desc} ({var}) - Set")
            results.append(True)
        else:
            print(f"WARN: {desc} ({var}) - Not set (will be configured)")
            results.append(True)  # Not critical for basic validation

    for var, desc in optional_vars:
        if os.environ.get(var):
            print(f"PASS: {desc} ({var}) - Set")
        else:
            print(f"INFO: {desc} ({var}) - Not set (optional)")

    return all(results)


def main():
    """Main validation function."""
    print("Devin Quick Validation - The HigherSelf Network Server")
    print("=" * 60)

    # Set PYTHONPATH to project root directory
    project_root = Path(__file__).parent.parent
    os.environ["PYTHONPATH"] = str(project_root)
    sys.path.insert(0, str(project_root))

    checks = []

    # Python version check
    print("\nPython Environment:")
    checks.append(check_python_version())

    # Core files check
    print("\nCore Files:")
    checks.append(check_file_exists("main.py", "Main Application File"))
    checks.append(check_file_exists("requirements.txt", "Requirements File"))
    checks.append(check_file_exists("pyproject.toml", "Project Configuration"))
    checks.append(check_file_exists("run_tests.py", "Test Runner"))

    # Directory structure check
    print("\nDirectory Structure:")
    checks.append(check_directory_exists("agents", "Agents Directory"))
    checks.append(check_directory_exists("api", "API Directory"))
    checks.append(check_directory_exists("services", "Services Directory"))
    checks.append(check_directory_exists("models", "Models Directory"))
    checks.append(check_directory_exists("tests", "Tests Directory"))

    # Core imports check
    print("\nCore Imports:")
    checks.append(check_import("pathlib", "Pathlib"))
    checks.append(check_import("json", "JSON"))
    checks.append(check_import("os", "OS"))
    checks.append(check_import("sys", "Sys"))

    # Project-specific imports (basic)
    print("\nProject Imports (Basic):")
    try:
        # Test basic model imports
        from models.base import BaseModel

        print("PASS: Base Models - Available")
        checks.append(True)
    except Exception as e:
        print(f"FAIL: Base Models - Error: {e}")
        checks.append(False)

    try:
        # Test settings import
        from config.settings import settings

        print("PASS: Settings Configuration - Available")
        checks.append(True)
    except Exception as e:
        print(f"FAIL: Settings Configuration - Error: {e}")
        checks.append(False)

    # Environment variables check
    checks.append(check_environment_variables())

    # Test execution capability
    print("\nTest Execution Check:")
    try:
        import subprocess  # nosec B404 - needed for test execution validation

        result = (
            subprocess.run(  # nosec B603, B607 - safe python command for validation
                ["python3", "-c", "print('Test execution works')"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        )
        if result.returncode == 0:
            print("PASS: Test Execution - Working")
            checks.append(True)
        else:
            print(f"FAIL: Test Execution - Failed: {result.stderr}")
            checks.append(False)
    except Exception as e:
        print(f"FAIL: Test Execution - Error: {e}")
        checks.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    passed = sum(checks)
    total = len(checks)
    success_rate = (passed / total) * 100

    print(f"Total Checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {success_rate:.1f}%")

    if success_rate >= 90:
        print("\nVALIDATION PASSED!")
        print("Environment is ready for Devin integration")
        print("You can proceed with automated testing")
        print("\nNext Steps:")
        print("   1. Run: python3 devin_automated_setup.py")
        print("   2. Or run: python3 run_tests.py")
        return 0
    elif success_rate >= 70:
        print("\nVALIDATION PARTIALLY PASSED")
        print("Some issues detected but environment is mostly ready")
        print("Check the failed items above and refer to documentation")
        return 1
    else:
        print("\nVALIDATION FAILED")
        print("Critical issues detected - environment needs setup")
        print("Refer to DEVIN_COMPREHENSIVE_SETUP_GUIDE.md")
        return 2


if __name__ == "__main__":
    sys.exit(main())
