#!/usr/bin/env python3
"""
Agent-Augmented Git Conflict Resolution Script
Leverages Windsurf IDE's agent augmentation system for intelligent git merge conflict handling.
"""

import os
import sys
import json
import subprocess
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class AgentGitResolver:
    def __init__(self, config_path: str = ".windsurf/git_conflict_resolution.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.repo_root = Path.cwd()
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def _load_config(self) -> Dict:
        """Load agent augmentation configuration for git conflict resolution."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration: {e}")
            sys.exit(1)
    
    def _run_command(self, command: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """Execute shell command with timeout and error handling."""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.repo_root
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout} seconds"
        except Exception as e:
            return False, "", str(e)
    
    def analyze_git_status(self) -> Dict:
        """ContextAnalyzer: Analyze current git status and conflict patterns."""
        print("🔍 ContextAnalyzer: Analyzing git status...")
        
        success, stdout, stderr = self._run_command("git status --porcelain")
        if not success:
            return {"error": f"Failed to get git status: {stderr}"}
        
        files = stdout.strip().split('\n') if stdout.strip() else []
        
        success, stdout, stderr = self._run_command("git merge-tree $(git merge-base HEAD origin/main) HEAD origin/main")
        
        analysis = {
            "current_files": len(files),
            "untracked_files": [f[3:] for f in files if f.startswith('??')],
            "modified_files": [f[3:] for f in files if f.startswith(' M') or f.startswith('M ')],
            "potential_conflicts": stdout.count('<<<<<<< ') if success else 0,
            "timestamp": self.timestamp
        }
        
        print(f"   📊 Current files: {analysis['current_files']}")
        print(f"   📊 Potential conflicts detected: {analysis['potential_conflicts']}")
        
        return analysis
    
    def create_safe_backup(self) -> Dict:
        """ConflictCoordinator: Create comprehensive backup before merge attempt."""
        print("💾 ConflictCoordinator: Creating safe backup...")
        
        config = self.config["gitConflictResolution"]["contextPreservation"]
        stash_message = f"{config['stashMessage']} - {self.timestamp}"
        
        success, stdout, stderr = self._run_command(f'git stash push -m "{stash_message}"')
        if not success:
            return {"error": f"Failed to create stash: {stderr}"}
        
        success, stdout, stderr = self._run_command("git stash list")
        stash_created = stash_message in stdout if success else False
        
        patch_file = f"/tmp/git_conflict_backup_{self.timestamp}.patch"
        self._run_command(f"git diff HEAD > {patch_file}")
        
        backup_info = {
            "stash_message": stash_message,
            "stash_created": stash_created,
            "patch_file": patch_file,
            "timestamp": self.timestamp
        }
        
        print(f"   ✅ Stash created: {stash_created}")
        print(f"   ✅ Patch backup: {patch_file}")
        
        return backup_info
    
    def attempt_merge(self) -> Dict:
        """ConflictCoordinator: Attempt to pull and merge changes from origin/main."""
        print("🔄 ConflictCoordinator: Attempting merge with origin/main...")
        
        success, stdout, stderr = self._run_command("git pull origin main", timeout=120)
        
        if success:
            print("   ✅ Merge completed successfully!")
            return {"success": True, "conflicts": []}
        
        if "CONFLICT" in stderr or "would be overwritten" in stderr:
            success, stdout, stderr = self._run_command("git status --porcelain")
            conflicts = [f[3:] for f in stdout.split('\n') if f.startswith('UU ') or f.startswith('AA ')]
            
            print(f"   ⚠️  Merge conflicts detected: {len(conflicts)} files")
            return {"success": False, "conflicts": conflicts, "error": "merge_conflicts"}
        
        print(f"   ❌ Merge failed: {stderr}")
        return {"success": False, "error": stderr}
    
    def categorize_conflicts(self, conflicts: List[str]) -> Dict:
        """FileClassifier: Categorize conflicts by type and priority."""
        print("📂 FileClassifier: Categorizing conflicts...")
        
        categories = self.config["gitConflictResolution"]["conflictCategories"]
        categorized = {cat: [] for cat in categories.keys()}
        uncategorized = []
        
        for conflict_file in conflicts:
            categorized_file = False
            
            for category, config in categories.items():
                if "files" in config and conflict_file in config["files"]:
                    categorized[category].append(conflict_file)
                    categorized_file = True
                    break
                
                if "patterns" in config:
                    for pattern in config["patterns"]:
                        if self._matches_pattern(conflict_file, pattern):
                            categorized[category].append(conflict_file)
                            categorized_file = True
                            break
                    if categorized_file:
                        break
            
            if not categorized_file:
                uncategorized.append(conflict_file)
        
        for category, files in categorized.items():
            if files:
                priority = categories[category]["priority"]
                print(f"   📋 {category} ({priority}): {len(files)} files")
        
        if uncategorized:
            print(f"   ❓ Uncategorized: {len(uncategorized)} files")
        
        return {"categorized": categorized, "uncategorized": uncategorized}
    
    def _matches_pattern(self, filepath: str, pattern: str) -> bool:
        """Simple pattern matching for file paths."""
        if '*' in pattern:
            if pattern.endswith('*'):
                return filepath.startswith(pattern[:-1])
            elif pattern.startswith('*'):
                return filepath.endswith(pattern[1:])
            else:
                return False
        return filepath == pattern
    
    def resolve_conflicts_by_category(self, categorized_conflicts: Dict) -> Dict:
        """ConflictResolver: Resolve conflicts based on category strategies."""
        print("🔧 ConflictResolver: Resolving conflicts by category...")
        
        categories = self.config["gitConflictResolution"]["conflictCategories"]
        resolution_results = {}
        
        high_priority = ["pydantic_migration", "dependency_updates", "ci_configuration"]
        
        for category in high_priority:
            if category in categorized_conflicts["categorized"] and categorized_conflicts["categorized"][category]:
                files = categorized_conflicts["categorized"][category]
                strategy = categories[category]["strategy"]
                
                print(f"   🔧 Resolving {category} ({len(files)} files) with strategy: {strategy}")
                
                if strategy == "preserve_pr4_changes":
                    for file in files:
                        success, _, stderr = self._run_command(f"git checkout --theirs {file}")
                        if success:
                            self._run_command(f"git add {file}")
                            print(f"      ✅ Preserved PR #4 changes: {file}")
                        else:
                            print(f"      ❌ Failed to resolve: {file} - {stderr}")
                
                resolution_results[category] = {"files": files, "strategy": strategy}
        
        return resolution_results
    
    def validate_resolution(self) -> Dict:
        """ValidationAgent: Validate that the resolution preserved critical functionality."""
        print("✅ ValidationAgent: Validating conflict resolution...")
        
        validation_config = self.config["gitConflictResolution"]["validation"]
        results = {}
        
        for check in validation_config["criticalChecks"]:
            name = check["name"]
            command = check["command"]
            timeout = check.get("timeout", 10)
            
            print(f"   🧪 Running validation: {name}")
            success, stdout, stderr = self._run_command(command, timeout)
            
            results[name] = {
                "success": success,
                "output": stdout.strip(),
                "error": stderr.strip() if stderr else None
            }
            
            if success:
                print(f"      ✅ {name}: PASSED")
            else:
                print(f"      ❌ {name}: FAILED - {stderr}")
        
        return results
    
    def execute_agent_assisted_resolution(self) -> Dict:
        """Main execution method for agent-assisted git conflict resolution."""
        print("🚀 Starting Agent-Assisted Git Conflict Resolution")
        print("=" * 60)
        
        results = {}
        
        try:
            results["analysis"] = self.analyze_git_status()
            if "error" in results["analysis"]:
                return results
            
            results["backup"] = self.create_safe_backup()
            if "error" in results["backup"]:
                return results
            
            results["merge"] = self.attempt_merge()
            
            if results["merge"]["success"]:
                print("🎉 Merge completed without conflicts!")
                results["validation"] = self.validate_resolution()
                return results
            
            if results["merge"].get("conflicts"):
                results["categorization"] = self.categorize_conflicts(results["merge"]["conflicts"])
                results["resolution"] = self.resolve_conflicts_by_category(results["categorization"])
                
                success, stdout, stderr = self._run_command("git commit --no-edit")
                if success:
                    print("   ✅ Merge commit completed")
                    results["validation"] = self.validate_resolution()
                else:
                    print(f"   ❌ Failed to complete merge: {stderr}")
                    results["error"] = f"Failed to complete merge: {stderr}"
            
            return results
            
        except Exception as e:
            print(f"❌ Agent resolution failed: {e}")
            return {"error": str(e)}

def main():
    """Main entry point for agent-assisted git conflict resolution."""
    resolver = AgentGitResolver()
    results = resolver.execute_agent_assisted_resolution()
    
    print("\n" + "=" * 60)
    print("📊 AGENT RESOLUTION SUMMARY")
    print("=" * 60)
    
    if "error" in results:
        print(f"❌ Resolution failed: {results['error']}")
        sys.exit(1)
    
    if results.get("merge", {}).get("success"):
        print("✅ Merge completed successfully without conflicts")
    elif results.get("resolution"):
        print("✅ Conflicts resolved using agent coordination")
    
    if results.get("validation"):
        validation = results["validation"]
        passed = sum(1 for v in validation.values() if v["success"])
        total = len(validation)
        print(f"🧪 Validation: {passed}/{total} checks passed")
        
        if passed == total:
            print("🎉 All validations passed - CI fixes are active!")
        else:
            print("⚠️  Some validations failed - manual review needed")
    
    print("\n💡 Next steps:")
    print("   1. Review the merge results")
    print("   2. Run your tests to verify functionality")
    print("   3. Commit any remaining changes if needed")

if __name__ == "__main__":
    main()
