#!/usr/bin/env python3
"""
Comprehensive test setup and validation for Devin.
This script provides all the working test commands and setup instructions.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description, allow_failure=False):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print("=" * 60)

    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=False)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        if allow_failure:
            print(f"⚠️  {description} - FAILED (exit code: {e.returncode}) - Expected")
            return True
        else:
            print(f"❌ {description} - FAILED (exit code: {e.returncode})")
            return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking Dependencies")
    print("=" * 60)

    dependencies = [
        ("python3", "python3 --version"),
        (
            "pytest",
            "python3 -c 'import pytest; print(f\"pytest {pytest.__version__}\")'",
        ),
        (
            "pydantic",
            "python3 -c 'import pydantic; print(f\"pydantic {pydantic.__version__}\")'",
        ),
        (
            "pydantic-settings",
            "python3 -c 'import pydantic_settings; print(\"pydantic-settings available\")'",
        ),
        ("redis", "python3 -c 'import redis; print(f\"redis {redis.__version__}\")'"),
    ]

    missing = []
    for name, cmd in dependencies:
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
            print(f"✅ {name} - Available")
        except subprocess.CalledProcessError:
            print(f"❌ {name} - Missing")
            missing.append(name)

    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print("Run: pip3 install redis pydantic-settings")
        return False
    else:
        print("\n✅ All dependencies available")
        return True


def main():
    """Main test setup function."""
    print("🚀 Devin Test Setup - The HigherSelf Network Server")
    print("=" * 60)

    # Check current directory
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")

    # Verify we're in the right place
    if not (current_dir / "pyproject.toml").exists():
        print("❌ Not in the correct project directory!")
        print("Expected to find pyproject.toml in current directory")
        return 1

    # Check dependencies
    if not check_dependencies():
        print("\n🔧 Install missing dependencies first!")
        return 1

    print(f"\n🧪 Running Test Suite")
    print("=" * 60)

    success_count = 0
    total_tests = 0

    # Test 1: Custom test runner (most reliable)
    total_tests += 1
    if run_command("python3 run_tests.py", "Custom Test Runner"):
        success_count += 1

    # Test 2: Basic functionality tests
    total_tests += 1
    if run_command(
        "python3 -m pytest tests/test_basic_functionality.py -v --no-cov",
        "Basic Functionality Tests",
    ):
        success_count += 1

    # Test 3: Simple Redis test
    total_tests += 1
    if run_command("python3 test_simple_redis.py", "Simple Redis Test"):
        success_count += 1

    # Test 4: Code formatting check
    total_tests += 1
    if run_command(
        "python3 -m black --check --diff tests/test_basic_functionality.py",
        "Code Formatting Check",
    ):
        success_count += 1

    # Test 5: Import validation
    total_tests += 1
    if run_command(
        "python3 -c \"from models.base import *; from models.content_models import *; print('✅ Core models import successfully')\"",
        "Core Models Import Test",
    ):
        success_count += 1

    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {success_count}")
    print(f"Failed: {total_tests - success_count}")

    if success_count == total_tests:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Project is ready for development")

        print(f"\n📋 WORKING COMMANDS FOR DEVIN:")
        print("=" * 60)
        print("# Navigate to project directory:")
        print("cd ~/repos/The-HigherSelf-Network-Server")
        print("")
        print("# Run reliable tests:")
        print("python3 run_tests.py")
        print("")
        print("# Run specific test file:")
        print("python3 -m pytest tests/test_basic_functionality.py -v --no-cov")
        print("")
        print("# Check code formatting:")
        print("python3 -m black --check --diff .")
        print("")
        print("# Simple dependency test:")
        print("python3 test_simple_redis.py")

        return 0
    else:
        print("\n⚠️  Some tests failed")
        print("🔧 Check the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
