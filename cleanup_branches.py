#!/usr/bin/env python3
"""
Grace Fields' Branch Cleanup Script
Consolidates repository to a single main branch.
"""

import subprocess  # nosec B404 - Required for git automation
import sys
from pathlib import Path


def run_command(command, description):
    """Run a git command and return success status."""
    print(f"Grace: {description}...")
    try:
        result = subprocess.run(  # nosec B602 - Controlled git commands only
            command, shell=True, capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            print(f"SUCCESS: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"FAILED: {description}")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: {description}")
        return False
    except Exception as e:
        print(f"ERROR: {description} - {e}")
        return False


def main():
    """Main cleanup function."""
    print("Grace Fields: Repository Branch Cleanup")
    print("=" * 50)

    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    print(f"Working in: {project_root}")

    # Check current status
    print("\nStep 1: Checking current repository status...")
    run_command("git status", "Repository status check")

    # List all branches
    print("\nStep 2: Listing all branches...")
    run_command("git branch -a", "List all branches")

    # Fetch latest from origin
    print("\nStep 3: Fetching latest from origin...")
    run_command("git fetch origin", "Fetch from origin")

    # Ensure we're on main
    print("\nStep 4: Switching to main branch...")
    run_command("git checkout main", "Switch to main")

    # Pull latest main
    print("\nStep 5: Pulling latest main...")
    run_command("git pull origin main", "Pull latest main")

    # Delete remote efficiency improvements branch
    print("\nStep 6: Deleting remote efficiency improvements branch...")
    success = run_command(
        "git push origin --delete devin/1734073027-efficiency-improvements",
        "Delete remote efficiency improvements branch",
    )

    if not success:
        print("Note: Remote branch may already be deleted or not exist")

    # Delete any local tracking branches
    print("\nStep 7: Cleaning up local tracking branches...")
    run_command("git remote prune origin", "Prune remote tracking branches")

    # Delete any local branches (except main)
    print("\nStep 8: Deleting local branches...")
    result = subprocess.run(  # nosec B602,B607
        "git branch", shell=True, capture_output=True, text=True
    )

    if result.returncode == 0:
        branches = result.stdout.strip().split("\n")
        for branch in branches:
            branch = branch.strip()
            if branch and not branch.startswith("*") and "main" not in branch:
                branch_name = branch.replace("*", "").strip()
                if branch_name and branch_name != "main":
                    run_command(
                        f"git branch -D {branch_name}",
                        f"Delete local branch {branch_name}",
                    )

    # Final verification
    print("\nStep 9: Final verification...")
    run_command("git branch -a", "List remaining branches")

    # Push any final changes
    print("\nStep 10: Ensuring main is up to date...")
    run_command("git push origin main", "Push main to origin")

    print("\n" + "=" * 50)
    print("Grace Fields: Branch cleanup completed!")
    print("Repository now has only the main branch.")
    print("=" * 50)


if __name__ == "__main__":
    main()
