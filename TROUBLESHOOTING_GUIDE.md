# 🚨 HigherSelf Network Server Troubleshooting Guide

## Issues Found and Fixed

### ✅ **Issue 1: Docker Compose Volume Mismatch**
**Problem**: Redis service referenced `redis_data_development` but volume was defined as `redis_data_dev`

**Solution**: 
- Fixed volume references in docker-compose.yml
- Added missing volume definitions for `development` environment
- Removed obsolete `version: '3.8'` attributes

**Status**: ✅ FIXED

### ✅ **Issue 2: Missing Environment File**
**Problem**: Docker Compose looking for `.env.development` file that didn't exist

**Solution**: 
- Created `.env.development` from `.env.example`

**Status**: ✅ FIXED

### ⚠️ **Issue 3: Docker Daemon Not Running**
**Problem**: Docker daemon is not running on your system

**Solution**: Start Docker Desktop or Docker daemon

---

## 🔧 Quick Fix Commands

### 1. Start Docker
```bash
# On macOS with Docker Desktop:
open -a Docker

# Wait for Docker to start (about 30 seconds)
# You'll see the Docker whale icon in your menu bar when ready
```

### 2. Verify Docker is Running
```bash
# Test Docker
docker --version
docker ps

# Test Docker Compose
docker-compose --version
```

### 3. Start HigherSelf Server
```bash
# Navigate to project directory
cd "/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server/The-HigherSelf-Network-Server-2"

# Start the server
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Test Voice Control API
```bash
# Wait for server to start (about 60 seconds)
sleep 60

# Test health endpoint
curl http://localhost:8000/health

# Test voice control endpoint
curl -X POST "http://localhost:8000/voice/server/control" \
  -H "Content-Type: application/json" \
  -d '{"command": "server status", "environment": "development"}'
```

---

## 🎤 Voice Control Testing

### Test Voice Commands in Termius
1. **Start Termius Pro**
2. **Connect to HigherSelf-Voice-Local host**
3. **Try these commands**:
   - "server status"
   - "show server logs"
   - "restart higher self server"

### Test 1Password Integration
1. **Open any app**
2. **Type these shortcuts**:
   - `;hsenv` - Server environment template
   - `;sgftp` - SiteGround FTP credentials
   - `;vclog` - Voice command log

---

## 🔍 Diagnostic Commands

### Check Docker Status
```bash
# Docker daemon status
docker info

# Docker Compose services
docker-compose ps

# Service logs
docker-compose logs -f higherself-server
```

### Check Server Health
```bash
# API health
curl http://localhost:8000/health

# Redis health
curl http://localhost:8000/health/redis

# MongoDB health
curl http://localhost:8000/health/mongodb
```

### Check Voice Control
```bash
# Test voice API
curl -X POST "http://localhost:8000/voice/server/control" \
  -H "Content-Type: application/json" \
  -d '{"command": "server status"}'

# Check voice service logs
docker-compose logs -f higherself-server | grep -i voice
```

---

## 🚨 Common Issues and Solutions

### Issue: "Cannot connect to Docker daemon"
**Solution**: 
```bash
# Start Docker Desktop
open -a Docker

# Or start Docker daemon (Linux)
sudo systemctl start docker
```

### Issue: "Port already in use"
**Solution**:
```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different ports in .env
SERVER_PORT=8001
```

### Issue: "Volume not found"
**Solution**:
```bash
# Remove old volumes
docker-compose down -v

# Recreate volumes
docker-compose up -d
```

### Issue: "Voice commands not working"
**Solution**:
1. **Check server is running**: `curl http://localhost:8000/health`
2. **Check Termius connection**: Verify SSH connection works
3. **Check microphone permissions**: System Preferences → Security & Privacy
4. **Check 1Password snippets**: Verify snippets are created

### Issue: "1Password snippets not expanding"
**Solution**:
1. **Check 1Password is unlocked**
2. **Verify Accessibility permissions**: System Preferences → Security & Privacy → Accessibility
3. **Restart 1Password app**
4. **Test with simple snippet first**

---

## 📊 System Requirements Check

### Required Software
- [ ] **Docker Desktop** (or Docker daemon)
- [ ] **Docker Compose** (usually included with Docker Desktop)
- [ ] **Node.js** (for Claude Code integration)
- [ ] **1Password** (for secure snippets)
- [ ] **Termius Pro** (for voice control)

### Required Ports
- [ ] **8000** - Main API server
- [ ] **27017** - MongoDB
- [ ] **6379** - Redis
- [ ] **8500** - Consul
- [ ] **9090** - Prometheus
- [ ] **3000** - Grafana

### Check Ports
```bash
# Check if ports are available
netstat -an | grep -E "(8000|27017|6379|8500|9090|3000)"

# Or use lsof
lsof -i :8000
lsof -i :27017
lsof -i :6379
```

---

## 🔄 Complete Reset Procedure

If you're having persistent issues, try this complete reset:

### 1. Stop Everything
```bash
# Stop all containers
docker-compose down -v

# Remove all containers and volumes
docker system prune -a --volumes
```

### 2. Clean Environment
```bash
# Remove environment files
rm -f .env.development

# Recreate from template
cp .env.example .env.development
```

### 3. Restart Fresh
```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to be ready
sleep 30

# Start services
docker-compose up -d

# Check status
docker-compose ps
```

### 4. Test Everything
```bash
# Test API
curl http://localhost:8000/health

# Test voice control
curl -X POST "http://localhost:8000/voice/server/control" \
  -H "Content-Type: application/json" \
  -d '{"command": "server status"}'
```

---

## 📞 Getting Help

### Check Logs
```bash
# Server logs
docker-compose logs -f higherself-server

# All service logs
docker-compose logs -f

# Specific service logs
docker-compose logs -f redis
docker-compose logs -f mongodb
```

### Debug Mode
```bash
# Enable debug mode in .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart server
docker-compose restart higherself-server
```

### Health Checks
```bash
# Comprehensive health check
curl http://localhost:8000/health | jq .

# Individual service health
curl http://localhost:8000/health/redis | jq .
curl http://localhost:8000/health/mongodb | jq .
```

---

## ✅ Success Checklist

When everything is working, you should see:

- [ ] **Docker running**: `docker ps` shows containers
- [ ] **Server responding**: `curl http://localhost:8000/health` returns 200
- [ ] **Voice API working**: Voice control endpoint responds
- [ ] **Termius connected**: Can SSH to server
- [ ] **1Password snippets**: Shortcuts expand properly
- [ ] **Voice commands**: "server status" works in Termius

**If all items are checked, your HigherSelf Network Server with voice control is fully operational!** 🎉
