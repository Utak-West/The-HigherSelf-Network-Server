# HigherSelf Network - SiteGround Launch Readiness Checklist

## Pre-Launch Verification for SiteGround Cloud Hosting Jump Start Plan

### 1. Environment Setup ✅

#### A. Server Configuration
```bash
# Verify SiteGround plan specifications
echo "SiteGround Plan: Jump Start (4 CPU, 8GB RAM, 40GB SSD)"
nproc  # Should show 4 cores
free -h  # Should show ~8GB total memory
df -h /  # Should show ~40GB total disk
```

#### B. Environment Variables
```bash
# Copy SiteGround-optimized environment file
cp deployment/siteground/.env.siteground .env

# Verify critical settings
grep -E "SERVER_WORKERS|REDIS_MAX_CONNECTIONS|LOG_LEVEL" .env
```

#### C. System Dependencies
```bash
# Install required packages
sudo apt update
sudo apt install -y redis-server mongodb nginx python3-pip docker.io

# Verify installations
redis-cli ping  # Should return PONG
mongo --version
nginx -v
docker --version
```

### 2. Resource Optimization ✅

#### A. Redis Configuration
```bash
# Apply SiteGround-optimized Redis config
sudo cp deployment/redis/redis.conf /etc/redis/redis.conf
sudo systemctl restart redis-server
sudo systemctl enable redis-server

# Verify Redis memory limit
redis-cli config get maxmemory  # Should show 1073741824 (1GB)
```

#### B. MongoDB Configuration
```bash
# Configure MongoDB for limited resources
sudo tee /etc/mongod.conf << EOF
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 1.5
net:
  maxIncomingConnections: 20
EOF

sudo systemctl restart mongod
sudo systemctl enable mongod
```

#### C. System Limits
```bash
# Configure system limits for SiteGround
sudo tee /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
* soft nproc 32768
* hard nproc 32768
EOF
```

### 3. Monitoring Setup ✅

#### A. Prometheus Configuration
```bash
# Copy SiteGround-specific Prometheus config
sudo mkdir -p /etc/prometheus
sudo cp deployment/siteground/prometheus-alerts.yml /etc/prometheus/

# Update prometheus.yml to include alerts
sudo tee -a /etc/prometheus/prometheus.yml << EOF
rule_files:
  - "prometheus-alerts.yml"
EOF

sudo systemctl restart prometheus
```

#### B. Grafana Dashboard
```bash
# Import SiteGround monitoring dashboard
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @deployment/siteground/grafana-dashboard.json
```

#### C. Automated Scripts
```bash
# Make scripts executable
chmod +x deployment/siteground/scripts/*.sh

# Set up cron jobs for automated maintenance
sudo tee /etc/cron.d/higherself-maintenance << EOF
# Memory cleanup every 30 minutes
*/30 * * * * root /path/to/deployment/siteground/scripts/memory_cleanup.sh

# Resource monitoring every 5 minutes
*/5 * * * * root /path/to/deployment/siteground/scripts/resource_monitor.sh

# Log rotation daily at 2 AM
0 2 * * * root /path/to/deployment/siteground/scripts/log_rotation.sh
EOF
```

### 4. Application Deployment ✅

#### A. Build and Deploy
```bash
# Build Docker images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy with SiteGround optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify all services are running
docker-compose ps
```

#### B. Health Checks
```bash
# Test application health
curl -f http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}

# Test Redis connectivity
redis-cli ping
# Expected: PONG

# Test MongoDB connectivity
mongo --eval "db.adminCommand('ismaster')"
# Expected: Connection successful
```

#### C. Performance Verification
```bash
# Test API response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
# Expected: < 500ms response time

# Check memory usage
free -m | awk 'NR==2{printf "Memory Usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }'
# Expected: < 80% memory usage

# Check CPU usage
top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print "CPU Usage: " $1"%"}'
# Expected: < 70% CPU usage
```

### 5. Security Configuration ✅

#### A. SSL/TLS Setup
```bash
# Install SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com

# Verify SSL configuration
curl -I https://yourdomain.com
# Expected: HTTP/2 200 with valid SSL
```

#### B. Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # Application (if needed)

# Verify firewall status
sudo ufw status
```

#### C. Rate Limiting
```bash
# Verify Nginx rate limiting is active
sudo nginx -t
sudo systemctl reload nginx

# Test rate limiting
for i in {1..20}; do curl -I http://localhost/api/test; done
# Expected: Some requests should return 429 (Too Many Requests)
```

### 6. Backup and Recovery ✅

#### A. Backup Configuration
```bash
# Test backup script
sudo /path/to/deployment/siteground/scripts/backup.sh

# Verify backup files
ls -la /home/backup/
# Expected: Recent backup files present
```

#### B. Recovery Testing
```bash
# Test database restore (use test data)
mongorestore --drop /home/backup/mongo_$(date +%Y%m%d)/

# Test Redis restore
redis-cli FLUSHALL
redis-cli --rdb /home/backup/redis_dump.rdb
```

### 7. Performance Baselines ✅

#### A. Load Testing
```bash
# Install Apache Bench for load testing
sudo apt install apache2-utils

# Test with 100 concurrent requests
ab -n 1000 -c 100 http://localhost:8000/health

# Expected results:
# - Requests per second: > 100
# - Time per request: < 1000ms
# - Failed requests: 0
```

#### B. Resource Monitoring
```bash
# Monitor resources during load test
./deployment/siteground/scripts/resource_monitor.sh

# Check metrics file
cat /var/log/higherself/metrics.json | jq '.resources'

# Expected:
# - CPU usage: < 85%
# - Memory usage: < 90%
# - Disk usage: < 80%
```

### 8. Final Verification ✅

#### A. Service Status Check
```bash
# Check all critical services
systemctl status redis-server mongodb nginx prometheus grafana-server

# Check Docker containers
docker-compose ps
# Expected: All services "Up" and healthy
```

#### B. Log Verification
```bash
# Check application logs for errors
tail -f /app/logs/app.log | grep -i error
# Expected: No critical errors

# Check system logs
journalctl -u higherself-network --since "1 hour ago" | grep -i error
# Expected: No critical errors
```

#### C. Monitoring Dashboard
```bash
# Access Grafana dashboard
curl -f http://localhost:3000/d/siteground-monitoring
# Expected: Dashboard loads successfully

# Check Prometheus targets
curl -f http://localhost:9090/targets
# Expected: All targets "UP"
```

### 9. Go-Live Checklist ✅

- [ ] All services running and healthy
- [ ] SSL certificate installed and valid
- [ ] Monitoring and alerting configured
- [ ] Backup system tested and working
- [ ] Performance baselines established
- [ ] Security configurations applied
- [ ] DNS records updated to point to server
- [ ] Load balancer configured (if applicable)
- [ ] CDN configured for static assets
- [ ] Error tracking and logging active

### 10. Post-Launch Monitoring ✅

#### First 24 Hours
- [ ] Monitor CPU usage every hour
- [ ] Check memory usage trends
- [ ] Verify disk space consumption
- [ ] Monitor API response times
- [ ] Check error rates and logs
- [ ] Verify backup completion

#### First Week
- [ ] Review performance trends
- [ ] Analyze user traffic patterns
- [ ] Check resource utilization trends
- [ ] Verify scaling thresholds
- [ ] Review and adjust monitoring alerts

### Emergency Contacts and Procedures

#### SiteGround Support
- Support Portal: https://my.siteground.com
- Emergency Phone: [Your SiteGround support number]

#### Escalation Procedures
1. **High CPU/Memory**: Run memory cleanup script
2. **Disk Space Critical**: Run emergency log cleanup
3. **Service Down**: Check Docker containers and restart if needed
4. **Database Issues**: Check MongoDB/Redis logs and restart services

### Success Criteria
- ✅ API response time < 500ms (95th percentile)
- ✅ Memory usage < 80% of 8GB
- ✅ CPU usage < 70% average
- ✅ Disk usage < 80% of 40GB
- ✅ Zero critical errors in logs
- ✅ All monitoring alerts configured
- ✅ Backup system operational
