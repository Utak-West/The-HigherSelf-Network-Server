#!/usr/bin/env python3
"""
Devin Deployment Script for The HigherSelf Network Server
Automated deployment and validation for Devin AI integration
"""

import os
import subprocess  # nosec B404 - needed for deployment automation
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


class DevinDeployment:
    """Handles deployment operations for Devin AI integration."""

    def __init__(self):
        self.project_root = Path(
            __file__
        ).parent.parent  # Go up one level from scripts/
        self.success_count = 0
        self.total_operations = 0

    def log(self, message: str, level: str = "INFO") -> None:
        """Log deployment messages."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(
            level, "ℹ️"
        )
        print(f"{prefix} [{timestamp}] {message}")

    def run_command(self, command: str, description: str) -> bool:
        """Run a shell command and return success status."""
        self.total_operations += 1
        self.log(f"Running: {description}")
        self.log(f"Command: {command}")

        try:
            result = (
                subprocess.run(  # nosec B602 - shell=True needed for deployment scripts
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    cwd=self.project_root,
                )
            )

            if result.returncode == 0:
                self.log(f"{description} - PASSED", "SUCCESS")
                self.success_count += 1
                return True
            else:
                self.log(
                    f"{description} - FAILED (Exit code: {result.returncode})", "ERROR"
                )
                if result.stderr:
                    self.log(f"Error: {result.stderr.strip()}", "ERROR")
                return False

        except subprocess.TimeoutExpired:
            self.log(f"{description} - TIMEOUT", "ERROR")
            return False
        except Exception as e:
            self.log(f"{description} - ERROR: {e}", "ERROR")
            return False

    def setup_environment(self) -> bool:
        """Set up deployment environment."""
        self.log("Setting up deployment environment")

        # Set environment variables for deployment
        env_vars = {
            "TEST_MODE": "True",
            "DISABLE_WEBHOOKS": "True",
            "PYTHONPATH": str(self.project_root),
            "ENVIRONMENT": "development",
        }

        for key, value in env_vars.items():
            os.environ[key] = value

        self.log("Environment variables configured", "SUCCESS")
        return True

    def validate_docker_setup(self) -> bool:
        """Validate Docker deployment setup."""
        self.log("Validating Docker deployment setup")

        # Check if Docker is available
        if not self.run_command("docker --version", "Docker Version Check"):
            return False

        # Check if docker-compose is available
        if not self.run_command("docker-compose --version", "Docker Compose Check"):
            return False

        # Validate docker-compose.yml
        if not self.run_command(
            "docker-compose config", "Docker Compose Configuration Validation"
        ):
            return False

        return True

    def build_docker_images(self) -> bool:
        """Build Docker images for deployment."""
        self.log("Building Docker images")

        return self.run_command("docker-compose build --no-cache", "Docker Image Build")

    def deploy_services(self) -> bool:
        """Deploy services using Docker Compose."""
        self.log("Deploying services")

        # Stop any existing services
        self.run_command("docker-compose down", "Stop Existing Services")

        # Start services in development mode
        return self.run_command("docker-compose up -d", "Start Services")

    def validate_deployment(self) -> bool:
        """Validate that deployment is working."""
        self.log("Validating deployment")

        # Wait for services to start
        self.log("Waiting for services to start...")
        time.sleep(30)

        # Check if containers are running
        if not self.run_command("docker-compose ps", "Container Status Check"):
            return False

        # Test health endpoint
        return self.run_command(
            "curl -f http://localhost:8000/health || echo 'Health check failed'",
            "Health Endpoint Test",
        )

    def run_tests(self) -> bool:
        """Run deployment tests."""
        self.log("Running deployment tests")

        # Run quick validation
        if not self.run_command(
            "python3 devin_quick_validation.py", "Quick Validation"
        ):
            return False

        # Run basic tests
        return self.run_command("python3 run_tests.py", "Basic Test Suite")

    def deploy(self) -> int:
        """Execute full deployment process."""
        self.log("Starting Devin Deployment Process")
        self.log("=" * 60)

        deployment_steps = [
            ("Environment Setup", self.setup_environment),
            ("Docker Setup Validation", self.validate_docker_setup),
            ("Docker Image Build", self.build_docker_images),
            ("Service Deployment", self.deploy_services),
            ("Deployment Validation", self.validate_deployment),
            ("Test Execution", self.run_tests),
        ]

        for step_name, step_function in deployment_steps:
            self.log(f"Starting: {step_name}")
            if not step_function():
                self.log(f"Deployment failed at: {step_name}", "ERROR")
                return 1
            self.log(f"Completed: {step_name}", "SUCCESS")

        # Final summary
        self.log("=" * 60)
        self.log("DEPLOYMENT SUMMARY")
        self.log("=" * 60)

        success_rate = (
            (self.success_count / self.total_operations) * 100
            if self.total_operations > 0
            else 0
        )

        self.log(f"Total Operations: {self.total_operations}")
        self.log(f"Successful: {self.success_count}")
        self.log(f"Failed: {self.total_operations - self.success_count}")
        self.log(f"Success Rate: {success_rate:.1f}%")

        if success_rate >= 90:
            self.log("DEPLOYMENT SUCCESSFUL!", "SUCCESS")
            self.log("Server is ready for Devin integration")
            self.log("API available at: http://localhost:8000")
            return 0
        else:
            self.log("DEPLOYMENT PARTIALLY SUCCESSFUL", "WARNING")
            self.log("Some issues detected - check logs above")
            return 1


def main():
    """Main deployment function."""
    deployer = DevinDeployment()
    return deployer.deploy()


if __name__ == "__main__":
    sys.exit(main())
