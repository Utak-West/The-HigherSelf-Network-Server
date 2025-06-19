# HigherSelf Network MCP Credentials Setup Guide

## 🔐 Essential API Credentials for Your MCP Servers

This guide walks you through obtaining the API credentials needed for your HigherSelf Network MCP integration.

## 1. 🗂️ Notion Integration Token (CRITICAL)

**Purpose**: Access your 2,791 contacts across The 7 Space, AM Consulting, and HigherSelf Core

### Steps:
1. **Go to**: [https://www.notion.so/profile/integrations](https://www.notion.so/profile/integrations)
2. **Click**: "Create new integration"
3. **Name**: "HigherSelf Network MCP Server"
4. **Description**: "AI agent integration for contact management and workflow automation"
5. **Associated workspace**: Select your HigherSelf workspace
6. **Copy the Integration Token** (starts with `secret_`)

### Grant Database Access:
After creating the integration, you need to grant it access to your databases:

1. **Go to each of your 16 core Notion databases**:
   - Business Entities Registry
   - Contacts & Profiles
   - Community Hub
   - Products & Services
   - Workflow Instances
   - Marketing Campaigns
   - Feedback & Surveys
   - Rewards & Bounties
   - Master Tasks
   - Agent Communication Patterns
   - Agent Registry
   - API Integrations Catalog
   - Data Transformations Registry
   - Notifications Templates
   - Use Cases Library
   - Workflows Library

2. **For each database**:
   - Click the "..." menu in the top right
   - Select "Add connections"
   - Choose "HigherSelf Network MCP Server"
   - Click "Confirm"

### Your Token:
```
NOTION_TOKEN=secret_your_actual_token_here
```

## 2. 🐙 GitHub Personal Access Token

**Purpose**: Repository management, code deployment, documentation updates

### Steps:
1. **Go to**: [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. **Click**: "Generate new token (classic)"
3. **Note**: "HigherSelf Network MCP Access"
4. **Expiration**: 90 days (or custom)
5. **Select scopes**:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `read:org` (Read org and team membership)
   - ✅ `read:user` (Read user profile data)
   - ✅ `user:email` (Access user email addresses)

### Your Token:
```
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_actual_token_here
```

## 3. 🔍 Brave Search API Key (Optional but Recommended)

**Purpose**: Market research, competitor analysis, art gallery trends

### Steps:
1. **Go to**: [https://api.search.brave.com/](https://api.search.brave.com/)
2. **Sign up** for a free account
3. **Verify your email**
4. **Go to the API dashboard**
5. **Copy your API key**

### Your Key:
```
BRAVE_API_KEY=your_actual_brave_api_key_here
```

## 4. 🗄️ PostgreSQL Connection (Optional - Advanced Analytics)

**Purpose**: Advanced analytics, reporting, business intelligence

### If you have PostgreSQL running:
```
POSTGRES_CONNECTION_STRING=postgresql://username:password@localhost:5432/higherself_network
```

### If you don't have PostgreSQL:
You can skip this for now and add it later when you need advanced analytics.

## 5. 📁 File System Access (Automatic)

**Purpose**: Document management, processing logs, asset organization

This is automatically configured to your HigherSelf Network Server directory:
```
/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server
```

## 🔧 Complete Augment Code Configuration

Here's your complete MCP server configuration with placeholders for your actual credentials:

```json
{
  "augment.advanced": {
    "mcpServers": [
      {
        "name": "notion-higherself",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-notion"],
        "env": {
          "NOTION_TOKEN": "secret_your_actual_notion_token_here"
        }
      },
      {
        "name": "github-higherself",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_actual_github_token_here"
        }
      },
      {
        "name": "brave-search-higherself",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        "env": {
          "BRAVE_API_KEY": "your_actual_brave_api_key_here"
        }
      },
      {
        "name": "filesystem-higherself",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/utakwest/Documents/HigherSelf/The HigherSelf Network /The HigherSelf Network Server"],
        "env": {}
      }
    ]
  }
}
```

## ✅ Testing Your Setup

After configuring your credentials:

1. **Restart Augment Code completely**
2. **Wait 30 seconds** for MCP servers to initialize
3. **Test with these queries**:

### Test Notion Integration:
```
"Show me my Notion databases"
"List contacts in my Business Entities database"
"How many contacts do I have across all databases?"
```

### Test GitHub Integration:
```
"List my GitHub repositories"
"Show recent commits in The-HigherSelf-Network-Server"
"What files are in my main repository?"
```

### Test Brave Search:
```
"Search for art gallery marketing trends"
"Find information about wellness center automation"
"Research consulting business best practices"
```

### Test File System:
```
"List files in my HigherSelf Network Server directory"
"Show me the contents of my agents folder"
"What documentation files do I have?"
```

## 🚨 Security Best Practices

### Protect Your Tokens:
- ✅ Never share tokens in screenshots or public repositories
- ✅ Use environment variables for sensitive credentials
- ✅ Rotate tokens regularly (every 90 days)
- ✅ Limit token permissions to minimum required scope

### Monitor Usage:
- 📊 Check API usage in each service's dashboard
- 🔍 Monitor for unusual activity
- 📝 Keep track of which applications have access

## 🆘 Troubleshooting

### Common Issues:

**"Invalid token" errors:**
- Double-check you copied the complete token
- Ensure no extra spaces or characters
- Verify the token hasn't expired

**"Permission denied" errors:**
- For Notion: Ensure integration has access to specific databases
- For GitHub: Check token scopes include required permissions
- For file system: Verify directory path is correct

**"Server not found" errors:**
- Check internet connectivity
- Verify package names are correct
- Try restarting Augment Code

## 🚀 Ready for AI Agent Enhancement!

Once your MCP servers are working, we'll immediately enhance your AI agents with:

1. **Nyra**: Real-time contact processing with Notion integration
2. **Liora**: Market research with Brave Search integration
3. **Atlas**: Knowledge management with File System integration
4. **All Agents**: Enhanced capabilities through MCP server access

**Let me know when your MCP servers are configured and we'll start implementing the three high-impact projects! 🎯**
