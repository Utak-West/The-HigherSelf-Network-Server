# MongoDB Configuration Guide for HigherSelf Network

## Overview

This comprehensive guide covers MongoDB configuration for the HigherSelf Network server, including setup, security, performance optimization, and operational best practices.

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Docker Setup](#docker-setup)
3. [Security Configuration](#security-configuration)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring and Maintenance](#monitoring-and-maintenance)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting)

## Environment Configuration

### Required Environment Variables

Add these variables to your `.env` file:

```bash
# MongoDB Core Configuration
MONGODB_URI=mongodb://higherself_app:secure_app_password@localhost:27017/higherselfnetwork
MONGODB_DB_NAME=higherselfnetwork
MONGODB_USERNAME=higherself_app
MONGODB_PASSWORD=secure_app_password

# MongoDB Admin Configuration
MONGODB_ROOT_USER=admin
MONGODB_ROOT_PASSWORD=secure_root_password

# MongoDB Features
MONGODB_ENABLED=true
MONGODB_PORT=27017

# Connection Pool Settings
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=5
MONGODB_MAX_IDLE_TIME_MS=30000
```

### Production Environment Variables

For production, use stronger passwords and consider MongoDB Atlas:

```bash
# Production MongoDB Atlas Example
MONGODB_URI=mongodb+srv://higherself_prod:STRONG_PASSWORD@cluster0.mongodb.net/higherselfnetwork?retryWrites=true&w=majority
MONGODB_DB_NAME=higherselfnetwork
MONGODB_USERNAME=higherself_prod
MONGODB_PASSWORD=STRONG_PRODUCTION_PASSWORD
```

## Docker Setup

### Docker Compose Configuration

The MongoDB service is configured in `docker-compose.yml` with:

- **Authentication enabled** (`--auth`)
- **Bind to all interfaces** (`--bind_ip_all`)
- **Logging configuration**
- **Health checks**
- **Resource limits**

### Starting MongoDB

```bash
# Start all services including MongoDB
docker-compose up -d

# Start only MongoDB
docker-compose up -d mongodb

# View MongoDB logs
docker-compose logs -f mongodb
```

### Initialization

MongoDB is automatically initialized with:
- Application user creation
- Database and collection setup
- Index creation for performance
- Initial data seeding

## Security Configuration

### Authentication

MongoDB is configured with:
- **Root user**: Administrative access
- **Application user**: Limited to `higherselfnetwork` database
- **Role-based access control** (RBAC)

### Network Security

- MongoDB runs on internal Docker network
- Only exposed on localhost by default
- Use VPN or SSH tunneling for remote access

### Data Encryption

For production, consider:
- **Encryption at rest**: MongoDB Enterprise feature
- **TLS/SSL encryption**: For data in transit
- **Field-level encryption**: For sensitive data

## Performance Optimization

### Indexes

The system creates optimized indexes for:
- **Unique identifiers**: `id`, `name` fields
- **Query patterns**: `status`, `type`, `timestamp`
- **Relationships**: Foreign key fields
- **TTL indexes**: Automatic data cleanup

### Connection Pooling

Configured for optimal performance:
- **Max pool size**: 50 connections
- **Min pool size**: 5 connections
- **Idle timeout**: 30 seconds

### Memory Management

- **WiredTiger cache**: Limited to 1GB in Docker
- **Adjust based on available RAM**
- **Monitor memory usage**

## Monitoring and Maintenance

### Health Checks

MongoDB health is monitored via:
- **Docker health checks**: Automatic container restart
- **Application health checks**: Connection validation
- **System health collection**: Performance metrics

### Metrics Collection

The system tracks:
- **Connection counts**
- **Query performance**
- **Resource utilization**
- **Error rates**

### Log Management

Logs are stored in:
- **Container logs**: `docker-compose logs mongodb`
- **MongoDB logs**: `./logs/mongodb/mongod.log`
- **Application logs**: Integration with system logging

## Backup and Recovery

### Automated Backups

Implement regular backups:

```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec higherselfnetwork-mongodb mongodump \
  --db higherselfnetwork \
  --out /backup/mongodb_$DATE
```

### Point-in-Time Recovery

For production:
- **Enable oplog**: For replica sets
- **Regular snapshots**: Daily/weekly backups
- **Test recovery procedures**: Validate backup integrity

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if MongoDB is running
   docker-compose ps mongodb
   
   # Check logs for errors
   docker-compose logs mongodb
   ```

2. **Authentication Failed**
   ```bash
   # Verify credentials in .env file
   # Check user creation in init script
   ```

3. **Performance Issues**
   ```bash
   # Check index usage
   db.collection.explain("executionStats").find(query)
   
   # Monitor slow queries
   db.setProfilingLevel(2, { slowms: 100 })
   ```

### Diagnostic Commands

```bash
# Connect to MongoDB shell
docker exec -it higherselfnetwork-mongodb mongosh

# Check database status
use higherselfnetwork
db.stats()

# List collections
show collections

# Check indexes
db.agents.getIndexes()

# Monitor operations
db.currentOp()
```

## Best Practices

### Development

1. **Use test data**: Separate test and production databases
2. **Index optimization**: Create indexes for query patterns
3. **Connection management**: Proper connection pooling
4. **Error handling**: Graceful error handling in code

### Production

1. **Replica sets**: High availability setup
2. **Sharding**: For large-scale deployments
3. **Monitoring**: Comprehensive monitoring setup
4. **Security**: Regular security audits
5. **Backups**: Automated backup procedures

### Code Integration

1. **Use repositories**: Abstract data access layer
2. **Validate data**: Use Pydantic models
3. **Handle transactions**: For multi-document operations
4. **Monitor performance**: Track query performance

## Next Steps

1. **Configure environment variables** in your `.env` file
2. **Start MongoDB** with `docker-compose up -d mongodb`
3. **Run initialization** to set up collections and indexes
4. **Test connection** using the provided diagnostic commands
5. **Implement monitoring** for production deployments

For additional support, refer to:
- [MongoDB Integration Guide](./MONGODB_INTEGRATION.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Monitoring Guide](./MONITORING_AND_TROUBLESHOOTING.md)
