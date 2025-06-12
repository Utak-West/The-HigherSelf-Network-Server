# Devin AI Integration Guide
## The HigherSelf Network Server - AI Agent Communication Protocol

> **Version**: 1.0.0  
> **Last Updated**: 2025-06-12  
> **Target Agent**: Devin AI (Autonomous Software Engineer)

---

## 🎯 Purpose

This guide establishes clear communication protocols, syntax standards, and operational procedures for **Devin AI** when working on The HigherSelf Network Server codebase. It prevents confusion between AI agents and ensures consistent, reliable automation.

## 🤖 Agent Identification

### Devin AI Profile
- **Name**: Devin AI
- **Role**: Autonomous Software Engineer
- **Primary Capabilities**:
  - Code generation and modification
  - Repository analysis and navigation
  - Automated testing and deployment
  - Git operations and branch management
  - Environment setup and configuration

### Communication Style
- **Tone**: Direct, technical, action-oriented
- **Format**: JSON, YAML, Python, Shell commands
- **Error Reporting**: Include full context and reproduction steps
- **Status Updates**: Use git commit messages for progress tracking

## 🚀 Quick Start for Devin

### Essential Commands Sequence
```bash
# 1. Navigate to project
cd ~/repos/The-HigherSelf-Network-Server

# 2. Set environment variables
export TEST_MODE=True
export DISABLE_WEBHOOKS=True
export PYTHONPATH=.

# 3. Run validation
python3 scripts/devin_simple_validation.py

# 4. Test server (brief)
python3 scripts/devin_test_server.py

# 5. Full deployment (if validation passes)
docker-compose up -d

# 6. Verify health
curl http://localhost:8000/health
```

### Automated Assistant
```bash
# Use the deployment assistant for automated operations
python3 scripts/devin_deployment_assistant.py validate
python3 scripts/devin_deployment_assistant.py deploy
python3 scripts/devin_deployment_assistant.py status
```

## 📁 Repository Structure

### Key Entry Points
- `main.py` - Main application entry point
- `scripts/devin_simple_validation.py` - Quick environment validation
- `scripts/devin_test_server.py` - Minimal test server
- `scripts/devin_deployment_assistant.py` - Automated deployment helper
- `docker-compose.yml` - Full stack deployment
- `DEVIN_DEPLOYMENT_READY.md` - Deployment documentation

### Critical Directories
```
agents/          # AI agent personalities and behaviors
├── agent_personalities.py  # Grace Fields and other agents
├── mcp_tools/              # MCP tools integration
└── tools/                  # Agent-specific tools

api/             # FastAPI routes and middleware
├── routers/                # API endpoint definitions
├── middleware/             # Security and rate limiting
└── models/                 # Request/response models

services/        # Business logic and external integrations
├── notion_service.py       # Notion database operations
├── ai_providers/           # AI service integrations
└── external/               # Third-party APIs

integrations/    # Platform-specific integrations
├── the7space/              # Art gallery integration
├── huggingface/            # AI model integration
└── capcut-pipit/           # Video editing integration

scripts/         # Utility and deployment scripts
├── devin_*.py              # Devin-specific tools
├── standalone/             # Independent utilities
└── deployment/             # Deployment automation

config/          # Configuration and settings
tests/           # Test suites and validation
docs/            # Documentation and guides
```

## 🔧 Syntax Standards

### Python Code Standards
```python
# Imports (use specific imports, avoid wildcards)
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# Field validators (correct format)
@field_validator('field_name', mode='before')
def validate_field(cls, v):
    if not v:
        raise ValueError('Field is required')
    return v

# Async functions (with proper error handling)
async def function_name(param: Type) -> ReturnType:
    """Function description."""
    try:
        result = await some_operation(param)
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise

# API endpoints (consistent structure)
@router.post("/endpoint", response_model=ResponseModel)
async def endpoint_name(
    request: RequestModel,
    service: Service = Depends(get_service)
) -> ResponseModel:
    """Endpoint description."""
    try:
        result = await service.process(request)
        return ResponseModel(**result)
    except Exception as e:
        logger.error(f"Endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Git Commit Standards
```
type(scope): description

Examples:
- fix(api): resolve import error in crawl_router.py
- feat(agents): add Devin training protocol  
- docs(readme): update deployment instructions
- refactor(services): optimize notion service performance
```

### Environment Variables
```bash
# Required for testing
TEST_MODE=True
DISABLE_WEBHOOKS=True
PYTHONPATH=.

# Optional for development
DEBUG=True
LOG_LEVEL=INFO
```

## 🔍 Validation Procedures

### Pre-Deployment Checklist
1. ✅ **Environment Check**: Python 3.8+, Docker, Git available
2. ✅ **Repository State**: Clean git status, no uncommitted changes
3. ✅ **Syntax Validation**: No import errors, proper field validators
4. ✅ **Simple Validation**: `devin_simple_validation.py` passes
5. ✅ **Test Server**: `devin_test_server.py` runs successfully
6. ✅ **Health Check**: All endpoints respond correctly

### Validation Commands
```bash
# Quick validation
python3 scripts/devin_simple_validation.py

# Comprehensive validation
python3 scripts/devin_deployment_assistant.py validate

# Test server (10-second test)
python3 scripts/devin_test_server.py

# Full deployment validation
docker-compose up -d && curl http://localhost:8000/health
```

## 🚨 Error Resolution Patterns

### Common Issues and Solutions

#### Import Errors
```bash
# Check Python path
python3 -c "import sys; print(sys.path)"

# Set PYTHONPATH
export PYTHONPATH=.

# Verify virtual environment
which python3
pip list | grep -E "(fastapi|pydantic|uvicorn)"
```

#### Merge Conflicts
```bash
# Check git status
git status

# Use automated resolution (if available)
python3 scripts/agent_git_resolver.py

# Manual resolution
git stash
git pull --rebase origin main
git stash pop
```

#### Validation Failures
```bash
# Run diagnostics
python3 scripts/devin_deployment_assistant.py troubleshoot

# Check logs
docker-compose logs --tail=50

# Reset environment
python3 scripts/devin_deployment_assistant.py reset
```

#### Deployment Issues
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose down && docker-compose up -d

# Health check
curl -v http://localhost:8000/health
```

## 🔄 Operational Protocols

### Deployment Workflow
1. **Validate Environment** → Run environment checks
2. **Code Validation** → Syntax and import verification
3. **Test Execution** → Run validation scripts
4. **Deployment** → Docker compose deployment
5. **Health Verification** → Endpoint and service checks
6. **Monitoring** → Ongoing health monitoring

### Collaboration Guidelines
- **Task Ownership**: First agent to claim task owns it
- **Handoff Protocol**: Clear status updates in commit messages
- **Shared Resources**: Use locking mechanisms for critical operations
- **Communication**: Git commits and repository documentation

### Safety Protocols
- **Backup Strategy**: Always backup before major changes
- **Rollback Plan**: Maintain rollback capability
- **Validation Required**: All changes must pass validation
- **Testing Required**: Automated testing before deployment

## 📊 Success Metrics

### Deployment Success Indicators
- ✅ Clean git repository state
- ✅ All validation scripts pass
- ✅ Services start without errors
- ✅ Health endpoints respond correctly
- ✅ No syntax or import errors
- ✅ Docker containers running
- ✅ API endpoints accessible

### Performance Benchmarks
- Validation time: < 2 minutes
- Deployment time: < 5 minutes
- Health check response: < 1 second
- Container startup: < 30 seconds

## 🎯 Next Steps for Devin

1. **Run Training Protocol**: `python3 scripts/devin_ai_agent_training_protocol.py`
2. **Validate Environment**: `python3 scripts/devin_deployment_assistant.py validate`
3. **Deploy Server**: `python3 scripts/devin_deployment_assistant.py deploy`
4. **Monitor Status**: `python3 scripts/devin_deployment_assistant.py status`
5. **Review Documentation**: Read `DEVIN_DEPLOYMENT_READY.md`

---

## 📞 Support and Resources

- **Training Protocol**: `scripts/devin_ai_agent_training_protocol.py`
- **Deployment Assistant**: `scripts/devin_deployment_assistant.py`
- **Validation Scripts**: `scripts/devin_simple_validation.py`
- **Test Server**: `scripts/devin_test_server.py`
- **Operation Logs**: `logs/devin_operations.log`

**Remember**: Always validate before deploying, communicate clearly through git commits, and use the automated tools provided for consistent operations.
