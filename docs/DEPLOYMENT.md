# Deployment Guide

This document provides instructions for deploying the Windsurf Agent Network on The HigherSelf Network Server, ensuring Notion remains the central hub for all operations.

## Deployment Requirements

- Python 3.10+
- The HigherSelf Network Server access
- Notion API integration token
- API keys for connected services (Typeform, HubSpot, Amelia, etc.)
- Sufficient permissions to configure webhooks on external services

## Environment Setup

1. Clone the repository on The HigherSelf Network Server:

   ```bash
   git clone https://github.com/the-higherself-network/windsurf-notion-agent.git
   cd windsurf-notion-agent
   ```

1. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

1. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

1. Edit the `.env` file with your API credentials and database IDs.

## Notion Database Setup

1. Ensure you have an integration token with sufficient permissions in your Notion workspace.

2. Set up the required Notion databases:

   a. Manually create the databases following the structure in `docs/NOTION_INTEGRATION.md`

   b. Alternatively, use the database setup tool:

   ```bash
   # Add NOTION_PARENT_PAGE_ID to your .env file
   python -m tools.notion_db_setup
   ```

3. Update your `.env` file with the generated database IDs.

## Running the Service

### Development Mode

For development and testing:

```bash
python main.py
```

### Production Deployment

For production deployment on The HigherSelf Network Server:

1. Set up a process manager (systemd, Supervisor, PM2, etc.)

   Example systemd service file (`/etc/systemd/system/windsurf-agent.service`):

   ```ini
   [Unit]
   Description=Windsurf Agent Network
   After=network.target

   [Service]
   User=higherself
   WorkingDirectory=/path/to/windsurf-notion-agent
   ExecStart=/path/to/windsurf-notion-agent/venv/bin/python main.py
   Restart=always
   RestartSec=10
   Environment="PYTHONUNBUFFERED=1"
   StandardOutput=journal
   StandardError=journal

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable windsurf-agent
   sudo systemctl start windsurf-agent
   ```

3. Set up Nginx as a reverse proxy:

   ```nginx
   server {
       listen 80;
       server_name agent-api.thehigherselfnetwork.com;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. Secure with SSL using Let's Encrypt:

   ```bash
   sudo certbot --nginx -d agent-api.thehigherselfnetwork.com
   ```

## Webhook Configuration

### Typeform

1. In your Typeform dashboard, navigate to the form settings
2. Go to Connect → Webhooks
3. Enter the webhook URL: `https://agent-api.thehigherselfnetwork.com/webhooks/typeform?business_entity_id=YOUR_ENTITY&workflow_id=YOUR_WORKFLOW`
4. Set the webhook secret (must match `WEBHOOK_SECRET` in your `.env`)
5. Test the webhook to ensure it's working

### Amelia

1. Configure Amelia to send webhooks for booking events
2. Set the webhook URL: `https://agent-api.thehigherselfnetwork.com/webhooks/amelia?workflow_id=YOUR_WORKFLOW`
3. Configure the webhook payload format to match the expected format
4. Set the webhook secret (must match `WEBHOOK_SECRET` in your `.env`)
5. Test with a test booking

## Monitoring and Maintenance

### Logs

Logs are stored in the `logs` directory and rotated automatically. To view logs:

```bash
tail -f logs/windsurf_agents.log
```

In production, logs are also sent to the system journal:

```bash
sudo journalctl -u windsurf-agent -f
```

### Health Checks

Monitor the health of the agent system:

```bash
curl http://localhost:8000/health
```

Set up regular health checks using a monitoring system.

### Backup

Regularly back up your `.env` file and any custom configurations. Notion data is backed up automatically by Notion.

## Troubleshooting

### Common Issues

1. **Webhook Errors**: Check the webhook secret and ensure the payload format matches what the agent expects.

2. **Notion API Issues**: Verify your Notion token has the correct permissions and database IDs are correct.

3. **Agent Failures**: Check the logs for detailed error messages. Most issues are related to configuration or API credentials.

4. **Workflow State Errors**: If workflow instances are not transitioning correctly, check the workflow definition and ensure the agent has the correct logic.

### Getting Help

For additional support, contact The HigherSelf Network's technical team or refer to the internal knowledge base.
