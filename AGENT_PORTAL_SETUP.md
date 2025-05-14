# The HigherSelf Network - Agent Portal Setup Guide

This guide will help you set up the Agent Portal system, which includes:

1. A web-based frontend for staff to interact with AI agents
2. A Notion database integration for task management
3. API endpoints for processing agent tasks

## Prerequisites

- The HigherSelf Network Server running in Docker
- A Notion account with API access
- A Notion integration token with write access
- A parent page in Notion where the database will be created

## Step 1: Configure Environment Variables

1. Make sure your `.env` file includes the following variables:

```
# Notion API Configuration
NOTION_API_TOKEN=your_notion_api_token
NOTION_PARENT_PAGE_ID=your_parent_page_id

# Optional: Notion Agent Tasks Database ID (will be created if not provided)
NOTION_AGENT_TASKS_DB=
```

2. Replace `your_notion_api_token` with your actual Notion API token
3. Replace `your_parent_page_id` with the ID of the parent page where the database will be created

## Step 2: Set Up the Notion Database

Run the setup script to create the Notion database:

```bash
python setup_agent_tasks.py
```

This will:
1. Create a new database in the specified parent page
2. Update your `.env` file with the database ID
3. Configure the database with the necessary properties

If successful, you'll see a message with the database ID and a link to access it.

## Step 3: Deploy the Frontend

### Option 1: Deploy to a Web Server

Use the provided deployment script:

```bash
sudo ./deploy_frontend.sh http://your-api-url/api/v1 https://notion.so/your-database-id
```

Replace:
- `http://your-api-url/api/v1` with your actual API URL
- `https://notion.so/your-database-id` with your Notion database URL

### Option 2: Serve Locally for Testing

For local testing, you can use Python's built-in HTTP server:

```bash
cd frontend
python -m http.server 8080
```

Then access the portal at http://localhost:8080

### Option 3: Deploy to GitHub Pages or Netlify

For a more permanent solution, you can deploy the frontend to a static hosting service:

**GitHub Pages:**
1. Create a new repository on GitHub
2. Push the frontend directory to the repository
3. Enable GitHub Pages in the repository settings

**Netlify:**
1. Sign up for a Netlify account
2. Connect your GitHub repository
3. Configure the build settings (not required for this static site)
4. Deploy

## Step 4: Configure CORS for the API

Ensure your API server allows cross-origin requests from your frontend domain:

1. Update the CORS settings in `api/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Replace with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

2. Restart the API server for the changes to take effect

## Step 5: Test the Integration

1. Open the Agent Portal in your web browser
2. Create a test task using one of the agents
3. Check that the task appears in the Notion database
4. Verify that the task is processed and results are displayed

## Step 6: Share with Staff

1. Provide staff with access to the Agent Portal URL
2. Share the Notion database with relevant team members
3. Direct staff to the README in the frontend directory for usage instructions

## Troubleshooting

### API Connection Issues

If the frontend cannot connect to the API:

1. Check that the API server is running
2. Verify the API URL in `frontend/app.js`
3. Ensure CORS is properly configured
4. Check for any network restrictions or firewalls

### Notion Integration Issues

If tasks are not appearing in Notion:

1. Verify your Notion API token has the necessary permissions
2. Check that the database ID in your `.env` file is correct
3. Ensure the Notion API is not rate-limited
4. Look for error messages in the API server logs

### Agent Processing Issues

If agents are not processing tasks:

1. Check that the agent manager service is running
2. Verify that the required dependencies are installed
3. Look for error messages in the API server logs
4. Test the agent endpoints directly using a tool like curl or Postman

## Customization

### Modifying the Frontend

The frontend is built with vanilla HTML, CSS, and JavaScript for simplicity. You can customize it by:

1. Editing `frontend/index.html` to change the layout and structure
2. Modifying `frontend/styles.css` to update the appearance
3. Updating `frontend/app.js` to change the functionality

### Adding New Agent Types

To add a new agent type:

1. Update the `agents` object in `services/agent_manager.py`
2. Add the new agent type to the form in `frontend/index.html`
3. Add task types and form templates in `frontend/app.js`
4. Update the Notion database to include the new agent type

### Extending the Notion Integration

To add more functionality to the Notion integration:

1. Modify `tools/notion_agent_tasks.py` to add new methods
2. Update the database schema as needed
3. Add new API endpoints in `api/routes/agent_tasks.py`

## Maintenance

### Backing Up the Notion Database

Notion automatically backs up your data, but you can also:

1. Export the database periodically
2. Create a script to back up task data to a local database
3. Use the Notion API to create snapshots of important data

### Monitoring System Health

To ensure the system is running smoothly:

1. Set up monitoring for the API server
2. Create health check endpoints
3. Implement logging for important events
4. Set up alerts for critical errors

## Security Considerations

1. Never expose your Notion API token in client-side code
2. Implement proper authentication for the Agent Portal
3. Validate all input from users before processing
4. Use HTTPS for all communications
5. Regularly update dependencies to patch security vulnerabilities

## Support

If you encounter any issues or have questions, please contact the development team.
