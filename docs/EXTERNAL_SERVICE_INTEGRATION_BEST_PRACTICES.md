# HigherSelf Network Server - External Service Integration Best Practices

## Overview

This comprehensive guide documents the established best practices for external service integration within the HigherSelf Network Server, based on the successful VirtualBox deployment and enterprise-grade automation platform architecture. These patterns have been proven in production across three business entities: The 7 Space (191 contacts), AM Consulting (1,300 contacts), and HigherSelf Core (1,300 contacts).

## Table of Contents

1. [Configuration Management Best Practices](#configuration-management-best-practices)
2. [Service Integration Architecture](#service-integration-architecture)
3. [Deployment and Infrastructure Patterns](#deployment-and-infrastructure-patterns)
4. [Business Entity Configuration Patterns](#business-entity-configuration-patterns)
5. [Security and Secrets Management](#security-and-secrets-management)
6. [Monitoring and Health Checks](#monitoring-and-health-checks)
7. [Implementation Templates](#implementation-templates)

## Configuration Management Best Practices

### Environment Variable Structure

The system uses a hierarchical environment variable structure that supports multi-tenant configuration:

```bash
# Core Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
MULTI_ENTITY_MODE=true
VM_DEPLOYMENT=true

# Business Entity Database IDs
NOTION_THE7SPACE_CONTACTS_DB=your_the7space_contacts_db_id
NOTION_AMCONSULTING_CONTACTS_DB=your_amconsulting_contacts_db_id
NOTION_HIGHERSELF_CONTACTS_DB=your_higherself_contacts_db_id

# Service-Specific Configuration
NOTION_API_TOKEN=secret_from_aws_secrets_manager
OPENAI_API_KEY=secret_from_aws_secrets_manager
MONGODB_URI=mongodb://higherself_user:${MONGODB_PASSWORD}@mongodb-vm:27017/higherself_production
```

### Secrets Management with AWS Secrets Manager

The system integrates with AWS Secrets Manager through Gruntwork Terragrunt:

```hcl
# terragrunt/modules/secrets-manager/terragrunt.hcl
secrets = {
  notion_api_token = {
    description = "Notion API token for HigherSelf Network Server integration"
    secret_string = get_env("NOTION_API_TOKEN", "")
    recovery_window_in_days = 7
  }
  
  openai_api_key = {
    description = "OpenAI API key for AI services"
    secret_string = get_env("OPENAI_API_KEY", "")
    recovery_window_in_days = 7
  }
  
  webhook_secret = {
    description = "Webhook secret for secure API communications"
    generate_secret_string = {
      password_length = 64
      exclude_characters = "\"@/\\"
    }
    recovery_window_in_days = 7
  }
}
```

### Terragrunt Configuration Patterns

Root-level configuration inheritance:

```hcl
# terragrunt.hcl
inputs = {
  project_name = "higherself-network-server"
  environment  = get_env("ENVIRONMENT", "development")
  aws_region = get_env("AWS_REGION", "us-east-1")
  
  common_tags = {
    Project     = "HigherSelf-Network-Server"
    Environment = get_env("ENVIRONMENT", "development")
    ManagedBy   = "terragrunt"
    Owner       = "HigherSelf-Network"
    Purpose     = "enterprise-automation-platform"
  }
}
```

## Service Integration Architecture

### Notion API Integration Pattern

The Notion service follows a robust pattern with testing mode support:

```python
class NotionService:
    def __init__(self, config: NotionIntegrationConfig):
        self.config = config
        self.client = Client(auth=config.token)
        self.db_mappings = config.database_mappings
        
        # Check if we're in testing mode
        if is_api_disabled("notion"):
            logger.warning("TESTING MODE ACTIVE: Notion API calls will be simulated")
    
    async def create_page(self, model: BaseModel) -> str:
        db_type = model.__class__.__name__
        
        if is_api_disabled("notion"):
            TestingMode.log_attempted_api_call(
                api_name="notion",
                endpoint="pages.create",
                method="POST",
                params={"parent": {"database_id": db_id}, "properties": properties}
            )
            return f"test_page_id_{db_type}_{model.id}"
        
        # Actual API call
        response = self.client.pages.create(...)
        return response["id"]
```

### OpenAI API Integration Pattern

Structured API request handling with proper error management:

```python
async def _process_openai_request(self, request: AIRequest) -> Optional[AIResponse]:
    provider_credentials = self.providers["openai"]
    
    headers = {
        "Authorization": f"Bearer {provider_credentials.api_key}",
        "Content-Type": "application/json",
    }
    
    if provider_credentials.organization_id:
        headers["OpenAI-Organization"] = provider_credentials.organization_id
    
    api_request = {
        "model": request.model,
        "messages": [m.dict() for m in request.messages],
    }
    
    # Add optional parameters
    if request.max_tokens is not None:
        api_request["max_tokens"] = request.max_tokens
    
    try:
        response = await self.async_post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=api_request
        )
        return self._parse_openai_response(response)
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None
```

### Email Service Configuration

SMTP integration with environment-specific settings:

```bash
# Email integration
ENABLE_EMAIL_AUTOMATION=true
EMAIL_PROVIDER=smtp
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_USE_TLS=true
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
```

## Deployment and Infrastructure Patterns

### VirtualBox VM Deployment Configuration

Multi-entity production deployment with resource allocation:

```yaml
# docker-compose.vm.yml
services:
  higherself-server:
    image: thehigherselfnetworkserver:vm-production
    container_name: higherself-server-vm
    ports:
      - "80:8000"
      - "443:8443"
    environment:
      - MULTI_ENTITY_MODE=true
      - VM_DEPLOYMENT=true
      - ENVIRONMENT=production
    labels:
      - "business.entities=the_7_space,am_consulting,higherself_core"
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 30s
      retries: 5
      start_period: 90s
```

### Service Health Check Patterns

Comprehensive health monitoring across all services:

```bash
# Health check verification script
verify_container_status() {
    local containers=(
        "higherself-server-vm"
        "higherself-mongodb-vm"
        "higherself-redis-vm"
        "higherself-consul-vm"
        "higherself-prometheus-vm"
        "higherself-grafana-vm"
    )
    
    for container in "${containers[@]}"; do
        if docker inspect "$container" --format='{{.State.Health.Status}}' | grep -q "healthy"; then
            echo "✅ $container is healthy"
        else
            echo "❌ $container health check failed"
        fi
    done
}
```

### Monitoring Configuration

Business entity-specific monitoring with Prometheus:

```yaml
# deployment/prometheus/vm/prometheus.yml
scrape_configs:
  - job_name: 'the-7-space-metrics'
    static_configs:
      - targets: ['higherself-server-vm:8000']
    metrics_path: '/metrics/the-7-space'
    params:
      entity: ['the_7_space']
  
  - job_name: 'am-consulting-metrics'
    static_configs:
      - targets: ['higherself-server-vm:8000']
    metrics_path: '/metrics/am-consulting'
    params:
      entity: ['am_consulting']
```

## Business Entity Configuration Patterns

### Multi-Tenant Database Mapping

Entity-specific database configuration:

```python
# config/notion_databases.py
NOTION_DATABASE_MAPPING = {
    "BusinessEntity": {
        "env_var": "NOTION_BUSINESS_ENTITIES_DB",
        "description": "Business Entities Registry",
        "required": True,
    },
    "ContactProfile": {
        "env_var": "NOTION_CONTACTS_PROFILES_DB", 
        "description": "Contacts & Profiles Database",
        "required": True,
    },
    "WorkflowInstance": {
        "env_var": "NOTION_ACTIVE_WORKFLOW_INSTANCES_DB",
        "description": "Active Workflow Instances Database", 
        "required": True,
    }
}
```

### Contact Classification and Workflow Automation

Business entity-specific workflow patterns:

```python
# config/business_entity_workflows.py
class BusinessEntityWorkflows:
    def _initialize_entity_configs(self):
        return {
            "the_7_space": BusinessEntityWorkflowConfig(
                entity_name="The 7 Space",
                primary_contact_types=[ContactType.ARTIST, ContactType.GALLERY_CONTACT],
                preferred_channels=[EngagementChannel.EMAIL, EngagementChannel.IN_PERSON],
                response_time_hours=24,
                follow_up_sequence_days=[1, 3, 7, 14, 30],
                success_metrics=["exhibition_bookings", "artist_registrations"]
            ),
            "am_consulting": BusinessEntityWorkflowConfig(
                entity_name="AM Consulting", 
                primary_contact_types=[ContactType.BUSINESS_CONTACT],
                preferred_channels=[EngagementChannel.EMAIL, EngagementChannel.PHONE],
                response_time_hours=4,
                follow_up_sequence_days=[1, 2, 5, 10, 21],
                success_metrics=["consultation_bookings", "client_conversions"]
            )
        }
```

### Priority-Based Deployment Configuration

Business priority order: AM Consulting > The 7 Space > HigherSelf Core

```bash
# Deployment priority configuration
BUSINESS_PRIORITY_ORDER="am_consulting,the_7_space,higherself_core"
AM_CONSULTING_CONTACTS=1300
THE_7_SPACE_CONTACTS=191  
HIGHERSELF_CORE_CONTACTS=1300
```

## Security and Secrets Management

### Vault Integration Pattern

Multi-backend secrets management with fallback:

```python
class SecretsManagerConfig(BaseModel):
    environment: str = Field(default="development")
    primary_backend: SecretBackend = Field(default=SecretBackend.VAULT)
    fallback_backend: SecretBackend = Field(default=SecretBackend.ENV_FILE)
    
    # AWS configuration
    aws_region: str = Field(default="us-east-1")
    aws_secret_name_prefix: str = Field(default="higherself-network-server")
    
    # Encryption configuration
    enable_encryption_at_rest: bool = Field(default=True)
```

### Secret Upload Automation

Automated secret management across multiple backends:

```python
def upload_to_vault(self, secret_def: SecretDefinition, secret_value: str) -> bool:
    try:
        secret_path = f"{secret_def.category.value}/{secret_def.name}"
        
        self.vault_client.secrets.kv.v2.create_or_update_secret(
            path=secret_path,
            secret={"value": secret_value}
        )
        
        print(f"✅ Uploaded to Vault: {secret_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to upload to Vault: {e}")
        return False
```

## Implementation Templates

### New Service Integration Template

1. **Environment Configuration**
```bash
# Add to .env.vm.production.template
NEW_SERVICE_ENABLED=true
NEW_SERVICE_API_KEY=your_api_key_here
NEW_SERVICE_ENDPOINT=https://api.newservice.com
```

2. **Secrets Manager Configuration**
```hcl
# Add to terragrunt/modules/secrets-manager/terragrunt.hcl
new_service_api_key = {
  description = "API key for New Service integration"
  secret_string = get_env("NEW_SERVICE_API_KEY", "")
  recovery_window_in_days = 7
}
```

3. **Service Implementation**
```python
class NewServiceIntegration:
    def __init__(self, config: NewServiceConfig):
        self.config = config
        self.client = NewServiceClient(api_key=config.api_key)
        
        if is_api_disabled("new_service"):
            logger.warning("TESTING MODE: New Service API calls will be simulated")
    
    async def process_request(self, request: NewServiceRequest):
        if is_api_disabled("new_service"):
            TestingMode.log_attempted_api_call(
                api_name="new_service",
                endpoint=request.endpoint,
                method="POST"
            )
            return MockResponse()
        
        return await self.client.post(request.endpoint, data=request.data)
```

4. **Health Check Integration**
```python
# Add to health check endpoint
async def check_new_service_health():
    try:
        response = await new_service_client.health_check()
        return {"status": "healthy", "service": "new_service"}
    except Exception as e:
        return {"status": "unhealthy", "service": "new_service", "error": str(e)}
```

This guide provides the foundation for implementing new external service integrations following the established patterns and best practices proven in the HigherSelf Network Server production environment.

## Advanced Integration Patterns

### Webhook Integration Pattern

Secure webhook handling with validation and business entity routing:

```python
# api/contact_workflow_webhooks.py
@router.post("/webhook/{entity_name}")
async def handle_entity_webhook(
    entity_name: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    # Validate webhook signature
    signature = request.headers.get("X-Webhook-Signature")
    if not validate_webhook_signature(signature, await request.body()):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Route to appropriate business entity handler
    entity_config = get_entity_config(entity_name)
    if not entity_config:
        raise HTTPException(status_code=404, detail="Entity not found")

    # Process webhook in background
    background_tasks.add_task(
        process_entity_webhook,
        entity_name,
        await request.json(),
        entity_config
    )

    return {"status": "accepted", "entity": entity_name}
```

### Rate Limiting and Circuit Breaker Pattern

Robust external API interaction with failure handling:

```python
import asyncio
from circuitbreaker import circuit

class ExternalServiceClient:
    def __init__(self, config):
        self.config = config
        self.rate_limiter = AsyncRateLimiter(
            max_calls=config.rate_limit,
            time_window=60
        )

    @circuit(failure_threshold=5, recovery_timeout=30)
    async def make_api_call(self, endpoint: str, data: dict):
        async with self.rate_limiter:
            try:
                response = await self.session.post(
                    f"{self.config.base_url}/{endpoint}",
                    json=data,
                    timeout=self.config.timeout
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"API call failed: {e}")
                raise
```

### Database Transaction Pattern

Ensuring data consistency across multiple services:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def multi_service_transaction():
    """Context manager for coordinating transactions across services."""
    transaction_id = str(uuid.uuid4())
    services_to_rollback = []

    try:
        # Begin transactions
        mongo_session = await mongodb_client.start_session()
        mongo_session.start_transaction()
        services_to_rollback.append(("mongodb", mongo_session))

        # Track external service operations
        external_operations = []

        yield {
            "transaction_id": transaction_id,
            "mongo_session": mongo_session,
            "external_operations": external_operations
        }

        # Commit all transactions
        await mongo_session.commit_transaction()

    except Exception as e:
        logger.error(f"Transaction {transaction_id} failed: {e}")

        # Rollback in reverse order
        for service_name, session in reversed(services_to_rollback):
            try:
                if service_name == "mongodb":
                    await session.abort_transaction()
            except Exception as rollback_error:
                logger.error(f"Rollback failed for {service_name}: {rollback_error}")

        raise
    finally:
        # Cleanup
        for service_name, session in services_to_rollback:
            if service_name == "mongodb":
                await session.end_session()
```

## Deployment Automation Best Practices

### Infrastructure as Code Templates

Complete Terragrunt module structure for new services:

```hcl
# terragrunt/modules/new-service/main.tf
resource "aws_secretsmanager_secret" "new_service_credentials" {
  name = "${var.project_name}-new-service-credentials-${var.environment}"
  description = "Credentials for New Service integration"

  tags = var.common_tags
}

resource "aws_secretsmanager_secret_version" "new_service_credentials" {
  secret_id = aws_secretsmanager_secret.new_service_credentials.id
  secret_string = jsonencode({
    api_key = var.new_service_api_key
    webhook_secret = var.new_service_webhook_secret
  })
}

# terragrunt/modules/new-service/terragrunt.hcl
terraform {
  source = "."
}

include "root" {
  path = find_in_parent_folders()
}

inputs = {
  new_service_api_key = get_env("NEW_SERVICE_API_KEY", "")
  new_service_webhook_secret = get_env("NEW_SERVICE_WEBHOOK_SECRET", "")
}
```

### Automated Testing Integration

Service integration testing with mock backends:

```python
# tests/integration/test_new_service.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def mock_new_service():
    with patch('services.new_service.NewServiceClient') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.mark.asyncio
async def test_new_service_integration(mock_new_service):
    # Setup
    mock_new_service.post.return_value = {"status": "success", "id": "test-123"}

    # Test
    service = NewServiceIntegration(config=test_config)
    result = await service.process_request(test_request)

    # Verify
    assert result["status"] == "success"
    mock_new_service.post.assert_called_once()
```

### Continuous Deployment Pipeline

GitHub Actions workflow for automated deployment:

```yaml
# .github/workflows/deploy-integration.yml
name: Deploy Service Integration

on:
  push:
    paths:
      - 'services/**'
      - 'terragrunt/modules/**'
    branches: [main]

jobs:
  test-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Integration Tests
        run: |
          python -m pytest tests/integration/ -v

  deploy-infrastructure:
    needs: test-integration
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Terragrunt
        run: |
          curl -Lo terragrunt https://github.com/gruntwork-io/terragrunt/releases/download/v0.45.0/terragrunt_linux_amd64
          chmod +x terragrunt
          sudo mv terragrunt /usr/local/bin/
      - name: Deploy Infrastructure
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        run: |
          ./terragrunt-deploy.sh production apply new-service
```

## Troubleshooting and Maintenance

### Common Integration Issues and Solutions

1. **API Rate Limiting**
```python
# Implement exponential backoff
async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
```

2. **Database Connection Issues**
```python
# Connection pool management
async def ensure_db_connection():
    if not mongodb_client.is_connected():
        await mongodb_client.reconnect()
        logger.info("Database connection restored")
```

3. **Secret Rotation Handling**
```python
# Automatic secret refresh
async def refresh_secrets_if_needed():
    if datetime.now() - last_secret_refresh > timedelta(hours=1):
        await secrets_manager.refresh_all_secrets()
        last_secret_refresh = datetime.now()
```

### Monitoring and Alerting Setup

Comprehensive monitoring configuration:

```python
# monitoring/service_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Service-specific metrics
service_requests_total = Counter(
    'service_requests_total',
    'Total service requests',
    ['service_name', 'method', 'status']
)

service_request_duration = Histogram(
    'service_request_duration_seconds',
    'Service request duration',
    ['service_name', 'method']
)

service_health_status = Gauge(
    'service_health_status',
    'Service health status (1=healthy, 0=unhealthy)',
    ['service_name']
)

# Usage in service
async def track_service_call(service_name: str, method: str):
    start_time = time.time()
    try:
        result = await make_service_call()
        service_requests_total.labels(
            service_name=service_name,
            method=method,
            status='success'
        ).inc()
        return result
    except Exception as e:
        service_requests_total.labels(
            service_name=service_name,
            method=method,
            status='error'
        ).inc()
        raise
    finally:
        duration = time.time() - start_time
        service_request_duration.labels(
            service_name=service_name,
            method=method
        ).observe(duration)
```

This comprehensive guide establishes the proven patterns and practices for robust external service integration within the HigherSelf Network Server enterprise automation platform.
