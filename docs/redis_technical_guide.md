# Redis Technical Guide for HigherSelf Network Server

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration](#configuration)
4. [Integration Points](#integration-points)
5. [Operations Guide](#operations-guide)
6. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
7. [Security](#security)
8. [Performance Optimization](#performance-optimization)

## Overview

Redis serves as the high-performance caching and messaging backbone for the HigherSelf Network Server. It provides:

- **Caching Layer**: Fast access to frequently used data
- **Real-time Messaging**: Agent communication via pub/sub
- **Session Management**: User session and authentication storage
- **Rate Limiting**: API request throttling and abuse prevention
- **Task Queues**: Background job processing and workflow orchestration

## Architecture

### Redis Service Structure

```
services/redis_service.py
├── RedisService (Singleton)
│   ├── Connection Management
│   │   ├── Synchronous Client
│   │   ├── Asynchronous Client
│   │   └── Connection Pooling
│   ├── Operations
│   │   ├── Basic (get, set, delete)
│   │   ├── Hash Operations
│   │   ├── Pub/Sub Messaging
│   │   └── Atomic Operations
│   ├── Health Monitoring
│   │   ├── Connection Health Checks
│   │   ├── Performance Metrics
│   │   └── Error Tracking
│   └── Retry Logic
│       ├── Exponential Backoff
│       ├── Connection Recovery
│       └── Graceful Degradation
```

### Integration Architecture

```
HigherSelf Network Server
├── API Layer
│   ├── Response Caching → Redis
│   ├── Rate Limiting → Redis
│   └── Session Management → Redis
├── Agent System
│   ├── Inter-agent Communication → Redis Pub/Sub
│   ├── Task Distribution → Redis Queues
│   └── State Synchronization → Redis
├── Notion Integration
│   ├── Data Caching → Redis
│   ├── Query Result Caching → Redis
│   └── Webhook Event Distribution → Redis
└── Background Services
    ├── Celery Task Queue → Redis
    ├── Scheduled Jobs → Redis
    └── Workflow Orchestration → Redis
```

## Configuration

### Environment Variables

#### Basic Connection
```bash
# Primary connection URI
REDIS_URI=redis://localhost:6379/0

# Individual components (if URI not used)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DATABASE=0
REDIS_USERNAME=default
REDIS_PASSWORD=your_password_here
```

#### Connection Pool Settings
```bash
REDIS_MAX_CONNECTIONS=10
REDIS_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
REDIS_SOCKET_TIMEOUT=5
REDIS_HEALTH_CHECK_INTERVAL=30
```

#### Security Settings
```bash
REDIS_SSL=false
REDIS_SSL_CERT_REQS=required
REDIS_SSL_CA_CERTS=/path/to/ca.crt
REDIS_SSL_CERTFILE=/path/to/client.crt
REDIS_SSL_KEYFILE=/path/to/client.key
```

#### Feature Flags
```bash
REDIS_CACHE_ENABLED=true
REDIS_PUBSUB_ENABLED=true
REDIS_SESSION_STORE_ENABLED=true
REDIS_RATE_LIMITING_ENABLED=true
ENABLE_REDIS=true
```

### Environment-Specific Configurations

#### Development
```bash
REDIS_URI=redis://localhost:6379/0
REDIS_PASSWORD=
REDIS_SSL=false
REDIS_MAX_CONNECTIONS=5
```

#### Staging
```bash
REDIS_URI=redis://default:staging_pass@staging-redis.example.com:6379/0
REDIS_PASSWORD=staging_pass
REDIS_SSL=true
REDIS_MAX_CONNECTIONS=10
```

#### Production
```bash
REDIS_URI=rediss://default:prod_pass@prod-redis.example.com:6380/0
REDIS_PASSWORD=prod_pass
REDIS_SSL=true
REDIS_MAX_CONNECTIONS=20
REDIS_TIMEOUT=10
```

## Integration Points

### 1. API Response Caching

**Purpose**: Cache expensive API responses to improve performance

**Implementation**:
```python
from services.redis_service import redis_service

# Cache API response
cache_key = f"api:notion:business_entities:{entity_id}"
redis_service.set(cache_key, response_data, ex=300)  # 5 minutes

# Retrieve from cache
cached_data = redis_service.get(cache_key, as_json=True)
```

**Key Patterns**:
- `api:notion:*` - Notion API responses
- `api:hubspot:*` - HubSpot API responses
- `api:typeform:*` - Typeform API responses

### 2. Agent Communication

**Purpose**: Enable real-time communication between named agents

**Implementation**:
```python
# Publish message to agents
channel = "higherself:agents:communication"
message = {
    "from": "grace_fields",
    "to": "all",
    "type": "task_assignment",
    "payload": {"task": "prepare_training", "priority": "high"}
}
redis_service.publish(channel, message)

# Subscribe to agent messages
pubsub = await redis_service.subscribe(channel)
await redis_service.listen(pubsub, handle_agent_message)
```

**Channel Patterns**:
- `higherself:agents:communication` - General agent communication
- `higherself:agents:tasks` - Task distribution
- `higherself:agents:status` - Agent status updates

### 3. Session Management

**Purpose**: Store user sessions and authentication data

**Implementation**:
```python
# Store session data
session_id = "sess_12345"
session_data = {
    "user_id": "user_67890",
    "authenticated": True,
    "permissions": ["read", "write"]
}
redis_service.hset(f"session:{session_id}", "data", session_data)
redis_service.expire(f"session:{session_id}", 3600)  # 1 hour

# Retrieve session
session = redis_service.hget(f"session:{session_id}", "data", as_json=True)
```

### 4. Rate Limiting

**Purpose**: Prevent API abuse and ensure fair usage

**Implementation**:
```python
# Check rate limit
rate_key = f"rate_limit:{user_id}:{endpoint}"
current_count = redis_service.incr(rate_key)
if current_count == 1:
    redis_service.expire(rate_key, 3600)  # 1 hour window

if current_count > rate_limit:
    raise RateLimitExceeded()
```

### 5. Task Queues

**Purpose**: Manage background jobs and workflow orchestration

**Implementation**:
```python
# Queue background task
task_data = {
    "task_type": "sync_notion_data",
    "parameters": {"database_id": "12345"},
    "priority": "normal"
}
redis_service.lpush("queue:background_tasks", task_data)

# Process tasks
task = redis_service.brpop("queue:background_tasks", timeout=30)
```

## Operations Guide

### Starting Redis Service

#### Local Development
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Test connection
redis-cli ping
```

#### Docker Development
```bash
# Start Redis container
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Connect to Redis CLI
docker exec -it redis redis-cli
```

#### Production Deployment
```bash
# Using Docker Compose
docker-compose up -d redis

# Check Redis status
docker-compose logs redis
```

### Health Checks

#### Manual Health Check
```python
from services.redis_service import redis_service

# Synchronous health check
health = redis_service.health_check()
print(f"Redis Status: {health['status']}")

# Asynchronous health check
health = await redis_service.async_health_check()
```

#### API Health Endpoint
```bash
# Check Redis health via API
curl http://localhost:8000/health

# Response includes Redis status
{
  "status": "healthy",
  "services": {
    "redis": {
      "status": "healthy",
      "latency": 0.001,
      "last_check": 1640995200
    }
  }
}
```

### Monitoring Commands

#### Redis CLI Monitoring
```bash
# Connect to Redis
redis-cli

# Monitor all commands
MONITOR

# Get Redis info
INFO

# Check memory usage
INFO memory

# List all keys (use carefully in production)
KEYS *

# Get key information
TYPE key_name
TTL key_name
```

#### Performance Metrics
```python
# Get Redis service metrics
metrics = redis_service.get_metrics()
print(f"Operations: {metrics['operations']}")
print(f"Errors: {metrics['errors']}")
print(f"Average Latency: {metrics['avg_latency']}")
```

### Backup and Recovery

#### Data Backup
```bash
# Create Redis snapshot
redis-cli BGSAVE

# Copy RDB file
cp /var/lib/redis/dump.rdb /backup/redis-backup-$(date +%Y%m%d).rdb
```

#### Data Recovery
```bash
# Stop Redis
sudo systemctl stop redis

# Restore RDB file
cp /backup/redis-backup-20240101.rdb /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis
```

## Monitoring & Troubleshooting

### Common Issues

#### Connection Refused
**Symptoms**: `ConnectionError: Connection refused`
**Solutions**:
1. Check if Redis server is running
2. Verify host and port settings
3. Check firewall rules
4. Ensure Redis is bound to correct interface

#### Authentication Failed
**Symptoms**: `AuthenticationError: invalid password`
**Solutions**:
1. Verify REDIS_PASSWORD is correct
2. Check Redis AUTH configuration
3. Ensure username is correct (default: "default")

#### SSL/TLS Errors
**Symptoms**: SSL certificate verification failed
**Solutions**:
1. Verify REDIS_SSL setting
2. Check certificate paths and permissions
3. Ensure Redis server supports SSL
4. Validate certificate chain

#### Performance Issues
**Symptoms**: High latency, timeouts
**Solutions**:
1. Increase connection pool size
2. Adjust timeout settings
3. Monitor Redis memory usage
4. Check for slow queries
5. Optimize data structures

### Monitoring Metrics

#### Key Metrics to Monitor
- **Connection Count**: Active connections to Redis
- **Memory Usage**: Redis memory consumption
- **Operations/Second**: Request rate
- **Latency**: Average response time
- **Error Rate**: Failed operations percentage
- **Cache Hit Rate**: Cache effectiveness

#### Alerting Thresholds
- Memory usage > 80%
- Connection count > 90% of max
- Average latency > 100ms
- Error rate > 1%
- Cache hit rate < 80%

## Security

### Authentication
```bash
# Set Redis password
CONFIG SET requirepass your_strong_password

# Use AUTH command
AUTH your_strong_password
```

### Network Security
```bash
# Bind to specific interface
bind 127.0.0.1 10.0.0.1

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_9a8b7c6d"
```

### SSL/TLS Configuration
```bash
# Redis 6.0+ SSL configuration
tls-port 6380
tls-cert-file /path/to/redis.crt
tls-key-file /path/to/redis.key
tls-ca-cert-file /path/to/ca.crt
```

## Performance Optimization

### Memory Optimization
```bash
# Set memory policy
maxmemory 256mb
maxmemory-policy allkeys-lru

# Enable compression
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
```

### Connection Optimization
```bash
# Adjust connection settings
timeout 300
tcp-keepalive 60
tcp-backlog 511
```

### Persistence Configuration
```bash
# RDB snapshots
save 900 1
save 300 10
save 60 10000

# AOF persistence
appendonly yes
appendfsync everysec
```

---

**Note**: This guide should be regularly updated as the HigherSelf Network Server evolves. For the latest information, consult the source code and configuration files.
