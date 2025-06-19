# Augment Code MCP Configuration Guide

## 🎯 Overview

This guide provides step-by-step instructions for configuring MCP (Model Context Protocol) servers in Augment Code to enhance your HigherSelf Network Server AI agent capabilities.

## 🚀 Quick Configuration Steps

### Step 1: Open Augment Code Settings

1. **Open Augment Code**
2. **Press `Cmd/Ctrl + Shift + P`** to open the command palette
3. **Type "Preferences: Open Settings (JSON)"** and select it
4. This will open your `settings.json` file

### Step 2: Add MCP Server Configuration

Add the following configuration to your `settings.json` file:

```json
{
  "augment.advanced": {
    "mcpServers": [
      {
        "name": "notion-higherself",
        "command": "npx",
        "args": ["-y", "@notionhq/notion-mcp-server"],
        "env": {
          "NOTION_TOKEN": "secret_your_notion_integration_token_here"
        }
      },
      {
        "name": "filesystem-higherself",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server"],
        "env": {}
      },
      {
        "name": "slack-higherself",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-slack"],
        "env": {
          "SLACK_BOT_TOKEN": "xoxb-your-bot-token-here",
          "SLACK_TEAM_ID": "your-team-id-here"
        }
      }
    ]
  }
}
```

### Step 3: Configure API Credentials

#### Notion Integration Token (REQUIRED)

1. **Go to Notion Integrations**: https://www.notion.so/profile/integrations
2. **Click "Create new integration"**
3. **Name it**: "HigherSelf Network MCP"
4. **Copy the integration token** (starts with "secret_")
5. **Replace the placeholder** in your settings:
   ```json
   "NOTION_TOKEN": "secret_your_actual_notion_token_here"
   ```
6. **Share your databases** with the integration:
   - Go to each Notion database you want to access
   - Click "Share" → "Invite" → Select your integration

#### Slack Bot Token (OPTIONAL)

1. **Go to Slack Apps**: https://api.slack.com/apps
2. **Create a new app** or use existing one
3. **Get Bot User OAuth Token** (starts with "xoxb-")
4. **Get your Team/Workspace ID**
5. **Replace the placeholders** in your settings:
   ```json
   "SLACK_BOT_TOKEN": "xoxb-your-actual-slack-token-here",
   "SLACK_TEAM_ID": "your-actual-team-id-here"
   ```

### Step 4: Save and Restart

1. **Save your settings.json file** (`Cmd/Ctrl + S`)
2. **Completely close Augment Code**
3. **Reopen Augment Code**
4. **Wait for MCP servers to initialize** (may take 30-60 seconds)

## 🧪 Testing Your Configuration

### Test Queries

Once configured, try these test queries in Augment Code:

```
"Show me my Notion databases"
"List files in my HigherSelf Network Server directory"
"Help me search my Notion workspace"
"Show me the structure of my project files"
"What contacts do I have in my Notion databases?"
```

### Verification Steps

1. **Check MCP Server Status**: Look for MCP server indicators in Augment Code
2. **Test Notion Access**: Try querying your Notion databases
3. **Test File System Access**: Try listing files in your project directory
4. **Check for Errors**: Look at Augment Code console for any error messages

## 🔧 Troubleshooting

### Common Issues

#### MCP Servers Not Starting
- **Check Node.js**: Ensure Node.js and npm are installed
- **Check Internet**: MCP servers need internet access to download packages
- **Check Syntax**: Verify your JSON configuration is valid
- **Restart Augment Code**: Sometimes a full restart is needed

#### Notion Integration Issues
- **Token Format**: Ensure token starts with "secret_"
- **Database Access**: Make sure you've shared databases with the integration
- **Permissions**: Check that the integration has the right permissions

#### File System Access Issues
- **Path Verification**: Ensure the path exists and is accessible
- **Permissions**: Check that Augment Code has file system access

### Debug Steps

1. **Check Augment Code Logs**: Look for MCP-related error messages
2. **Test Individual Servers**: Try running MCP servers manually
3. **Verify Credentials**: Double-check all API tokens and IDs
4. **Network Connectivity**: Ensure internet access for package downloads

## 🎯 Next Steps

Once your MCP servers are configured and working:

1. **Verify All Servers**: Ensure Notion and File System MCP servers are operational
2. **Test Core Functionality**: Try the test queries above
3. **Begin Project Implementation**: Start with Project 1 (Real-Time AI Agent Contact Processing)
4. **Monitor Performance**: Watch for any issues or optimization opportunities

## 📋 Configuration Checklist

- [ ] Augment Code settings.json updated with MCP configuration
- [ ] Notion integration token configured and databases shared
- [ ] File system path verified and accessible
- [ ] Augment Code restarted completely
- [ ] MCP servers initialized successfully
- [ ] Test queries working properly
- [ ] Ready to implement AI agent enhancements

## 🚀 Ready for AI Agent Enhancement

With MCP servers configured, you can now:

- **Access Notion databases** directly from AI agents
- **Read and write files** in your project directory
- **Integrate with team communication** via Slack (if configured)
- **Build intelligent workflows** that span multiple systems
- **Implement the three high-impact projects** with enhanced capabilities

Your HigherSelf Network Server is now ready for the next level of AI agent integration! 🎉
