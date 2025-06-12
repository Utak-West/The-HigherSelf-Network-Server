#!/usr/bin/env python3
"""
Automated Setup and Testing Script for Devin AI Integration
The HigherSelf Network Server - Comprehensive Environment Setup

This script provides automated setup, dependency management, and testing
specifically designed for Devin's automated testing system.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class DevinSetupManager:
    """Manages automated setup and testing for Devin AI integration."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.success_count = 0
        self.total_tests = 0
        self.results = []

    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(
            level, "📝"
        )
        print(f"{prefix} {message}")

    def run_command(
        self, command: str, description: str, critical: bool = False
    ) -> bool:
        """Run a command and return success status."""
        self.log(f"Running: {description}")
        self.log(f"Command: {command}")

        try:
            result = subprocess.run(
                command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            self.log(f"{description} - PASSED", "SUCCESS")
            self.results.append((description, True, ""))
            return True
        except subprocess.CalledProcessError as e:
            error_msg = f"Exit code: {e.returncode}"
            if e.stderr:
                error_msg += f", Error: {e.stderr.strip()}"
            self.log(f"{description} - FAILED ({error_msg})", "ERROR")
            self.results.append((description, False, error_msg))

            if critical:
                self.log("Critical failure detected. Stopping setup.", "ERROR")
                sys.exit(1)
            return False

    def setup_environment(self) -> bool:
        """Set up the test environment with required variables."""
        self.log("Setting up test environment variables")

        # Set test environment variables
        test_env = {
            "TEST_MODE": "True",
            "DISABLE_WEBHOOKS": "True",
            "NOTION_API_TOKEN": "test_notion_token",
            "REDIS_URI": "redis://localhost:6379/0",
            "REDIS_PASSWORD": "test_password",
            "MONGODB_URI": "mongodb://localhost:27017/test_db",
            "OPENAI_API_KEY": "test_openai_key",
            "PYTHONPATH": str(self.project_root),
        }

        for key, value in test_env.items():
            os.environ[key] = value

        self.log("Test environment variables configured", "SUCCESS")
        return True

    def check_python_setup(self) -> bool:
        """Verify Python installation and version."""
        self.total_tests += 1
        if self.run_command("python3 --version", "Python Version Check"):
            self.success_count += 1
            return True
        return False

    def install_dependencies(self) -> bool:
        """Install required Python dependencies."""
        self.total_tests += 1

        # Check if requirements.txt exists
        if not (self.project_root / "requirements.txt").exists():
            self.log("requirements.txt not found", "ERROR")
            return False

        if self.run_command(
            "pip3 install --upgrade pip && pip3 install -r requirements.txt",
            "Install Python Dependencies",
        ):
            self.success_count += 1
            return True
        return False

    def install_dev_dependencies(self) -> bool:
        """Install development and testing dependencies."""
        self.total_tests += 1
        dev_packages = [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
            "black",
            "isort",
            "flake8",
            "mypy",
            "bandit",
            "safety",
        ]

        if self.run_command(
            f"pip3 install {' '.join(dev_packages)}", "Install Development Dependencies"
        ):
            self.success_count += 1
            return True
        return False

    def run_syntax_checks(self) -> bool:
        """Run Python syntax validation."""
        self.total_tests += 1
        if self.run_command(
            "python3 -c \"import py_compile; py_compile.compile('main.py', doraise=True); print('✅ main.py syntax is valid')\"",
            "Main File Syntax Check",
        ):
            self.success_count += 1
            return True
        return False

    def run_import_tests(self) -> bool:
        """Test core module imports."""
        self.total_tests += 1
        if self.run_command(
            "python3 -c \"from models.base import *; from models.content_models import *; print('✅ Core models import successfully')\"",
            "Core Models Import Test",
        ):
            self.success_count += 1
            return True
        return False

    def run_basic_functionality_tests(self) -> bool:
        """Run the basic functionality test suite."""
        self.total_tests += 1
        if self.run_command(
            "python3 -m pytest tests/test_basic_functionality.py -v --no-cov",
            "Basic Functionality Tests",
        ):
            self.success_count += 1
            return True
        return False

    def run_redis_connection_test(self) -> bool:
        """Test Redis connection (mocked)."""
        self.total_tests += 1
        if self.run_command(
            "python3 -m pytest tests/test_redis_connection.py -v --no-cov",
            "Redis Connection Test",
        ):
            self.success_count += 1
            return True
        return False

    def run_configuration_check(self) -> bool:
        """Verify configuration files exist."""
        self.total_tests += 1
        if self.run_command(
            "python3 -c \"from pathlib import Path; assert Path('pyproject.toml').exists(); assert Path('.flake8').exists(); print('✅ Configuration files are present')\"",
            "Configuration Files Check",
        ):
            self.success_count += 1
            return True
        return False

    def run_code_quality_checks(self) -> bool:
        """Run code quality and formatting checks."""
        checks = [
            ("black --check --diff .", "Black Code Formatting Check"),
            ("isort --check-only --diff .", "Import Sorting Check"),
            ("flake8 --select=E9,F63,F7,F82 .", "Critical Flake8 Checks"),
        ]

        passed = 0
        for command, description in checks:
            self.total_tests += 1
            if self.run_command(command, description):
                self.success_count += 1
                passed += 1

        return passed == len(checks)

    def run_comprehensive_test_suite(self) -> bool:
        """Run the project's comprehensive test runner."""
        self.total_tests += 1
        if self.run_command("python3 run_tests.py", "Comprehensive Test Suite"):
            self.success_count += 1
            return True
        return False

    def generate_report(self) -> None:
        """Generate a comprehensive test report."""
        print("\n" + "=" * 80)
        print("🎯 DEVIN AUTOMATED SETUP - FINAL REPORT")
        print("=" * 80)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.success_count}")
        print(f"Failed: {self.total_tests - self.success_count}")
        print(f"Success Rate: {(self.success_count/self.total_tests)*100:.1f}%")

        print("\n📊 DETAILED RESULTS:")
        print("-" * 80)
        for description, passed, error in self.results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status:<8} {description}")
            if not passed and error:
                print(f"         Error: {error}")

        print("\n🚀 RECOMMENDED NEXT STEPS:")
        if self.success_count == self.total_tests:
            print("✅ All tests passed! Environment is ready for development.")
            print("✅ You can now run: python3 main.py")
            print("✅ Or start with Docker: docker-compose up")
        else:
            print("⚠️  Some tests failed. Check the errors above.")
            print("🔧 Try running individual commands to debug issues.")
            print("📚 Refer to DEVIN_COMPREHENSIVE_SETUP_GUIDE.md for details.")

    def run_full_setup(self) -> int:
        """Run the complete automated setup process."""
        self.log("Starting Devin Automated Setup for The HigherSelf Network Server")
        self.log(f"Project Root: {self.project_root}")

        # Setup phases
        setup_phases = [
            ("Environment Setup", self.setup_environment),
            ("Python Setup Check", self.check_python_setup),
            ("Install Dependencies", self.install_dependencies),
            ("Install Dev Dependencies", self.install_dev_dependencies),
            ("Syntax Checks", self.run_syntax_checks),
            ("Import Tests", self.run_import_tests),
            ("Configuration Check", self.run_configuration_check),
            ("Basic Functionality Tests", self.run_basic_functionality_tests),
            ("Redis Connection Test", self.run_redis_connection_test),
            ("Code Quality Checks", self.run_code_quality_checks),
            ("Comprehensive Test Suite", self.run_comprehensive_test_suite),
        ]

        self.log(f"Running {len(setup_phases)} setup phases...")

        for phase_name, phase_func in setup_phases:
            self.log(f"\n🔄 Starting Phase: {phase_name}")
            try:
                phase_func()
            except Exception as e:
                self.log(f"Phase {phase_name} failed with exception: {e}", "ERROR")

        # Generate final report
        self.generate_report()

        # Return appropriate exit code
        return 0 if self.success_count == self.total_tests else 1


def main():
    """Main entry point for the automated setup script."""
    setup_manager = DevinSetupManager()
    return setup_manager.run_full_setup()


if __name__ == "__main__":
    sys.exit(main())
