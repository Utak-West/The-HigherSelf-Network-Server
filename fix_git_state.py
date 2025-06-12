#!/usr/bin/env python3
"""
Script to fix git state when git commands are hanging.
This manually resets the git index and cleans up any problematic state.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command_with_timeout(command, timeout=10):
    """Run a command with timeout to prevent hanging."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd(),
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {command}")
        return False, "", "Command timed out"
    except Exception as e:
        print(f"Command failed: {command} - {e}")
        return False, "", str(e)


def cleanup_git_locks():
    """Remove any git lock files that might be causing issues."""
    lock_files = [
        ".git/index.lock",
        ".git/HEAD.lock",
        ".git/refs/heads/main.lock",
        ".git/config.lock",
    ]

    for lock_file in lock_files:
        if os.path.exists(lock_file):
            try:
                os.remove(lock_file)
                print(f"Removed lock file: {lock_file}")
            except Exception as e:
                print(f"Failed to remove {lock_file}: {e}")


def reset_git_state():
    """Reset git state to clean working directory."""
    print("🔧 Fixing Git State...")
    print("=" * 50)

    # Step 1: Clean up lock files
    print("Step 1: Cleaning up git lock files...")
    cleanup_git_locks()

    # Step 2: Try basic git status with timeout
    print("Step 2: Testing git status...")
    success, stdout, stderr = run_command_with_timeout(
        "git status --porcelain", timeout=5
    )

    if success:
        print("✅ Git is responsive")
        if stdout.strip():
            print("📋 Uncommitted changes found:")
            print(stdout)

            # Step 3: Add and commit changes
            print("Step 3: Adding and committing changes...")
            success, _, stderr = run_command_with_timeout("git add .", timeout=10)
            if success:
                success, _, stderr = run_command_with_timeout(
                    'git commit -m "Fix: Resolve uncommitted changes for clean repository state"',
                    timeout=15,
                )
                if success:
                    print("✅ Changes committed successfully")

                    # Step 4: Push changes
                    print("Step 4: Pushing changes...")
                    success, _, stderr = run_command_with_timeout(
                        "git push origin main", timeout=20
                    )
                    if success:
                        print("✅ Changes pushed successfully")
                    else:
                        print(f"⚠️  Push failed: {stderr}")
                else:
                    print(f"❌ Commit failed: {stderr}")
            else:
                print(f"❌ Add failed: {stderr}")
        else:
            print("✅ Working directory is clean")
    else:
        print("❌ Git is still unresponsive, trying manual reset...")

        # Manual reset approach
        print("Step 3: Manual git reset...")
        success, _, stderr = run_command_with_timeout(
            "git reset --hard HEAD", timeout=10
        )
        if success:
            print("✅ Hard reset successful")
        else:
            print(f"❌ Hard reset failed: {stderr}")

        # Clean untracked files
        print("Step 4: Cleaning untracked files...")
        success, _, stderr = run_command_with_timeout("git clean -fd", timeout=10)
        if success:
            print("✅ Untracked files cleaned")
        else:
            print(f"⚠️  Clean failed: {stderr}")

    # Final verification
    print("\nStep 5: Final verification...")
    success, stdout, stderr = run_command_with_timeout("git status", timeout=5)
    if success:
        print("✅ Final git status:")
        print(stdout)
    else:
        print(f"❌ Final verification failed: {stderr}")

    print("\n" + "=" * 50)
    print("🎯 Git State Fix Complete")


if __name__ == "__main__":
    reset_git_state()
