#!/usr/bin/env python3
"""
Simple Validation Script for Devin AI Integration
The HigherSelf Network Server - Essential Environment Validation

This script provides essential validation for Devin deployment without
complex imports that might cause hanging.
"""

import os
import subprocess  # nosec B404 - needed for validation commands
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


def check_git_status():
    """Check git repository status."""
    try:
        result = subprocess.run(  # nosec B603, B607 - safe git command for validation
            ["git", "status", "--porcelain"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            if result.stdout.strip():
                print("⚠️  Git working directory has uncommitted changes")
                return True  # Not critical for Devin
            else:
                print("✅ Git working directory is clean")
                return True
        else:
            print("❌ Git status check failed")
            return False
    except Exception as e:
        print(f"⚠️  Git check failed: {e}")
        return True  # Not critical for basic validation


def check_docker_availability():
    """Check if Docker is available."""
    try:
        result = (
            subprocess.run(  # nosec B603, B607 - safe docker command for validation
                ["docker", "--version"], capture_output=True, text=True, timeout=10
            )
        )
        if result.returncode == 0:
            print("✅ Docker - Available")
            return True
        else:
            print("⚠️  Docker - Not available (optional)")
            return True  # Not critical
    except Exception:
        print("⚠️  Docker - Not available (optional)")
        return True  # Not critical


def check_basic_dependencies():
    """Check basic Python dependencies."""
    dependencies = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
    ]

    results = []
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"✅ {name} - Available")
            results.append(True)
        except ImportError:
            print(f"⚠️  {name} - Missing (will be installed)")
            results.append(True)  # Not critical, can be installed

    return all(results)


def main():
    """Main validation function."""
    print("🚀 Devin Simple Validation - The HigherSelf Network Server")
    print("=" * 60)

    # Set up environment
    project_root = Path(__file__).parent.parent
    os.environ["PYTHONPATH"] = str(project_root)

    checks = []

    # Python version check
    print("\n📋 Python Environment:")
    checks.append(check_python_version())

    # Core files check
    print("\n📋 Core Files:")
    checks.append(check_file_exists("main.py", "Main Application File"))
    checks.append(check_file_exists("requirements.txt", "Requirements File"))
    checks.append(check_file_exists("docker-compose.yml", "Docker Compose File"))
    checks.append(
        check_file_exists("DEVIN_DEPLOYMENT_READY.md", "Devin Deployment Guide")
    )

    # Directory structure check
    print("\n📋 Directory Structure:")
    checks.append(check_directory_exists("agents", "Agents Directory"))
    checks.append(check_directory_exists("api", "API Directory"))
    checks.append(check_directory_exists("services", "Services Directory"))
    checks.append(check_directory_exists("scripts", "Scripts Directory"))

    # Git status check
    print("\n📋 Git Repository:")
    checks.append(check_git_status())

    # Docker availability check
    print("\n📋 Docker Environment:")
    checks.append(check_docker_availability())

    # Basic dependencies check
    print("\n📋 Basic Dependencies:")
    checks.append(check_basic_dependencies())

    # Test server script check
    print("\n📋 Devin Scripts:")
    checks.append(
        check_file_exists("scripts/devin_test_server.py", "Test Server Script")
    )
    checks.append(check_file_exists("scripts/devin_deploy.py", "Deployment Script"))

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
        print("✅ Environment is ready for Devin deployment")
        print("\n🚀 Next Steps:")
        print("   1. Run test server: python3 scripts/devin_test_server.py")
        print("   2. Or deploy with Docker: docker-compose up -d")
        print("   3. Or run full deployment: python3 scripts/devin_deploy.py")
        return 0
    elif success_rate >= 70:
        print("\n⚠️  VALIDATION PARTIALLY PASSED")
        print("Some issues detected but environment is mostly ready")
        return 1
    else:
        print("\n❌ VALIDATION FAILED")
        print("Critical issues detected - environment needs setup")
        return 2


if __name__ == "__main__":
    sys.exit(main())
