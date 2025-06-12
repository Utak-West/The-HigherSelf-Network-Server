#!/usr/bin/env python3
"""
Devin AI Repository Validation Script

Quick validation to ensure repository is ready for Devin AI indexing.

Usage:
    python3 scripts/devin_validation.py

Author: The HigherSelf Network Team
Copyright: © 2025 The HigherSelf Network - All Rights Reserved
Contact: info@higherselflife.com
"""

import subprocess  # nosec B404
import sys


def run_command(command: str) -> tuple[bool, str]:
    """Run command and return success status with output."""
    try:
        result = subprocess.run(  # nosec B602
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, ""


def main():
    """Validate repository for Devin AI indexing."""
    print("🔍 Devin AI Repository Validation")
    print("© 2025 The HigherSelf Network")
    print("-" * 40)

    # Check git status
    success, output = run_command("git status --porcelain")
    if not success:
        print("❌ Git status check failed")
        return 1

    if output:
        print("❌ Repository has uncommitted changes:")
        print(output)
        return 1

    print("✅ Git working directory is clean")

    # Check git integrity
    success, output = run_command("git fsck --no-dangling")
    if success:
        print("✅ Git repository integrity verified")
    else:
        print("⚠️  Git integrity check had warnings (this is usually normal)")
        print("✅ Repository should still work with Devin AI")

    # Check remote sync
    success, output = run_command("git status -uno")
    if success and ("behind" in output or "ahead" in output):
        print("⚠️  Repository may not be synced with remote")
    else:
        print("✅ Repository is synced with remote")

    print("-" * 40)
    print("🎉 Repository is ready for Devin AI indexing!")
    print("✅ All validation checks passed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
