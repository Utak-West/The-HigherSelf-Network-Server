# Developer Tooling Guide - Higher Self Network

## Overview

This comprehensive guide covers how to work effectively with Confluence, Jira, Linear, Supabase, and Notion from VS Code, providing developers with the tools and workflows needed for productive development on the Higher Self Network project.

## VS Code Setup and Configuration

### Required Extensions

#### Core Development Extensions
```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.pylint",
    "ms-vscode.vscode-typescript-next",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-json"
  ]
}
```

#### Project Management Extensions
```json
{
  "recommendations": [
    "atlassian.atlascode",
    "linear.linear",
    "notion.notion-enhancer",
    "supabase.supabase",
    "github.vscode-pull-request-github"
  ]
}
```

#### Productivity Extensions
```json
{
  "recommendations": [
    "ms-vscode.vscode-todo-highlight",
    "gruntfuggly.todo-tree",
    "streetsidesoftware.code-spell-checker",
    "ms-vscode.vscode-markdown-preview-enhanced",
    "yzhang.markdown-all-in-one"
  ]
}
```

### VS Code Settings Configuration

#### Python Development Settings
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.sortImports.args": ["--profile", "black"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### File Association Settings
```json
{
  "files.associations": {
    "*.env.example": "properties",
    "*.env.local": "properties",
    "docker-compose*.yml": "dockercompose",
    "Dockerfile*": "dockerfile"
  }
}
```

## Confluence Integration

### AtlasCode Extension Setup

#### Installation and Configuration
1. Install the **Atlassian for VS Code** extension
2. Configure connection to Confluence:
   ```
   Command Palette → Atlassian: Add Product
   → Select Confluence
   → Enter: https://utak.atlassian.net/wiki
   ```

#### Key Features
- **Page Creation:** Create and edit Confluence pages directly from VS Code
- **Content Search:** Search Confluence content without leaving the editor
- **Link Integration:** Insert links to Confluence pages in code comments
- **Template Support:** Use predefined templates for documentation

#### Workflow Integration
```markdown
<!-- In code comments -->
// See deployment guide: [Confluence Link](https://utak.atlassian.net/wiki/spaces/OPERATIONS/pages/...)

<!-- In README files -->
For detailed architecture information, see our [Confluence Documentation](link).
```

### Best Practices
- **Document as you code:** Create Confluence pages for complex features
- **Link code to docs:** Reference Confluence pages in code comments
- **Use templates:** Standardize documentation format
- **Regular updates:** Keep documentation current with code changes

## Jira Integration

### AtlasCode Jira Features

#### Issue Management
- **Create issues** directly from VS Code
- **View issue details** in sidebar
- **Transition issues** through workflow states
- **Add comments** and update descriptions

#### Code Integration
```python
# TODO: THE-123 - Implement Redis connection retry logic
# FIXME: THE-124 - Handle edge case in user authentication
```

#### Branch and Commit Integration
```bash
# Automatic branch naming
git checkout -b THE-123-fix-redis-connection

# Commit message format
git commit -m "THE-123: Fix Redis connection configuration

- Update environment variable loading
- Add connection retry mechanism
- Implement graceful degradation"
```

### Workflow Commands
```
Ctrl+Shift+P → Atlassian: Create Issue
Ctrl+Shift+P → Atlassian: View My Issues
Ctrl+Shift+P → Atlassian: Transition Issue
```

## Linear Integration

### Linear VS Code Extension

#### Setup
1. Install **Linear** extension
2. Authenticate with Linear account
3. Configure workspace: `the-higherself-network`

#### Key Features
- **Issue creation** from selected code
- **Branch creation** with Linear issue naming
- **Status updates** from commit messages
- **Issue search** and filtering

#### Workflow Integration
```typescript
// Create issue from code selection
// 1. Select problematic code
// 2. Right-click → Linear: Create Issue from Selection
// 3. Fill in issue details
// 4. Automatic branch creation option

// Status updates via commits
git commit -m "THE-123: Implement user authentication

Fixes THE-123
- Add JWT token validation
- Implement user session management
- Add password hashing utilities"
```

### Keyboard Shortcuts
```
Ctrl+Shift+L → Open Linear panel
Ctrl+Alt+I → Create issue from selection
Ctrl+Alt+B → Create branch from issue
```

## Supabase Integration

### Supabase Extension Setup

#### Installation and Configuration
1. Install **Supabase** extension
2. Connect to project:
   ```
   Project URL: https://mmmtfmulvmvtxybwxxrr.supabase.co
   Anon Key: [Your anon key]
   Service Role Key: [Your service role key]
   ```

#### Database Management
- **Schema visualization** in VS Code sidebar
- **Query execution** with syntax highlighting
- **Table data browsing** and editing
- **Real-time subscriptions** monitoring

#### Development Workflow
```sql
-- Execute queries directly in VS Code
SELECT * FROM business_entities 
WHERE status = 'active'
LIMIT 10;

-- Create and test functions
CREATE OR REPLACE FUNCTION get_user_profile(user_id UUID)
RETURNS TABLE(name TEXT, email TEXT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT u.name, u.email
  FROM users u
  WHERE u.id = user_id;
END;
$$;
```

### Local Development Setup
```bash
# Install Supabase CLI
npm install -g supabase

# Initialize local development
supabase init
supabase start

# Link to remote project
supabase link --project-ref mmmtfmulvmvtxybwxxrr
```

## Notion Integration

### Notion Enhancement Extension

#### Setup and Configuration
1. Install **Notion Enhancer** extension
2. Configure API integration:
   ```
   API Token: [Your Notion integration token]
   Database IDs: [Configure for each database]
   ```

#### Database Integration
```javascript
// Access Notion databases from VS Code
const databases = {
  businessEntities: "1f021ff4d5fb80d1bf33e3383cc65b5f",
  contactsProfiles: "1f021ff4d5fb80e2a492d5da5a412df6",
  communityHub: "1f021ff4d5fb80f08a7fc4819e480d6e"
};

// Query database directly
const results = await notion.databases.query({
  database_id: databases.businessEntities,
  filter: {
    property: "Status",
    select: { equals: "Active" }
  }
});
```

#### Content Management
- **Page creation** from VS Code
- **Database queries** with IntelliSense
- **Content synchronization** with code documentation
- **Template management** for consistent formatting

### Development Workflow
```markdown
<!-- Link code to Notion pages -->
/**
 * Business Entity Management Service
 * 
 * Notion Database: Business Entities Registry
 * Documentation: [Notion Page Link]
 * 
 * @see https://notion.so/business-entities-guide
 */
```

## Integrated Development Workflow

### Daily Development Routine

#### 1. Morning Setup
```bash
# Check Linear issues assigned to you
Linear: View My Issues (Ctrl+Shift+L)

# Review Confluence updates
Atlassian: Recent Activity

# Check Supabase project status
Supabase: View Project Health
```

#### 2. Feature Development
```bash
# 1. Create branch from Linear issue
git checkout -b THE-123-feature-name

# 2. Update Notion documentation
# 3. Write code with proper comments
# 4. Test with Supabase integration
# 5. Commit with Linear issue reference
git commit -m "THE-123: Implement feature

- Add new functionality
- Update documentation
- Add tests"
```

#### 3. Code Review Process
```bash
# 1. Create pull request with Linear integration
# 2. Update Confluence documentation if needed
# 3. Notify team via Jira comments
# 4. Monitor Supabase performance impact
```

### Cross-Tool Synchronization

#### Issue Tracking Flow
```
Linear Issue → Jira Epic → Confluence Documentation → Code Implementation → Supabase Deployment
```

#### Documentation Flow
```
Code Comments → Confluence Pages → Notion Database → Team Knowledge Base
```

## Troubleshooting Common Issues

### Authentication Problems

#### Confluence/Jira Connection Issues
```bash
# Clear cached credentials
Command Palette → Atlassian: Sign Out
Command Palette → Atlassian: Sign In

# Check network connectivity
curl -I https://utak.atlassian.net/wiki
```

#### Linear Authentication
```bash
# Re-authenticate Linear extension
Command Palette → Linear: Sign Out
Command Palette → Linear: Sign In
```

### Extension Conflicts

#### Python Extension Issues
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.defaultInterpreterPath": "./venv/bin/python"
}
```

#### Performance Optimization
```json
{
  "files.watcherExclude": {
    "**/node_modules/**": true,
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/venv/**": true,
    "**/__pycache__/**": true
  }
}
```

### Database Connection Issues

#### Supabase Connection Problems
```bash
# Test connection
supabase status

# Reset local environment
supabase stop
supabase start
```

#### Notion API Issues
```javascript
// Test API connection
const { Client } = require('@notionhq/client');
const notion = new Client({ auth: process.env.NOTION_TOKEN });

// Test query
const response = await notion.databases.list();
console.log(response);
```

## Performance Optimization

### VS Code Performance
```json
{
  "extensions.autoUpdate": false,
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/.git": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/venv": true
  }
}
```

### Extension Management
- **Disable unused extensions** for better performance
- **Use workspace-specific settings** for project configurations
- **Regular cleanup** of cached data and temporary files

## Security Best Practices

### API Key Management
```bash
# Use environment variables
export NOTION_API_TOKEN="secret_..."
export SUPABASE_ANON_KEY="eyJ..."

# Never commit API keys to version control
echo "*.env" >> .gitignore
```

### Access Control
- **Use least privilege** principle for API tokens
- **Regular token rotation** for security
- **Monitor access logs** for unusual activity

This guide provides the foundation for effective development tooling integration. Regular updates and team feedback will help refine these practices over time.
