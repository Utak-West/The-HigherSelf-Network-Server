# Credential Acquisition Guide for Higher Self Network Server

This guide provides instructions for securely obtaining and managing API credentials for all services used by the Higher Self Network Server, in compliance with our Integration Security Rules, particularly "API Key Management" which states: "Never hardcode API keys in the codebase. Use environment variables and secure storage for all integration credentials."

## Core Services

### Notion

1. Visit [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Create a new integration with the required capabilities
3. Add the integration to your workspace
4. Note the "Internal Integration Token" (starts with `secret_`)
5. Set `NOTION_API_TOKEN` in your environment file

### MongoDB

**Development:**
1. Install MongoDB locally or use MongoDB Atlas free tier
2. Create a database user with appropriate permissions
3. Set `MONGODB_CONNECTION_STRING` using the format: `mongodb://username:password@localhost:27017/database_name`

**Production:**
1. Create a dedicated MongoDB Atlas cluster with appropriate security settings
2. Enable network security features (IP whitelisting, VPC peering)
3. Create a database user with least privilege permissions
4. Set `MONGODB_CONNECTION_STRING` using the provided connection string

### PostgreSQL

**Development:**
1. Install PostgreSQL locally or use a cloud provider's free tier
2. Create a database user with appropriate permissions
3. Set `POSTGRES_CONNECTION_STRING` using the format: `postgresql://username:password@localhost:5432/database_name`

**Production:**
1. Use a managed PostgreSQL service with high availability
2. Enable encryption for data at rest and in transit
3. Create a database user with least privilege permissions
4. Set `POSTGRES_CONNECTION_STRING` with the secure connection string

### Redis

**Development:**
1. Install Redis locally or use a cloud provider's free tier
2. Set `REDIS_URL` using the format: `redis://localhost:6379/0`

**Production:**
1. Use a managed Redis service with persistence configuration
2. Enable encryption and authentication
3. Set `REDIS_URL` using the secured connection string

### Supabase

1. Create an account at [https://supabase.com](https://supabase.com)
2. Create a new project
3. Navigate to Project Settings → API
4. Copy the URL and API keys
5. Navigate to Account → Access Tokens to create a personal access token
6. Set the following environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY` (use the `anon` key for public operations or `service_role` for admin)
   - `SUPABASE_ACCESS_TOKEN` (your personal access token)

## Payment Processing

### Stripe

1. Create an account at [https://stripe.com](https://stripe.com)
2. Navigate to Developers → API keys
3. For development, use the test keys (starting with `sk_test_`)
4. For production, use the live keys (starting with `sk_live_`)
5. Set `STRIPE_API_KEY` environment variable
6. Follow PCI compliance guidelines for handling payment information

## Source Control & Collaboration

### GitHub

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Create a token with the necessary permissions:
   - For read-only operations: `repo:status`, `repo_deployment`, `public_repo`, `read:org`
   - For write operations: Add `repo` scope
3. Store the token as `GITHUB_PAT`
4. Consider using fine-grained tokens with limited repository access

## Design & Frontend

### Figma

1. Log in to your Figma account
2. Go to Settings → Personal access tokens
3. Create a new personal access token with a descriptive name
4. Set `FIGMA_API_KEY` environment variable

### Softr

1. Log in to your [Softr](https://www.softr.io/) account
2. Go to Settings → API keys
3. Create a new API key with required permissions
4. Copy your App ID from your Softr dashboard
5. Set the following environment variables:
   - `SOFTR_API_KEY`
   - `SOFTR_APP_ID`
   - `SOFTR_API_URL` (typically `https://api.softr.io/v1`)
   - `STAFF_API_KEY` (for staff-specific operations)

## AI & Machine Learning

### Perplexity

1. Sign up for [Perplexity API access](https://www.perplexity.ai/)
2. Generate an API key from your account settings
3. Set `PERPLEXITY_API_KEY` environment variable

### Hugging Face

1. Create an account on [Hugging Face](https://huggingface.co/)
2. Go to Settings → Access Tokens
3. Create a new token with read or write access as needed
4. Set the following environment variables:
   - `HUGGINGFACE_API_KEY`
   - `HUGGINGFACE_API_URL` (typically `https://api-inference.huggingface.co/models/`)

## Security Best Practices

1. **Rotation Policy**: Implement a key rotation schedule for all credentials
   - Development: Every 90 days
   - Production: Every 30-60 days

2. **Access Limitation**: Limit API key permissions to only what is necessary
   - Create read-only keys when possible
   - Scope keys to specific resources
   - Use separate keys for different components

3. **Monitoring**: Set up monitoring for unusual API usage patterns
   - Monitor rate limits and usage metrics
   - Set alerts for anomalous activity

4. **Secrets Management**:
   - Development: Use `.env` files excluded from version control
   - Staging/Testing: Use environment variables in CI/CD systems
   - Production: Use a dedicated secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)

5. **Authentication Flow**:
   - Follow the proper authentication flows for staff-agent interactions through Softr interfaces
   - Implement proper OAuth flows where appropriate

## Workflow-Specific Credentials

### Softr Interface Publishing Workflow
- Required: `SOFTR_API_KEY`, `SOFTR_APP_ID`, `SOFTR_API_URL`
- Ensure staff permissions are properly set with `STAFF_API_KEY`

### Agent Communication Security Workflow
- Required: `NOTION_AGENT_COMMUNICATION_DB`, `NOTION_AGENT_REGISTRY_DB`
- Ensure communication patterns are properly secured

### Gallery Exhibit Management Workflow
- Required: `NOTION_PRODUCTS_SERVICES_DB`, `NOTION_BUSINESS_ENTITIES_DB`
- For integration with e-commerce: `WOOCOMMERCE_CONSUMER_KEY`, `WOOCOMMERCE_CONSUMER_SECRET`

### Wellness Service Booking Workflow
- Required: `NOTION_PRODUCTS_SERVICES_DB`, `NOTION_CONTACTS_PROFILES_DB`
- For appointment integration: `AMELIA_API_KEY`, `AMELIA_ENDPOINT`

### Content Creation and Distribution Workflow
- Required: `BEEHIIV_API_KEY`, `BEEHIIV_PUBLICATION_ID`
- For newsletter automation

## Testing Your Setup

After obtaining all required credentials and setting up your environment variables, run:

```bash
# Load the appropriate environment
python scripts/load_env.py --env development

# Validate that all required variables are set
python scripts/validate_env.py
```

This will verify that your environment is properly configured before starting the server.
