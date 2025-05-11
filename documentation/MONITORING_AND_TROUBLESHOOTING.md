# The HigherSelf Network Server - Monitoring and Troubleshooting Guide

This guide provides detailed information on monitoring The HigherSelf Network Server, identifying common issues, and implementing solutions to ensure smooth operation.

## Table of Contents

1. [System Health Monitoring](#system-health-monitoring)
2. [Log Analysis](#log-analysis)
3. [Performance Monitoring](#performance-monitoring)
4. [Common Issues and Solutions](#common-issues-and-solutions)
5. [Integration Troubleshooting](#integration-troubleshooting)
6. [Agent Troubleshooting](#agent-troubleshooting)
7. [Recovery Procedures](#recovery-procedures)
8. [Maintenance Tasks](#maintenance-tasks)

## System Health Monitoring

### Health Endpoint

The system provides a `/health` endpoint that returns the current status of all components:

```bash
curl http://localhost:8000/health
```

Example response:
```json
{
  "status": "healthy",
  "timestamp": "2023-07-15T14:32:45Z",
  "version": "1.0.0",
  "components": {
    "notion_service": "healthy",
    "agents": {
      "nyra": "healthy",
      "solari": "healthy",
      "ruvo": "healthy",
      "liora": "healthy",
      "sage": "healthy",
      "elan": "healthy",
      "zevi": "healthy"
    },
    "integrations": {
      "typeform": "healthy",
      "woocommerce": "healthy",
      "amelia": "degraded",
      "beehiiv": "healthy",
      "circle": "healthy"
    }
  }
}
```

Status values:
- `healthy`: Component is functioning normally
- `degraded`: Component is functioning but with issues
- `unhealthy`: Component is not functioning
- `unknown`: Component status cannot be determined

### Service Status Endpoints

Check the status of specific services:

```bash
curl http://localhost:8000/api/status/notion
curl http://localhost:8000/api/status/typeform
curl http://localhost:8000/api/status/woocommerce
# etc.
```

### Automated Monitoring

Set up automated monitoring using tools like:

1. **Prometheus + Grafana**:
   - The server exposes metrics at `/metrics` endpoint
   - Configure Prometheus to scrape these metrics
   - Set up Grafana dashboards for visualization

2. **Healthchecks.io**:
   - Configure periodic pings to the health endpoint
   - Set up alerts for failed checks

3. **Docker monitoring**:
   - If using Docker, monitor container health
   - Use `docker stats` for resource usage

## Log Analysis

### Log Locations

Logs are stored in multiple locations:

- **Application logs**: `logs/app.log`
- **Docker logs**: Access with `docker-compose logs`
- **Structured JSON logs**: `logs/json/app.json` (if enabled)

### Log Levels

The system uses the following log levels:

- `DEBUG`: Detailed debugging information
- `INFO`: General operational information
- `WARNING`: Issues that might need attention
- `ERROR`: Error conditions that should be addressed
- `CRITICAL`: Critical conditions requiring immediate attention

### Searching Logs

Use standard tools to search logs:

```bash
# Search for errors
grep ERROR logs/app.log

# Search for a specific agent
grep "Nyra" logs/app.log

# Search for a specific workflow
grep "workflow_id-123456" logs/app.log

# Search for integration issues
grep -E "typeform|woocommerce|amelia" logs/app.log | grep ERROR
```

### Log Rotation

Logs are automatically rotated:
- When they reach 10MB in size
- Compressed after rotation
- Kept for 30 days by default

## Performance Monitoring

### Resource Usage

Monitor system resource usage:

```bash
# For Docker deployment
docker stats

# For direct Python deployment
top -p $(pgrep -f "python main.py")
```

### Database Performance

Monitor Notion API usage:
- Check the Agent Communication database for API call logs
- Look for slow API calls (>1 second)
- Monitor API rate limiting errors

### Request Latency

The server logs request latency for all API endpoints. Look for patterns of increasing latency, which may indicate:
- Network issues
- Notion API slowdowns
- Resource constraints

## Common Issues and Solutions

### Notion API Token Issues

**Symptoms**:
- Errors in logs: "Notion API authentication failed"
- Agents unable to read or write to Notion

**Solutions**:
1. Verify the token in `.env` file
2. Check that the token has not expired
3. Ensure the integration has access to all required pages
4. Generate a new token if necessary

### Webhook Signature Verification Failures

**Symptoms**:
- Errors in logs: "Invalid webhook signature"
- Webhooks being received but not processed

**Solutions**:
1. Verify `WEBHOOK_SECRET` in `.env` matches the secret configured in the external service
2. Check for clock synchronization issues
3. Ensure the webhook payload is not being modified in transit

### Agent Registration Failures

**Symptoms**:
- Errors in logs: "Failed to register agent in Notion"
- Missing agents in the Agent Registry database

**Solutions**:
1. Check Notion API permissions
2. Verify the Agent Registry database ID in `.env`
3. Manually create an agent record as a workaround
4. Restart the server to trigger re-registration

### Message Bus Communication Issues

**Symptoms**:
- Errors in logs: "Failed to deliver message"
- Agents not responding to events

**Solutions**:
1. Check agent subscription status
2. Verify message format
3. Restart the server to reset the message bus
4. Check for deadlocks or infinite loops

## Integration Troubleshooting

### Typeform Integration

**Common Issues**:
- Webhook not receiving form submissions
- Form data not being processed

**Troubleshooting Steps**:
1. Verify webhook URL in Typeform settings
2. Check webhook secret
3. Test with a manual form submission
4. Check Typeform API key validity

### WooCommerce Integration

**Common Issues**:
- Orders not being synchronized
- Product data missing

**Troubleshooting Steps**:
1. Verify API credentials
2. Check webhook configuration
3. Test connection with a manual API call
4. Verify SSL certificate if using HTTPS

### Amelia Booking Integration

**Common Issues**:
- Bookings not being detected
- Appointment data incomplete

**Troubleshooting Steps**:
1. Check Amelia webhook configuration
2. Verify API endpoint and credentials
3. Test with a manual booking
4. Check for custom fields that might be missing

### Circle.so Community Integration

**Common Issues**:
- Community events not being tracked
- Member data not synchronizing

**Troubleshooting Steps**:
1. Verify Circle API token
2. Check community ID
3. Test with a manual API call
4. Verify webhook configuration

## Agent Troubleshooting

### Nyra (Lead Capture)

**Common Issues**:
- Leads not being processed
- Workflow instances not being created

**Troubleshooting Steps**:
1. Check Typeform integration
2. Verify lead capture workflow templates
3. Check for validation errors in lead data
4. Verify business entity mappings

### Solari (Booking)

**Common Issues**:
- Bookings not being processed
- Order confirmations not being sent

**Troubleshooting Steps**:
1. Check Amelia and WooCommerce integrations
2. Verify booking workflow templates
3. Check for missing product mappings
4. Verify email template configurations

### Ruvo (Task Management)

**Common Issues**:
- Tasks not being created
- Task assignments failing

**Troubleshooting Steps**:
1. Check Tasks database access
2. Verify task template configurations
3. Check for missing assignee information
4. Verify workflow stage transitions

### Other Agents

For Liora, Sage, Elan, and Zevi, follow similar troubleshooting patterns:
1. Check relevant integrations
2. Verify database access
3. Check template configurations
4. Look for specific error messages in logs

## Recovery Procedures

### Database Recovery

If Notion databases become corrupted:

1. Use the database backup tool:
   ```bash
   python -m tools.notion_backup restore --date 2023-07-15
   ```

2. Manual recovery:
   - Restore from the most recent backup
   - Re-run the database setup tool if necessary
   - Update database IDs in `.env`

### Service Recovery

If the server becomes unresponsive:

1. **Docker deployment**:
   ```bash
   docker-compose restart
   ```

2. **Direct Python deployment**:
   ```bash
   pkill -f "python main.py"
   python main.py
   ```

3. **Full recovery**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Integration Recovery

If an integration fails:

1. Verify API credentials
2. Update the credentials in `.env` if necessary
3. Restart the server to reinitialize integrations
4. Run manual synchronization if available:
   ```bash
   curl -X POST http://localhost:8000/api/sync/typeform
   curl -X POST http://localhost:8000/api/sync/woocommerce
   # etc.
   ```

## Maintenance Tasks

### Regular Maintenance

Perform these tasks weekly:

1. **Check logs for errors**:
   ```bash
   grep ERROR logs/app.log | tail -n 100
   ```

2. **Verify all integrations**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Clean up old workflow instances**:
   - Archive completed workflows older than 30 days
   - Use the cleanup tool:
     ```bash
     python -m tools.cleanup_workflows --days 30
     ```

4. **Backup environment configuration**:
   ```bash
   cp .env .env.backup-$(date +%Y%m%d)
   ```

### Monthly Maintenance

Perform these tasks monthly:

1. **Update the system**:
   ```bash
   git pull
   docker-compose down
   docker-compose up -d
   ```

2. **Rotate API credentials**:
   - Generate new API keys for integrated services
   - Update `.env` with new credentials
   - Restart the server

3. **Review agent performance**:
   - Check agent statistics in Notion
   - Optimize workflow templates based on performance
   - Update agent configurations if necessary

4. **Database optimization**:
   - Archive old data
   - Verify database relationships
   - Check for orphaned records
