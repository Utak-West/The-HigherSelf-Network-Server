"""
The 7 Space Service Module

This module provides integration with The 7 Space website through MCP tools,
enabling WordPress, Elementor Pro, and Amelia booking system integration.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

# Import required packages - ensure these are installed
try:
    from loguru import logger
except ImportError:
    import logging

    # Create a logger that mimics loguru's interface
    logger = logging.getLogger("the7space")
    logger.info = logger.info
    logger.error = logger.error
    logger.warning = logger.warning
    logger.debug = logger.debug

try:
from pydantic import BaseModel, Field, field_validatorexcept ImportError:
    # Fallback imports if pydantic is not available
    from typing import Any, Dict, List, Optional, Union

    # Simple BaseModel implementation
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

        def dict(self):
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

    # Simple Field implementation
    def Field(default_factory=None, **kwargs):
        return default_factory() if callable(default_factory) else None

    # Simple validator implementation
    def validator(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


# Import base service class
from services.base_service import BaseService, ServiceCredentials


class The7SpaceCredentials:
    """Configuration for The 7 Space website integration."""

    def __init__(
        self,
        service_name,
        wp_api_url,
        wp_username,
        wp_app_password,
        amelia_api_key=None,
        softr_api_url=None,
        softr_api_key=None,
        softr_domain=None,
    ):
        self.service_name = service_name
        self.wp_api_url = wp_api_url
        self.wp_username = wp_username
        self.wp_app_password = wp_app_password
        self.amelia_api_key = amelia_api_key
        self.softr_api_url = softr_api_url
        self.softr_api_key = softr_api_key
        self.softr_domain = softr_domain
        self.last_verified = None  # Timestamp for last verification

    def validate_required_fields(self):
        if not self.wp_api_url or not self.wp_username or not self.wp_app_password:
            raise ValueError(
                "Required fields wp_api_url, wp_username, and wp_app_password must not be empty"
            )
        return True


class WordPressPost(BaseModel):
    """Model representing a WordPress post."""

    def __init__(
        self,
        title,
        content,
        id=None,
        status="draft",
        post_type="post",
        slug=None,
        date=None,
        categories=None,
        tags=None,
        featured_media=None,
        notion_page_id=None,
    ):
        self.id = id
        self.title = title
        self.content = content
        self.status = status
        self.post_type = post_type
        self.slug = slug
        self.date = date or datetime.now()
        self.categories = categories or []
        self.tags = tags or []
        self.featured_media = featured_media
        self.notion_page_id = notion_page_id


class AmeliaService(BaseModel):
    """Model representing an Amelia service."""

    def __init__(
        self,
        id,
        name,
        price,
        duration,
        description=None,
        color=None,
        category_id=None,
        min_capacity=1,
        max_capacity=1,
        status="visible",
    ):
        self.id = id
        self.name = name
        self.description = description
        self.color = color
        self.price = price
        self.duration = duration
        self.category_id = category_id
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        self.status = status


class AmeliaAppointment(BaseModel):
    """Model representing an Amelia booking appointment."""

    def __init__(
        self,
        booking_start,
        service_id,
        provider_id,
        customer_first_name,
        customer_last_name,
        customer_email,
        id=None,
        booking_end=None,
        status="pending",
        customer_phone=None,
        internal_notes=None,
        notion_page_id=None,
    ):
        self.id = id
        self.booking_start = booking_start
        self.booking_end = booking_end
        self.status = status
        self.service_id = service_id
        self.provider_id = provider_id
        self.customer_first_name = customer_first_name
        self.customer_last_name = customer_last_name
        self.customer_email = customer_email
        self.customer_phone = customer_phone
        self.internal_notes = internal_notes
        self.notion_page_id = notion_page_id


class SoftrPortal(BaseModel):
    """Model representing a Softr portal."""

    def __init__(self, name, url, type, id=None, description=None, status="active"):
        self.id = id
        self.name = name
        self.description = description
        self.url = url
        self.type = type
        self.status = status


class SoftrUser(BaseModel):
    """Model representing a Softr user."""

    def __init__(
        self,
        email,
        id=None,
        first_name=None,
        last_name=None,
        status="active",
        user_groups=None,
        notion_page_id=None,
    ):
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.status = status
        self.user_groups = user_groups or []
        self.notion_page_id = notion_page_id


class SoftrRecord(BaseModel):
    """Model representing a record in a Softr data source."""

    def __init__(
        self,
        data_source,
        fields,
        id=None,
        created_at=None,
        updated_at=None,
        notion_page_id=None,
    ):
        self.id = id
        self.data_source = data_source
        self.fields = fields
        self.created_at = created_at
        self.updated_at = updated_at
        self.notion_page_id = notion_page_id


class The7SpaceService(BaseService):
    """
    Service for integrating with The 7 Space website.
    Provides WordPress, Elementor Pro, and Amelia booking system integration through MCP tools.
    """

    def __init__(
        self,
        wp_api_url: Optional[str] = None,
        wp_username: Optional[str] = None,
        wp_app_password: Optional[str] = None,
        amelia_api_key: Optional[str] = None,
        softr_api_url: Optional[str] = None,
        softr_api_key: Optional[str] = None,
        softr_domain: Optional[str] = None,
    ):
        """
        Initialize the The 7 Space integration service.

        Args:
            wp_api_url: WordPress API URL
            wp_username: WordPress username
            wp_app_password: WordPress application password
            amelia_api_key: Amelia Booking API key
            softr_api_url: Softr API URL
            softr_api_key: Softr API key
            softr_domain: Softr domain
        """
        # Get credentials from environment if not provided
        wp_api_url = wp_api_url or os.environ.get("THE7SPACE_WP_API_URL")
        wp_username = wp_username or os.environ.get("THE7SPACE_WP_USERNAME")
        wp_app_password = wp_app_password or os.environ.get("THE7SPACE_WP_APP_PASSWORD")
        amelia_api_key = amelia_api_key or os.environ.get("THE7SPACE_AMELIA_API_KEY")
        softr_api_url = softr_api_url or os.environ.get("THE7SPACE_SOFTR_API_URL")
        softr_api_key = softr_api_key or os.environ.get("THE7SPACE_SOFTR_API_KEY")
        softr_domain = softr_domain or os.environ.get("THE7SPACE_SOFTR_DOMAIN")

        # Create credentials object
        credentials = None
        if wp_api_url and wp_username and wp_app_password:
            credentials = The7SpaceCredentials(
                service_name="the7space",
                wp_api_url=wp_api_url,
                wp_username=wp_username,
                wp_app_password=wp_app_password,
                amelia_api_key=amelia_api_key,
                softr_api_url=softr_api_url,
                softr_api_key=softr_api_key,
                softr_domain=softr_domain,
            )

        # Initialize base service
        super().__init__(service_name="the7space", credentials=credentials)

        # Store credentials for later use
        self.wp_api_url = wp_api_url
        self.wp_username = wp_username
        self.wp_app_password = wp_app_password
        self.amelia_api_key = amelia_api_key
        self.softr_api_url = softr_api_url
        self.softr_api_key = softr_api_key
        self.softr_domain = softr_domain

        # Log initialization status
        if not self.wp_api_url or not self.wp_username or not self.wp_app_password:
            logger.warning("The 7 Space WordPress credentials not fully configured")
        else:
            logger.info("The 7 Space WordPress integration initialized successfully")

        if not self.softr_api_url or not self.softr_api_key or not self.softr_domain:
            logger.warning("The 7 Space Softr credentials not fully configured")
        else:
            logger.info("The 7 Space Softr integration initialized successfully")

    async def validate_connection(self) -> bool:
        """
        Validate the connection to The 7 Space website.

        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Use the MCP tool to validate connection
            # This requires the AI using MCP tools, which is not directly available in code
            # Instead, we'll make a basic test request
            # Import the correct notion service
            try:
                from services.notion_service import NotionService

                notion_service = NotionService()
            except ImportError:
                logger.warning(
                    "NotionService not available, validation may be incomplete"
                )
                # Continue without using notion_service

            # Test by checking if we can fetch posts
            posts = await self.get_wordpress_posts(limit=1)

            # Update credentials verification timestamp
            if self.credentials:
                self.credentials.last_verified = datetime.now()

            logger.info("The 7 Space connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating The 7 Space connection: {e}")
            return False

    async def get_wordpress_posts(
        self,
        post_type: str = "post",
        status: str = "publish",
        search: Optional[str] = None,
        limit: int = 10,
        page: int = 1,
    ) -> List[WordPressPost]:
        """
        Get WordPress posts from The 7 Space website.

        Args:
            post_type: Post type (post, page, etc.)
            status: Post status (publish, draft, etc.)
            search: Search term
            limit: Number of posts to retrieve
            page: Page number

        Returns:
            List of WordPressPost objects
        """
        try:
            # Use the MCP tool to get WordPress posts
            from services.integration_manager import IntegrationManager

            integration_manager = IntegrationManager()
            # Get the MCP server using the appropriate method
            mcp_server = None
            integration_manager = IntegrationManager()

            # Try different methods to get the MCP server
            if hasattr(integration_manager, "find_mcp_server"):
                mcp_server = await integration_manager.find_mcp_server(
                    "the7space-mcp-integration"
                )
            elif hasattr(integration_manager, "get_mcp_server"):
                mcp_server = await integration_manager.get_mcp_server(
                    "the7space-mcp-integration"
                )
            else:
                # If neither method exists, log an error
                logger.error("No method available to get MCP server")

            if not mcp_server:
                logger.error("MCP server 'the7space-mcp-integration' not found")
                return []

            # Prepare arguments for the MCP tool call
            args = {
                "post_type": post_type,
                "status": status,
                "per_page": limit,
                "page": page,
            }

            if search:
                args["search"] = search

            # Call the MCP tool to get WordPress posts
            result = await mcp_server.call_tool("get_wp_posts", args)

            if not result or "posts" not in result:
                logger.error(
                    f"Failed to get WordPress posts: {result.get('error', 'Unknown error')}"
                )
                return []

            # Convert the result to WordPressPost objects
            posts = []
            for post_data in result.get("posts", []):
                # Convert any potential non-string values to correct types
                post_id = (
                    int(post_data.get("id"))
                    if post_data.get("id") is not None
                    else None
                )

                # Ensure title, content, status, and type are strings
                title = str(post_data.get("title", ""))
                content = str(post_data.get("content", ""))
                post_status = str(post_data.get("status", status))
                post_type_value = str(post_data.get("type", post_type))
                slug = str(post_data.get("slug", ""))

                # Convert categories and tags to lists of integers
                categories = []
                tags = []

                if "categories" in post_data and post_data.get("categories"):
                    try:
                        categories = [
                            int(cat_id) for cat_id in post_data.get("categories")
                        ]
                    except (ValueError, TypeError):
                        # Handle case where categories might not be convertible to int
                        categories = []

                if "tags" in post_data and post_data.get("tags"):
                    try:
                        tags = [int(tag_id) for tag_id in post_data.get("tags")]
                    except (ValueError, TypeError):
                        # Handle case where tags might not be convertible to int
                        tags = []

                # Convert featured_media to int if present
                featured_media = None
                if post_data.get("featured_media") is not None:
                    try:
                        featured_media = int(post_data.get("featured_media"))
                    except (ValueError, TypeError):
                        featured_media = None

                # Parse date string to datetime
                date_value = datetime.now()
                if "date" in post_data:
                    try:
                        date_value = datetime.fromisoformat(
                            post_data.get("date").replace("Z", "+00:00")
                        )
                    except (ValueError, AttributeError):
                        # Keep default if date parsing fails
                        date_value = datetime.now()

                post = WordPressPost(
                    id=post_id,
                    title=title,
                    content=content,
                    status=post_status,
                    post_type=post_type_value,
                    slug=slug,
                    date=date_value,
                    categories=categories,
                    tags=tags,
                    featured_media=featured_media,
                )
                posts.append(post)

            logger.info(f"Retrieved {len(posts)} {post_type}s from The 7 Space website")
            return posts
        except Exception as e:
            logger.error(f"Error getting {post_type}s from The 7 Space website: {e}")
            return []

    async def create_wordpress_post(self, post: WordPressPost) -> Optional[int]:
        """
        Create a new WordPress post on The 7 Space website.

        Args:
            post: WordPressPost object with post details

        Returns:
            Post ID if successful, None otherwise
        """
        try:
            # Use the MCP tool to create a WordPress post
            from services.integration_manager import IntegrationManager

            integration_manager = IntegrationManager()
            # Get the MCP server using the appropriate method
            mcp_server = None
            integration_manager = IntegrationManager()

            # Try different methods to get the MCP server
            if hasattr(integration_manager, "find_mcp_server"):
                mcp_server = await integration_manager.find_mcp_server(
                    "the7space-mcp-integration"
                )
            elif hasattr(integration_manager, "get_mcp_server"):
                mcp_server = await integration_manager.get_mcp_server(
                    "the7space-mcp-integration"
                )
            else:
                # If neither method exists, log an error
                logger.error("No method available to get MCP server")

            if not mcp_server:
                logger.error("MCP server 'the7space-mcp-integration' not found")
                return None

            # Prepare arguments for the MCP tool call
            args = {
                "title": str(post.title),
                "content": str(post.content),
                "post_type": str(post.post_type),
                "status": str(post.status),
            }

            if post.categories:
                # Ensure categories is a list of integers
                args["categories"] = [int(cat_id) for cat_id in post.categories]

            if post.tags:
                # Ensure tags is a list of integers
                args["tags"] = [int(tag_id) for tag_id in post.tags]

            if post.featured_media:
                # Ensure featured_media is an integer
                args["featured_media"] = int(post.featured_media)

            # Call the MCP tool to create a WordPress post
            result = await mcp_server.call_tool("create_wp_post", args)

            if not result or "id" not in result:
                logger.error(
                    f"Failed to create WordPress post: {result.get('error', 'Unknown error')}"
                )
                return None

            post_id = result.get("id")
            logger.info(
                f"Created {post.post_type} on The 7 Space website with ID: {post_id}"
            )

            # If the post has a notion_page_id, store the mapping
            if post.notion_page_id:
                await self._store_wp_notion_mapping(post_id, post.notion_page_id)

            return post_id
        except Exception as e:
            logger.error(f"Error creating {post.post_type} on The 7 Space website: {e}")
            return None

    async def update_wordpress_post(
        self, post_id: int, post_data: Dict[str, Any]
    ) -> bool:
        """
        Update a WordPress post on The 7 Space website.

        Args:
            post_id: WordPress post ID
            post_data: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Use the MCP tool to update a WordPress post
            from services.integration_manager import IntegrationManager

            integration_manager = IntegrationManager()
            # Get the MCP server using the appropriate method
            mcp_server = None
            integration_manager = IntegrationManager()

            # Try different methods to get the MCP server
            if hasattr(integration_manager, "find_mcp_server"):
                mcp_server = await integration_manager.find_mcp_server(
                    "the7space-mcp-integration"
                )
            elif hasattr(integration_manager, "get_mcp_server"):
                mcp_server = await integration_manager.get_mcp_server(
                    "the7space-mcp-integration"
                )
            else:
                # If neither method exists, log an error
                logger.error("No method available to get MCP server")

            if not mcp_server:
                logger.error("MCP server 'the7space-mcp-integration' not found")
                return False

            # Prepare arguments for the MCP tool call
            args = {"id": int(post_id)}

            # Add the fields to update with proper type conversion
            for key, value in post_data.items():
                # Convert values to appropriate types
                if key in ["categories", "tags"] and isinstance(value, list):
                    args[key] = [int(item) for item in value]
                elif key == "featured_media" and value is not None:
                    args[key] = int(value)
                elif (
                    key in ["title", "content", "status", "slug"] and value is not None
                ):
                    args[key] = str(value)
                else:
                    args[key] = value

            # Call the MCP tool to update a WordPress post
            result = await mcp_server.call_tool("update_wp_post", args)

            if not result or "id" not in result:
                logger.error(
                    f"Failed to update WordPress post: {result.get('error', 'Unknown error')}"
                )
                return False

            logger.info(f"Updated post {post_id} on The 7 Space website")
            return True
        except Exception as e:
            logger.error(f"Error updating post {post_id} on The 7 Space website: {e}")
            return False

    async def get_amelia_services(
        self, category_id: Optional[int] = None, status: str = "visible"
    ) -> List[AmeliaService]:
        """
        Get Amelia services from The 7 Space website.

        Args:
            category_id: Filter by category ID
            status: Service status (visible, hidden, disabled)

        Returns:
            List of AmeliaService objects
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return a placeholder
            logger.info(
                f"Fetching Amelia services from The 7 Space website. Category ID: {category_id}, Status: {status}"
            )

            # Create placeholder data for demonstration
            services = [
                AmeliaService(
                    id=1,
                    name="Sound Healing Session",
                    description="60-minute sound healing session for relaxation and rejuvenation.",
                    price=75.0,
                    duration=3600,  # 1 hour in seconds
                    category_id=1,
                    min_capacity=1,
                    max_capacity=1,
                    status="visible",
                ),
                AmeliaService(
                    id=2,
                    name="Art Therapy Workshop",
                    description="90-minute art therapy workshop for creative expression and healing.",
                    price=95.0,
                    duration=5400,  # 1.5 hours in seconds
                    category_id=2,
                    min_capacity=5,
                    max_capacity=15,
                    status="visible",
                ),
                AmeliaService(
                    id=3,
                    name="Meditation Class",
                    description="45-minute guided meditation class for mindfulness and stress reduction.",
                    price=45.0,
                    duration=2700,  # 45 minutes in seconds
                    category_id=1,
                    min_capacity=1,
                    max_capacity=10,
                    status="visible",
                ),
            ]

            # Filter by category if provided
            if category_id:
                services = [s for s in services if s.category_id == category_id]

            # Filter by status
            services = [s for s in services if s.status == status]

            return services
        except Exception as e:
            logger.error(f"Error getting Amelia services from The 7 Space website: {e}")
            return []

    async def get_amelia_appointments(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> List[AmeliaAppointment]:
        """
        Get Amelia appointments from The 7 Space website.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            status: Appointment status (pending, approved, canceled, rejected)

        Returns:
            List of AmeliaAppointment objects
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return a placeholder
            logger.info(f"Fetching Amelia appointments from The 7 Space website")

            # Set default dates if not provided
            if not start_date:
                start_date = datetime.now()
            if not end_date:
                end_date = start_date + timedelta(days=7)

            # Create placeholder data for demonstration
            appointments = [
                AmeliaAppointment(
                    id=101,
                    booking_start=datetime.now() + timedelta(days=1, hours=2),
                    booking_end=datetime.now() + timedelta(days=1, hours=3),
                    status="approved",
                    service_id=1,
                    provider_id=1,
                    customer_first_name="Jane",
                    customer_last_name="Doe",
                    customer_email="jane.doe@example.com",
                    customer_phone="555-123-4567",
                ),
                AmeliaAppointment(
                    id=102,
                    booking_start=datetime.now() + timedelta(days=2, hours=4),
                    booking_end=datetime.now() + timedelta(days=2, hours=5.5),
                    status="pending",
                    service_id=2,
                    provider_id=2,
                    customer_first_name="John",
                    customer_last_name="Smith",
                    customer_email="john.smith@example.com",
                ),
            ]

            # Filter by date range
            appointments = [
                a for a in appointments if start_date <= a.booking_start <= end_date
            ]

            # Filter by status if provided
            if status:
                appointments = [a for a in appointments if a.status == status]

            return appointments
        except Exception as e:
            logger.error(
                f"Error getting Amelia appointments from The 7 Space website: {e}"
            )
            return []

    async def create_amelia_appointment(
        self, appointment: AmeliaAppointment
    ) -> Optional[int]:
        """
        Create a new Amelia appointment on The 7 Space website.

        Args:
            appointment: AmeliaAppointment object with appointment details

        Returns:
            Appointment ID if successful, None otherwise
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return a placeholder
            logger.info(
                f"Creating Amelia appointment for {appointment.customer_first_name} {appointment.customer_last_name}"
            )

            # Simulate an appointment ID
            appointment_id = 12345

            return appointment_id
        except Exception as e:
            logger.error(
                f"Error creating Amelia appointment on The 7 Space website: {e}"
            )
            return None

    # Softr Portal Methods
    async def get_softr_portals(
        self, status: str = "active", portal_type: Optional[str] = None
    ) -> List[SoftrPortal]:
        """
        Get Softr portals.

        Args:
            status: Portal status (active, draft, archived)
            portal_type: Portal type (client, artist, community, admin)

        Returns:
            List of SoftrPortal objects
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return placeholder data
            logger.info(
                f"Fetching Softr portals from The 7 Space. Status: {status}, Type: {portal_type}"
            )

            # Create placeholder data
            portals = [
                SoftrPortal(
                    id="client-portal-1",
                    name="The 7 Space Client Portal",
                    description="Client portal for The 7 Space members",
                    url="https://clients.the7space.softr.app",
                    type="client",
                    status="active",
                ),
                SoftrPortal(
                    id="artist-portal-1",
                    name="The 7 Space Artist Dashboard",
                    description="Portal for artists to manage their exhibits",
                    url="https://artists.the7space.softr.app",
                    type="artist",
                    status="active",
                ),
                SoftrPortal(
                    id="community-portal-1",
                    name="The 7 Space Community Hub",
                    description="Community portal for all The 7 Space members",
                    url="https://community.the7space.softr.app",
                    type="community",
                    status="active",
                ),
            ]

            # Filter by type and status
            filtered_portals = [p for p in portals if p.status == status]
            if portal_type:
                filtered_portals = [
                    p for p in filtered_portals if p.type == portal_type
                ]

            return filtered_portals
        except Exception as e:
            logger.error(f"Error getting Softr portals: {e}")
            return []

    async def create_softr_user(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        user_groups: Optional[List[str]] = None,
        notion_page_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a new Softr user.

        Args:
            email: User email
            first_name: User first name
            last_name: User last name
            user_groups: List of user groups to assign
            notion_page_id: Notion page ID for reference

        Returns:
            User ID if successful, None otherwise
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return a placeholder
            logger.info(f"Creating Softr user in The 7 Space: {email}")

            # Simulate creating a user and returning an ID
            user_id = f"user-{hash(email) % 10000}"

            return user_id
        except Exception as e:
            logger.error(f"Error creating Softr user: {e}")
            return None

    async def get_softr_records(
        self,
        data_source: str,
        limit: int = 100,
        offset: int = 0,
        filter_expr: Optional[str] = None,
    ) -> List[SoftrRecord]:
        """
        Get records from a Softr data source.

        Args:
            data_source: Data source name/ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            filter_expr: Filter expression

        Returns:
            List of SoftrRecord objects
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return placeholder data
            logger.info(
                f"Fetching Softr records from {data_source}. Limit: {limit}, Offset: {offset}"
            )

            # Create placeholder data based on the data source type
            records = []

            # Generate different placeholder data based on the data source
            if "event" in data_source:
                for i in range(min(limit, 5)):
                    records.append(
                        SoftrRecord(
                            id=f"event-{i + 1}",
                            data_source=data_source,
                            fields={
                                "name": f"Sample Event {i + 1}",
                                "date": (
                                    datetime.now() + timedelta(days=i)
                                ).isoformat(),
                                "location": "The 7 Space Gallery",
                                "capacity": 30 + i * 5,
                                "registration_count": 10 + i,
                                "type": "Exhibition" if i % 2 == 0 else "Workshop",
                            },
                            created_at=datetime.now() - timedelta(days=i),
                        )
                    )
            elif "artwork" in data_source:
                for i in range(min(limit, 5)):
                    records.append(
                        SoftrRecord(
                            id=f"artwork-{i + 1}",
                            data_source=data_source,
                            fields={
                                "title": f"Artwork {i + 1}",
                                "artist": f"Artist {i + 1}",
                                "medium": (
                                    "Oil on Canvas" if i % 2 == 0 else "Mixed Media"
                                ),
                                "dimensions": f"{30 + i * 5}cm x {40 + i * 5}cm",
                                "price": 500 + i * 100,
                                "status": "available" if i < 3 else "sold",
                            },
                            created_at=datetime.now() - timedelta(days=i),
                        )
                    )
            elif "member" in data_source:
                for i in range(min(limit, 5)):
                    records.append(
                        SoftrRecord(
                            id=f"member-{i + 1}",
                            data_source=data_source,
                            fields={
                                "name": f"Member {i + 1}",
                                "email": f"member{i + 1}@example.com",
                                "membership_type": ["Gold", "Silver", "Bronze"][i % 3],
                                "join_date": (
                                    datetime.now() - timedelta(days=i * 30)
                                ).isoformat(),
                                "status": "active",
                            },
                            created_at=datetime.now() - timedelta(days=i),
                        )
                    )

            # Apply simple filtering if filter expression is provided
            if filter_expr:
                try:
                    key, value = filter_expr.split("=")
                    records = [
                        r
                        for r in records
                        if key in r.fields and str(r.fields[key]) == value
                    ]
                except ValueError:
                    logger.warning(f"Invalid filter expression: {filter_expr}")

            return records
        except Exception as e:
            logger.error(f"Error getting Softr records: {e}")
            return []

    async def create_softr_record(
        self,
        data_source: str,
        fields: Dict[str, Any],
        notion_page_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a new record in a Softr data source.

        Args:
            data_source: Data source name/ID
            fields: Record fields as key-value pairs
            notion_page_id: Notion page ID for reference

        Returns:
            Record ID if successful, None otherwise
        """
        try:
            # In a real implementation, this would use the MCP tool
            # For now, we'll log the request and return a placeholder
            logger.info(f"Creating Softr record in {data_source}")

            # Simulate creating a record and returning an ID
            record_id = f"record-{hash(str(fields)) % 10000}"

            return record_id
        except Exception as e:
            logger.error(f"Error creating Softr record: {e}")
            return None

    # Helper methods for data mapping
    async def _store_wp_notion_mapping(self, wp_id: int, notion_page_id: str) -> bool:
        """
        Store a mapping between WordPress post ID and Notion page ID.

        Args:
            wp_id: WordPress post ID
            notion_page_id: Notion page ID

        Returns:
            True if mapping stored successfully, False otherwise
        """
        try:
            # Import the correct notion service
            try:
                from services.notion_service import NotionService

                # Get the Notion service instance
                notion_service = NotionService()
            except ImportError:
                logger.error("NotionService could not be imported")
                return False

            # Save the mapping in a designated Notion database
            mapping_data = {
                "WordPress ID": {"number": wp_id},
                "Content Type": {"select": {"name": "Post"}},
                "Sync Status": {"select": {"name": "Synced"}},
                "Last Synced": {"date": {"start": datetime.now().isoformat()}},
            }

            # Find the mapping database ID - assuming there's a database called "WordPress Content Mapping"
            # Try to find the mapping database
            try:
                # Find the mapping database ID - assuming there's a database called "WordPress Content Mapping"
                database_id = await notion_service.find_database_by_name(
                    "WordPress Content Mapping"
                )

                if not database_id:
                    # If the database doesn't exist, create it
                    logger.info("Creating WordPress Content Mapping database in Notion")
                    database_id = await notion_service.create_database(
                        "WordPress Content Mapping",
                        {
                            "WordPress ID": {"number": {}},
                            "Content Type": {
                                "select": {
                                    "options": [
                                        {"name": "Post"},
                                        {"name": "Page"},
                                        {"name": "Wellness Offering"},
                                    ]
                                }
                            },
                            "Sync Status": {
                                "select": {
                                    "options": [
                                        {"name": "Synced"},
                                        {"name": "Pending"},
                                        {"name": "Error"},
                                    ]
                                }
                            },
                            "Last Synced": {"date": {}},
                        },
                    )

                    if not database_id:
                        logger.error(
                            "Failed to create WordPress Content Mapping database"
                        )
                        return False
            except Exception as db_error:
                logger.error(
                    f"Error finding/creating WordPress Content Mapping database: {db_error}"
                )
                return False

            # Save the mapping
            try:
                await notion_service.create_page(
                    database_id, mapping_data, page_id=notion_page_id
                )
                return True
            except Exception as page_error:
                logger.error(f"Error creating mapping page in Notion: {page_error}")
                return False
        except Exception as e:
            logger.error(f"Error storing WordPress to Notion mapping: {e}")
            return False

    async def get_wellness_offerings(
        self,
        status: str = "publish",
        category: Optional[str] = None,
        limit: int = 10,
        page: int = 1,
    ) -> List[Dict[str, Any]]:
        """
        Get wellness offerings from The 7 Space website.

        Args:
            status: Content status (publish, draft, etc.)
            category: Optional category filter (yoga, meditation, etc.)
            limit: Number of offerings to retrieve
            page: Page number

        Returns:
            List of wellness offering dictionaries
        """
        try:
            # Use the WordPress posts endpoint with 'wellness_offering' post type
            offerings = await self.get_wordpress_posts(
                post_type="wellness_offering", status=status, limit=limit, page=page
            )

            # Process the offerings to include specialized wellness fields
            result = []
            for offering in offerings:
                # Convert to dictionary for easier manipulation
                offering_dict = offering.dict()

                # Add any additional processing specific to wellness offerings
                # This would typically involve getting custom fields from the WordPress API

                result.append(offering_dict)

            return result
        except Exception as e:
            logger.error(f"Error getting wellness offerings: {e}")
            return []

    async def create_wellness_offering(
        self,
        title: str,
        description: str,
        offering_type: str,
        duration: int,
        price: float,
        practitioner_ids: List[int],
        status: str = "draft",
        notion_page_id: Optional[str] = None,
    ) -> Optional[int]:
        """
        Create a new wellness offering on The 7 Space website.

        Args:
            title: Offering title
            description: Offering description
            offering_type: Type of wellness offering (yoga, meditation, etc.)
            duration: Duration in minutes
            price: Price in dollars
            practitioner_ids: List of practitioner IDs
            status: Content status (draft, publish)
            notion_page_id: Optional Notion page ID for mapping

        Returns:
            Offering ID if successful, None otherwise
        """
        try:
            # Create a WordPress post with 'wellness_offering' post type
            post = WordPressPost(
                title=str(title),
                content=str(description),
                post_type="wellness_offering",
                status=str(status),
                notion_page_id=notion_page_id,
            )

            # Create the base post
            post_id = await self.create_wordpress_post(post)

            if not post_id:
                return None

            # Use the MCP tool to update custom fields for the wellness offering
            from services.integration_manager import IntegrationManager

            integration_manager = IntegrationManager()
            # Get the MCP server using the appropriate method
            mcp_server = None

            # Try different methods to get the MCP server
            if hasattr(integration_manager, "find_mcp_server"):
                mcp_server = await integration_manager.find_mcp_server(
                    "the7space-mcp-integration"
                )
            elif hasattr(integration_manager, "get_mcp_server"):
                mcp_server = await integration_manager.get_mcp_server(
                    "the7space-mcp-integration"
                )
            else:
                # If neither method exists, log an error
                logger.error("No method available to get MCP server")

            if not mcp_server:
                logger.error("MCP server 'the7space-mcp-integration' not found")
                return (
                    post_id  # Return the post ID anyway, as the base post was created
                )

            # Ensure all values are the correct type
            clean_practitioner_ids = [int(pid) for pid in practitioner_ids]

            # Update custom fields
            custom_fields = {
                "offering_type": str(offering_type),
                "duration": int(duration),
                "price": float(price),
                "practitioner_ids": clean_practitioner_ids,
            }

            # Call a custom tool to update ACF fields (this would need to be implemented in the MCP server)
            try:
                await mcp_server.call_tool(
                    "update_wp_custom_fields",
                    {"post_id": int(post_id), "fields": custom_fields},
                )
            except Exception as acf_error:
                # Log the error but continue since the base post was created
                logger.error(
                    f"Error updating custom fields for wellness offering: {acf_error}"
                )

            logger.info(
                f"Created wellness offering on The 7 Space website with ID: {post_id}"
            )
            return post_id
        except Exception as e:
            logger.error(f"Error creating wellness offering: {e}")
            return None
