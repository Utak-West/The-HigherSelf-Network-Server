# Master Business Operations Dashboard - API Documentation

## Table of Contents

1. [Introduction](#introduction)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [API Endpoints](#api-endpoints)
   - [Authentication](#authentication-endpoints)
   - [Organizations](#organization-endpoints)
   - [Users](#user-endpoints)
   - [Dashboard](#dashboard-endpoints)
   - [Integrations](#integration-endpoints)
   - [Monitoring](#monitoring-endpoints)
   - [Business Metrics](#business-metrics-endpoints)

## Introduction

The Master Business Operations Dashboard API provides a comprehensive set of endpoints for managing and monitoring business operations across multiple organizations. This RESTful API follows standard HTTP conventions and uses JSON for data exchange.

### Base URL

- **Development**: `http://localhost:3000/api`
- **Staging**: `https://staging-api.dashboard.example.com/api`
- **Production**: `https://api.dashboard.example.com/api`

### API Versioning

The current API version is v1. The version is included in the URL path:

```
/api/v1/resource
```

## Authentication

The API uses JSON Web Tokens (JWT) for authentication. To access protected endpoints, you must include the JWT token in the Authorization header of your requests.

### Token Format

```
Authorization: Bearer <token>
```

### Token Expiration

Access tokens expire after 24 hours. You can use the refresh token endpoint to obtain a new access token without requiring the user to log in again.

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of requests. In case of an error, the response body will contain additional information about the error.

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // Optional additional error details
  }
}
```

### Common Error Codes

| Status Code | Error Code           | Description                                     |
|-------------|----------------------|-------------------------------------------------|
| 400         | BAD_REQUEST          | The request was malformed or invalid            |
| 401         | UNAUTHORIZED         | Authentication is required or has failed        |
| 403         | FORBIDDEN            | The authenticated user lacks required permissions|
| 404         | NOT_FOUND            | The requested resource was not found            |
| 409         | CONFLICT             | The request conflicts with the current state    |
| 422         | VALIDATION_ERROR     | The request data failed validation              |
| 429         | TOO_MANY_REQUESTS    | Rate limit exceeded                             |
| 500         | INTERNAL_SERVER_ERROR| An unexpected error occurred on the server      |

## Rate Limiting

To ensure API stability and prevent abuse, rate limiting is implemented on all endpoints. The current limits are:

- **Standard endpoints**: 100 requests per minute per IP address
- **Authentication endpoints**: 10 requests per minute per IP address

Rate limit information is included in the response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1625097600
```

## API Endpoints

### Authentication Endpoints

#### Login

Authenticates a user and returns access and refresh tokens.

- **URL**: `/auth/login`
- **Method**: `POST`
- **Auth Required**: No

**Request Body**:

```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400,
    "user": {
      "id": "user123",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "admin",
      "organizationId": "org123"
    }
  }
}
```

#### Refresh Token

Generates a new access token using a valid refresh token.

- **URL**: `/auth/refresh`
- **Method**: `POST`
- **Auth Required**: No

**Request Body**:

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "accessToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expiresIn": 86400
  }
}
```

#### Logout

Invalidates the current refresh token.

- **URL**: `/auth/logout`
- **Method**: `POST`
- **Auth Required**: Yes

**Request Body**:

```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### Organization Endpoints

#### Get All Organizations

Returns a list of all organizations the authenticated user has access to.

- **URL**: `/organizations`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": [
    {
      "id": "org123",
      "name": "A.M. Consulting",
      "slug": "am-consulting",
      "type": "consulting",
      "createdAt": "2025-01-15T10:30:00Z",
      "updatedAt": "2025-06-01T14:45:00Z"
    },
    {
      "id": "org456",
      "name": "The 7 Space",
      "slug": "seven-space",
      "type": "gallery",
      "createdAt": "2025-02-10T09:15:00Z",
      "updatedAt": "2025-06-05T11:20:00Z"
    }
  ]
}
```

#### Get Organization by ID

Returns details for a specific organization.

- **URL**: `/organizations/:id`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": "org123",
    "name": "A.M. Consulting",
    "slug": "am-consulting",
    "type": "consulting",
    "address": "123 Business Ave, Suite 100",
    "city": "San Francisco",
    "state": "CA",
    "zipCode": "94105",
    "country": "USA",
    "phone": "+1 (415) 555-1234",
    "email": "info@amconsulting.example.com",
    "website": "https://amconsulting.example.com",
    "logo": "https://assets.dashboard.example.com/logos/am-consulting.png",
    "settings": {
      "timezone": "America/Los_Angeles",
      "dateFormat": "MM/DD/YYYY",
      "fiscalYearStart": "01-01"
    },
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-06-01T14:45:00Z"
  }
}
```

#### Create Organization

Creates a new organization.

- **URL**: `/organizations`
- **Method**: `POST`
- **Auth Required**: Yes
- **Permissions**: Admin

**Request Body**:

```json
{
  "name": "HigherSelf Network",
  "slug": "higherself-network",
  "type": "network",
  "address": "456 Digital Blvd",
  "city": "Austin",
  "state": "TX",
  "zipCode": "78701",
  "country": "USA",
  "phone": "+1 (512) 555-6789",
  "email": "info@higherself.example.com",
  "website": "https://higherself.example.com",
  "settings": {
    "timezone": "America/Chicago",
    "dateFormat": "MM/DD/YYYY",
    "fiscalYearStart": "01-01"
  }
}
```

**Success Response**:

- **Code**: 201 Created
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": "org789",
    "name": "HigherSelf Network",
    "slug": "higherself-network",
    "type": "network",
    "address": "456 Digital Blvd",
    "city": "Austin",
    "state": "TX",
    "zipCode": "78701",
    "country": "USA",
    "phone": "+1 (512) 555-6789",
    "email": "info@higherself.example.com",
    "website": "https://higherself.example.com",
    "settings": {
      "timezone": "America/Chicago",
      "dateFormat": "MM/DD/YYYY",
      "fiscalYearStart": "01-01"
    },
    "createdAt": "2025-06-30T15:20:00Z",
    "updatedAt": "2025-06-30T15:20:00Z"
  }
}
```

#### Update Organization

Updates an existing organization.

- **URL**: `/organizations/:id`
- **Method**: `PUT`
- **Auth Required**: Yes
- **Permissions**: Admin

**Request Body**:

```json
{
  "name": "HigherSelf Network",
  "phone": "+1 (512) 555-9876",
  "settings": {
    "timezone": "America/Denver"
  }
}
```

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": "org789",
    "name": "HigherSelf Network",
    "slug": "higherself-network",
    "type": "network",
    "address": "456 Digital Blvd",
    "city": "Austin",
    "state": "TX",
    "zipCode": "78701",
    "country": "USA",
    "phone": "+1 (512) 555-9876",
    "email": "info@higherself.example.com",
    "website": "https://higherself.example.com",
    "settings": {
      "timezone": "America/Denver",
      "dateFormat": "MM/DD/YYYY",
      "fiscalYearStart": "01-01"
    },
    "createdAt": "2025-06-30T15:20:00Z",
    "updatedAt": "2025-06-30T15:45:00Z"
  }
}
```

### User Endpoints

#### Get All Users

Returns a list of all users in the authenticated user's organization.

- **URL**: `/users`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Query Parameters**:

- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Number of users per page (default: 20)
- `role` (optional): Filter by user role (admin, manager, user)
- `status` (optional): Filter by user status (active, inactive)

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "user123",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "admin",
        "status": "active",
        "lastLogin": "2025-06-29T14:30:00Z",
        "createdAt": "2025-01-15T10:30:00Z",
        "updatedAt": "2025-06-29T14:30:00Z"
      },
      {
        "id": "user456",
        "name": "Jane Smith",
        "email": "jane.smith@example.com",
        "role": "manager",
        "status": "active",
        "lastLogin": "2025-06-28T09:15:00Z",
        "createdAt": "2025-02-10T09:15:00Z",
        "updatedAt": "2025-06-28T09:15:00Z"
      }
    ],
    "pagination": {
      "total": 15,
      "pages": 1,
      "page": 1,
      "limit": 20
    }
  }
}
```

#### Get User by ID

Returns details for a specific user.

- **URL**: `/users/:id`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager, or Self

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": "user123",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "role": "admin",
    "status": "active",
    "phone": "+1 (415) 555-1234",
    "position": "CEO",
    "department": "Executive",
    "profileImage": "https://assets.dashboard.example.com/profiles/john-doe.jpg",
    "preferences": {
      "theme": "dark",
      "notifications": {
        "email": true,
        "push": true
      }
    },
    "lastLogin": "2025-06-29T14:30:00Z",
    "createdAt": "2025-01-15T10:30:00Z",
    "updatedAt": "2025-06-29T14:30:00Z"
  }
}
```

#### Create User

Creates a new user in the authenticated user's organization.

- **URL**: `/users`
- **Method**: `POST`
- **Auth Required**: Yes
- **Permissions**: Admin

**Request Body**:

```json
{
  "name": "Alice Johnson",
  "email": "alice.johnson@example.com",
  "password": "securepassword",
  "role": "manager",
  "phone": "+1 (415) 555-5678",
  "position": "Operations Manager",
  "department": "Operations"
}
```

**Success Response**:

- **Code**: 201 Created
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": "user789",
    "name": "Alice Johnson",
    "email": "alice.johnson@example.com",
    "role": "manager",
    "status": "active",
    "phone": "+1 (415) 555-5678",
    "position": "Operations Manager",
    "department": "Operations",
    "createdAt": "2025-06-30T15:20:00Z",
    "updatedAt": "2025-06-30T15:20:00Z"
  }
}
```

#### Update User

Updates an existing user.

- **URL**: `/users/:id`
- **Method**: `PUT`
- **Auth Required**: Yes
- **Permissions**: Admin, or Self (limited fields)

**Request Body**:

```json
{
  "name": "Alice R. Johnson",
  "phone": "+1 (415) 555-9876",
  "preferences": {
    "theme": "light"
  }
}
```

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": "user789",
    "name": "Alice R. Johnson",
    "email": "alice.johnson@example.com",
    "role": "manager",
    "status": "active",
    "phone": "+1 (415) 555-9876",
    "position": "Operations Manager",
    "department": "Operations",
    "preferences": {
      "theme": "light",
      "notifications": {
        "email": true,
        "push": true
      }
    },
    "createdAt": "2025-06-30T15:20:00Z",
    "updatedAt": "2025-06-30T15:45:00Z"
  }
}
```

### Dashboard Endpoints

#### Get Dashboard Overview

Returns an overview of key metrics for the dashboard.

- **URL**: `/dashboard/overview`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Any authenticated user

**Query Parameters**:

- `period` (optional): Time period for metrics (day, week, month, quarter, year, default: month)

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "organization": {
      "id": "org123",
      "name": "A.M. Consulting"
    },
    "metrics": {
      "financial": [
        {
          "name": "Monthly Revenue",
          "value": 45250,
          "unit": "currency",
          "trend": 5.7,
          "target": 48000
        },
        {
          "name": "Average Project Value",
          "value": 8500,
          "unit": "currency",
          "trend": 3.2,
          "target": 9000
        }
      ],
      "operations": [
        {
          "name": "Active Practitioners",
          "value": 18,
          "unit": "number",
          "trend": 2,
          "target": 20
        },
        {
          "name": "Open Conflicts",
          "value": 3,
          "unit": "number",
          "trend": -2,
          "target": 0
        }
      ],
      "customer": [
        {
          "name": "Client Satisfaction",
          "value": 4.7,
          "unit": "rating",
          "trend": 0.2,
          "target": 4.8
        }
      ]
    },
    "recentActivity": [
      {
        "id": "act123",
        "type": "conflict_resolved",
        "description": "Schedule conflict between practitioners resolved",
        "timestamp": "2025-06-29T14:30:00Z",
        "user": {
          "id": "user456",
          "name": "Jane Smith"
        }
      },
      {
        "id": "act124",
        "type": "practitioner_added",
        "description": "New practitioner Dr. Robert Chen added",
        "timestamp": "2025-06-28T10:15:00Z",
        "user": {
          "id": "user123",
          "name": "John Doe"
        }
      }
    ],
    "alerts": [
      {
        "id": "alert123",
        "level": "warning",
        "message": "Client billing dispute requires attention",
        "timestamp": "2025-06-29T09:45:00Z"
      }
    ]
  }
}
```

### Integration Endpoints

#### Get All Integrations

Returns a list of all integrations for the authenticated user's organization.

- **URL**: `/integrations`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "service_name": "am_consulting",
      "service_type": "api",
      "is_active": true,
      "last_sync": "2025-06-29T14:30:00Z",
      "sync_status": "completed",
      "error_count": 0,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-06-29T14:30:00Z"
    },
    {
      "id": 2,
      "service_name": "seven_space",
      "service_type": "api",
      "is_active": true,
      "last_sync": "2025-06-29T15:45:00Z",
      "sync_status": "completed",
      "error_count": 0,
      "created_at": "2025-02-10T09:15:00Z",
      "updated_at": "2025-06-29T15:45:00Z"
    },
    {
      "id": 3,
      "service_name": "higherself_network",
      "service_type": "api",
      "is_active": true,
      "last_sync": "2025-06-29T16:30:00Z",
      "sync_status": "completed",
      "error_count": 0,
      "created_at": "2025-03-05T13:45:00Z",
      "updated_at": "2025-06-29T16:30:00Z"
    }
  ]
}
```

#### Get Integration by ID

Returns details for a specific integration.

- **URL**: `/integrations/:id`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "service_name": "am_consulting",
    "service_type": "api",
    "config": {
      "apiUrl": "https://api.amconsulting.example.com",
      "syncSchedule": "0 0 * * *",
      "syncEnabled": true,
      "dataMapping": {
        "conflicts": {
          "enabled": true,
          "fields": ["id", "title", "description", "status", "priority", "assignedTo", "createdAt", "updatedAt"]
        },
        "practitioners": {
          "enabled": true,
          "fields": ["id", "name", "specialty", "availability", "hourlyRate", "status"]
        },
        "revenue": {
          "enabled": true,
          "fields": ["period", "amount", "source", "category"]
        }
      }
    },
    "is_active": true,
    "last_sync": "2025-06-29T14:30:00Z",
    "sync_status": "completed",
    "sync_results": {
      "conflicts": { "added": 1, "updated": 2, "errors": 0 },
      "practitioners": { "added": 0, "updated": 4, "errors": 0 },
      "revenue": { "added": 6, "updated": 0, "errors": 0 }
    },
    "error_count": 0,
    "error_message": null,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-06-29T14:30:00Z"
  }
}
```

#### Initialize A.M. Consulting Integration

Initializes the A.M. Consulting integration for the authenticated user's organization.

- **URL**: `/integrations/am-consulting/initialize`
- **Method**: `POST`
- **Auth Required**: Yes
- **Permissions**: Admin

**Request Body**:

```json
{
  "apiUrl": "https://api.amconsulting.example.com",
  "apiKey": "your_am_consulting_api_key",
  "syncSchedule": "0 0 * * *",
  "syncEnabled": true,
  "performInitialSync": true,
  "dataMapping": {
    "conflicts": {
      "enabled": true,
      "fields": ["id", "title", "description", "status", "priority", "assignedTo", "createdAt", "updatedAt"]
    },
    "practitioners": {
      "enabled": true,
      "fields": ["id", "name", "specialty", "availability", "hourlyRate", "status"]
    },
    "revenue": {
      "enabled": true,
      "fields": ["period", "amount", "source", "category"]
    }
  }
}
```

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "integrationId": 1,
    "message": "A.M. Consulting integration initialized successfully"
  }
}
```

#### Trigger Integration Sync

Triggers a manual sync for a specific integration.

- **URL**: `/integrations/:id/sync`
- **Method**: `POST`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "status": "completed",
    "results": {
      "conflicts": { "added": 1, "updated": 2, "errors": 0 },
      "practitioners": { "added": 0, "updated": 4, "errors": 0 },
      "revenue": { "added": 6, "updated": 0, "errors": 0 }
    },
    "totalAdded": 7,
    "totalUpdated": 6,
    "totalErrors": 0
  }
}
```

### Monitoring Endpoints

#### Get System Health

Returns the current health status of the system.

- **URL**: `/monitoring/health`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "timestamp": 1625097600000,
    "status": "healthy",
    "cpu": {
      "usage": "25.40",
      "status": "healthy"
    },
    "memory": {
      "total": "8.00 GB",
      "used": "3.20 GB",
      "free": "4.80 GB",
      "usage": "40.00",
      "status": "healthy"
    },
    "database": {
      "activeConnections": 5,
      "maxConnections": 100,
      "connectionUsage": "5.00",
      "queryLatency": "15.20",
      "status": "healthy"
    },
    "api": {
      "requestsPerMinute": 45,
      "avgResponseTime": "120.50",
      "errorRate": "0.50",
      "status": "healthy"
    },
    "uptime": {
      "system": "15d 7h 30m 15s",
      "process": "5d 12h 45m 30s"
    }
  }
}
```

#### Get Historical Metrics

Returns historical system metrics for trending analysis.

- **URL**: `/monitoring/history`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Query Parameters**:

- `hours` (optional): Number of hours of history to retrieve (default: 24)

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": [
    {
      "timestamp": 1625097600000,
      "cpu": "25.40",
      "memory": "40.00",
      "dbConnections": "5.00",
      "dbLatency": "15.20",
      "apiRequests": 45,
      "apiLatency": "120.50",
      "apiErrors": "0.50"
    },
    {
      "timestamp": 1625094000000,
      "cpu": "30.20",
      "memory": "42.50",
      "dbConnections": "8.00",
      "dbLatency": "18.70",
      "apiRequests": 62,
      "apiLatency": "135.80",
      "apiErrors": "0.80"
    }
  ]
}
```

#### Get Alerts

Returns recent system alerts.

- **URL**: `/monitoring/alerts`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Admin, Manager

**Query Parameters**:

- `limit` (optional): Maximum number of alerts to retrieve (default: 10)

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": [
    {
      "type": "api",
      "level": "warning",
      "message": "High API error rate: 5.20%",
      "timestamp": 1625097000000
    },
    {
      "type": "memory",
      "level": "warning",
      "message": "High memory usage: 82.30%",
      "timestamp": 1625096400000
    }
  ]
}
```

### Business Metrics Endpoints

#### Get Business Metrics

Returns business metrics for the authenticated user's organization.

- **URL**: `/metrics`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Any authenticated user

**Query Parameters**:

- `category` (optional): Filter by metric category (financial, operations, customer)
- `period` (optional): Time period for metrics (day, week, month, quarter, year, default: month)
- `startDate` (optional): Start date for custom period (YYYY-MM-DD)
- `endDate` (optional): End date for custom period (YYYY-MM-DD)

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "id": 1,
        "category": "financial",
        "name": "monthly_revenue",
        "value": 45250,
        "unit": "currency",
        "target_value": 48000,
        "period_start": "2025-06-01T00:00:00Z",
        "period_end": "2025-06-30T23:59:59Z",
        "metadata": {
          "source": "am_consulting_integration",
          "previousValue": 42800,
          "changePercentage": 5.7
        }
      },
      {
        "id": 2,
        "category": "operations",
        "name": "active_practitioners",
        "value": 18,
        "unit": "number",
        "target_value": 20,
        "period_start": "2025-06-01T00:00:00Z",
        "period_end": "2025-06-30T23:59:59Z",
        "metadata": {
          "source": "am_consulting_integration"
        }
      },
      {
        "id": 3,
        "category": "operations",
        "name": "monthly_visitors",
        "value": 460,
        "unit": "number",
        "target_value": 500,
        "period_start": "2025-06-01T00:00:00Z",
        "period_end": "2025-06-30T23:59:59Z",
        "metadata": {
          "source": "seven_space_integration",
          "previousValue": 420,
          "changePercentage": 9.5
        }
      }
    ],
    "summary": {
      "total_metrics": 3,
      "categories": {
        "financial": 1,
        "operations": 2,
        "customer": 0
      },
      "period": {
        "start": "2025-06-01T00:00:00Z",
        "end": "2025-06-30T23:59:59Z"
      }
    }
  }
}
```

#### Get Metric Trends

Returns trend data for a specific metric over time.

- **URL**: `/metrics/:id/trends`
- **Method**: `GET`
- **Auth Required**: Yes
- **Permissions**: Any authenticated user

**Query Parameters**:

- `period` (optional): Time period for trends (day, week, month, quarter, year, default: month)
- `points` (optional): Number of data points to return (default: 12)

**Success Response**:

- **Code**: 200 OK
- **Content**:

```json
{
  "success": true,
  "data": {
    "metric": {
      "id": 1,
      "category": "financial",
      "name": "monthly_revenue",
      "unit": "currency"
    },
    "trends": [
      {
        "period_start": "2025-01-01T00:00:00Z",
        "period_end": "2025-01-31T23:59:59Z",
        "value": 38500
      },
      {
        "period_start": "2025-02-01T00:00:00Z",
        "period_end": "2025-02-28T23:59:59Z",
        "value": 39200
      },
      {
        "period_start": "2025-03-01T00:00:00Z",
        "period_end": "2025-03-31T23:59:59Z",
        "value": 40100
      },
      {
        "period_start": "2025-04-01T00:00:00Z",
        "period_end": "2025-04-30T23:59:59Z",
        "value": 41500
      },
      {
        "period_start": "2025-05-01T00:00:00Z",
        "period_end": "2025-05-31T23:59:59Z",
        "value": 42800
      },
      {
        "period_start": "2025-06-01T00:00:00Z",
        "period_end": "2025-06-30T23:59:59Z",
        "value": 45250
      }
    ],
    "analysis": {
      "min": 38500,
      "max": 45250,
      "avg": 41225,
      "total": 247350,
      "trend_percentage": 17.5
    }
  }
}
```

