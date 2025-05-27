# Enhanced Barter System Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the enhanced HigherSelf Network Barter System with multi-language support, user integration, and advanced features.

## Prerequisites

### System Requirements

#### Production Environment
- **CPU**: 4 cores minimum (8 recommended)
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 100GB SSD minimum (500GB recommended)
- **Network**: 1Gbps connection
- **OS**: Ubuntu 20.04 LTS or CentOS 8

#### Database Requirements
- **PostgreSQL**: Version 14+ with PostGIS 3.1+
- **Storage**: 50GB minimum for database
- **Memory**: 4GB dedicated RAM minimum

#### Cache Requirements
- **Redis**: Version 6+ 
- **Memory**: 2GB minimum (4GB recommended)

## Installation Steps

### 1. Database Setup

```bash
# Install PostgreSQL with PostGIS
sudo apt install postgresql-14 postgresql-14-postgis-3

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE higherself_network;
CREATE USER higherself_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE higherself_network TO higherself_user;
ALTER USER higherself_user CREATEDB;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
\q
EOF
```

### 2. Run Enhanced Migrations

```bash
# Navigate to project directory
cd /path/to/higherself-network

# Run migrations in order
sudo -u postgres psql -d higherself_network -f db/barter_schema.sql
sudo -u postgres psql -d higherself_network -f db/migrations/04_enhance_barter_system.sql
```

### 3. Redis Configuration

```bash
# Install and configure Redis
sudo apt install redis-server

# Edit Redis configuration
sudo nano /etc/redis/redis.conf
```

Key Redis settings:
```ini
maxmemory 2gb
maxmemory-policy allkeys-lru
requirepass your_redis_password
bind 127.0.0.1
save 900 1
appendonly yes
```

### 4. Application Configuration

Create enhanced `.env` file:

```bash
# Database Configuration
DATABASE_URL=postgresql://higherself_user:secure_password@localhost/higherself_network
REDIS_URL=redis://:redis_password@localhost:6379/0

# Enhanced Barter System Settings
DEFAULT_CULTURAL_REGION=NORTH_AMERICA
SUPPORTED_LANGUAGES=en,es,fr,de,pt,zh,ja,ar,hi,ru,nl,sv,no,da,fi
SEARCH_CACHE_TTL=3600
MAX_SEARCH_RADIUS_KM=500
DEFAULT_SEARCH_LIMIT=20

# Translation Services
GOOGLE_TRANSLATE_API_KEY=your_google_api_key
AZURE_TRANSLATOR_KEY=your_azure_key
TRANSLATION_PROVIDER=local  # or 'google', 'azure'

# Geolocation Services
GEOCODING_API_KEY=your_geocoding_api_key
GEOCODING_PROVIDER=google  # or 'mapbox', 'here'

# User Verification
VERIFICATION_REQUIRED=true
VERIFICATION_DOCUMENT_STORAGE=local  # or 's3', 'gcs'

# Performance Settings
ENABLE_SEARCH_CACHE=true
ENABLE_TRANSLATION_CACHE=true
ENABLE_METRICS_COLLECTION=true
ENABLE_AUDIT_LOGGING=true

# Security Settings
ENABLE_RATE_LIMITING=true
MAX_REQUESTS_PER_MINUTE=60
ENABLE_CORS=true
CORS_ORIGINS=["https://yourdomain.com"]

# Notification Settings
ENABLE_EMAIL_NOTIFICATIONS=true
ENABLE_PUSH_NOTIFICATIONS=true
NOTIFICATION_QUEUE_SIZE=1000

# Integration Settings
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
GOHIGHLEVEL_API_KEY=your_ghl_api_key
SOFTR_WEBHOOK_SECRET=your_softr_secret
```

### 5. Install Dependencies

```bash
# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate

# Install enhanced requirements
pip install --upgrade pip
pip install -r requirements.txt

# Additional dependencies for enhanced features
pip install googletrans==4.0.0rc1
pip install azure-cognitiveservices-language-translator
pip install geopy
pip install pycountry
pip install langdetect
```

## Service Configuration

### 1. Create Systemd Service

Create `/etc/systemd/system/higherself-barter.service`:

```ini
[Unit]
Description=HigherSelf Network Enhanced Barter System
After=network.target postgresql.service redis.service
Requires=postgresql.service redis.service

[Service]
Type=exec
User=higherself
Group=higherself
WorkingDirectory=/home/higherself/The-HigherSelf-Network-Server
Environment=PATH=/home/higherself/The-HigherSelf-Network-Server/venv/bin
ExecStart=/home/higherself/The-HigherSelf-Network-Server/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Enhanced security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/higherself /tmp /home/higherself/uploads

[Install]
WantedBy=multi-user.target
```

### 2. Nginx Configuration

Enhanced Nginx configuration with rate limiting and security:

```nginx
upstream higherself_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;
limit_req_zone $binary_remote_addr zone=search:10m rate=20r/s;
limit_req_zone $binary_remote_addr zone=translate:10m rate=5r/s;

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';";
    
    # Main API endpoints
    location /barter/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://higherself_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Search endpoints with higher rate limit
    location /barter/search/ {
        limit_req zone=search burst=50 nodelay;
        proxy_pass http://higherself_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Translation endpoints with stricter limits
    location /barter/translations/ {
        limit_req zone=translate burst=10 nodelay;
        proxy_pass http://higherself_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Authentication endpoints
    location ~ ^/(auth|login|register) {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://higherself_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Testing the Deployment

### 1. Health Checks

```bash
# Test database connection
python -c "
import asyncpg
import asyncio

async def test_db():
    conn = await asyncpg.connect('postgresql://higherself_user:password@localhost/higherself_network')
    result = await conn.fetchval('SELECT 1')
    await conn.close()
    print(f'Database test: {result}')

asyncio.run(test_db())
"

# Test Redis connection
redis-cli -a your_redis_password ping

# Test application startup
curl http://localhost:8000/health
```

### 2. Feature Testing

```bash
# Test enhanced search
curl -X GET "http://localhost:8000/barter/search/enhanced?lat=40.7128&lon=-74.0060&radius_km=50&language=en"

# Test user profile creation
curl -X POST "http://localhost:8000/barter/users/profiles" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "preferred_language": "en", "timezone_name": "America/New_York"}'

# Test translation creation
curl -X POST "http://localhost:8000/barter/translations" \
  -H "Content-Type: application/json" \
  -d '{"entity_type": "listing", "entity_id": "uuid-here", "field_name": "title", "translated_text": "Test Translation", "language_code": "es"}'
```

## Monitoring and Maintenance

### 1. Log Configuration

Create log rotation for enhanced logging:

```bash
# Create log directory
sudo mkdir -p /var/log/higherself
sudo chown higherself:higherself /var/log/higherself

# Configure logrotate
sudo tee /etc/logrotate.d/higherself << EOF
/var/log/higherself/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 higherself higherself
    postrotate
        systemctl reload higherself-barter
    endscript
}
EOF
```

### 2. Performance Monitoring

Create monitoring script `/home/higherself/monitor_barter.sh`:

```bash
#!/bin/bash

LOG_FILE="/var/log/higherself/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Check application health
if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "$DATE - Application health check failed" >> $LOG_FILE
    systemctl restart higherself-barter
fi

# Check database performance
DB_CONNECTIONS=$(sudo -u postgres psql -d higherself_network -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='higherself_network';")
if [ "$DB_CONNECTIONS" -gt 80 ]; then
    echo "$DATE - High database connections: $DB_CONNECTIONS" >> $LOG_FILE
fi

# Check Redis memory usage
REDIS_MEMORY=$(redis-cli -a your_redis_password info memory | grep used_memory_human | cut -d: -f2)
echo "$DATE - Redis memory usage: $REDIS_MEMORY" >> $LOG_FILE

# Check search cache hit rate
CACHE_HITS=$(redis-cli -a your_redis_password info stats | grep keyspace_hits | cut -d: -f2)
CACHE_MISSES=$(redis-cli -a your_redis_password info stats | grep keyspace_misses | cut -d: -f2)
if [ "$CACHE_MISSES" -gt 0 ]; then
    HIT_RATE=$(echo "scale=2; $CACHE_HITS / ($CACHE_HITS + $CACHE_MISSES) * 100" | bc)
    echo "$DATE - Cache hit rate: $HIT_RATE%" >> $LOG_FILE
fi
```

### 3. Backup Strategy

Enhanced backup script `/home/higherself/backup_enhanced.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/higherself/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="higherself_network"

mkdir -p $BACKUP_DIR

# Database backup with compression
sudo -u postgres pg_dump $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Redis backup
redis-cli -a your_redis_password --rdb $BACKUP_DIR/redis_backup_$DATE.rdb

# Application configuration backup
tar -czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    /home/higherself/The-HigherSelf-Network-Server/.env \
    /etc/nginx/sites-available/higherself-barter \
    /etc/systemd/system/higherself-barter.service

# Translation cache backup
redis-cli -a your_redis_password --scan --pattern "barter:translation:*" | \
    xargs redis-cli -a your_redis_password dump > $BACKUP_DIR/translations_$DATE.dump

# Clean old backups (keep 14 days)
find $BACKUP_DIR -name "*backup_*" -mtime +14 -delete
```

## Troubleshooting

### Common Issues

1. **Translation Service Errors**
   - Check API keys in environment variables
   - Verify network connectivity to translation services
   - Monitor rate limits for external APIs

2. **Search Performance Issues**
   - Check PostGIS indexes: `EXPLAIN ANALYZE` on search queries
   - Monitor Redis memory usage and cache hit rates
   - Review search cache TTL settings

3. **User Profile Integration Issues**
   - Verify user ID format consistency
   - Check authentication token validation
   - Review user profile creation logs

4. **Multi-language Display Issues**
   - Verify translation cache is working
   - Check language code format (ISO 639-1)
   - Review browser language detection

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Create additional indexes for enhanced features
   CREATE INDEX CONCURRENTLY idx_barter_translations_lookup 
   ON barter_translations (entity_type, entity_id, language_code);
   
   CREATE INDEX CONCURRENTLY idx_barter_user_profiles_activity 
   ON barter_user_profiles (last_activity DESC);
   
   CREATE INDEX CONCURRENTLY idx_barter_search_cache_expires 
   ON barter_search_cache (expires_at) WHERE expires_at > NOW();
   ```

2. **Redis Optimization**
   ```bash
   # Optimize Redis for translation caching
   redis-cli CONFIG SET maxmemory-policy allkeys-lru
   redis-cli CONFIG SET save "900 1 300 10 60 10000"
   ```

3. **Application Tuning**
   - Increase worker processes for high load
   - Implement connection pooling for database
   - Use async/await for all I/O operations
   - Enable gzip compression for API responses

This enhanced deployment guide ensures optimal performance and reliability for the multi-language, location-based barter system.
