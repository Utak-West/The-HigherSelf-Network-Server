# The HigherSelf Network Server Training Manual

## Introduction

Welcome to The HigherSelf Network Server training manual. This document provides comprehensive guidance for both technical staff and other stakeholders who will interact with our integration platform. 

**Core Principle**: Notion serves as the central data and workflow management hub for all operations within The HigherSelf Network, including The Connection Practice and The 7 Space. All integrations and automations are designed around this principle.

## Table of Contents

1. [System Overview](#system-overview)
2. [For Technical Staff](#for-technical-staff)
   - [Architecture](#architecture)
   - [Integration Services](#integration-services)
   - [Development Workflow](#development-workflow)
   - [Deployment Process](#deployment-process)
   - [Troubleshooting](#troubleshooting)
3. [For Non-Technical Staff](#for-non-technical-staff)
   - [Understanding Data Flow](#understanding-data-flow)
   - [Working with Notion](#working-with-notion)
   - [Service Integrations](#service-integrations)
   - [Common Scenarios](#common-scenarios)
4. [Reference](#reference)
   - [Glossary](#glossary)
   - [API Reference](#api-reference)
   - [Environment Variables](#environment-variables)

---

## System Overview

The HigherSelf Network Server is an integration platform that connects various third-party services with Notion as the central hub. This architecture ensures all data and workflows remain synchronized and centrally managed, regardless of where interactions originate.

Key components include:

- **API Server**: Handles incoming requests and routes them to appropriate services
- **Integration Manager**: Coordinates data flow between services and Notion
- **Service Integrations**: Connect to external platforms like TypeForm, WooCommerce, Acuity, etc.
- **Notion Service**: Ensures all data is properly synchronized with Notion databases

![Architecture Overview](../architecture/architecture-overview.png)

---

## For Technical Staff

### Architecture

The HigherSelf Network Server follows a modular, service-oriented architecture built on these principles:

1. **Notion-Centric Design**: All data ultimately flows to/from Notion
2. **Service Abstraction**: Standardized interfaces for all third-party integrations
3. **Asynchronous Processing**: Non-blocking I/O operations for better performance
4. **Robust Error Handling**: Comprehensive logging and recovery mechanisms

#### Base Service Pattern

All service integrations inherit from the `BaseService` class, which provides:

```python
class BaseService:
    """Base class for all service integrations."""
    
    async def validate_connection(self) -> bool:
        """Verify connection to the service API."""
        
    async def async_get/post/put/patch/delete():
        """Standardized HTTP methods with error handling."""
        
    def validate_model(self, model: BaseModel) -> None:
        """Validate Pydantic models."""
```

#### Data Flow Pattern

```
Third-Party Service → Service Integration → Integration Manager → Notion Service → Notion
```

And in the reverse direction:

```
Notion → Notion Service → Integration Manager → Service Integration → Third-Party Service
```

### Integration Services

#### Adding a New Service

To integrate a new third-party service:

1. Create a new file in the `services/` directory named `[service_name]_service.py`
2. Create credential and data models using Pydantic:

```python
class NewServiceCredentials(ServiceCredentials):
    """Credentials for the new service."""
    api_key: str
    
    class Config:
        env_prefix = "NEW_SERVICE_"

class NewServiceData(BaseModel):
    """Data model for the new service."""
    id: Optional[str] = None
    name: str
    # Other fields...
    notion_page_id: Optional[str] = None
```

3. Implement the service class:

```python
class NewService(BaseService):
    """Integration with the new service."""
    
    def __init__(self, api_key: str = None):
        """Initialize with environment variables if not provided."""
        api_key = api_key or os.environ.get("NEW_SERVICE_API_KEY")
        credentials = NewServiceCredentials(
            service_name="new_service",
            api_key=api_key
        )
        super().__init__(service_name="new_service", credentials=credentials)
    
    async def validate_connection(self) -> bool:
        """Validate connection to the service API."""
        # Implementation...
    
    async def create_item(self, item: NewServiceData) -> Optional[str]:
        """Create a new item in the service."""
        # Implementation...
        
        # Always update with Notion reference if available
        if item.notion_page_id:
            # Add metadata about Notion management
            item.meta_data["notion_managed"] = True
            item.meta_data["notion_sync_time"] = datetime.now().isoformat()
```

4. Register in the Integration Manager:

```python
# In integration_manager.py
if self.config.enable_new_service:
    new_service = NewService()
    new_initialized = await new_service.validate_connection()
    self.services["new_service"] = new_service
    self.initialization_status["new_service"] = new_initialized
```

#### Required Methods

Each service integration should implement:

- `validate_connection()`: Verify API credentials
- Service-specific methods for CRUD operations
- `sync_from_notion()`: Update service from Notion data
- `update_notion_reference()`: Update service item with Notion reference

### Development Workflow

#### Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
   cd The-HigherSelf-Network-Server
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with required credentials (see `.env.example`)

5. Run the server:
   ```bash
   python main.py
   ```

#### Code Quality Standards

- **Type Hints**: Always use proper Python type annotations
- **Docstrings**: Document all classes and methods
- **Error Handling**: Use try/except blocks for external API calls
- **Logging**: Use the loguru logger for all operations
- **Tests**: Write unit tests for all service methods

#### Pull Request Process

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/new-service-integration
   ```

2. Implement changes following coding standards

3. Test your implementation:
   ```bash
   pytest tests/
   ```

4. Push changes and create PR:
   ```bash
   git push -u origin feature/new-service-integration
   ```

5. PR must pass automated checks and code review

### Deployment Process

Deployment uses Docker and GitHub Actions for automation.

#### Environment Configuration

Ensure all required environment variables are configured:

1. **Notion credentials**:
   - `NOTION_API_TOKEN`
   - `NOTION_DATABASE_IDS` for each integrated database

2. **Service-specific credentials**:
   - API keys
   - Webhook secrets
   - Base URLs

#### Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t higherself-network-server .
   ```

2. Run with environment variables:
   ```bash
   docker run -d \
     --name higherself-server \
     --env-file .env \
     -p 8000:8000 \
     higherself-network-server
   ```

#### Automated Deployment

The GitHub Actions workflow in `.github/workflows/docker-build-deploy.yml` handles:

1. Building and testing the application
2. Security scanning
3. Deploying to the production VM
4. Updating Notion with deployment status

### Troubleshooting

#### Common Issues and Solutions

1. **Connection Failures**:
   - Check API credentials in environment variables
   - Verify network connectivity to third-party services
   - Inspect logs for specific error messages

2. **Data Synchronization Issues**:
   - Check Notion database IDs in configuration
   - Verify Notion API token permissions
   - Look for validation errors in service data models

3. **Webhook Processing Errors**:
   - Verify webhook signatures
   - Check endpoint configuration in third-party services
   - Ensure proper error handling in webhook handlers

#### Logging

All operations are logged using the Loguru library:

```python
# In any service file
from loguru import logger

logger.info("Operation completed successfully")
logger.error(f"Error occurred: {e}")
```

Logs are stored in the `logs/` directory and also sent to Notion when configured.

#### Health Checks

Endpoint: `/health`
Returns: Service status information including:
- Notion connection status
- All integrated services status
- Last sync timestamps

---

## For Non-Technical Staff

### Understanding Data Flow

The HigherSelf Network Server ensures all your business tools work together with Notion as the central hub. Here's how information flows:

1. **Data Entry**: Information enters the system through various channels:
   - Form submissions (TypeForm)
   - Orders (WooCommerce)
   - Appointments (Acuity, Amelia)
   - User feedback
   - AI interactions

2. **Central Storage**: All information is stored in Notion databases:
   - Client information
   - Orders and transactions
   - Appointments and bookings
   - Feedback and interactions
   - Workflow status

3. **Synchronization**: Changes in one system automatically update others:
   - Notion → All integrated services
   - Integrated services → Notion

### Working with Notion

#### Key Databases

1. **Clients Database**: Central repository of all client information
2. **Products Database**: Products/services from WooCommerce
3. **Orders Database**: Purchase history from WooCommerce
4. **Appointments Database**: Bookings from Acuity/Amelia
5. **Feedback Database**: User feedback collection
6. **Active Workflow Instances**: Tracks processes across all services

#### Best Practices

1. **Always Use Notion for Updates**:
   - Make changes in Notion when possible
   - These changes will synchronize to other platforms

2. **Understand Notion-Managed Properties**:
   - Look for "Notion Managed" property in records
   - Check "Last Sync" timestamps for freshness

3. **Database Relationships**:
   - Clients link to Orders, Appointments, etc.
   - Follow relations to see complete client history

### Service Integrations

#### TypeForm Integration

The TypeForm integration automatically:
- Collects form submissions
- Creates new entries in appropriate Notion databases
- Updates existing records when relevant
- Notifies staff of important submissions

**Usage**: Configure form endpoints in TypeForm admin panel

#### WooCommerce Integration

The WooCommerce integration:
- Syncs products between Notion and your online store
- Processes orders and updates inventory
- Maintains customer purchase history
- Triggers fulfillment workflows

**Usage**: Products managed in Notion will update in WooCommerce

#### Acuity/Amelia Integration

These scheduling integrations:
- Sync availability with Notion calendars
- Process appointment bookings
- Update client records with appointment history
- Manage notifications and reminders

**Usage**: View and manage all appointments in Notion

#### User Feedback Integration

This integration:
- Collects feedback from multiple channels
- Organizes by sentiment and category
- Links feedback to relevant clients/products
- Facilitates response tracking

**Usage**: Review feedback in the Notion Feedback database

#### AI Provider Integration

This integration:
- Routes AI interactions to appropriate providers
- Stores conversation history in Notion
- Allows for review and training improvements
- Maintains consistent knowledge across platforms

**Usage**: View AI interactions in the dedicated Notion database

### Common Scenarios

#### New Client Registration

1. Client completes TypeForm registration
2. System automatically:
   - Creates Notion client record
   - Sends welcome email
   - Establishes WooCommerce account
   - Initiates onboarding workflow

#### Appointment Booking

1. Client books through Acuity/Amelia
2. System automatically:
   - Updates Notion appointment database
   - Links to client record
   - Notifies relevant staff
   - Creates follow-up tasks

#### Order Processing

1. Client purchases through WooCommerce
2. System automatically:
   - Updates Notion orders database
   - Links to client record
   - Initiates fulfillment workflow
   - Schedules follow-up communications

#### Feedback Collection

1. Client submits feedback
2. System automatically:
   - Updates Notion feedback database
   - Links to relevant records
   - Analyzes sentiment
   - Creates follow-up tasks if needed

---

## Reference

### Glossary

- **API**: Application Programming Interface - allows systems to communicate
- **Integration**: Connection between different software systems
- **Webhook**: Automated message sent when something happens
- **Sync/Synchronization**: Keeping data consistent across platforms
- **Workflow**: Series of steps to complete a process
- **Database**: Structured collection of information
- **Record**: Single entry in a database (e.g., one client)
- **Property**: Field or attribute in a database record
- **Relation**: Connection between records in different databases

### API Reference

The HigherSelf Network Server exposes these API endpoints:

- `/api/webhooks/{service_name}`: Receive webhook events
- `/api/services/{service_name}/{action}`: Perform service actions
- `/api/notion/sync`: Manually trigger Notion synchronization
- `/api/health`: Check system health status

### Environment Variables

Key environment variables include:

- `NOTION_API_TOKEN`: Authentication for Notion API
- `NOTION_*_DATABASE_ID`: IDs for each Notion database
- `SERVICE_API_KEY`: Authentication for each service (replace SERVICE with service name)
- `ENABLE_SERVICE`: Toggle for each integration (true/false)

For complete reference, see `.env.example` in the repository.

---

## Support and Resources

For technical assistance, please contact:
- Technical Support: [support@thehigherself.network](mailto:support@thehigherself.network)

Additional resources:
- [GitHub Repository](https://github.com/Utak-West/The-HigherSelf-Network-Server)
- [API Documentation](https://api.thehigherself.network/docs)
- [Notion API Documentation](https://developers.notion.com/)
- [Service Integration Guides](https://thehigherself.network/guides)

---

**Remember**: Notion serves as the central hub for all data and workflows in The HigherSelf Network ecosystem. All integrations are designed to support this core principle.

---

*Updated: May 2025*