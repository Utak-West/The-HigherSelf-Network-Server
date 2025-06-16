# HigherSelf Network Server - Enterprise Secrets Management Guide

## Overview

The HigherSelf Network Server implements enterprise-grade secrets management with multiple backend support, automatic rotation, and comprehensive audit logging. This guide covers the complete setup, configuration, and operational procedures for managing secrets securely across all deployment environments.

## Architecture

### Multi-Backend Approach

Our secrets management strategy uses a layered approach with multiple backends:

1. **HashiCorp Vault** (Primary) - Enterprise-grade secrets management
2. **AWS Secrets Manager** (Cloud Integration) - For AWS-hosted services
3. **Docker Secrets** (Container Security) - For containerized deployments
4. **Environment Variables** (Development) - For local development only

### Environment-Specific Configuration

- **Development**: Environment variables with Vault fallback
- **Staging**: Vault primary with AWS Secrets Manager fallback
- **Production**: Vault primary with AWS Secrets Manager fallback + Docker Secrets

## Quick Start

### 1. Initial Setup

```bash
# Install required dependencies
pip install hvac boto3 cryptography

# Run the setup script
python scripts/setup_secrets_management.py --environment development

# For production
python scripts/setup_secrets_management.py --environment production --vault-addr https://vault.higherself.network
```

### 2. Environment Configuration

Copy the appropriate template file:

```bash
# Development
cp .env.development.template .env

# Production
cp .env.production.template .env.production
```

### 3. Start Services with Secrets Management

```bash
# Development with basic secrets
docker-compose up -d

# Production with full secrets management
docker-compose -f docker-compose.yml -f deployment/docker-compose.secrets.yml up -d
```

## Detailed Configuration

### HashiCorp Vault Setup

#### 1. Vault Installation and Initialization

```bash
# Start Vault server
docker run -d --name vault \
  -p 8200:8200 \
  -v vault_data:/vault/data \
  -v ./deployment/vault:/vault/config \
  hashicorp/vault:1.15 \
  vault server -config=/vault/config/vault.hcl

# Initialize Vault (first time only)
export VAULT_ADDR=http://localhost:8200
vault operator init -key-shares=5 -key-threshold=3

# Unseal Vault
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>
```

#### 2. Configure Vault Policies

```bash
# Create application policy
vault policy write higherself-app-production - <<EOF
path "higherself-production/data/*" {
  capabilities = ["read"]
}
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

# Create service-specific policies
vault policy write higherself-notion-production - <<EOF
path "higherself-production/data/api_keys/notion" {
  capabilities = ["read"]
}
EOF
```

#### 3. Store Secrets in Vault

```bash
# Enable KV v2 secrets engine
vault secrets enable -path=higherself-production kv-v2

# Store API keys
vault kv put higherself-production/api_keys/notion_api_token value="secret_your_actual_token"
vault kv put higherself-production/api_keys/openai_api_key value="sk-your_actual_key"

# Store database credentials
vault kv put higherself-production/database/mongodb_password value="your_secure_password"
vault kv put higherself-production/database/redis_password value="your_redis_password"

# Store security keys
vault kv put higherself-production/jwt/secret_key value="your_jwt_secret"
vault kv put higherself-production/webhooks/secret value="your_webhook_secret"
```

### AWS Secrets Manager Setup

#### 1. Create Secrets in AWS

```bash
# Create secret for API keys
aws secretsmanager create-secret \
  --name "higherself-network-server-production-api-keys-notion" \
  --description "Notion API token for HigherSelf Network Server" \
  --secret-string '{"value":"secret_your_actual_token"}'

# Create secret for database credentials
aws secretsmanager create-secret \
  --name "higherself-network-server-production-database-mongodb" \
  --description "MongoDB credentials" \
  --secret-string '{"username":"higherself_prod","password":"your_secure_password"}'
```

#### 2. Configure IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:*:secret:higherself-network-server-*"
    }
  ]
}
```

### Docker Secrets Setup

#### 1. Create Docker Secrets

```bash
# Create secrets for production deployment
echo "secret_your_actual_token" | docker secret create higherself-notion-api-token-production -
echo "your_secure_password" | docker secret create higherself-mongodb-password-production -
echo "your_jwt_secret" | docker secret create higherself-jwt-secret-production -
```

#### 2. Use Secrets in Docker Compose

```yaml
services:
  windsurf-agent:
    secrets:
      - higherself-notion-api-token-production
      - higherself-mongodb-password-production
      - higherself-jwt-secret-production
    environment:
      SECRETS_BACKEND: vault
      VAULT_ADDR: http://vault:8200

secrets:
  higherself-notion-api-token-production:
    external: true
  higherself-mongodb-password-production:
    external: true
  higherself-jwt-secret-production:
    external: true
```

## Secret Categories and Organization

### API Keys (`api_keys/`)
- `notion_api_token` - Notion API integration token
- `openai_api_key` - OpenAI API key for LLM operations
- `anthropic_api_key` - Anthropic Claude API key
- `huggingface_api_key` - Hugging Face API key
- `typeform_api_key` - TypeForm API key
- `airtable_api_key` - Airtable API key
- `gohighlevel_client_secret` - GoHighLevel OAuth client secret

### Database Credentials (`database/`)
- `mongodb_password` - MongoDB application user password
- `redis_password` - Redis authentication password
- `supabase_api_key` - Supabase API key

### Security Keys (`jwt/`, `webhooks/`, `encryption/`)
- `jwt/secret_key` - JWT signing secret key
- `webhooks/secret` - Webhook validation secret
- `encryption/key` - Application encryption key

## Secret Rotation

### Automatic Rotation

The system supports automatic rotation for supported secret types:

```python
# Configure rotation in your application
from services.secrets_rotation import create_rotation_service
from services.secrets_manager import get_secrets_manager

# Setup rotation service
secrets_manager = await get_secrets_manager()
rotation_service = await create_rotation_service(secrets_manager)

# Run rotation check (typically via cron job)
await rotation_service.run_rotation_check("production")
```

### Manual Rotation

```bash
# Rotate a specific secret
python -c "
import asyncio
from services.secrets_rotation import create_rotation_service
from services.secrets_manager import get_secrets_manager
from config.secrets_config import get_secrets_config

async def rotate_secret():
    config = get_secrets_config('production')
    secrets_manager = await get_secrets_manager()
    rotation_service = await create_rotation_service(secrets_manager)
    
    # Find the secret definition
    secret_def = next(s for s in config.secrets if s.name == 'jwt_secret_key')
    result = await rotation_service.rotate_secret(secret_def)
    print(f'Rotation result: {result.status}')

asyncio.run(rotate_secret())
"
```

### Rotation Schedule

| Secret Type | Development | Staging | Production |
|-------------|-------------|---------|------------|
| API Keys | 90 days | 60 days | 30 days |
| JWT Keys | Manual | 14 days | 7 days |
| Database | Manual | 90 days | 90 days |
| Webhooks | Manual | 60 days | 30 days |
| Encryption | Manual | 365 days | 365 days |

## Monitoring and Auditing

### Audit Logging

All secret access is logged for compliance:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "SECRET_ACCESS",
  "secret_name": "notion_api_token",
  "category": "api_keys",
  "environment": "production",
  "user": "windsurf-agent",
  "source_ip": "10.0.1.100"
}
```

### Monitoring Metrics

Key metrics to monitor:
- Secret access frequency
- Failed authentication attempts
- Rotation success/failure rates
- Secret age and expiration warnings

### Alerting

Configure alerts for:
- Failed secret rotations
- Secrets approaching expiration
- Unusual access patterns
- Authentication failures

## Security Best Practices

### Access Control
1. **Principle of Least Privilege** - Grant minimal required permissions
2. **Service-Specific Policies** - Create dedicated policies for each service
3. **Regular Access Reviews** - Audit and revoke unnecessary access

### Secret Management
1. **Never Commit Secrets** - Use `.gitignore` for all `.env` files
2. **Strong Secret Generation** - Use cryptographically secure random generation
3. **Regular Rotation** - Implement automated rotation where possible
4. **Secure Transmission** - Always use TLS for secret transmission

### Operational Security
1. **Backup Encryption** - Encrypt all secret backups
2. **Multi-Factor Authentication** - Require MFA for administrative access
3. **Network Segmentation** - Isolate secrets management infrastructure
4. **Incident Response** - Have procedures for secret compromise

## Troubleshooting

### Common Issues

#### Vault Connection Issues
```bash
# Check Vault status
vault status

# Check network connectivity
curl -k $VAULT_ADDR/v1/sys/health

# Verify authentication
vault auth -method=token
```

#### Secret Not Found
```bash
# List available secrets
vault kv list higherself-production/

# Check secret path
vault kv get higherself-production/api_keys/notion_api_token
```

#### Docker Secrets Issues
```bash
# List Docker secrets
docker secret ls

# Inspect secret
docker secret inspect higherself-notion-api-token-production
```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
export SECRETS_DEBUG=true
python main.py
```

## Migration Guide

### From Environment Variables to Vault

1. **Backup Current Configuration**
   ```bash
   cp .env .env.backup
   ```

2. **Store Secrets in Vault**
   ```bash
   # Extract secrets from .env and store in Vault
   python scripts/migrate_env_to_vault.py --environment production
   ```

3. **Update Application Configuration**
   ```bash
   # Update .env to use Vault
   SECRETS_BACKEND=vault
   VAULT_ADDR=https://vault.higherself.network
   ```

4. **Test and Validate**
   ```bash
   # Test secret retrieval
   python -c "
   import asyncio
   from services.secrets_manager import get_secret, SecretCategory
   
   async def test():
       token = await get_secret('notion_api_token', SecretCategory.API_KEYS)
       print('✅ Secret retrieval successful' if token else '❌ Secret retrieval failed')
   
   asyncio.run(test())
   "
   ```

## Support and Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review audit logs
   - Check secret expiration warnings
   - Verify backup integrity

2. **Monthly**
   - Rotate development secrets
   - Review access policies
   - Update documentation

3. **Quarterly**
   - Security assessment
   - Disaster recovery testing
   - Performance optimization

### Getting Help

- **Documentation**: Check this guide and inline code documentation
- **Logs**: Review application and audit logs
- **Monitoring**: Check Grafana dashboards for metrics
- **Support**: Contact the HigherSelf Network development team

---

*This guide is part of the HigherSelf Network Server enterprise automation platform documentation.*
