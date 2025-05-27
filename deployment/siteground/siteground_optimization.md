# SiteGround Hosting Optimization Guide for HigherSelf Network

## Current Plan Analysis
**SiteGround Cloud Hosting Jump Start Plan:**
- 4 CPU cores
- 8 GB RAM
- 40 GB SSD storage
- 5 TB bandwidth
- Expires: Feb 9, 2026

## 1. Server Configuration Optimizations

### Resource Allocation Strategy
```bash
# Environment variables for SiteGround optimization
SERVER_WORKERS=2                    # Optimized for 4-core setup
REDIS_MAX_CONNECTIONS=8             # Reduced from 10 for memory efficiency
REDIS_MAXMEMORY=1GB                 # Allocate 1GB of 8GB RAM to Redis
REDIS_MAXMEMORY_POLICY=allkeys-lru  # Evict least recently used keys
LOG_LEVEL=INFO                      # Reduce verbose logging
CELERY_WORKER_CONCURRENCY=2         # Limit concurrent tasks
```

### Memory Management
- **Application**: 4GB (50% of total RAM)
- **Redis Cache**: 1GB (12.5% of total RAM)
- **MongoDB**: 1.5GB (18.75% of total RAM)
- **System/OS**: 1.5GB (18.75% of total RAM)

### CPU Optimization
- **Main Application**: 2 workers (50% CPU allocation)
- **Celery Workers**: 2 concurrent tasks (25% CPU allocation)
- **Database Operations**: 1 core reserved (25% CPU allocation)

## 2. Redis Configuration for SiteGround

### Optimized Redis Settings
```redis
# Memory optimization for 8GB RAM environment
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 1000

# Connection optimization
timeout 300
tcp-keepalive 60
maxclients 50

# Performance tuning
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
set-max-intset-entries 512
```

### Cache Strategy
- **L1 Cache (Memory)**: 256MB - Frequently accessed data
- **L2 Cache (Redis)**: 512MB - Session data, API responses
- **L3 Cache (Disk)**: 256MB - Static content, templates

## 3. Database Optimization

### MongoDB Configuration
```yaml
# Optimized for limited resources
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1.5
    collectionConfig:
      blockCompressor: snappy
    indexConfig:
      prefixCompression: true

operationProfiling:
  slowOpThresholdMs: 100
  mode: slowOp

net:
  maxIncomingConnections: 20
```

### Connection Pooling
- **MongoDB**: Max 20 connections
- **Redis**: Max 8 connections
- **HTTP**: Max 100 concurrent connections

## 4. Storage Optimization (40GB SSD)

### Disk Space Allocation
- **Application Code**: 2GB
- **Logs**: 5GB (with rotation)
- **Database Data**: 15GB
- **Cache/Temp**: 5GB
- **Backups**: 8GB
- **System Reserve**: 5GB

### Log Management
```bash
# Logrotate configuration
/app/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    maxsize 100M
}
```

## 5. Performance Monitoring

### Key Metrics to Track
1. **CPU Usage**: Target <70% average
2. **Memory Usage**: Target <80% of 8GB
3. **Disk I/O**: Monitor for bottlenecks
4. **Network**: Track bandwidth usage
5. **Response Times**: Target <500ms for API calls

### Monitoring Tools
- **Built-in**: Prometheus + Grafana stack
- **SiteGround**: Site Tools monitoring
- **Custom**: Health check endpoints

## 6. Caching Strategy

### Multi-Level Caching
```python
# Cache hierarchy
CACHE_LEVELS = {
    'hot': 60,      # 1 minute - frequently accessed
    'warm': 300,    # 5 minutes - moderately accessed
    'cold': 1800,   # 30 minutes - rarely accessed
}

CACHE_SIZES = {
    'notion_api': 100,      # 100 entries max
    'sessions': 500,        # 500 active sessions
    'workflows': 50,        # 50 workflow templates
}
```

### Content Delivery
- **Static Assets**: SiteGround CDN
- **API Responses**: Redis caching
- **Database Queries**: Query result caching

## 7. Security Optimizations

### Resource Protection
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

# Connection limits
limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
limit_conn conn_limit_per_ip 10;
```

### SSL/TLS Configuration
- **Protocol**: TLS 1.2+ only
- **Ciphers**: Strong cipher suites
- **HSTS**: Enabled with 1-year max-age

## 8. Backup Strategy

### Automated Backups
```bash
#!/bin/bash
# Daily backup script for SiteGround
BACKUP_DIR="/home/backup"
DATE=$(date +%Y%m%d)

# Database backup
mongodump --out $BACKUP_DIR/mongo_$DATE
redis-cli BGSAVE

# Application backup
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /app

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

## 9. Launch Readiness Checklist

### Pre-Launch Tasks
- [ ] Configure environment variables
- [ ] Set up monitoring dashboards
- [ ] Test backup/restore procedures
- [ ] Verify SSL certificates
- [ ] Configure rate limiting
- [ ] Set up log rotation
- [ ] Test health check endpoints
- [ ] Verify Redis memory limits
- [ ] Configure MongoDB connection limits
- [ ] Test failover procedures

### Performance Baselines
- [ ] API response time <500ms
- [ ] Memory usage <6.4GB (80% of 8GB)
- [ ] CPU usage <70% average
- [ ] Disk usage <32GB (80% of 40GB)
- [ ] Redis hit ratio >90%

## 10. Scaling Considerations

### When to Upgrade
- **CPU**: Sustained >80% usage for 24+ hours
- **Memory**: Consistent >85% usage for 12+ hours
- **Storage**: >90% disk usage
- **Response Time**: >1 second average for 95th percentile
- **Error Rate**: >2% sustained error rate
- **Redis Memory**: >90% of allocated memory consistently

### Scaling Metrics Thresholds

#### Immediate Action Required (Upgrade Within 24 Hours)
```bash
# CPU Usage > 90% for 2+ hours
# Memory Usage > 95% for 1+ hour
# Disk Usage > 95%
# Response Time > 2 seconds (95th percentile)
# Error Rate > 5%
```

#### Plan Upgrade Recommended (Upgrade Within 1 Week)
```bash
# CPU Usage > 80% for 24+ hours
# Memory Usage > 85% for 12+ hours
# Disk Usage > 85%
# Response Time > 1 second (95th percentile)
# Redis Memory > 90% consistently
```

#### Monitor Closely (Consider Upgrade Within 1 Month)
```bash
# CPU Usage > 70% average
# Memory Usage > 75% average
# Disk Usage > 75%
# Response Time > 750ms (95th percentile)
# Growing traffic trends
```

### SiteGround Plan Upgrade Path

#### Current: Jump Start Plan ($100/month)
- 4 CPU cores, 8GB RAM, 40GB SSD
- **Capacity**: ~1,000 concurrent users
- **API Calls**: ~10,000 requests/hour

#### Next: Business Plan ($200/month)
- 8 CPU cores, 16GB RAM, 80GB SSD
- **Capacity**: ~2,500 concurrent users
- **API Calls**: ~25,000 requests/hour
- **Migration Impact**: 2x performance improvement

#### Future: Business Plus Plan ($300/month)
- 12 CPU cores, 24GB RAM, 120GB SSD
- **Capacity**: ~5,000 concurrent users
- **API Calls**: ~50,000 requests/hour
- **Migration Impact**: 3x performance improvement

#### Enterprise: Super Power Plan ($400/month)
- 16 CPU cores, 32GB RAM, 160GB SSD
- **Capacity**: ~10,000 concurrent users
- **API Calls**: ~100,000 requests/hour
- **Migration Impact**: 4x performance improvement

### Alternative Scaling Options

#### Horizontal Scaling (Multi-Server)
- **Load Balancer**: Distribute traffic across multiple servers
- **Database Clustering**: MongoDB replica sets
- **Redis Clustering**: Distributed caching
- **CDN Integration**: Offload static content

#### Hybrid Cloud Approach
- **SiteGround**: Primary application server
- **AWS/GCP**: Database and storage services
- **CloudFlare**: CDN and DDoS protection
- **Redis Cloud**: Managed Redis service

### Cost-Benefit Analysis

#### Jump Start → Business Plan Upgrade
- **Cost Increase**: $100/month (100% increase)
- **Performance Gain**: 2x CPU, 2x RAM, 2x Storage
- **ROI Threshold**: >2,000 active users or >$200/month revenue

#### Business → Business Plus Upgrade
- **Cost Increase**: $100/month (50% increase)
- **Performance Gain**: 1.5x CPU, 1.5x RAM, 1.5x Storage
- **ROI Threshold**: >4,000 active users or >$400/month revenue

### Migration Planning

#### Pre-Migration Checklist
- [ ] Backup all data and configurations
- [ ] Test application on new plan (staging environment)
- [ ] Update monitoring thresholds for new resources
- [ ] Plan maintenance window (2-4 hours)
- [ ] Notify users of potential downtime

#### Migration Process
1. **Preparation** (1 week before)
   - Create full system backup
   - Test restore procedures
   - Update DNS TTL to 300 seconds

2. **Migration Day**
   - Create final backup
   - Upgrade SiteGround plan
   - Restore application and data
   - Update configuration for new resources
   - Test all functionality

3. **Post-Migration** (24-48 hours)
   - Monitor performance metrics
   - Verify all services operational
   - Update monitoring alerts
   - Document new baselines

### Emergency Scaling Procedures

#### Immediate Traffic Spike Response
```bash
# Enable aggressive caching
redis-cli config set maxmemory-policy allkeys-lru

# Reduce worker processes temporarily
export SERVER_WORKERS=1
export CELERY_WORKER_CONCURRENCY=1

# Enable rate limiting
nginx -s reload  # Apply stricter rate limits

# Monitor and alert
./deployment/siteground/scripts/resource_monitor.sh
```

#### Temporary Load Reduction
```bash
# Disable non-essential features
export ENABLE_TYPEFORM=false
export ENABLE_WOOCOMMERCE=false
export ENABLE_USER_FEEDBACK=false

# Increase cache timeouts
export CACHE_DEFAULT_TIMEOUT=1800
export CACHE_HOT_TIMEOUT=300

# Restart application with new settings
docker-compose restart windsurf-agent
```
