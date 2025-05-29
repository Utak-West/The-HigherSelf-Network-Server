# The HigherSelf Network Server

## Intelligent Automation for Art Gallery, Wellness Center & Consultancy Operations

## Overview

Welcome to **The HigherSelf Network Server** - an intelligent automation platform designed specifically for art galleries, wellness centers, and consultancy businesses. Our system creates harmony between your business operations through a unique agent-based architecture with Notion as the central hub.

### What Makes Us Special

The HigherSelf Network Server features a team of **named agent personalities**, each with distinct characteristics and responsibilities. These agents work together seamlessly to automate your workflows while maintaining the human touch that makes your business special.

### Notion as Your Central Hub

All data, workflows, and communications flow through Notion, creating a unified system that's both powerful and user-friendly. Your team already knows and loves Notion - now it becomes the command center for your entire operation.

## Core Features

### Notion-Powered Operations

* **Centralized Database Hub**: 16 interconnected Notion databases
* **Real-time Synchronization**: All systems stay in perfect harmony
* **Visual Workflow Tracking**: See exactly where every process stands
* **Customizable Views**: Adapt Notion views to your team's needs

### Intelligent Agent System

* **Named Agent Personalities**: Each with unique characteristics
* **Specialized Capabilities**: Experts in their respective domains
* **Autonomous Decision Making**: Agents handle routine tasks independently
* **Graceful Orchestration**: Coordinated by the Grace Fields Master Orchestrator

### Seamless Integrations

* **Comprehensive API Support**: Connect with all your essential tools
* **Webhook Endpoints**: Receive real-time data from external systems
* **Bidirectional Sync**: Data flows both ways between systems
* **Secure Authentication**: All connections use modern security standards
* **Softr Integration**: Staff interfaces with agents through Softr

### Robust Architecture

* **Pydantic Data Validation**: Ensures data integrity throughout
* **State Machine Workflows**: Structured processes with clear stages
* **Comprehensive Logging**: Complete audit trail of all activities
* **Extensible Design**: Easily add new capabilities as you grow

### Retrieval Augmented Generation (RAG)

* **Knowledge Retrieval**: Access relevant information from various sources
* **Web Crawling**: Automatically extract content from websites using Crawl4AI
* **Vector Embeddings**: Convert content into semantic vector representations
* **Contextual Generation**: Generate responses enhanced with retrieved context
* **Atlas Integration**: Dedicated RAG agent (Atlas) for knowledge management
* **Cross-Agent Knowledge Sharing**: All agents can request contextual information from Atlas

### Flexible Embedding Providers

* **Multiple Providers**: Support for OpenAI, Anthropic, and local embeddings
* **Automatic Fallback**: Gracefully degrade to available providers
* **Local Processing**: Process sensitive data locally with sentence-transformers
* **Mock Providers**: Test without external API keys

### Recent Integrations (Production Ready)

#### Hugging Face Pro Integration

* **Specialized NLP Tasks**: Access to state-of-the-art models for summarization, translation, and more
* **Notion Integration**: Process text from Notion pages with Hugging Face models
* **Webhook Support**: Trigger Hugging Face processing from external systems
* **Task-Specific Models**: Curated model recommendations for different NLP tasks
* **Intelligent Model Selection**: Automatic selection of the best model based on task and agent capabilities
* **Agent Mixin**: Easy integration of Hugging Face capabilities into any agent
* **Performance Optimization**: Balance between speed and quality based on task requirements
* **Status**: ✅ Production Ready - Full implementation with Notion sync

#### MCP Tools Integration

* **Model Context Protocol**: Access to standardized AI tool interfaces
* **Multi-Provider OCR**: Tesseract, Google Vision, and ABBYY OCR services
* **Web Browser Tools**: Automated web interaction capabilities
* **Memory Tools**: Persistent memory management for agents
* **Perplexity Integration**: Enhanced search and research capabilities
* **Status**: ✅ Production Ready - Core tools implemented and tested

#### The7Space Integration

* **WordPress Integration**: Content management and publishing
* **Elementor Pro Support**: Advanced page building capabilities
* **Amelia Booking System**: Appointment and service booking management
* **Softr Interface**: Staff interaction with agents through web interface
* **Status**: ✅ Production Ready - Full API integration with authentication

#### CapCut-Pipit Integration

* **Video Export Processing**: Direct export from CapCut to HigherSelf Network
* **Payment Processing**: Premium video feature payments through Pipit
* **Metadata Management**: Video information storage in Notion
* **Webhook Support**: Real-time status updates from both platforms
* **Status**: ✅ Production Ready - Complete video and payment workflow

#### Newark Initiative Integration

* **Specialized Wellness Agents**: Five dedicated agents for Newark wellness programs
* **Crisis Intervention Support**: Coordinated response capabilities
* **Homelessness Outreach**: Targeted program management
* **Community Health Tracking**: Comprehensive wellness monitoring
* **Status**: ✅ Production Ready - Specialized agent deployment ready

### Legacy Integrations (Stable)

#### Softr Integration

* **Staff Agent Interface**: Allow staff to interact with agents through Softr
* **Secure Authentication**: Staff authentication and authorization
* **Interaction History**: Track and manage staff-agent interactions
* **Webhook Support**: Process events from Softr in real-time
* **Status**: ✅ Stable - Ongoing maintenance mode

## Database Structure

The HigherSelf Network Server uses a carefully designed system of 16 interconnected Notion databases that work together to create a powerful, flexible automation platform.

### Database Organization

#### Core Operational Databases

* **Business Entities**: Registry of all business entities using the system (art gallery, wellness center, consultancy)
  * **Key Properties:** Name, Type, Contact Info, Logo
  * **Relations:** Products, Workflows, Team Members
* **Contacts & Profiles**: Unified customer/contact database for all entities and interactions
  * **Key Properties:** Name, Email, Phone, Tags
  * **Relations:** Bookings, Orders, Feedback
* **Community Hub**: Community member profiles and engagement tracking
  * **Key Properties:** Member Since, Engagement Level
  * **Relations:** Events, Content, Discussions
* **Products & Services**: Catalog of all available products and services across businesses
  * **Key Properties:** Name, Type, Price, Availability
  * **Relations:** Business Entity, Orders, Content
* **Active Workflows**: Currently active workflow instances being processed
  * **Key Properties:** Status, Stage, Start Date
  * **Relations:** Tasks, Contacts, Template
* **Marketing Campaigns**: Marketing initiatives and performance tracking
  * **Key Properties:** Name, Channel, Status, Metrics
  * **Relations:** Audience Segments, Content
* **Feedback & Surveys**: Customer feedback and survey responses
  * **Key Properties:** Type, Rating, Date, Source
  * **Relations:** Contact, Product/Service
* **Rewards & Bounties**: Incentive programs and achievements
  * **Key Properties:** Type, Value, Criteria
  * **Relations:** Contacts, Campaigns
* **Master Tasks**: Centralized task management system
  * **Key Properties:** Title, Status, Due Date, Priority
  * **Relations:** Assignee, Workflow, Business Entity

#### Agent & System Support Databases

* **Agent Communication**: Record of all agent interactions and messages
  * **Key Properties:** Sender, Recipient, Message Type
  * **Relations:** Workflows, Tasks
* **Agent Registry**: Inventory of all available agents and their capabilities
  * **Key Properties:** Name, Type, Status, Version
  * **Relations:** APIs Used, Business Entities
* **API Integrations**: Catalog of all integrated external services
  * **Key Properties:** Service Name, Status, Last Sync
  * **Relations:** Agents, Workflows
* **Data Transformations**: Data mapping configurations between systems
  * **Key Properties:** Source, Target, Mapping Rules
  * **Relations:** API Integrations
* **Notification Templates**: Templates for system and user notifications
  * **Key Properties:** Type, Channel, Subject, Body
  * **Relations:** Workflows, Triggers
* **Use Cases Library**: Documented use cases for reference
  * **Key Properties:** Title, Category, Steps
  * **Relations:** Workflows, Business Entities
* **Workflows Library**: Template workflows that can be instantiated
  * **Key Properties:** Name, Type, Stages, Triggers
  * **Relations:** Tasks, Agents, Business Entities

## Key Automation Flows

The HigherSelf Network Server implements powerful automation flows that streamline operations across your businesses. Each flow is handled by specialized agents working together through Notion.

## Business Workflows

### Customer Acquisition

### Lead Capture & Nurturing

* **Handled by Nyra & Ruvo**
* Consolidates leads from multiple sources (Typeform, website forms, social media) and nurtures them through personalized follow-up sequences.
* **Key Features:**
  * Automatic lead qualification and scoring
  * Personalized follow-up task creation
  * Interest-based tagging and segmentation
  * Conversion tracking across touchpoints

### Booking & Order Management

* **Handled by Solari & Ruvo**
* Manages the complete lifecycle of bookings (retreats, consultations) and orders (art pieces, products) from initial purchase through fulfillment.
* **Key Features:**
  * Automated confirmation and reminder emails
  * Preparation task creation for team members
  * Payment tracking and receipt generation
  * Post-experience follow-up sequences

### Marketing Campaign Orchestration

* **Handled by Liora, Elan & Zevi**
* Coordinates multi-channel marketing campaigns across email, social media, and other platforms with targeted messaging for different audience segments.
* **Key Features:**
  * Audience segmentation and targeting
  * Content scheduling and distribution
  * Performance tracking and analytics
  * A/B testing and optimization

### Community Engagement

* **Handled by Sage & Elan**
* Nurtures community relationships through Circle.so, facilitating discussions, events, and content sharing to build a vibrant, engaged community.
* **Key Features:**
  * New member welcome sequences
  * Engagement tracking and nurturing
  * Content curation and sharing
  * Event coordination and follow-up

### Content Lifecycle Management

* **Handled by Elan & Liora**
* Manages the complete content creation process from ideation through creation, review, publication, and performance analysis.
* **Key Features:**
  * Content calendar management
  * Review and approval workflows
  * Multi-platform distribution
  * Performance tracking and insights

## Meet Your Agent Team

The HigherSelf Network features a unique team of digital agents, each with their own personality and specialized skills. These aren't just algorithms - they're digital team members designed to bring intention and care to your automated processes.

### Agent Personalities

| Agent            | Role                           | Personality                 | Key Capabilities                                                        |
| ---------------- | ------------------------------ | --------------------------- | ----------------------------------------------------------------------- |
| **Nyra**         | Lead Capture Specialist        | Intuitive & Responsive      | Lead processing, contact management, workflow creation                  |
| **Solari**       | Booking & Order Manager        | Clear & Luminous            | Appointment scheduling, order processing, inventory tracking            |
| **Ruvo**         | Task Orchestrator              | Grounded & Task-driven      | Task creation, deadline tracking, project coordination                  |
| **Liora**        | Marketing Strategist           | Elegant & Strategic         | Campaign management, performance tracking, audience targeting           |
| **Sage**         | Community Curator              | Warm & Connected            | Community engagement, relationship building, discussion facilitation    |
| **Elan**         | Content Choreographer          | Creative & Adaptive         | Content creation, distribution management, performance analysis         |
| **Zevi**         | Audience Analyst               | Analytical & Sharp          | Data analysis, audience segmentation, trend identification              |
| **Atlas**        | Knowledge Retrieval Specialist | Knowledgeable & Resourceful | RAG-enhanced knowledge retrieval, semantic search, content indexing     |
| **Grace Fields** | Master Orchestrator            | Harmonious & Coordinating   | Agent coordination, workflow orchestration, customer service excellence |

### How They Work Together

Our agents collaborate seamlessly across your business processes:

* **Nyra** captures a new lead, which **Ruvo** turns into follow-up tasks
* **Liora** creates marketing campaigns based on **Zevi's** audience insights
* **Elan** develops content that **Sage** shares with your community
* **Solari** manages bookings that originated from **Liora's** campaigns
* **Atlas** provides contextual knowledge to enhance all agents' capabilities
* **Grace Fields** ensures all agents work together harmoniously

### Business Applications

| Business Type       | How Agents Help                                                                                                   |
| ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| **Art Gallery**     | Capture exhibition interest, process artwork sales, manage exhibitions, market artists, engage collectors         |
| **Wellness Center** | Process retreat inquiries, manage service bookings, coordinate practitioners, promote programs, nurture community |
| **Consultancy**     | Capture consultation requests, schedule meetings, track projects, market expertise, maintain relationships        |

## Getting Started

### Prerequisites

Before you begin, ensure you have:

* Python 3.10 or higher
* Docker (recommended for production)
* Notion account with admin access
* API keys for your integrated services

### Installation Options

### Docker Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Start with Docker Compose
docker-compose up -d
```

This will start the server and all required services in containers.

### Direct Python Installation

```bash
# Clone the repository
git clone https://github.com/Utak-West/The-HigherSelf-Network-Server.git
cd The-HigherSelf-Network-Server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Start the server
python main.py
```

For detailed cloud deployment instructions, see our [Deployment Guide](./documentation/DEPLOYMENT_AND_TRAINING.md).

We recommend using the following providers:

* AWS Elastic Container Service
* Google Cloud Run
* Azure Container Instances
* Digital Ocean App Platform

### Configuration

The system is configured through environment variables in the `.env` file:

### API Credentials

* Using a strong, randomly generated webhook secret
* Setting up SSL/TLS encryption
* Implementing proper access controls

## Business Application Workflows

The HigherSelf Network Server automates key business workflows for your art gallery, wellness center, and consultancy operations:

### Art Gallery Operations

* Exhibition Planning & Management: From concept to opening night
* Artist Relationship Management: Track communications and agreements
* Artwork Sales Processing: Handle purchases, shipping, and commissions
* Collector Engagement: Nurture relationships with art collectors

### Wellness Center Operations

* Retreat Booking Management: Handle registrations and preparations
* Practitioner Scheduling: Coordinate sessions and resources
* Client Journey Tracking: Monitor wellness progress and engagement
* Program Development: Create and refine wellness offerings

### Consultancy Operations

* Client Onboarding: Streamline the intake process
* Project Management: Track deliverables and milestones
* Knowledge Management: Organize insights and resources
* Client Reporting: Generate and deliver professional reports

### Cross-Business Operations

* Marketing Campaign Management: Coordinate multi-channel outreach
* Content Creation & Distribution: Manage your content lifecycle
* Community Engagement: Nurture your online community
* Lead Capture & Nurturing: Convert interest into engagement

## Enhanced Customer Service Orchestration

The HigherSelf Network Server features Grace Fields' sophisticated customer service capabilities that deliver exceptional support experiences through intelligent agent coordination and human escalation protocols.

### Customer Service Excellence Features

#### Intelligent Request Routing
* **Automatic Issue Classification**: AI-powered categorization of customer requests
* **Severity Level Assessment**: 4-tier severity system (Level 1-4) for appropriate response
* **Business Entity Awareness**: Specialized handling for art gallery, wellness center, and consultancy operations
* **Priority-Based Processing**: Urgent, high, medium, and low priority handling

#### Multi-Agent Coordination Patterns
* **Level 1 - Standard Delegation**: Single agent handles routine requests (1-2 agents)
* **Level 2 - Multi-Agent Coordination**: Complex issues requiring specialist collaboration (3-4 agents)
* **Level 3 - Full Network Response**: High-impact situations with comprehensive agent involvement (5+ agents)
* **Level 4 - Human Escalation**: Issues requiring human judgment and expertise

#### Professional Communication Standards
* **Warm, Professional Tone**: Grace Fields maintains empathetic yet efficient communication
* **Business-Specific Greetings**: Customized responses for each business entity type
* **Response Templates**: Standardized yet personalized communication for consistency
* **Real-Time Status Updates**: Customers stay informed throughout the resolution process

#### Human Escalation Protocol
* **Automatic Trigger Detection**: Legal issues, high-value refunds, VIP client concerns
* **Structured Escalation Notifications**: Complete interaction history and context provided
* **Priority Flagging**: Urgent cases receive immediate human attention
* **Ticket Management**: Comprehensive tracking from escalation to resolution

#### Workflow Harmony Monitoring
* **Real-Time Coordination Tracking**: Monitor active workflows and agent interactions
* **Performance Metrics**: Customer satisfaction, resolution rates, and response times
* **System Health Monitoring**: Integration status for Notion, Redis, and MongoDB
* **Optimization Recommendations**: Data-driven suggestions for service improvement

### Customer Service Capabilities by Business Type

#### Art Gallery Customer Service
* **Collector Relationship Management**: VIP treatment for high-value collectors
* **Artwork Inquiry Processing**: Detailed information about pieces and availability
* **Exhibition Booking Support**: Private viewing appointments and event coordination
* **Purchase and Shipping Coordination**: Secure transaction and delivery management

#### Wellness Center Customer Service
* **Retreat Booking Assistance**: Comprehensive support for wellness program enrollment
* **Practitioner Scheduling**: Coordination with specialized wellness professionals
* **Health Journey Support**: Ongoing guidance and program recommendations
* **Community Integration**: Connection with wellness community and support groups

#### Consultancy Customer Service
* **Professional Service Coordination**: Expert matching and project scoping
* **Confidential Communication**: Secure handling of sensitive business information
* **Project Status Updates**: Regular progress reports and milestone tracking
* **Strategic Consultation Support**: Access to specialized expertise and resources

### Customer Service Performance Metrics

#### Response Time Standards
* **Urgent Priority**: 30 minutes initial response, 1 hour human escalation
* **High Priority**: 1 hour initial response, 2 hours human escalation
* **Medium Priority**: 2 hours initial response, 4 hours human escalation
* **Low Priority**: 4 hours initial response, 1 business day human escalation

#### Quality Assurance Targets
* **Customer Satisfaction Score**: Target >95% satisfaction across all interactions
* **First Contact Resolution Rate**: Target >80% of issues resolved without escalation
* **Multi-Agent Coordination Success**: Target >90% of complex workflows completed smoothly
* **Human Escalation Accuracy**: Target >95% of escalations genuinely requiring human intervention

### Training and Quality Assurance

#### Comprehensive Training Scenarios
* **Standard Delegation Training**: 20+ scenarios covering routine customer service situations
* **Multi-Agent Coordination Training**: Complex scenarios requiring specialist collaboration
* **Escalation Protocol Training**: High-stakes situations requiring human intervention
* **Business-Specific Training**: Customized scenarios for each business entity type

#### Continuous Improvement
* **Performance Analytics**: Real-time monitoring of customer service metrics
* **Agent Coordination Optimization**: Ongoing refinement of multi-agent workflows
* **Customer Feedback Integration**: Service improvements based on customer input
* **Staff Training Updates**: Regular updates to training materials and protocols

## Integration Ecosystem

The HigherSelf Network Server connects with your essential business tools:

### Core Integrations

* **Notion** - Central data hub and workflow management
* **Typeform** - Form data collection and lead capture
* **WooCommerce** - E-commerce and product management
* **Amelia** - Appointment and booking management
* **Circle.so** - Community engagement and management
* **Beehiiv** - Newsletter and email marketing

### AI & Automation Integrations

* **Hugging Face Pro** - Advanced NLP and AI model access
* **MCP Tools** - Model Context Protocol standardized tools
* **N8N** - Workflow automation platform
* **Zapier** - Integration and automation workflows
* **TutorLM** - Educational content and tutoring
* **Plaud** - Voice recording and transcription

### Specialized Platform Integrations

* **The7Space** - WordPress, Elementor Pro, and Amelia integration
* **CapCut** - Video editing and export processing
* **Pipit** - Payment processing for premium features
* **Newark Initiative** - Specialized wellness and community health tools

### Future Integrations (Planned)

* **Barter Payment System** - Alternative value exchange mechanisms
* **Advanced Analytics Platform** - Enhanced business intelligence
* **Multi-language Support** - International market expansion tools

## Documentation

### Deployment Guide

Comprehensive instructions for deploying the system in various environments.

[Read the Deployment Guide](./documentation/DEPLOYMENT_AND_TRAINING.md)

### Agent System Guide

Detailed information about agent personalities and how to work with them.

[Read the Agent Guide](./documentation/AGENT_SYSTEM_GUIDE.md)

### Customer Service Orchestration Guide

Comprehensive guide to Grace Fields' enhanced customer service capabilities, delegation protocols, and multi-agent coordination patterns.

[Read the Customer Service Guide](./documentation/GRACE_FIELDS_CUSTOMER_SERVICE_GUIDE.md)

### RAG Agent Guide

Learn how to use Atlas, the Knowledge Retrieval Specialist, for enhanced contextual capabilities.

[Read the RAG Agent Guide](./documentation/RAG_AGENT_GUIDE.md)

### Monitoring Guide

Instructions for monitoring system health and troubleshooting issues.

[Read the Monitoring Guide](./documentation/MONITORING_AND_TROUBLESHOOTING.md)

### N8N & Zapier Guide

Guide for integrating with N8N and Zapier workflow automation platforms.

[Read the Integration Guide](./N8N_Zapier_Integration_Guide.md)

### Hugging Face Guides

Guides for using Hugging Face models with agents and Notion for specialized NLP tasks.

[Read the Hugging Face Integration Guide](./documentation/HUGGINGFACE_INTEGRATION.md)
[Read the Hugging Face Agent Integration Guide](./documentation/HUGGINGFACE_AGENT_INTEGRATION.md)
[Read the Hugging Face Optimization Plan](./documentation/HUGGINGFACE_OPTIMIZATION_PLAN.md)

### Softr Integration Guide

Guide for enabling staff to interface with agents through Softr.

[Read the Softr Integration Guide](./documentation/SOFTR_INTEGRATION.md)

## For Developers

### System Architecture

The HigherSelf Network Server implements a hub-and-spoke architecture with Notion as the central hub:

#### Key Components

1. Models (`/models`): Pydantic models defining data structures
2. Services (`/services`): Service classes for external API interactions
3. Agents (`/agents`): Agent implementations with specific responsibilities
4. API (`/api`): FastAPI server for external communication

#### Data Flow

1. External events trigger webhook calls to the API
2. Events are processed by appropriate agents
3. Agents create or update records in Notion via the NotionService
4. Workflow instances track the state of business processes
5. History logs maintain a complete audit trail

#### API Endpoints

The server exposes several API endpoints for integration with external systems:

| Platform | Endpoint                        | Description                        |
| -------- | ------------------------------- | ---------------------------------- |
| N8N      | `/api/external/n8n/callback`    | Receives workflow data from N8N    |
| Zapier   | `/api/external/zapier/callback` | Receives workflow data from Zapier |

### Adding a New Agent

1. Create a new file in the `agents` directory
2. Extend the `BaseAgent` class
3. Implement the required abstract methods
4. Register the agent in `agents/__init__.py`
5. Add initialization in `main.py`

```python
from agents.base_agent import BaseAgent

class MyNewAgent(BaseAgent):
    """
    My new agent that handles specific tasks.
    """

    def __init__(self, notion_client, **kwargs):
        super().__init__(name="MyNewAgent", notion_client=notion_client, **kwargs)
        self.agent_type = "MyNewAgentType"

    async def process_event(self, event_type: str, event_data: dict) -> dict:
        """Process an event received by this agent."""
        # Implementation here
        return {"status": "processed"}

    async def check_health(self) -> dict:
        """Check the health status of this agent."""
        return {"status": "healthy"}
```

### Adding a New Integration

To add support for a new integration:

1. Add the API platform to `ApiPlatform` enum in `models/base.py`
2. Create new Pydantic models for the integration's data structures
3. Create a new service class in the `services` directory
4. Implement a new agent or extend an existing one
5. Add webhook endpoints if needed

```python
# 1. Add to ApiPlatform enum
class ApiPlatform(str, Enum):
    # Existing platforms...
    MY_NEW_PLATFORM = "my_new_platform"

# 2. Create service class
class MyNewPlatformService(BaseService):
    """Service for interacting with My New Platform."""

    def __init__(self):
        super().__init__(service_name="my_new_platform")
        # Initialize service

    async def validate_connection(self) -> bool:
        """Validate the connection to the service."""
        # Implementation here
        return True
```

## Support & Community

### Contact Support

For questions or assistance, contact The HigherSelf Network team:

["mailto:support@higherself.network">support@higherself.network

### Training & Consulting

Need help getting started? We offer personalized training and consulting services.

[Learn More](https://higherself.network/training)

---

&copy; 2023-2025 The HigherSelf Network - All Rights Reserved

Proprietary software for art gallery, wellness center, and consultancy automation
