# Code Standards and Patterns
## GoHighLevel Integration - The HigherSelf Network Server

### **CODING STANDARDS**

#### **Python Style Guide**
- **PEP 8 Compliance**: All code must follow PEP 8 standards
- **Line Length**: Maximum 88 characters (Black formatter standard)
- **Imports**: Organized in groups (standard library, third-party, local)
- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: Google-style docstrings for all public methods

#### **Example Code Structure**
```python
"""
GoHighLevel service implementation for The HigherSelf Network Server.

This module provides comprehensive integration with GoHighLevel CRM API,
supporting multi-business portfolio management and cross-business automation.
"""

import asyncio
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp
from loguru import logger
from pydantic import BaseModel, Field, validator

from services.base_service import BaseService, ServiceCredentials
from config.settings import settings


class GoHighLevelCredentials(ServiceCredentials):
    """Credentials for GoHighLevel API integration."""

    client_id: str = Field(..., description="GoHighLevel OAuth client ID")
    client_secret: str = Field(..., description="GoHighLevel OAuth client secret")
    access_token: Optional[str] = Field(None, description="Current access token")
    refresh_token: Optional[str] = Field(None, description="Refresh token for token renewal")
    location_id: str = Field(..., description="GoHighLevel location/sub-account ID")
    webhook_secret: str = Field(..., description="Webhook signature verification secret")

    class Config:
        env_prefix = "GOHIGHLEVEL_"

    @validator('client_id', 'client_secret', 'location_id', 'webhook_secret')
    def validate_required_fields(cls, v: str) -> str:
        """Validate that required fields are not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("This field is required and cannot be empty")
        return v.strip()
```

---

### **SERVICE IMPLEMENTATION PATTERNS**

#### **Base Service Inheritance Pattern**
```python
class GoHighLevelService(BaseService):
    """
    Service for interacting with GoHighLevel CRM API.

    Provides comprehensive CRM functionality including contacts, opportunities,
    campaigns, and appointments management across multiple business sub-accounts.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        location_id: Optional[str] = None,
        webhook_secret: Optional[str] = None
    ):
        """
        Initialize GoHighLevel service.

        Args:
            client_id: OAuth client ID (defaults to environment variable)
            client_secret: OAuth client secret (defaults to environment variable)
            location_id: GoHighLevel location ID (defaults to environment variable)
            webhook_secret: Webhook verification secret (defaults to environment variable)
        """
        # Get credentials from environment if not provided
        client_id = client_id or settings.integrations.gohighlevel_client_id
        client_secret = client_secret or settings.integrations.gohighlevel_client_secret
        location_id = location_id or settings.integrations.gohighlevel_location_id
        webhook_secret = webhook_secret or settings.integrations.gohighlevel_webhook_secret

        # Create credentials object
        credentials = None
        if all([client_id, client_secret, location_id, webhook_secret]):
            credentials = GoHighLevelCredentials(
                service_name="gohighlevel",
                client_id=client_id,
                client_secret=client_secret,
                location_id=location_id,
                webhook_secret=webhook_secret
            )

        # Initialize base service
        super().__init__(service_name="gohighlevel", credentials=credentials)

        # GoHighLevel specific configuration
        self.api_base_url = "https://services.leadconnectorhq.com"
        self.api_version = "v1"
        self.rate_limit_requests = 100
        self.rate_limit_window = 10  # seconds

        if not credentials:
            logger.warning("GoHighLevel credentials not fully configured")

    async def validate_credentials(self) -> bool:
        """
        Validate GoHighLevel API credentials.

        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.credentials:
            logger.error("GoHighLevel credentials not configured")
            return False

        try:
            # Test API access with location info endpoint
            url = f"{self.api_base_url}/{self.api_version}/locations/{self.credentials.location_id}"
            headers = await self._get_auth_headers()

            response = await self.async_get(url, headers=headers)

            # Update credentials verification timestamp
            self.credentials.last_verified = datetime.now()

            logger.info("GoHighLevel credentials validated successfully")
            return True

        except Exception as e:
            logger.error(f"Invalid GoHighLevel credentials: {e}")
            return False
```

---

### **ERROR HANDLING PATTERNS**

#### **Comprehensive Exception Handling**
```python
from typing import Optional
from enum import Enum

class GoHighLevelError(Exception):
    """Base exception for GoHighLevel API errors."""
    pass

class GoHighLevelAuthError(GoHighLevelError):
    """Authentication/authorization errors."""
    pass

class GoHighLevelRateLimitError(GoHighLevelError):
    """Rate limit exceeded errors."""
    pass

class GoHighLevelValidationError(GoHighLevelError):
    """Data validation errors."""
    pass

async def _handle_api_response(self, response: aiohttp.ClientResponse) -> Dict[str, Any]:
    """
    Handle GoHighLevel API response with comprehensive error handling.

    Args:
        response: aiohttp response object

    Returns:
        Parsed JSON response data

    Raises:
        GoHighLevelAuthError: For authentication failures
        GoHighLevelRateLimitError: For rate limit violations
        GoHighLevelValidationError: For validation errors
        GoHighLevelError: For other API errors
    """
    try:
        if response.status == 200:
            return await response.json()

        elif response.status == 401:
            error_data = await response.json()
            logger.error(f"GoHighLevel authentication error: {error_data}")
            raise GoHighLevelAuthError(f"Authentication failed: {error_data.get('message', 'Unknown error')}")

        elif response.status == 429:
            retry_after = response.headers.get('Retry-After', '60')
            logger.warning(f"GoHighLevel rate limit exceeded. Retry after {retry_after} seconds")
            raise GoHighLevelRateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds")

        elif response.status == 422:
            error_data = await response.json()
            logger.error(f"GoHighLevel validation error: {error_data}")
            raise GoHighLevelValidationError(f"Validation failed: {error_data.get('message', 'Unknown error')}")

        else:
            error_text = await response.text()
            logger.error(f"GoHighLevel API error {response.status}: {error_text}")
            raise GoHighLevelError(f"API error {response.status}: {error_text}")

    except aiohttp.ClientError as e:
        logger.error(f"GoHighLevel client error: {e}")
        raise GoHighLevelError(f"Client error: {e}")
```

---

### **PYDANTIC MODEL PATTERNS**

#### **Business-Specific Model Structure**
```python
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

class BusinessType(str, Enum):
    """Enumeration of supported business types."""
    ART_GALLERY = "art_gallery"
    WELLNESS_CENTER = "wellness_center"
    CONSULTANCY = "consultancy"
    INTERIOR_DESIGN = "interior_design"
    LUXURY_RENOVATIONS = "luxury_renovations"
    EXECUTIVE_WELLNESS = "executive_wellness"
    CORPORATE_WELLNESS = "corporate_wellness"

class ContactSource(str, Enum):
    """Enumeration of contact sources."""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    ADVERTISING = "advertising"
    EVENT = "event"
    CROSS_BUSINESS = "cross_business"

class GHLContact(BaseModel):
    """GoHighLevel contact model with cross-business support."""

    id: Optional[str] = Field(None, description="GoHighLevel contact ID")
    first_name: str = Field(..., description="Contact first name")
    last_name: str = Field(..., description="Contact last name")
    email: str = Field(..., description="Contact email address")
    phone: Optional[str] = Field(None, description="Contact phone number")

    # Business context
    primary_business: BusinessType = Field(..., description="Primary business interest")
    source: ContactSource = Field(ContactSource.WEBSITE, description="Lead source")

    # Cross-business tracking
    business_interests: List[BusinessType] = Field(default_factory=list, description="All business interests")
    cross_sell_potential: Dict[BusinessType, float] = Field(default_factory=dict, description="Cross-sell scores")

    # Custom fields by business type
    art_gallery_fields: Optional[Dict[str, Any]] = Field(None, description="Art gallery specific fields")
    wellness_fields: Optional[Dict[str, Any]] = Field(None, description="Wellness specific fields")
    consultancy_fields: Optional[Dict[str, Any]] = Field(None, description="Consultancy specific fields")
    home_services_fields: Optional[Dict[str, Any]] = Field(None, description="Home services specific fields")

    # Integration tracking
    notion_page_id: Optional[str] = Field(None, description="Notion page ID for sync")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @validator('email')
    def validate_email(cls, v: str) -> str:
        """Validate email format."""
        if not v or '@' not in v:
            raise ValueError("Valid email address is required")
        return v.lower().strip()

    @validator('business_interests')
    def validate_business_interests(cls, v: List[BusinessType], values: Dict[str, Any]) -> List[BusinessType]:
        """Ensure primary business is included in interests."""
        primary_business = values.get('primary_business')
        if primary_business and primary_business not in v:
            v.append(primary_business)
        return v
```

---

### **ASYNC PATTERNS AND BEST PRACTICES**

#### **Rate Limiting Implementation**
```python
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

class RateLimiter:
    """Rate limiter for GoHighLevel API compliance."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 10):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[datetime] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """
        Acquire permission to make an API request.

        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = datetime.now()

            # Remove requests outside the current window
            cutoff = now - timedelta(seconds=self.window_seconds)
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]

            # Check if we can make another request
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = (oldest_request + timedelta(seconds=self.window_seconds) - now).total_seconds()

                if wait_time > 0:
                    logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                    await asyncio.sleep(wait_time)
                    return await self.acquire()  # Recursive call after waiting

            # Record this request
            self.requests.append(now)

# Usage in service methods
async def create_contact(self, contact_data: GHLContact) -> Optional[str]:
    """Create contact with rate limiting."""
    await self.rate_limiter.acquire()

    try:
        # API call implementation
        pass
    except GoHighLevelRateLimitError:
        # Handle rate limit with exponential backoff
        await asyncio.sleep(2 ** self.retry_count)
        return await self.create_contact(contact_data)
```

---

### **TESTING PATTERNS**

#### **Comprehensive Test Structure**
```python
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from services.gohighlevel_service import GoHighLevelService
from models.gohighlevel_models import GHLContact, BusinessType

class TestGoHighLevelService:
    """Test suite for GoHighLevel service."""

    @pytest.fixture
    async def ghl_service(self):
        """Create GoHighLevel service instance for testing."""
        service = GoHighLevelService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            location_id="test_location_id",
            webhook_secret="test_webhook_secret"
        )
        return service

    @pytest.fixture
    def sample_contact(self):
        """Create sample contact for testing."""
        return GHLContact(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1234567890",
            primary_business=BusinessType.ART_GALLERY,
            business_interests=[BusinessType.ART_GALLERY, BusinessType.INTERIOR_DESIGN]
        )

    @pytest.mark.asyncio
    async def test_create_contact_success(self, ghl_service, sample_contact):
        """Test successful contact creation."""
        with patch.object(ghl_service, 'async_post') as mock_post:
            mock_post.return_value = {"id": "test_contact_id"}

            result = await ghl_service.create_contact(sample_contact)

            assert result == "test_contact_id"
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_rate_limiting(self, ghl_service):
        """Test rate limiting functionality."""
        # Mock rapid API calls
        with patch.object(ghl_service, 'async_get') as mock_get:
            mock_get.return_value = {"data": "test"}

            # Make requests that should trigger rate limiting
            tasks = [ghl_service.get_contact("test_id") for _ in range(150)]
            results = await asyncio.gather(*tasks)

            # Verify all requests completed successfully
            assert len(results) == 150
            assert all(result is not None for result in results)
```

This code standards document ensures all AI assistants follow consistent patterns while implementing the GoHighLevel integration, maintaining code quality and system reliability.
