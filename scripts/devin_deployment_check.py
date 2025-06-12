#!/usr/bin/env python3
"""
Devin Deployment Check Script
Quick validation that the deployment is ready for Devin AI integration
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional


def log(message: str, level: str = "INFO") -> None:
    """Log messages with appropriate formatting."""
    prefix = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(
        level, "ℹ️"
    )
    print(f"{prefix} {message}")


def run_command(command: str, timeout: int = 30) -> tuple[bool, str, str]:
    """Run a command and return success status, stdout, stderr."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def check_docker_status() -> bool:
    """Check if Docker services are running."""
    log("Checking Docker services...")

    # Check if docker compose is available (try modern first, then legacy)
    success, _, _ = run_command("docker compose version")
    if not success:
        success, _, _ = run_command("docker-compose --version")
        if not success:
            log("Docker Compose not available", "ERROR")
            return False

    # Check container status (try modern first, then legacy)
    success, stdout, stderr = run_command("docker compose ps --format json")
    if not success:
        success, stdout, stderr = run_command("docker-compose ps --format json")
    if not success:
        log("Failed to get container status", "ERROR")
        return False

    try:
        containers = []
        for line in stdout.strip().split("\n"):
            if line.strip():
                containers.append(json.loads(line))

        running_containers = [c for c in containers if c.get("State") == "running"]

        log(f"Found {len(running_containers)} running containers")

        # Check for key services
        required_services = ["windsurf-agent", "mongodb", "redis"]
        running_services = [c["Service"] for c in running_containers]

        for service in required_services:
            if service in running_services:
                log(f"✅ {service} is running", "SUCCESS")
            else:
                log(f"❌ {service} is not running", "ERROR")
                return False

        return True

    except (json.JSONDecodeError, KeyError) as e:
        log(f"Failed to parse container status: {e}", "ERROR")
        return False


def check_api_health() -> bool:
    """Check if the API is responding to health checks."""
    log("Checking API health...")

    # Try health endpoint
    success, stdout, stderr = run_command("curl -f -s http://localhost:8000/health")
    if success:
        log("API health check passed", "SUCCESS")
        return True
    else:
        log("API health check failed", "ERROR")
        log(f"Error: {stderr}", "ERROR")
        return False


def check_environment() -> bool:
    """Check environment configuration."""
    log("Checking environment configuration...")

    # Check if .env file exists
    if not Path(".env").exists():
        log(".env file not found", "ERROR")
        return False

    log(".env file found", "SUCCESS")

    # Check key environment variables
    required_vars = ["TEST_MODE", "DISABLE_WEBHOOKS"]
    for var in required_vars:
        if os.environ.get(var):
            log(f"{var} is set", "SUCCESS")
        else:
            log(f"{var} is not set", "WARNING")

    return True


def check_repository_state() -> bool:
    """Check repository state for Devin deployment."""
    log("Checking repository state...")

    # Check git status
    success, stdout, stderr = run_command("git status --porcelain")
    if not success:
        log("Failed to check git status", "ERROR")
        return False

    # Check current branch
    success, stdout, stderr = run_command("git branch --show-current")
    if success and stdout.strip() == "main":
        log("On main branch", "SUCCESS")
    else:
        log("Not on main branch", "WARNING")

    # Check for single branch
    success, stdout, stderr = run_command("git branch -a")
    if success:
        branches = [line.strip() for line in stdout.split("\n") if line.strip()]
        local_branches = [b for b in branches if not b.startswith("remotes/")]
        if len(local_branches) == 1 and "main" in local_branches[0]:
            log("Single-branch structure confirmed", "SUCCESS")
        else:
            log("Multiple branches detected", "WARNING")

    return True


def check_devin_scripts() -> bool:
    """Check if Devin-specific scripts are available."""
    log("Checking Devin scripts...")

    scripts = [
        "devin_quick_validation.py",
        "devin_automated_setup.py",
        "devin_test_server.py",
        "devin_deploy.py",
    ]

    all_present = True
    for script in scripts:
        if Path(script).exists():
            log(f"{script} found", "SUCCESS")
        else:
            log(f"{script} missing", "ERROR")
            all_present = False

    return all_present


def main() -> int:
    """Main validation function."""
    log("Devin Deployment Check - The HigherSelf Network Server")
    log("=" * 60)

    checks = [
        ("Environment Configuration", check_environment),
        ("Repository State", check_repository_state),
        ("Devin Scripts", check_devin_scripts),
        ("Docker Services", check_docker_status),
        ("API Health", check_api_health),
    ]

    passed = 0
    total = len(checks)

    for check_name, check_function in checks:
        log(f"\nRunning: {check_name}")
        if check_function():
            passed += 1
            log(f"{check_name} - PASSED", "SUCCESS")
        else:
            log(f"{check_name} - FAILED", "ERROR")

    # Summary
    log("\n" + "=" * 60)
    log("DEPLOYMENT CHECK SUMMARY")
    log("=" * 60)

    success_rate = (passed / total) * 100
    log(f"Total Checks: {total}")
    log(f"Passed: {passed}")
    log(f"Failed: {total - passed}")
    log(f"Success Rate: {success_rate:.1f}%")

    if success_rate == 100:
        log("\n🎉 DEPLOYMENT READY FOR DEVIN!", "SUCCESS")
        log("All systems are operational")
        log("API available at: http://localhost:8000")
        return 0
    elif success_rate >= 80:
        log("\n⚠️  DEPLOYMENT MOSTLY READY", "WARNING")
        log("Some minor issues detected")
        log("Deployment should work but check failed items")
        return 1
    else:
        log("\n❌ DEPLOYMENT NOT READY", "ERROR")
        log("Critical issues detected")
        log("Fix the failed checks before proceeding")
        return 2


if __name__ == "__main__":
    sys.exit(main())
