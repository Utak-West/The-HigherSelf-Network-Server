
# AI Agent Training Protocol Report
Generated: 2025-06-12T12:54:04.793223
Protocol Version: 1.0.0

## Agent Identification and Roles
{
  "devin": {
    "name": "Devin AI",
    "role": "Autonomous Software Engineer",
    "capabilities": [
      "Code generation and modification",
      "Repository analysis and navigation",
      "Automated testing and deployment",
      "Git operations and branch management",
      "Environment setup and configuration"
    ],
    "communication_style": "Direct, technical, action-oriented",
    "preferred_formats": [
      "JSON",
      "YAML",
      "Python",
      "Shell commands"
    ]
  },
  "grace_fields": {
    "name": "Grace Fields",
    "role": "Customer Service & Business Operations Agent",
    "capabilities": [
      "Customer interaction and support",
      "Business process automation",
      "Notion database management",
      "Workflow orchestration",
      "Multi-platform integration"
    ],
    "communication_style": "Professional, empathetic, solution-focused",
    "preferred_formats": [
      "Natural language",
      "Structured data",
      "API responses"
    ]
  },
  "augment_agent": {
    "name": "Augment Agent",
    "role": "Code Analysis & Enhancement Assistant",
    "capabilities": [
      "Codebase analysis and understanding",
      "Code quality improvement",
      "Documentation generation",
      "Refactoring suggestions",
      "Architecture recommendations"
    ],
    "communication_style": "Analytical, detailed, educational",
    "preferred_formats": [
      "Code snippets",
      "Documentation",
      "Analysis reports"
    ]
  }
}

## Devin-Specific Guidelines
{
  "repository_navigation": {
    "entry_points": [
      "main.py - Main application entry point",
      "scripts/devin_simple_validation.py - Quick environment validation",
      "scripts/devin_test_server.py - Minimal test server",
      "docker-compose.yml - Full stack deployment",
      "DEVIN_DEPLOYMENT_READY.md - Deployment documentation"
    ],
    "key_directories": {
      "agents/": "AI agent personalities and behaviors",
      "api/": "FastAPI routes and middleware",
      "services/": "Business logic and external integrations",
      "integrations/": "Third-party platform integrations",
      "scripts/": "Utility and deployment scripts",
      "config/": "Configuration and settings",
      "tests/": "Test suites and validation"
    }
  },
  "deployment_procedures": {
    "validation_sequence": [
      "1. Run python3 scripts/devin_simple_validation.py",
      "2. Check git status for clean working directory",
      "3. Run python3 scripts/devin_test_server.py (brief test)",
      "4. Execute docker-compose up -d for full deployment",
      "5. Verify health endpoints and service status"
    ],
    "environment_setup": {
      "python_version": "3.8+",
      "required_tools": [
        "docker",
        "git",
        "python3",
        "pip"
      ],
      "environment_variables": [
        "TEST_MODE=True for testing",
        "DISABLE_WEBHOOKS=True for local development",
        "PYTHONPATH=. for imports"
      ]
    }
  },
  "error_handling": {
    "import_errors": "Check PYTHONPATH and virtual environment",
    "merge_conflicts": "Use scripts/agent_git_resolver.py for automation",
    "validation_failures": "Run devin_simple_validation.py for diagnosis",
    "deployment_issues": "Check docker-compose logs and health endpoints"
  },
  "communication_patterns": {
    "status_updates": "Use git commit messages for progress tracking",
    "error_reporting": "Include full error context and reproduction steps",
    "success_confirmation": "Provide validation results and next steps",
    "handoff_protocol": "Clear documentation of current state and next actions"
  }
}

## Syntax Conventions
{
  "python": {
    "style_guide": "PEP 8 with Black formatting (88 char line length)",
    "import_order": "isort with profile=black",
    "type_hints": "Required for all public functions and methods",
    "docstrings": "Google style docstrings",
    "error_handling": "Explicit exception handling with logging",
    "async_patterns": "Use async/await for I/O operations"
  },
  "git": {
    "commit_format": "type(scope): description",
    "branch_naming": "feature/description or fix/description",
    "merge_strategy": "Rebase for clean history",
    "conflict_resolution": "Use automated scripts when possible"
  },
  "api": {
    "response_format": "JSON with consistent error structure",
    "status_codes": "Standard HTTP status codes",
    "authentication": "Bearer token or API key based",
    "rate_limiting": "Implement for all external APIs"
  }
}

## Operational Protocols
{
  "deployment": {
    "validation_required": true,
    "testing_required": true,
    "backup_strategy": "Always backup before major changes",
    "rollback_plan": "Maintain rollback capability",
    "monitoring": "Health checks and logging required"
  },
  "collaboration": {
    "conflict_resolution": "First agent to claim task owns it",
    "handoff_protocol": "Clear status updates in commit messages",
    "shared_resources": "Use locking mechanisms for critical operations",
    "communication_channel": "Git commits and repository documentation"
  }
}

## Syntax Examples
{
  "python_imports": {
    "correct": [
      "from datetime import datetime",
      "from typing import Dict, List, Optional",
      "from pydantic import BaseModel, Field, field_validator"
    ],
    "avoid": [
      "from pydantic import *",
      "import typing as t",
      "from datetime import *"
    ]
  },
  "git_commands": {
    "safe_operations": [
      "git status",
      "git log --oneline -5",
      "git fetch origin",
      "git pull --rebase origin main"
    ],
    "requires_caution": [
      "git push origin main",
      "git merge",
      "git rebase",
      "git reset --hard"
    ]
  },
  "validation_patterns": {
    "field_validators": [
      "@field_validator('field_name', mode='before')",
      "def validate_field(cls, v):",
      "    if not v:",
      "        raise ValueError('Field is required')",
      "    return v"
    ],
    "error_handling": [
      "try:",
      "    # operation",
      "except SpecificException as e:",
      "    logger.error(f'Operation failed: {e}')",
      "    raise HTTPException(status_code=400, detail=str(e))"
    ]
  }
}

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
