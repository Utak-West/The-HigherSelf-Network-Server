# Devin AI Integration Guide
## The HigherSelf Network Server - Automated Testing & Development

### 🎯 **Quick Start for Devin**

```bash
# 1. Navigate to project directory
cd ~/repos/The-HigherSelf-Network-Server

# 2. Quick validation (30 seconds)
python3 devin_quick_validation.py

# 3. Full automated setup (2-5 minutes)
python3 devin_automated_setup.py

# 4. Run reliable tests
python3 run_tests.py
```

---

## 📋 **Project Overview**

**The HigherSelf Network Server** is a comprehensive AI-powered network server featuring:
- **FastAPI** backend with async support
- **Multi-agent AI system** with named personalities
- **Notion** as central data hub
- **Redis** for caching and messaging
- **MongoDB** for data persistence
- **Neo4j** for knowledge graphs
- **Docker** containerization

---

## 🔧 **Dependency Management**

### Python Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Development dependencies
pip install pytest pytest-asyncio black isort flake8 mypy bandit safety

# Optional LangChain dependencies
pip install -r requirements-langchain.txt
```

### Node.js Dependencies
```bash
# Main project
npm install

# API Gateway
cd api-gateway && npm install

# Strapi CMS
cd strapi-cms && npm install
```

---

## 🎨 **Code Quality Standards**

### Formatting & Linting
```bash
# Format code (Black - 88 char line length)
black . --line-length 88

# Sort imports (isort - Black compatible)
isort . --profile black

# Lint code (Flake8)
flake8 .

# Type checking (MyPy)
mypy .

# Security analysis (Bandit)
bandit -r .

# Vulnerability check (Safety)
safety check
```

### Pre-commit Hooks
```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

**Configuration Files:**
- `pyproject.toml` - Black, isort, MyPy configuration
- `.flake8` - Flake8 configuration
- `.pre-commit-config.yaml` - Pre-commit hooks

---

## 🧪 **Testing Framework**

### Reliable Test Commands (Always Pass)
```bash
# Comprehensive test runner (RECOMMENDED)
python3 run_tests.py

# Basic functionality tests
python3 -m pytest tests/test_basic_functionality.py -v --no-cov

# Redis connection test (mocked)
python3 -m pytest tests/test_redis_connection.py -v --no-cov

# Syntax validation
python3 -c "import py_compile; py_compile.compile('main.py', doraise=True)"

# Import validation
python3 -c "from models.base import *; from models.content_models import *"
```

### Test Coverage
```bash
# Generate coverage report
python3 -m pytest --cov=. --cov-report=html

# View coverage
open htmlcov/index.html
```

### Test Configuration
- **pytest**: Main testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **conftest.py**: Global test configuration with mocking

---

## 🚀 **Local Development Setup**

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Required variables (minimum):
NOTION_API_TOKEN=your_token_here
REDIS_URI=redis://localhost:6379/0
MONGODB_URI=mongodb://localhost:27017/higherselfnetwork
OPENAI_API_KEY=your_openai_key_here

# Test mode variables:
TEST_MODE=True
DISABLE_WEBHOOKS=True
```

### Application Startup
```bash
# Development mode
python3 main.py

# With specific log level
LOG_LEVEL=DEBUG python3 main.py

# Using Uvicorn directly
uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload

# Production-like with Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 -k uvicorn.workers.UvicornWorker main:app
```

### Docker Development
```bash
# Start full stack
docker-compose up -d

# Start only databases
docker-compose up -d mongodb redis neo4j

# View logs
docker-compose logs -f windsurf-agent

# Health check
curl -f http://localhost:8000/health
```

---

## ✅ **Verification Commands**

### Health Checks
```bash
# Application health
curl -f http://localhost:8000/health

# Service status
docker-compose ps

# Database connections
python3 -c "from services.redis_service import redis_service; redis_service._sync_client.ping()"
```

### System Validation
```bash
# Environment validation
python3 scripts/validate_env.py

# Quick validation (for Devin)
python3 devin_quick_validation.py

# Full automated setup (for Devin)
python3 devin_automated_setup.py
```

---

## 🎯 **Devin-Specific Commands**

### Automated Setup & Testing
```bash
# Quick validation (30 seconds)
python3 devin_quick_validation.py

# Full automated setup (2-5 minutes)
python3 devin_automated_setup.py

# Reliable test suite
python3 run_tests.py
```

### Test Environment Setup
```bash
# Set test mode
export TEST_MODE=True
export DISABLE_WEBHOOKS=True
export PYTHONPATH=$PWD

# Run tests without external dependencies
python3 -m pytest tests/test_basic_functionality.py -v --no-cov
```

---

## 🚨 **Known Issues & Solutions**

### Common Issues
1. **Import Errors**: Ensure `PYTHONPATH` is set to project root
2. **Redis Errors**: Use Docker Redis or set `TEST_MODE=True`
3. **Notion Errors**: Set test environment variables
4. **Path Issues**: Use absolute path `~/repos/The-HigherSelf-Network-Server`

### Tests to Avoid (External Dependencies)
- `tests/test_grace_fields_customer_service.py`
- `tests/test_rag_notion_integration.py`
- `tests/test_aqua_voice.py`

---

## 📊 **Project Structure**

```
The-HigherSelf-Network-Server/
├── agents/                 # AI agent implementations
├── api/                   # FastAPI routes and middleware
├── config/                # Configuration files
├── models/                # Data models and schemas
├── services/              # Business logic services
├── tests/                 # Test suite
├── tools/                 # Utility scripts
├── main.py               # Application entry point
├── run_tests.py          # Test runner
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
├── docker-compose.yml    # Docker services
└── .env.example          # Environment template
```

---

## 🔐 **Security & Environment**

### Environment Variables
- **Required**: `NOTION_API_TOKEN`, `REDIS_URI`, `MONGODB_URI`
- **Optional**: `OPENAI_API_KEY`, `NEO4J_URI`
- **Testing**: `TEST_MODE=True`, `DISABLE_WEBHOOKS=True`

### Security Scanning
```bash
# Security analysis
bandit -r . -f json -o security-report.json

# Dependency vulnerabilities
safety check

# Node.js audit
npm audit
```

---

## 📚 **Documentation**

- **DEVIN_COMPREHENSIVE_SETUP_GUIDE.md** - Complete setup guide
- **DEVIN_TESTING_GUIDE.md** - Original testing guide
- **README.md** - Main project documentation
- **docs/** - Detailed documentation directory

---

## 🎉 **Success Criteria**

### For Devin Integration
1. ✅ `python3 devin_quick_validation.py` passes (>90% success rate)
2. ✅ `python3 devin_automated_setup.py` completes successfully
3. ✅ `python3 run_tests.py` passes all tests
4. ✅ `python3 main.py` starts without errors
5. ✅ Health endpoint responds: `curl -f http://localhost:8000/health`

### Expected Outputs
- **Validation**: "🎉 VALIDATION PASSED!"
- **Setup**: "✅ All tests passed! Environment is ready for development."
- **Tests**: "🎉 ALL TESTS PASSED!"
- **Application**: Server starts on port 8000

---

**This guide provides everything needed for successful Devin AI integration with The HigherSelf Network Server.**
