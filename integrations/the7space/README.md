# The 7 Space MCP Integration

This integration connects The HigherSelf Network Server with The 7 Space website, providing tools for WordPress, Elementor Pro, and Amelia booking system integration through MCP (Model Context Protocol).

## Overview

This integration includes:

1. **MCP Server** - A TypeScript-based MCP server that exposes tools for interacting with The 7 Space website
2. **Service Module** - A Python module that integrates with the MCP tools from the main server
3. **Agent Integration** - Helper classes to connect the HigherSelf agents with The 7 Space service

## MCP Tools

The integration provides the following MCP tools:

### WordPress Tools

- `get_wp_posts`: Retrieve WordPress posts with filtering options
- `create_wp_post`: Create a new WordPress post or page
- `update_wp_post`: Update an existing WordPress post or page

### Elementor Pro Tools

- `get_elementor_templates`: Get available Elementor templates
- `apply_elementor_template`: Apply an Elementor template to a page

### Amelia Booking Tools

- `get_amelia_services`: Get available Amelia services
- `get_amelia_appointments`: Get Amelia appointments with filtering options
- `create_amelia_appointment`: Create a new Amelia appointment

## Setup Instructions

### Prerequisites

1. **WordPress Website** with:
   - WordPress REST API enabled
   - Application password created for an admin user
   - Elementor Pro installed
   - Amelia booking plugin installed and configured

2. **Required Python Dependencies**:

   ```
   pydantic>=2.0.0
   loguru>=0.7.0
   ```

### Configuration

1. Set up the MCP server:

   ```bash
   # Navigate to the MCP server directory
   cd ~/Documents/Cline/MCP/the7space-integration
   
   # Install dependencies
   npm install
   
   # Build the server
   npm run build
   ```

2. Add environment variables to your `.env` file:

   ```
   THE7SPACE_WP_API_URL=https://the7space.com
   THE7SPACE_WP_USERNAME=your_admin_username
   THE7SPACE_WP_APP_PASSWORD=your_application_password
   THE7SPACE_AMELIA_API_KEY=your_amelia_api_key
   ```

3. Add the MCP server configuration to your MCP settings file (see `mcp_integration.json` for details)

## Agent Integration

This integration extends the capabilities of these agents:

1. **Content Lifecycle Agent** - For managing WordPress content
2. **Booking Agent** - For managing Amelia bookings
3. **Lead Capture Agent** - For processing leads from The 7 Space website

To register with an agent:

```python
from integrations.the7space.agent_integration import get_the7space_integration

# Get the integration
the7space_integration = await get_the7space_integration()

# Register with an agent
await the7space_integration.register_with_content_lifecycle_agent(content_agent)
await the7space_integration.register_with_booking_agent(booking_agent)
await the7space_integration.register_with_lead_capture_agent(lead_agent)
```

## Implementation Notes

- The agent integration requires extending the base agent classes with registration methods for providers and handlers.
- The service file has placeholder implementations that would be replaced with actual MCP tool calls in a production environment.
- Error handling and logging follow the same patterns used in the rest of the codebase.

## Future Enhancements

- Add tools for WooCommerce integration
- Implement media upload and management
- Add support for custom post types and taxonomies
- Extend Elementor integration with custom widget support
