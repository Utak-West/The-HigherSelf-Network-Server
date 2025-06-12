#!/usr/bin/env python3
"""
Validation script to verify agent augmentation configuration is properly set up.
"""

import json
import os
import sys
from pathlib import Path


def validate_config_files():
    """Validate that all required configuration files exist and are valid."""
    repo_root = Path.cwd()

    required_files = [
        ".windsurf/agent_augmentation.json",
        ".windsurf/git_conflict_resolution.json",
        "scripts/agent_git_resolver.py",
    ]

    print("🔍 Validating Agent Augmentation Configuration")
    print("=" * 50)

    all_valid = True

    for file_path in required_files:
        full_path = repo_root / file_path

        if not full_path.exists():
            print(f"❌ Missing: {file_path}")
            all_valid = False
            continue

        if file_path.endswith(".json"):
            try:
                with open(full_path, "r") as f:
                    config = json.load(f)
                print(f"✅ Valid JSON: {file_path}")

                if "agentAugmentation" in config:
                    capabilities = config["agentAugmentation"].get("capabilities", [])
                    print(f"   📋 Capabilities: {len(capabilities)} enabled")

                if "gitConflictResolution" in config:
                    workflow = config["gitConflictResolution"].get("workflow", {})
                    phases = workflow.get("phases", [])
                    print(f"   📋 Workflow phases: {len(phases)} configured")

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON: {file_path} - {e}")
                all_valid = False
        else:
            if os.access(full_path, os.X_OK):
                print(f"✅ Executable: {file_path}")
            else:
                print(f"⚠️  Not executable: {file_path}")

    print("\n" + "=" * 50)

    if all_valid:
        print("🎉 All configuration files are valid!")
        print("\n💡 Ready to run: python scripts/agent_git_resolver.py")
        return True
    else:
        print("❌ Configuration validation failed")
        return False


def test_agent_coordination():
    """Test that agent coordination patterns are properly configured."""
    try:
        with open(".windsurf/agent_augmentation.json", "r") as f:
            base_config = json.load(f)

        with open(".windsurf/git_conflict_resolution.json", "r") as f:
            git_config = json.load(f)

        print("\n🤖 Agent Coordination Test")
        print("=" * 30)

        base_capabilities = base_config["agentAugmentation"]["capabilities"]
        required_capabilities = [
            "contextAwareness",
            "multiAgentCoordination",
            "errorRecovery",
            "performanceOptimization",
        ]

        for capability in required_capabilities:
            if capability in base_capabilities:
                print(f"✅ {capability}: Available")
            else:
                print(f"❌ {capability}: Missing")

        git_agents = git_config["gitConflictResolution"]["coordination"][
            "supportAgents"
        ]
        print(f"\n📋 Git Resolution Agents: {len(git_agents)} configured")
        for agent in git_agents:
            print(f"   🤖 {agent}")

        return True

    except Exception as e:
        print(f"❌ Agent coordination test failed: {e}")
        return False


def main():
    """Main validation function."""
    print("🚀 Agent Augmentation System Validation")
    print("=" * 60)

    config_valid = validate_config_files()
    coordination_valid = test_agent_coordination()

    if config_valid and coordination_valid:
        print("\n🎉 VALIDATION SUCCESSFUL")
        print("Your agent augmentation system is ready for git conflict resolution!")
        print("\nNext step: python scripts/agent_git_resolver.py")
        return 0
    else:
        print("\n❌ VALIDATION FAILED")
        print("Please check the configuration files and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
