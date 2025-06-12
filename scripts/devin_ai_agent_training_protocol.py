#!/usr/bin/env python3
"""
Devin AI Agent Training Protocol
The HigherSelf Network Server - AI Agent Communication Standards

This script establishes clear communication protocols, syntax standards, and
operational guidelines for Devin and other AI agents working on this codebase.

Purpose: Prevent confusion between AI agents and establish consistent patterns.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class DevinTrainingProtocol:
    """
    Training protocol for Devin AI and other agents working on The HigherSelf Network Server.

    This class defines:
    - Communication standards
    - Syntax conventions
    - Operational protocols
    - Error handling patterns
    - Deployment procedures
    """

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.protocol_version = "1.0.0"
        self.last_updated = datetime.now().isoformat()

    def get_communication_standards(self) -> Dict:
        """Define clear communication standards for AI agents."""
        return {
            "agent_identification": {
                "devin": {
                    "name": "Devin AI",
                    "role": "Autonomous Software Engineer",
                    "capabilities": [
                        "Code generation and modification",
                        "Repository analysis and navigation",
                        "Automated testing and deployment",
                        "Git operations and branch management",
                        "Environment setup and configuration",
                    ],
                    "communication_style": "Direct, technical, action-oriented",
                    "preferred_formats": ["JSON", "YAML", "Python", "Shell commands"],
                },
                "grace_fields": {
                    "name": "Grace Fields",
                    "role": "Customer Service & Business Operations Agent",
                    "capabilities": [
                        "Customer interaction and support",
                        "Business process automation",
                        "Notion database management",
                        "Workflow orchestration",
                        "Multi-platform integration",
                    ],
                    "communication_style": "Professional, empathetic, solution-focused",
                    "preferred_formats": [
                        "Natural language",
                        "Structured data",
                        "API responses",
                    ],
                },
                "augment_agent": {
                    "name": "Augment Agent",
                    "role": "Code Analysis & Enhancement Assistant",
                    "capabilities": [
                        "Codebase analysis and understanding",
                        "Code quality improvement",
                        "Documentation generation",
                        "Refactoring suggestions",
                        "Architecture recommendations",
                    ],
                    "communication_style": "Analytical, detailed, educational",
                    "preferred_formats": [
                        "Code snippets",
                        "Documentation",
                        "Analysis reports",
                    ],
                },
            },
            "syntax_conventions": {
                "python": {
                    "style_guide": "PEP 8 with Black formatting (88 char line length)",
                    "import_order": "isort with profile=black",
                    "type_hints": "Required for all public functions and methods",
                    "docstrings": "Google style docstrings",
                    "error_handling": "Explicit exception handling with logging",
                    "async_patterns": "Use async/await for I/O operations",
                },
                "git": {
                    "commit_format": "type(scope): description",
                    "branch_naming": "feature/description or fix/description",
                    "merge_strategy": "Rebase for clean history",
                    "conflict_resolution": "Use automated scripts when possible",
                },
                "api": {
                    "response_format": "JSON with consistent error structure",
                    "status_codes": "Standard HTTP status codes",
                    "authentication": "Bearer token or API key based",
                    "rate_limiting": "Implement for all external APIs",
                },
            },
            "operational_protocols": {
                "deployment": {
                    "validation_required": True,
                    "testing_required": True,
                    "backup_strategy": "Always backup before major changes",
                    "rollback_plan": "Maintain rollback capability",
                    "monitoring": "Health checks and logging required",
                },
                "collaboration": {
                    "conflict_resolution": "First agent to claim task owns it",
                    "handoff_protocol": "Clear status updates in commit messages",
                    "shared_resources": "Use locking mechanisms for critical operations",
                    "communication_channel": "Git commits and repository documentation",
                },
            },
        }

    def get_devin_specific_guidelines(self) -> Dict:
        """Specific guidelines for Devin AI agent."""
        return {
            "repository_navigation": {
                "entry_points": [
                    "main.py - Main application entry point",
                    "scripts/devin_simple_validation.py - Quick environment validation",
                    "scripts/devin_test_server.py - Minimal test server",
                    "docker-compose.yml - Full stack deployment",
                    "DEVIN_DEPLOYMENT_READY.md - Deployment documentation",
                ],
                "key_directories": {
                    "agents/": "AI agent personalities and behaviors",
                    "api/": "FastAPI routes and middleware",
                    "services/": "Business logic and external integrations",
                    "integrations/": "Third-party platform integrations",
                    "scripts/": "Utility and deployment scripts",
                    "config/": "Configuration and settings",
                    "tests/": "Test suites and validation",
                },
            },
            "deployment_procedures": {
                "validation_sequence": [
                    "1. Run python3 scripts/devin_simple_validation.py",
                    "2. Check git status for clean working directory",
                    "3. Run python3 scripts/devin_test_server.py (brief test)",
                    "4. Execute docker-compose up -d for full deployment",
                    "5. Verify health endpoints and service status",
                ],
                "environment_setup": {
                    "python_version": "3.8+",
                    "required_tools": ["docker", "git", "python3", "pip"],
                    "environment_variables": [
                        "TEST_MODE=True for testing",
                        "DISABLE_WEBHOOKS=True for local development",
                        "PYTHONPATH=. for imports",
                    ],
                },
            },
            "error_handling": {
                "import_errors": "Check PYTHONPATH and virtual environment",
                "merge_conflicts": "Use scripts/agent_git_resolver.py for automation",
                "validation_failures": "Run devin_simple_validation.py for diagnosis",
                "deployment_issues": "Check docker-compose logs and health endpoints",
            },
            "communication_patterns": {
                "status_updates": "Use git commit messages for progress tracking",
                "error_reporting": "Include full error context and reproduction steps",
                "success_confirmation": "Provide validation results and next steps",
                "handoff_protocol": "Clear documentation of current state and next actions",
            },
        }

    def get_syntax_examples(self) -> Dict:
        """Provide concrete syntax examples for consistency."""
        return {
            "python_imports": {
                "correct": [
                    "from datetime import datetime",
                    "from typing import Dict, List, Optional",
                    "from pydantic import BaseModel, Field, field_validator",
                ],
                "avoid": [
                    "from pydantic import *",
                    "import typing as t",
                    "from datetime import *",
                ],
            },
            "git_commands": {
                "safe_operations": [
                    "git status",
                    "git log --oneline -5",
                    "git fetch origin",
                    "git pull --rebase origin main",
                ],
                "requires_caution": [
                    "git push origin main",
                    "git merge",
                    "git rebase",
                    "git reset --hard",
                ],
            },
            "validation_patterns": {
                "field_validators": [
                    "@field_validator('field_name', mode='before')",
                    "def validate_field(cls, v):",
                    "    if not v:",
                    "        raise ValueError('Field is required')",
                    "    return v",
                ],
                "error_handling": [
                    "try:",
                    "    # operation",
                    "except SpecificException as e:",
                    "    logger.error(f'Operation failed: {e}')",
                    "    raise HTTPException(status_code=400, detail=str(e))",
                ],
            },
        }

    def generate_training_report(self) -> str:
        """Generate a comprehensive training report for AI agents."""
        standards = self.get_communication_standards()
        devin_guidelines = self.get_devin_specific_guidelines()
        syntax_examples = self.get_syntax_examples()

        report = f"""
# AI Agent Training Protocol Report
Generated: {self.last_updated}
Protocol Version: {self.protocol_version}

## Agent Identification and Roles
{json.dumps(standards['agent_identification'], indent=2)}

## Devin-Specific Guidelines
{json.dumps(devin_guidelines, indent=2)}

## Syntax Conventions
{json.dumps(standards['syntax_conventions'], indent=2)}

## Operational Protocols
{json.dumps(standards['operational_protocols'], indent=2)}

## Syntax Examples
{json.dumps(syntax_examples, indent=2)}

## Quick Reference for Devin

### Essential Commands
1. Validation: `python3 scripts/devin_simple_validation.py`
2. Test Server: `python3 scripts/devin_test_server.py`
3. Full Deployment: `docker-compose up -d`
4. Git Status: `git status`
5. Health Check: `curl http://localhost:8000/health`

### Key Files to Monitor
- main.py (application entry)
- requirements.txt (dependencies)
- docker-compose.yml (deployment config)
- .env files (environment variables)
- scripts/devin_*.py (Devin-specific tools)

### Error Resolution Patterns
1. Import errors → Check PYTHONPATH and virtual environment
2. Merge conflicts → Use automated resolution scripts
3. Validation failures → Run diagnostic scripts
4. Deployment issues → Check logs and health endpoints

### Communication Protocol
- Use clear, technical language
- Provide specific error messages and context
- Include reproduction steps for issues
- Document all changes in git commits
- Validate before and after major operations

## Success Metrics
- Clean git repository state
- All validation scripts pass
- Services start without errors
- Health endpoints respond correctly
- No syntax or import errors
"""
        return report


def main():
    """Main function to generate and display training protocol."""
    print("🤖 Devin AI Agent Training Protocol")
    print("=" * 60)

    protocol = DevinTrainingProtocol()

    # Generate training report
    report = protocol.generate_training_report()

    # Save to file
    report_path = protocol.project_root / "docs" / "devin_training_protocol.md"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w") as f:
        f.write(report)

    print(f"✅ Training protocol generated: {report_path}")
    print("\n📋 Quick Reference for Devin:")
    print("1. Always run validation before major operations")
    print("2. Use consistent syntax patterns as defined in protocol")
    print("3. Communicate clearly with technical precision")
    print("4. Follow git best practices for clean history")
    print("5. Validate deployment after changes")

    print(f"\n🎯 Protocol Version: {protocol.protocol_version}")
    print(f"📅 Last Updated: {protocol.last_updated}")

    return 0


class DevinCommandReference:
    """Quick command reference for Devin AI operations."""

    @staticmethod
    def get_essential_commands() -> Dict[str, List[str]]:
        """Get essential commands for Devin operations."""
        return {
            "validation": [
                "cd ~/repos/The-HigherSelf-Network-Server",
                "export TEST_MODE=True",
                "export DISABLE_WEBHOOKS=True",
                "python3 scripts/devin_simple_validation.py",
                "python3 scripts/devin_test_server.py",
            ],
            "git_operations": [
                "git status",
                "git pull --rebase origin main",
                "git add .",
                "git commit -m 'type: description'",
                "git push origin main",
            ],
            "deployment": [
                "docker-compose down",
                "docker-compose up -d",
                "curl http://localhost:8000/health",
                "docker-compose logs -f",
            ],
            "troubleshooting": [
                "python3 -c 'import sys; print(sys.path)'",
                "which python3",
                "pip list | grep -E '(fastapi|pydantic|uvicorn)'",
                "docker ps",
                "docker-compose ps",
            ],
        }

    @staticmethod
    def get_syntax_patterns() -> Dict[str, str]:
        """Get consistent syntax patterns for Devin."""
        return {
            "field_validator": """@field_validator('field_name', mode='before')
def validate_field(cls, v):
    if not v:
        raise ValueError('Field is required')
    return v""",
            "async_function": """async def function_name(param: Type) -> ReturnType:
    \"\"\"Function description.\"\"\"
    try:
        result = await some_operation(param)
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise""",
            "api_endpoint": """@router.post("/endpoint", response_model=ResponseModel)
async def endpoint_name(
    request: RequestModel,
    service: Service = Depends(get_service)
) -> ResponseModel:
    \"\"\"Endpoint description.\"\"\"
    try:
        result = await service.process(request)
        return ResponseModel(**result)
    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))""",
            "git_commit": """type(scope): description

- Fix specific issue or add feature
- Include context and reasoning
- Reference issue numbers if applicable

Examples:
- fix(api): resolve import error in crawl_router.py
- feat(agents): add Devin training protocol
- docs(readme): update deployment instructions""",
        }


if __name__ == "__main__":
    sys.exit(main())
