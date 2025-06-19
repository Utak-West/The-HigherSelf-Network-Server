# HigherSelf Network MCP Setup Instructions

## 🚀 Quick Setup for Augment Code

Here's the **step-by-step approach** to get MCP servers working in Augment Code:

### Step 1: Configure Augment Code Settings

1. **Open Augment Code**
2. **Press `Cmd/Ctrl + Shift + P`**
3. **Type "Preferences: Open Settings (JSON)"**
4. **Add this configuration to your settings:**

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

### Step 2: Get Your API Credentials

#### Notion Integration Token (REQUIRED)
1. Go to [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. Click "Create new integration"
3. Name it "HigherSelf Network MCP"
4. Copy the integration token (starts with "secret_")
5. Grant access to your databases by sharing them with the integration

#### Slack Bot Token (OPTIONAL)
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Create a new app or use existing one
3. Get Bot User OAuth Token (starts with "xoxb-")
4. Get your Team/Workspace ID

### Step 3: Update Your Settings

Replace the placeholder values in your Augment Code settings:

```json
"NOTION_TOKEN": "secret_your_actual_notion_token_here"
"SLACK_BOT_TOKEN": "xoxb-your-actual-slack-token-here"
"SLACK_TEAM_ID": "your-actual-team-id-here"
```

### Step 4: Restart Augment Code

1. **Completely close Augment Code**
2. **Reopen Augment Code**
3. **Wait for MCP servers to initialize**

### Step 5: Test Your Setup

Try these test queries in Augment Code:

```
"Show me my Notion databases"
"List files in my HigherSelf Network Server directory"
"Help me search my Notion workspace"
"Show me the structure of my project files"
```

## 🎯 Priority MCP Servers for Your Projects

### Project 1: Real-Time AI Agent Contact Processing
- ✅ **Notion MCP Server** (contact storage and management)
- ✅ **File System MCP Server** (processing logs and file access)
- 🔄 **Slack MCP Server** (team notifications - optional)

### Project 2: Multi-Entity Workflow Expansion
- ✅ **Notion MCP Server** (multi-entity contact data)
- ✅ **File System MCP Server** (workflow configuration files)
- 🔄 **Additional servers** (can be added later as needed)

### Project 3: Bidirectional Notion Intelligence Hub
- ✅ **Notion MCP Server** (primary database operations)
- ✅ **File System MCP Server** (document sync and management)
- 🔄 **Enhanced integrations** (expandable architecture)

## 🚀 Ready to Proceed?

Once you have the **Notion** and **File System** MCP servers working, we can immediately start implementing **Project 1: Real-Time AI Agent Contact Processing Pipeline**.

The beauty is that your existing system already has:
- ✅ WordPress integration capturing contacts
- ✅ Nyra agent processing leads
- ✅ Workflow orchestration system
- ✅ Notion database structure

We just need to enhance Nyra with MCP capabilities to:
1. **Store contacts directly in Notion** via MCP
2. **Log processing activities** via File System MCP
3. **Trigger intelligent workflows** based on contact analysis

## 🆘 Troubleshooting

### If MCP servers don't start:
1. Check the Augment Code console for error messages
2. Verify your API tokens are correct
3. Ensure you have internet connectivity
4. Try restarting Augment Code

### If you get permission errors:
- The `npx` approach should avoid permission issues
- No global installation required
- Packages are downloaded on-demand

### If packages aren't found:
- The `@modelcontextprotocol/` packages are the official ones
- They should be available in the npm registry
- Try testing individual packages with `npx @modelcontextprotocol/server-notion --help`

## 📞 Next Steps

**Let me know when you have the MCP servers configured and we'll immediately start enhancing your AI agents with these new capabilities!**

The first enhancement will be integrating Nyra with the Notion MCP server to process your WordPress contact captures in real-time with intelligent Notion database updates.
