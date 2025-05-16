# The 7 Space Integration MCP Server

This MCP (Model Context Protocol) server provides integration tools for The 7 Space website, enabling interaction with WordPress, Elementor Pro, and Amelia booking system.

## Features

### WordPress Integration

- Retrieve posts and pages
- Create and update content
- Manage media

### Elementor Pro Integration

- Get available templates
- Apply templates to pages

### Amelia Booking Integration

- Retrieve services and appointments
- Create new bookings
- Manage customers

## Setup

1. Install dependencies:

```bash
cd ~/Documents/Cline/MCP/the7space-integration
npm install
```

2. Create a `.env` file with your credentials (see `.env.example` for reference):

```
WP_API_URL=https://your-wordpress-site.com
WP_USERNAME=your_admin_username
WP_APP_PASSWORD=your_application_password
AMELIA_API_KEY=your_amelia_api_key
```

To generate a WordPress application password:

1. Go to your WordPress admin dashboard
2. Navigate to Users → Profile
3. Scroll down to "Application Passwords"
4. Enter a name (e.g., "MCP Integration") and click "Add New"
5. Copy the generated password

3. Build the project:

```bash
npm run build
```

## MCP Configuration

Add the following configuration to your MCP settings file at `~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-cline/settings/mcp_settings.json`:

```json
{
  "mcpServers": {
    "the7space": {
      "command": "node",
      "args": ["~/Documents/Cline/MCP/the7space-integration/build/index.js"],
      "env": {
        "WP_API_URL": "https://the7space.com",
        "WP_USERNAME": "your_admin_username",
        "WP_APP_PASSWORD": "your_application_password",
        "AMELIA_API_KEY": "your_amelia_api_key"
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

## Available Tools

The server provides the following tools:

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

## Example Usage

Once configured, you can use these tools in your conversations:

```
Can you get the list of recent blog posts from The 7 Space website?
```

```
Please create a new booking for a sound healing session on Friday at 2pm for John Doe (john.doe@example.com).
```

```
Can you check all upcoming appointments for next week?
