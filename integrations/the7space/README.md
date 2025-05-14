# The 7 Space - Integration and Visualization Templates

This project provides integration components and templates for The 7 Space (Art Gallery & Wellness Center) to connect Softr interfaces with the Higher Self Network server.

## Project Overview

The 7 Space requires comprehensive interfaces for managing art gallery and wellness center operations. This project implements:

1. **Softr Template Prompts** - Ready-to-use templates for building Softr interfaces
2. **Pydantic Models** - Data models for the Higher Self Network server integration
3. **API Integration** - Connectivity between Softr interfaces and backend services
4. **Dashboard Configurations** - Visualization templates for business intelligence

## Directory Structure

```
the7space-notion-integration/
│
├── src/
│   ├── models/              # Pydantic data models
│   │   ├── the7space_models.py       # Business domain models
│   │   └── softr_integration_models.py # API integration models
│   │
│   ├── api/                 # API connectivity
│   │   └── higherself_network_api.py  # Higher Self Network API client
│   │
│   ├── visualizations/      # Dashboard templates
│   │   └── dashboard_config.py       # Dashboard configuration
│   │
│   └── app.py              # Main application for API endpoints
│
├── config/                 # Configuration files
├── tests/                  # Test suite
├── docs/                   # Documentation
└── softr_template_prompts.md  # Softr interface templates
```

## Softr Templates

The project includes comprehensive template prompts for building Softr interfaces:

- **Client Portal** - Personalized interface for clients
- **Artist Dashboard** - Tools for gallery artists
- **Public Gallery Website** - Public-facing art gallery interface
- **Wellness Center Booking** - Service booking system
- **Sales Dashboard** - Financial analytics
- **Client Acquisition Workflow** - Lead generation and nurturing
- **Inventory Management** - Art inventory system
- **Event Management** - Exhibition and event organization

## Data Models

The project implements Pydantic models to define the data structures needed for the integration:

1. **Business Domain Models**
   - Artist, Artwork, Client, Sale, Event, WellnessService, Booking, etc.

2. **API Integration Models**
   - WebhookPayload, ApiResponse, ArtworkListRequest, ServiceBookingRequest, etc.

## Integration with Higher Self Network Server

The API integration follows the centralized deployment principles specified in The HigherSelf Network guidelines, ensuring:

1. All data flows through the Higher Self Network server
2. Secure API authentication and webhook handling
3. Proper error handling and logging
4. Workflow instance management through the API

## Dashboard Configurations

Visualization templates are provided for:

- Sales performance tracking
- Inventory management
- Event planning and analysis
- Wellness service monitoring
- Client relationship management

## Setup Instructions

1. Install dependencies:
   ```bash
   cd /Users/utakwest/CascadeProjects/the7space-notion-integration
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```
   HIGHERSELF_SERVER_API_ENDPOINT=https://api.higherselfnetwork.com
   HIGHERSELF_API_KEY=your_api_key
   HIGHERSELF_WEBHOOK_SECRET=your_webhook_secret
   HIGHERSELF_SOFTR_SITE_ID=your_softr_site_id
   ```

3. Run the API server:
   ```bash
   cd /Users/utakwest/CascadeProjects/the7space-notion-integration/src
   python app.py
   ```

## Using Softr Templates

1. Copy the desired template from `softr_template_prompts.md`
2. Create a new Softr project or page
3. Use the prompt to guide your Softr interface development
4. Connect Softr to the Higher Self Network server using the API endpoints

## API Endpoints

The integration API provides endpoints for:

- Artwork listings and details
- Event management
- Service bookings
- Art purchases
- User profiles
- Dashboard data

## Next Steps

1. Configure your Softr interface according to the templates
2. Deploy the integration API to the Higher Self Network server
3. Connect your Softr interfaces to the API endpoints
4. Test the full integration flow
5. Deploy to production

## Contributing

When extending this project, ensure all additions adhere to The HigherSelf Network principles, particularly the centralized deployment and data management guidelines.
