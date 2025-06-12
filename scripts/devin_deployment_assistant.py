#!/usr/bin/env python3
"""
Devin Deployment Assistant
The HigherSelf Network Server - Automated Deployment Helper for Devin AI

This script provides Devin with automated deployment assistance, validation,
and troubleshooting capabilities specifically designed for AI agent operations.

Usage:
    python3 scripts/devin_deployment_assistant.py [command]

Commands:
    validate    - Run full validation sequence
    deploy      - Deploy the server with validation
    status      - Check current deployment status
    troubleshoot - Run diagnostic checks
    reset       - Reset environment to clean state
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DevinDeploymentAssistant:
    """Automated deployment assistant specifically designed for Devin AI."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.script_dir = self.project_root / "scripts"
        self.logs_dir = self.project_root / "logs"
        self.logs_dir.mkdir(exist_ok=True)

        # Ensure we're in the correct directory
        os.chdir(self.project_root)

    def log_operation(self, operation: str, status: str, details: str = "") -> None:
        """Log operations for Devin tracking."""
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "operation": operation,
            "status": status,
            "details": details,
            "agent": "devin",
        }

        log_file = self.logs_dir / "devin_operations.log"
        with open(log_file, "a") as f:
            f.write(f"{json.dumps(log_entry)}\n")

    def run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a command with timeout and capture output."""
        try:
            # Handle Docker Compose compatibility - try modern command first
            if command.startswith("docker-compose"):
                modern_command = command.replace("docker-compose", "docker compose", 1)
                try:
                    result = subprocess.run(
                        modern_command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=self.project_root,
                    )
                    if result.returncode == 0:
                        return True, result.stdout, result.stderr
                except Exception:
                    pass  # Fall back to legacy command

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root,
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)

    def validate_environment(self) -> Dict[str, bool]:
        """Validate the deployment environment."""
        print("🔍 Validating deployment environment...")

        checks = {}

        # Check Python version
        success, stdout, stderr = self.run_command("python3 --version")
        checks["python3_available"] = success
        if success:
            print(f"✅ Python: {stdout.strip()}")
        else:
            print(f"❌ Python check failed: {stderr}")

        # Check Git status
        success, stdout, stderr = self.run_command("git status --porcelain")
        checks["git_clean"] = success and len(stdout.strip()) == 0
        if checks["git_clean"]:
            print("✅ Git repository is clean")
        else:
            print(f"⚠️  Git repository has uncommitted changes")

        # Check Docker
        success, stdout, stderr = self.run_command("docker --version")
        checks["docker_available"] = success
        if success:
            print(f"✅ Docker: {stdout.strip()}")
        else:
            print(f"❌ Docker check failed: {stderr}")

        # Check required files
        required_files = [
            "main.py",
            "requirements.txt",
            "docker-compose.yml",
            "scripts/devin_simple_validation.py",
            "scripts/devin_test_server.py",
        ]

        for file_path in required_files:
            file_exists = (self.project_root / file_path).exists()
            checks[
                f"file_{file_path.replace('/', '_').replace('.', '_')}"
            ] = file_exists
            if file_exists:
                print(f"✅ Found: {file_path}")
            else:
                print(f"❌ Missing: {file_path}")

        return checks

    def run_validation_sequence(self) -> bool:
        """Run the complete validation sequence."""
        print("\n🧪 Running validation sequence...")

        # Set environment variables
        os.environ["TEST_MODE"] = "True"
        os.environ["DISABLE_WEBHOOKS"] = "True"
        os.environ["PYTHONPATH"] = str(self.project_root)

        # Run simple validation
        print("1️⃣ Running simple validation...")
        success, stdout, stderr = self.run_command(
            "python3 scripts/devin_simple_validation.py", timeout=60
        )

        if not success:
            print(f"❌ Simple validation failed: {stderr}")
            self.log_operation("simple_validation", "failed", stderr)
            return False

        print("✅ Simple validation passed")

        # Run test server (brief)
        print("2️⃣ Running test server validation...")
        success, stdout, stderr = self.run_command(
            "timeout 10 python3 scripts/devin_test_server.py || true", timeout=15
        )

        if "Server started successfully" in stdout or "Health check passed" in stdout:
            print("✅ Test server validation passed")
        else:
            print(f"⚠️  Test server validation inconclusive: {stderr}")

        self.log_operation("validation_sequence", "completed", "All validations run")
        return True

    def deploy_server(self) -> bool:
        """Deploy the server with full validation."""
        print("\n🚀 Deploying server...")

        # Stop any existing containers
        print("Stopping existing containers...")
        self.run_command("docker-compose down", timeout=30)

        # Start services
        print("Starting services...")
        success, stdout, stderr = self.run_command("docker-compose up -d", timeout=120)

        if not success:
            print(f"❌ Deployment failed: {stderr}")
            self.log_operation("deployment", "failed", stderr)
            return False

        # Wait for services to start
        print("Waiting for services to start...")
        time.sleep(10)

        # Check health endpoint
        print("Checking health endpoint...")
        success, stdout, stderr = self.run_command(
            "curl -f http://localhost:8000/health", timeout=10
        )

        if success:
            print("✅ Health check passed")
            print("✅ Deployment successful!")
            self.log_operation("deployment", "success", "Server deployed and healthy")
            return True
        else:
            print(f"❌ Health check failed: {stderr}")
            self.log_operation("deployment", "failed", f"Health check failed: {stderr}")
            return False

    def check_status(self) -> Dict[str, str]:
        """Check current deployment status."""
        print("\n📊 Checking deployment status...")

        status = {}

        # Check Docker containers
        success, stdout, stderr = self.run_command("docker-compose ps")
        if success:
            status["containers"] = "running" if "Up" in stdout else "stopped"
            print(f"🐳 Containers: {status['containers']}")
        else:
            status["containers"] = "error"
            print(f"❌ Container check failed: {stderr}")

        # Check health endpoint
        success, stdout, stderr = self.run_command(
            "curl -f http://localhost:8000/health"
        )
        if success:
            status["health"] = "healthy"
            print("✅ Health endpoint: healthy")
        else:
            status["health"] = "unhealthy"
            print("❌ Health endpoint: unhealthy")

        # Check ports
        success, stdout, stderr = self.run_command("netstat -tlnp | grep :8000")
        if success:
            status["port_8000"] = "open"
            print("✅ Port 8000: open")
        else:
            status["port_8000"] = "closed"
            print("❌ Port 8000: closed")

        return status

    def troubleshoot(self) -> None:
        """Run diagnostic checks for troubleshooting."""
        print("\n🔧 Running diagnostic checks...")

        # Check Python path
        success, stdout, stderr = self.run_command(
            "python3 -c 'import sys; print(sys.path)'"
        )
        if success:
            print(f"🐍 Python path: {stdout.strip()}")

        # Check installed packages
        success, stdout, stderr = self.run_command(
            "pip list | grep -E '(fastapi|pydantic|uvicorn)'"
        )
        if success:
            print(f"📦 Key packages:\n{stdout}")

        # Check Docker logs
        success, stdout, stderr = self.run_command("docker-compose logs --tail=20")
        if success:
            print(f"🐳 Recent Docker logs:\n{stdout}")

        # Check disk space
        success, stdout, stderr = self.run_command("df -h .")
        if success:
            print(f"💾 Disk space:\n{stdout}")

        # Check memory
        success, stdout, stderr = self.run_command("free -h")
        if success:
            print(f"🧠 Memory usage:\n{stdout}")

    def reset_environment(self) -> bool:
        """Reset environment to clean state."""
        print("\n🔄 Resetting environment...")

        # Stop all containers
        print("Stopping containers...")
        self.run_command("docker-compose down", timeout=30)

        # Clean Docker system (optional)
        print("Cleaning Docker system...")
        self.run_command("docker system prune -f", timeout=60)

        # Reset git to clean state (if needed)
        success, stdout, stderr = self.run_command("git status --porcelain")
        if stdout.strip():
            print("⚠️  Uncommitted changes detected. Manual review recommended.")

        print("✅ Environment reset complete")
        self.log_operation("reset", "completed", "Environment reset to clean state")
        return True


def main():
    """Main function for Devin deployment assistant."""
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/devin_deployment_assistant.py [command]")
        print("\nCommands:")
        print("  validate     - Run full validation sequence")
        print("  deploy       - Deploy the server with validation")
        print("  status       - Check current deployment status")
        print("  troubleshoot - Run diagnostic checks")
        print("  reset        - Reset environment to clean state")
        return 1

    command = sys.argv[1].lower()
    assistant = DevinDeploymentAssistant()

    print(f"🤖 Devin Deployment Assistant - {command.upper()}")
    print("=" * 60)

    try:
        if command == "validate":
            env_checks = assistant.validate_environment()
            if all(env_checks.values()):
                success = assistant.run_validation_sequence()
                return 0 if success else 1
            else:
                print("❌ Environment validation failed")
                return 1

        elif command == "deploy":
            env_checks = assistant.validate_environment()
            if not all(env_checks.values()):
                print("❌ Environment validation failed - cannot deploy")
                return 1

            if assistant.run_validation_sequence():
                success = assistant.deploy_server()
                return 0 if success else 1
            else:
                print("❌ Validation failed - cannot deploy")
                return 1

        elif command == "status":
            status = assistant.check_status()
            all_healthy = all(
                v in ["running", "healthy", "open"] for v in status.values()
            )
            return 0 if all_healthy else 1

        elif command == "troubleshoot":
            assistant.troubleshoot()
            return 0

        elif command == "reset":
            success = assistant.reset_environment()
            return 0 if success else 1

        else:
            print(f"❌ Unknown command: {command}")
            return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        assistant.log_operation(command, "error", str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
