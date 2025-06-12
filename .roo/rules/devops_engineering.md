# HigherSelf DevOps Engineer

## Description
Specialized mode for managing deployment and monitoring of The HigherSelf Network Server

## Instructions
- Focus on Docker deployment configurations
- Implement Prometheus and Grafana monitoring
- Ensure proper environment variable management
- Design logging aggregation strategies
- Implement health check endpoints
- Create alerting rules for critical services
- Design backup and recovery procedures

## Capabilities
- Analyze existing deployment configurations
- Generate Docker and docker-compose files
- Create monitoring dashboards
- Implement logging configurations
- Design CI/CD pipeline improvements

## Docker Compose Template

```yaml
version: '3.8'

services:
  # Main application server
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: higherselfnetwork/server:${VERSION:-latest}
    container_name: higherselfnetwork-server
    restart: unless-stopped
    ports:
      - "${SERVER_PORT:-8000}:8000"
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - NOTION_API_TOKEN=${NOTION_API_TOKEN}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - MONGODB_URI=mongodb://mongodb:27017/higherselfnetwork
      - MONGODB_USERNAME=${MONGODB_USERNAME}
      - MONGODB_PASSWORD=${MONGODB_PASSWORD}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - mongodb
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - higherselfnetwork

  # Redis for caching and message queue
  redis:
    image: redis:7-alpine
    container_name: higherselfnetwork-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - redis-data:/data
    networks:
      - higherselfnetwork

  # MongoDB for document storage
  mongodb:
    image: mongo:6
    container_name: higherselfnetwork-mongodb
    restart: unless-stopped
    environment:
      - MONGO_INITDB_ROOT_USERNAME=${MONGODB_USERNAME}
      - MONGO_INITDB_ROOT_PASSWORD=${MONGODB_PASSWORD}
    ports:
      - "${MONGODB_PORT:-27017}:27017"
    volumes:
      - mongodb-data:/data/db
    networks:
      - higherselfnetwork

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    container_name: higherselfnetwork-prometheus
    restart: unless-stopped
    ports:
      - "${PROMETHEUS_PORT:-9090}:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - higherselfnetwork

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: higherselfnetwork-grafana
    restart: unless-stopped
    ports:
      - "${GRAFANA_PORT:-3000}:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - higherselfnetwork

  # Loki for log aggregation
  loki:
    image: grafana/loki:latest
    container_name: higherselfnetwork-loki
    restart: unless-stopped
    ports:
      - "${LOKI_PORT:-3100}:3100"
    volumes:
      - ./monitoring/loki-config.yaml:/etc/loki/local-config.yaml
      - loki-data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - higherselfnetwork

  # Promtail for log collection
  promtail:
    image: grafana/promtail:latest
    container_name: higherselfnetwork-promtail
    restart: unless-stopped
    volumes:
      - ./logs:/var/log/higherselfnetwork
      - ./monitoring/promtail-config.yaml:/etc/promtail/config.yaml
    command: -config.file=/etc/promtail/config.yaml
    depends_on:
      - loki
    networks:
      - higherselfnetwork

volumes:
  redis-data:
  mongodb-data:
  prometheus-data:
  grafana-data:
  loki-data:

networks:
  higherselfnetwork:
    driver: bridge
```

## Monitoring Configuration

### Prometheus Configuration (prometheus.yml)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          # - alertmanager:9093

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'higherselfnetwork'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['app:8000']
```

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "components": {
            "api": "healthy",
            "notion": await check_notion_health(),
            "redis": await check_redis_health(),
            "mongodb": await check_mongodb_health(),
            "agents": await check_agents_health()
        }
    }

    # Determine overall status
    if any(status != "healthy" for status in health_status["components"].values()):
        health_status["status"] = "degraded"

    if all(status == "unhealthy" for status in health_status["components"].values()):
        health_status["status"] = "unhealthy"

    return health_status
```

## Backup Strategy

1. **Database Backups**
   - MongoDB: Daily full backup, hourly incremental backups
   - Redis: RDB snapshots every 15 minutes
   - Retention: 7 days of daily backups, 24 hours of hourly backups

2. **Application Data Backups**
   - Vector store data: Daily full backup
   - Logs: Retained for 30 days
   - Configuration: Version controlled in Git

3. **Notion Data**
   - Daily export of critical databases
   - Webhook event logs for audit trail

4. **Backup Storage**
   - Primary: Local encrypted storage
   - Secondary: Cloud object storage (S3 or equivalent)
   - Tertiary: Offline cold storage for monthly archives
