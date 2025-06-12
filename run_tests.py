#!/usr/bin/env python3
"""
Test Runner for The HigherSelf Network Server
Simplified test runner for Devin deployment validation
"""

import os
import subprocess
import sys
from pathlib import Path


def setup_test_environment():
    """Set up test environment variables."""
    test_env = {
        "TEST_MODE": "True",
        "DISABLE_WEBHOOKS": "True",
        "PYTHONPATH": str(Path(__file__).parent),
        "ENVIRONMENT": "development",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    print("✅ Test environment configured")


def run_command(command, description):
    """Run a command and return success status."""
    print(f"🔄 Running: {description}")
    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True, timeout=60
        )
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        return False
    except subprocess.TimeoutExpired:
        print(f"❌ {description} - TIMEOUT")
        return False


def main():
    """Main test runner function."""
    print("=" * 60)
    print("🧪 The HigherSelf Network Server - Test Runner")
    print("=" * 60)

    setup_test_environment()

    # Basic validation tests
    tests = [
        (
            'python3 -c \'import sys; sys.path.append("."); from pathlib import Path; assert Path("main.py").exists(); print("Main file exists")\'',
            "Main File Check",
        ),
        (
            "python3 -c 'from models.base import *; print(\"Base models import successfully\")'",
            "Base Models Import",
        ),
        (
            "python3 -c 'from config.settings import *; print(\"Settings import successfully\")'",
            "Settings Import",
        ),
        ("python3 scripts/devin_quick_validation.py", "Quick Validation"),
    ]

    passed = 0
    total = len(tests)

    for command, description in tests:
        if run_command(command, description):
            passed += 1

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("🚀 Environment is ready for deployment")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("🔧 Check the errors above for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
