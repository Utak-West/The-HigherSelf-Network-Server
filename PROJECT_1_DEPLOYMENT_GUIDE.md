# Project 1: Real-Time AI Agent Contact Processing Pipeline - Deployment Guide

## 🎯 Overview

This guide walks you through deploying **Project 1: Real-Time AI Agent Contact Processing Pipeline**, which enhances Nyra with real-time contact processing capabilities and integrates with your existing WordPress webhook system.

## 🚀 What's Been Implemented

### ✅ Core Components Created

1. **Enhanced Nyra Agent** (`agents/nyra_realtime_enhanced.py`)
   - Real-time contact processing queue
   - Multi-entity business logic (The 7 Space, AM Consulting, HigherSelf Core)
   - Intelligent contact classification and routing
   - MCP server integration ready
   - Processing metrics and monitoring

2. **Enhanced Webhook Integration** (`api/contact_workflow_webhooks.py`)
   - AI agent integration with WordPress webhooks
   - Real-time contact queuing for AI processing
   - Background task processing

3. **Enhanced Main Application** (`main_realtime_enhanced.py`)
   - Real-time AI agent initialization
   - Enhanced API endpoints for AI status and metrics
   - Lifespan management for AI agents

4. **Comprehensive Testing** (`test_realtime_ai_integration.py`)
   - Full test suite for real-time AI integration
   - Multi-entity contact processing tests
   - Webhook integration verification

## 🔧 Deployment Steps

### Step 1: Backup Current System
```bash
# Create backup of current main.py
cp main.py main_backup.py

# Create backup of current webhook file
cp api/contact_workflow_webhooks.py api/contact_workflow_webhooks_backup.py
```

### Step 2: Install Dependencies
```bash
# Ensure all required packages are installed
pip install -r requirements.txt

# If you need additional packages for real-time processing
pip install aiohttp pytest
```

### Step 3: Environment Configuration
```bash
# Add these environment variables to your .env file
echo "MCP_ENABLED=false" >> .env
echo "MCP_NOTION_ENABLED=false" >> .env
echo "MCP_FILESYSTEM_ENABLED=false" >> .env
echo "MCP_GITHUB_ENABLED=false" >> .env
echo "MCP_BRAVE_SEARCH_ENABLED=false" >> .env
echo "REALTIME_AI_ENABLED=true" >> .env
```

### Step 4: Deploy Enhanced System
```bash
# Option A: Test with enhanced main application
python main_realtime_enhanced.py

# Option B: Integrate with existing main.py (recommended for production)
# See integration instructions below
```

### Step 5: Test the Integration
```bash
# Run comprehensive test suite
python test_realtime_ai_integration.py

# Test individual components
curl http://localhost:8000/api/ai/status
curl http://localhost:8000/api/ai/metrics
curl http://localhost:8000/api/health/realtime
```

## 🔄 Integration with Existing main.py

To integrate with your existing `main.py`, add these components:

### 1. Import Enhanced Nyra
```python
from agents.nyra_realtime_enhanced import NyraRealtimeEnhanced
from api import contact_workflow_webhooks
```

### 2. Initialize in Startup
```python
# In your existing agent initialization section
nyra_realtime = NyraRealtimeEnhanced(
    notion_client=notion_service,
    mcp_enabled=os.getenv("MCP_ENABLED", "false").lower() == "true"
)

# Start real-time processing
await nyra_realtime.start_realtime_processing()

# Initialize webhook integration
contact_workflow_webhooks.initialize_ai_agents(nyra_realtime)
```

### 3. Add New API Endpoints
```python
@app.get("/api/ai/status")
async def get_ai_status():
    if nyra_realtime:
        return await nyra_realtime.get_processing_status()
    return {"error": "AI agent not initialized"}
```

## 🧪 Testing Your Deployment

### 1. Basic Health Check
```bash
curl http://localhost:8000/api/health/realtime
```

Expected response:
```json
{
  "status": "healthy",
  "components": {
    "notion_service": true,
    "nyra_realtime": true,
    "ai_processing": true,
    "mcp_integration": false
  }
}
```

### 2. AI Status Check
```bash
curl http://localhost:8000/api/ai/status
```

Expected response:
```json
{
  "is_processing": true,
  "queue_size": 0,
  "metrics": {
    "contacts_processed": 0,
    "processing_errors": 0,
    "average_processing_time": 0.0
  },
  "mcp_enabled": false
}
```

### 3. Test Contact Processing
```bash
curl -X POST http://localhost:8000/api/ai/process-contact \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@the7space.com",
    "first_name": "Test",
    "last_name": "User",
    "message": "Testing AI processing",
    "interests": ["art", "gallery"],
    "source": "test"
  }'
```

### 4. Test WordPress Webhook Integration
```bash
curl -X POST http://localhost:8000/api/contact-workflows/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "webhook@the7space.com",
    "first_name": "Webhook",
    "last_name": "Test",
    "message": "Testing webhook with AI processing",
    "interests": ["wellness"]
  }'
```

## 📊 Monitoring and Metrics

### Real-Time Monitoring
```bash
# Check AI processing metrics
curl http://localhost:8000/api/ai/metrics

# Monitor processing queue
watch -n 5 'curl -s http://localhost:8000/api/ai/status | jq .queue_size'
```

### Log Monitoring
```bash
# Monitor application logs for AI processing
tail -f logs/higherself_network.log | grep "nyra_realtime"

# Monitor contact processing
tail -f logs/higherself_network.log | grep "Contact processed"
```

## 🔧 Troubleshooting

### Common Issues

**1. AI Agent Not Starting**
```bash
# Check Notion service initialization
curl http://localhost:8000/api/health/realtime

# Verify environment variables
env | grep NOTION_TOKEN
```

**2. Contacts Not Being Processed**
```bash
# Check queue status
curl http://localhost:8000/api/ai/status

# Check processing metrics
curl http://localhost:8000/api/ai/metrics
```

**3. Webhook Integration Issues**
```bash
# Test webhook endpoint directly
curl -X POST http://localhost:8000/api/contact-workflows/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

### Debug Mode
```bash
# Run with debug logging
DEBUG=true python main_realtime_enhanced.py

# Enable verbose AI processing logs
NYRA_DEBUG=true python main_realtime_enhanced.py
```

## 🚀 Next Steps

Once Project 1 is successfully deployed:

1. **Monitor Performance**: Watch processing metrics and queue sizes
2. **Test with Real Data**: Process actual contacts from The 7 Space website
3. **Prepare for MCP Integration**: Set up MCP servers when ready
4. **Scale to Project 2**: Extend to AM Consulting and HigherSelf Core entities
5. **Implement Project 3**: Add bidirectional Notion synchronization

## 📈 Success Metrics

Your deployment is successful when:

- ✅ AI status endpoint returns `is_processing: true`
- ✅ Webhook integration includes `ai_processing_queued: true`
- ✅ Contact processing completes in under 5 seconds
- ✅ Processing metrics show zero errors
- ✅ Queue size remains manageable (< 10 contacts)

## 🎯 Business Impact

With Project 1 deployed, you now have:

- **Real-time contact processing** from The 7 Space website
- **Intelligent contact classification** by business entity
- **Enhanced workflow automation** with AI insights
- **Scalable foundation** for multi-entity expansion
- **MCP integration readiness** for future enhancements

**Ready to transform your contact processing with AI-powered automation! 🚀**
