#!/usr/bin/env python3
"""
Test runner for The HigherSelf Network Server project.
Provides reliable testing commands for the Metro Power dashboard development.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
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
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False


def main():
    """Main test runner function."""
    print("🚀 The HigherSelf Network Server - Test Runner")
    print("Metro Power Dashboard Project - Testing Suite")
    print(f"Python version: {sys.version}")

    # Change to project directory
    project_root = Path(__file__).parent
    print(f"Project root: {project_root}")

    success_count = 0
    total_tests = 0

    # Test 1: Basic functionality tests (most reliable)
    total_tests += 1
    if run_command(
        "python3 -m pytest tests/test_basic_functionality.py -v --no-cov",
        "Basic Functionality Tests",
    ):
        success_count += 1

    # Test 2: Syntax check on main.py
    total_tests += 1
    if run_command(
        "python3 -c \"import py_compile; py_compile.compile('main.py', doraise=True); print('✅ main.py syntax is valid')\"",
        "Main File Syntax Check",
    ):
        success_count += 1

    # Test 3: Import test for models (lightweight)
    total_tests += 1
    if run_command(
        "python3 -c \"from models.base import *; from models.content_models import *; print('✅ Core models import successfully')\"",
        "Core Models Import Test",
    ):
        success_count += 1

    # Test 4: Configuration validation
    total_tests += 1
    if run_command(
        "python3 -c \"from pathlib import Path; assert Path('pyproject.toml').exists(); assert Path('.flake8').exists(); print('✅ Configuration files are present')\"",
        "Configuration Files Check",
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
        print("🎉 ALL TESTS PASSED!")
        print("✅ Project is ready for Metro Power dashboard development")
        return 0
    else:
        print("⚠️  Some tests failed")
        print("🔧 Check the output above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
