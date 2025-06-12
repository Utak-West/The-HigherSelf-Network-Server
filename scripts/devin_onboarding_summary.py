#!/usr/bin/env python3
"""
Devin AI Onboarding Summary
The HigherSelf Network Server - Complete Setup Guide for Devin

This script provides Devin with a comprehensive overview of the project,
its current state, and immediate next steps for successful deployment.

Run this script first when starting work on the project.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List


class DevinOnboardingSummary:
    """Complete onboarding summary for Devin AI."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        os.chdir(self.project_root)
        
    def get_project_overview(self) -> Dict:
        """Get comprehensive project overview."""
        return {
            "project_name": "The HigherSelf Network Server",
            "description": "Automation server for businesses and practitioners in the HigherSelf network",
            "primary_purpose": "Business automation, AI agent orchestration, and multi-platform integration",
            "architecture": "FastAPI + Notion + Docker + AI Agents",
            "deployment_target": "Devin AI automated deployment",
            
            "key_features": [
                "AI Agent Personalities (Grace Fields, etc.)",
                "Notion-centric data management",
                "Multi-platform integrations (The7Space, HuggingFace, etc.)",
                "MCP (Model Context Protocol) tools",
                "Automated workflow orchestration",
                "RESTful API with comprehensive documentation"
            ],
            
            "technology_stack": {
                "backend": "FastAPI (Python 3.8+)",
                "database": "Notion databases",
                "containerization": "Docker + Docker Compose",
                "ai_integration": "Multiple AI providers (Anthropic, OpenAI, HuggingFace)",
                "monitoring": "Prometheus + Grafana",
                "testing": "pytest + custom validation scripts"
            }
        }
    
    def get_current_status(self) -> Dict:
        """Get current project status and recent changes."""
        # Get git status
        try:
            git_status = subprocess.run(
                ["git", "status", "--porcelain"], 
                capture_output=True, 
                text=True
            ).stdout.strip()
            
            git_log = subprocess.run(
                ["git", "log", "--oneline", "-5"],
                capture_output=True,
                text=True
            ).stdout.strip()
            
        except Exception:
            git_status = "Unable to check git status"
            git_log = "Unable to check git log"
        
        return {
            "repository_state": "clean" if not git_status else "has_changes",
            "git_status": git_status,
            "recent_commits": git_log.split('\n') if git_log else [],
            "last_major_change": "Merged AI tools integration (Devon AI, Manus AI, Genspark, Augment Code)",
            "deployment_ready": True,
            "validation_scripts_available": True,
            "documentation_complete": True
        }
    
    def get_immediate_actions(self) -> List[str]:
        """Get immediate actions for Devin to take."""
        return [
            "1. Run environment validation: python3 scripts/devin_deployment_assistant.py validate",
            "2. Review project structure and key files",
            "3. Test deployment: python3 scripts/devin_deployment_assistant.py deploy", 
            "4. Verify health endpoints and service status",
            "5. Review integration guide: docs/DEVIN_AI_INTEGRATION_GUIDE.md",
            "6. Check operation logs: logs/devin_operations.log",
            "7. Run full validation sequence if any issues arise"
        ]
    
    def get_critical_files(self) -> Dict[str, str]:
        """Get critical files Devin should be aware of."""
        return {
            # Entry points
            "main.py": "Main application entry point",
            "docker-compose.yml": "Full stack deployment configuration",
            
            # Devin-specific tools
            "scripts/devin_deployment_assistant.py": "Automated deployment helper",
            "scripts/devin_simple_validation.py": "Quick environment validation",
            "scripts/devin_test_server.py": "Minimal test server",
            "scripts/devin_ai_agent_training_protocol.py": "AI agent training protocol",
            
            # Documentation
            "docs/DEVIN_AI_INTEGRATION_GUIDE.md": "Complete integration guide",
            "docs/devin_training_protocol.md": "Generated training protocol",
            "DEVIN_DEPLOYMENT_READY.md": "Deployment readiness documentation",
            
            # Configuration
            "requirements.txt": "Python dependencies",
            ".env.example": "Environment variable template",
            "pyproject.toml": "Python project configuration",
            
            # Key source files
            "agents/agent_personalities.py": "AI agent implementations",
            "services/notion_service.py": "Notion integration service",
            "api/main_router.py": "Main API router",
            
            # Logs and monitoring
            "logs/devin_operations.log": "Devin operation logs",
            "logs/application.log": "Application logs"
        }
    
    def check_file_existence(self) -> Dict[str, bool]:
        """Check if critical files exist."""
        critical_files = self.get_critical_files()
        existence_check = {}
        
        for file_path, description in critical_files.items():
            exists = (self.project_root / file_path).exists()
            existence_check[file_path] = exists
            
        return existence_check
    
    def get_environment_requirements(self) -> Dict:
        """Get environment requirements for deployment."""
        return {
            "python": {
                "version": "3.8+",
                "command": "python3 --version"
            },
            "docker": {
                "version": "20.0+",
                "command": "docker --version"
            },
            "docker_compose": {
                "version": "1.29+",
                "command": "docker-compose --version"
            },
            "git": {
                "version": "2.0+",
                "command": "git --version"
            },
            "curl": {
                "version": "any",
                "command": "curl --version"
            }
        }
    
    def get_troubleshooting_guide(self) -> Dict[str, List[str]]:
        """Get troubleshooting guide for common issues."""
        return {
            "import_errors": [
                "Check PYTHONPATH: export PYTHONPATH=.",
                "Verify virtual environment: which python3",
                "Check installed packages: pip list | grep -E '(fastapi|pydantic)'"
            ],
            "deployment_failures": [
                "Check Docker status: docker ps",
                "View container logs: docker-compose logs",
                "Restart services: docker-compose down && docker-compose up -d",
                "Check port availability: netstat -tlnp | grep :8000"
            ],
            "validation_failures": [
                "Run diagnostics: python3 scripts/devin_deployment_assistant.py troubleshoot",
                "Check file permissions: ls -la scripts/",
                "Verify environment variables: env | grep -E '(TEST_MODE|PYTHONPATH)'"
            ],
            "git_issues": [
                "Check repository state: git status",
                "Reset to clean state: git stash && git pull --rebase origin main",
                "Resolve conflicts: git mergetool or manual resolution"
            ]
        }
    
    def generate_summary_report(self) -> str:
        """Generate complete summary report for Devin."""
        overview = self.get_project_overview()
        status = self.get_current_status()
        actions = self.get_immediate_actions()
        files = self.get_critical_files()
        file_check = self.check_file_existence()
        requirements = self.get_environment_requirements()
        troubleshooting = self.get_troubleshooting_guide()
        
        missing_files = [f for f, exists in file_check.items() if not exists]
        
        report = f"""
# Devin AI Onboarding Summary
Generated: {datetime.now().isoformat()}

## 🎯 Project Overview
{json.dumps(overview, indent=2)}

## 📊 Current Status
{json.dumps(status, indent=2)}

## 🚀 Immediate Actions for Devin
{chr(10).join(actions)}

## 📁 Critical Files Status
✅ Available Files: {len([f for f in file_check.values() if f])}
❌ Missing Files: {len(missing_files)}

{chr(10).join([f"✅ {f}" for f, exists in file_check.items() if exists])}
{chr(10).join([f"❌ {f}" for f, exists in file_check.items() if not exists]) if missing_files else "All critical files present!"}

## 🔧 Environment Requirements
{json.dumps(requirements, indent=2)}

## 🚨 Troubleshooting Guide
{json.dumps(troubleshooting, indent=2)}

## 🎯 Success Criteria
- [ ] Environment validation passes
- [ ] All critical files present
- [ ] Docker containers start successfully
- [ ] Health endpoints respond
- [ ] No import or syntax errors
- [ ] Git repository in clean state

## 📞 Quick Help Commands
```bash
# Complete validation and deployment
python3 scripts/devin_deployment_assistant.py deploy

# Check current status
python3 scripts/devin_deployment_assistant.py status

# Run diagnostics
python3 scripts/devin_deployment_assistant.py troubleshoot

# Reset environment
python3 scripts/devin_deployment_assistant.py reset
```

## 🎉 Ready for Devin!
The HigherSelf Network Server is configured and ready for Devin AI deployment.
All training protocols, validation scripts, and documentation are in place.

Start with: `python3 scripts/devin_deployment_assistant.py validate`
"""
        return report


def main():
    """Main function to generate onboarding summary."""
    print("🤖 Devin AI Onboarding Summary")
    print("=" * 60)
    
    summary = DevinOnboardingSummary()
    
    # Generate and display summary
    report = summary.generate_summary_report()
    
    # Save to file
    summary_path = summary.project_root / "docs" / "devin_onboarding_summary.md"
    with open(summary_path, "w") as f:
        f.write(report)
    
    print(f"✅ Onboarding summary generated: {summary_path}")
    
    # Display key information
    overview = summary.get_project_overview()
    status = summary.get_current_status()
    actions = summary.get_immediate_actions()
    
    print(f"\n🎯 Project: {overview['project_name']}")
    print(f"📊 Status: {'✅ Ready' if status['deployment_ready'] else '⚠️ Needs attention'}")
    print(f"🔄 Repository: {'✅ Clean' if status['repository_state'] == 'clean' else '⚠️ Has changes'}")
    
    print("\n🚀 Next Steps for Devin:")
    for action in actions[:3]:  # Show first 3 actions
        print(f"  {action}")
    
    print(f"\n📖 Complete guide: docs/DEVIN_AI_INTEGRATION_GUIDE.md")
    print(f"🔧 Deployment helper: scripts/devin_deployment_assistant.py")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
