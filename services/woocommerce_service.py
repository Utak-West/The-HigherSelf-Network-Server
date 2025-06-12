"""
WooCommerce integration service for The HigherSelf Network Server.
This service handles integration with WooCommerce while maintaining Notion as the central hub.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, cast

from loguru import logger
from pydantic import BaseModel, Field, field_validator

# Import WooCommerce API but wrapped for async usage
from woocommerce import API as SyncAPI

# Import base service class
from services.base_service import BaseService, ServiceCredentials


class WooCommerceCredentials(ServiceCredentials):
    """Configuration for WooCommerce API integration."""
    url: str
    consumer_key: str
    consumer_secret: str
    version: str = "wc/v3"
    webhook_secret: Optional[str] = None

    class Config:
        env_prefix = "WOOCOMMERCE_"

@field_validator('url', 'consumer_key', 'consumer_secret', mode='before')
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError("This field is required")
        return v


class WooProduct(BaseModel):
    """Model representing a WooCommerce product."""
    id: Optional[int] = None
    name: str
    type: str = "simple"
    status: str = "publish"
    regular_price: str
    description: str
    short_description: Optional[str] = None
    categories: List[Dict[str, Any]] = Field(default_factory=list)
    images: List[Dict[str, Any]] = Field(default_factory=list)
    meta_data: List[Dict[str, Any]] = Field(default_factory=list)
    notion_page_id: Optional[str] = None

@field_validator('name', mode='before')
    def validate_name(cls, v):
        if not v or len(v) < 3:
            raise ValueError("Product name must be at least 3 characters")
        return v

@field_validator('regular_price', mode='before')
    def validate_price(cls, v):
        if not v:
            raise ValueError("Price is required")
        try:
            float(v)
        except ValueError:
            raise ValueError("Price must be a valid number")
        return v


class WooOrder(BaseModel):
    """Model representing a WooCommerce order."""
    id: Optional[int] = None
    status: str
    date_created: datetime
    customer_id: int
    customer_note: Optional[str] = None
    billing: Dict[str, Any] = Field(default_factory=dict)
    shipping: Dict[str, Any] = Field(default_factory=dict)
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    total: str
    payment_method: str
    payment_method_title: str
    meta_data: List[Dict[str, Any]] = Field(default_factory=list)
    notion_page_id: Optional[str] = None


class WooCustomer(BaseModel):
    """Model representing a WooCommerce customer."""
    id: Optional[int] = None
    email: str
    first_name: str
    last_name: str
    username: Optional[str] = None
    billing: Dict[str, Any] = Field(default_factory=dict)
    shipping: Dict[str, Any] = Field(default_factory=dict)
    meta_data: List[Dict[str, Any]] = Field(default_factory=list)
    notion_page_id: Optional[str] = None


class AsyncWooCommerceAPI:
    """Async wrapper around the WooCommerce API."""

    def __init__(self, url: str, consumer_key: str, consumer_secret: str, version: str = "wc/v3", timeout: int = 30):
        """
        Initialize the async WooCommerce API wrapper.

        Args:
            url: WooCommerce store URL
            consumer_key: WooCommerce API consumer key
            consumer_secret: WooCommerce API consumer secret
            version: WooCommerce API version
            timeout: Request timeout in seconds
        """
        self.sync_client = SyncAPI(
            url=url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version=version,
            timeout=timeout
        )

    async def get(self, endpoint: str, **kwargs) -> Any:
        """Perform an async GET request."""
        return await asyncio.to_thread(self.sync_client.get, endpoint, **kwargs)

    async def post(self, endpoint: str, data: Dict[str, Any], **kwargs) -> Any:
        """Perform an async POST request."""
        return await asyncio.to_thread(self.sync_client.post, endpoint, data, **kwargs)

    async def put(self, endpoint: str, data: Dict[str, Any], **kwargs) -> Any:
        """Perform an async PUT request."""
        return await asyncio.to_thread(self.sync_client.put, endpoint, data, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> Any:
        """Perform an async DELETE request."""
        return await asyncio.to_thread(self.sync_client.delete, endpoint, **kwargs)


class WooCommerceService(BaseService):
    """
    Service for interacting with WooCommerce.
    Ensures all data is synchronized with Notion as the central hub.
    """

    def __init__(self, url: str = None, consumer_key: str = None, consumer_secret: str = None, version: str = None):
        """
        Initialize the WooCommerce service.

        Args:
            url: WooCommerce store URL
            consumer_key: WooCommerce API consumer key
            consumer_secret: WooCommerce API consumer secret
            version: WooCommerce API version
        """
        # Get credentials from environment if not provided
        url = url or os.environ.get("WOOCOMMERCE_URL")
        consumer_key = consumer_key or os.environ.get("WOOCOMMERCE_CONSUMER_KEY")
        consumer_secret = consumer_secret or os.environ.get("WOOCOMMERCE_CONSUMER_SECRET")
        version = version or os.environ.get("WOOCOMMERCE_VERSION", "wc/v3")
        webhook_secret = os.environ.get("WOOCOMMERCE_WEBHOOK_SECRET")

        # Create credentials object
        credentials = None
        if url and consumer_key and consumer_secret:
            credentials = WooCommerceCredentials(
                service_name="woocommerce",
                url=url,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                version=version,
                webhook_secret=webhook_secret
            )

        # Initialize base service
        super().__init__(service_name="woocommerce", credentials=credentials)

        # Specific WooCommerce properties
        self.url = url
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.version = version
        self.client = None

        if not self.url or not self.consumer_key or not self.consumer_secret:
            logger.warning("WooCommerce credentials not fully configured")
        else:
            try:
                self.client = AsyncWooCommerceAPI(
                    url=self.url,
                    consumer_key=self.consumer_key,
                    consumer_secret=self.consumer_secret,
                    version=self.version,
                    timeout=30
                )
                logger.info("WooCommerce client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing WooCommerce client: {e}")

    async def validate_connection(self) -> bool:
        """
        Validate the WooCommerce API connection.

        Returns:
            True if connection is valid, False otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return False

        try:
            # Test connection by making a simple API call (now using async)
            response = await self.client.get("system_status")

            # Update credentials verification timestamp
            if self.credentials:
                self.credentials.last_verified = datetime.now()

            logger.info("WooCommerce connection validated successfully")
            return True
        except Exception as e:
            logger.error(f"Error validating WooCommerce connection: {e}")
            return False

    async def get_product(self, product_id: int) -> Optional[WooProduct]:
        """
        Get a product from WooCommerce by ID.

        Args:
            product_id: WooCommerce product ID

        Returns:
            WooProduct if found, None otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return None

        try:
            # Use async client
            data = await self.client.get(f"products/{product_id}")

            # Extract Notion page ID from meta data if it exists
            notion_page_id = None
            for meta in data.get("meta_data", []):
                if meta.get("key") == "notion_page_id":
                    notion_page_id = meta.get("value")

            product = WooProduct(
                id=data.get("id"),
                name=data.get("name"),
                type=data.get("type"),
                status=data.get("status"),
                regular_price=data.get("regular_price", "0"),
                description=data.get("description", ""),
                short_description=data.get("short_description", ""),
                categories=data.get("categories", []),
                images=data.get("images", []),
                meta_data=data.get("meta_data", []),
                notion_page_id=notion_page_id
            )
            return product
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return None

    async def create_product(self, product: WooProduct) -> Optional[int]:
        """
        Create a new product in WooCommerce.

        Args:
            product: WooProduct model with product details

        Returns:
            Product ID if successful, None otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return None

        try:
            # Validate product data first
            self.validate_model(product)

            # Prepare product data
            product_data = {
                "name": product.name,
                "type": product.type,
                "regular_price": product.regular_price,
                "description": product.description,
                "status": product.status,
            }

            if product.short_description:
                product_data["short_description"] = product.short_description

            if product.categories:
                product_data["categories"] = product.categories

            if product.images:
                product_data["images"] = product.images

            # Add meta data including Notion page ID if available
            meta_data = []
            for meta in product.meta_data:
                meta_data.append(meta)

            if product.notion_page_id:
                meta_data.append({
                    "key": "notion_page_id",
                    "value": product.notion_page_id
                })

                # Also add a metadata field to indicate this is managed by Notion
                meta_data.append({
                    "key": "notion_managed",
                    "value": "true"
                })

                # Add sync timestamp
                meta_data.append({
                    "key": "notion_sync_time",
                    "value": datetime.now().isoformat()
                })

            if meta_data:
                product_data["meta_data"] = meta_data

            # Use async client
            data = await self.client.post("products", product_data)

            product_id = data.get("id")
            logger.info(f"Created WooCommerce product: {product_id}")
            return product_id
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error creating product: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            return None

    async def update_product(self, product_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update a product in WooCommerce.

        Args:
            product_id: WooCommerce product ID
            update_data: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return False

        try:
            response = self.client.put(f"products/{product_id}", update_data)

            if response.status_code in (200, 201):
                logger.info(f"Updated WooCommerce product: {product_id}")
                return True
            else:
                logger.error(f"Error updating product {product_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            return False

    async def sync_product_to_notion(self, product_id: int, notion_page_id: str) -> bool:
        """
        Update the WooCommerce product with its associated Notion page ID.

        Args:
            product_id: WooCommerce product ID
            notion_page_id: Notion page ID

        Returns:
            True if sync successful, False otherwise
        """
        update_data = {
            "meta_data": [
                {
                    "key": "notion_page_id",
                    "value": notion_page_id
                },
                {
                    "key": "synced_to_notion",
                    "value": "true"
                },
                {
                    "key": "notion_sync_time",
                    "value": datetime.now().isoformat()
                }
            ]
        }

        return await self.update_product(product_id, update_data)

    async def get_order(self, order_id: int) -> Optional[WooOrder]:
        """
        Get an order from WooCommerce by ID.

        Args:
            order_id: WooCommerce order ID

        Returns:
            WooOrder if found, None otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return None

        try:
            response = self.client.get(f"orders/{order_id}")

            if response.status_code == 200:
                data = response.json()

                # Extract Notion page ID from meta data if it exists
                notion_page_id = None
                for meta in data.get("meta_data", []):
                    if meta.get("key") == "notion_page_id":
                        notion_page_id = meta.get("value")

                order = WooOrder(
                    id=data.get("id"),
                    status=data.get("status"),
                    date_created=datetime.fromisoformat(data.get("date_created").replace("Z", "+00:00")),
                    customer_id=data.get("customer_id"),
                    customer_note=data.get("customer_note", ""),
                    billing=data.get("billing", {}),
                    shipping=data.get("shipping", {}),
                    line_items=data.get("line_items", []),
                    total=data.get("total", "0"),
                    payment_method=data.get("payment_method", ""),
                    payment_method_title=data.get("payment_method_title", ""),
                    meta_data=data.get("meta_data", []),
                    notion_page_id=notion_page_id
                )
                return order
            else:
                logger.error(f"Error getting order {order_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return None

    async def update_order(self, order_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update an order in WooCommerce.

        Args:
            order_id: WooCommerce order ID
            update_data: Dictionary of fields to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return False

        try:
            response = self.client.put(f"orders/{order_id}", update_data)

            if response.status_code in (200, 201):
                logger.info(f"Updated WooCommerce order: {order_id}")
                return True
            else:
                logger.error(f"Error updating order {order_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False

    async def sync_order_to_notion(self, order_id: int, notion_page_id: str) -> bool:
        """
        Update the WooCommerce order with its associated Notion page ID.

        Args:
            order_id: WooCommerce order ID
            notion_page_id: Notion page ID

        Returns:
            True if sync successful, False otherwise
        """
        update_data = {
            "meta_data": [
                {
                    "key": "notion_page_id",
                    "value": notion_page_id
                },
                {
                    "key": "synced_to_notion",
                    "value": "true"
                },
                {
                    "key": "notion_sync_time",
                    "value": datetime.now().isoformat()
                }
            ]
        }

        return await self.update_order(order_id, update_data)

    async def get_recent_orders(self, limit: int = 10) -> List[WooOrder]:
        """
        Get recent orders from WooCommerce.

        Args:
            limit: Maximum number of orders to retrieve

        Returns:
            List of WooOrder objects
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return []

        try:
            response = self.client.get("orders", params={"per_page": limit, "orderby": "date", "order": "desc"})

            if response.status_code == 200:
                data = response.json()
                orders = []

                for item in data:
                    try:
                        # Extract Notion page ID from meta data if it exists
                        notion_page_id = None
                        for meta in item.get("meta_data", []):
                            if meta.get("key") == "notion_page_id":
                                notion_page_id = meta.get("value")

                        order = WooOrder(
                            id=item.get("id"),
                            status=item.get("status"),
                            date_created=datetime.fromisoformat(item.get("date_created").replace("Z", "+00:00")),
                            customer_id=item.get("customer_id"),
                            customer_note=item.get("customer_note", ""),
                            billing=item.get("billing", {}),
                            shipping=item.get("shipping", {}),
                            line_items=item.get("line_items", []),
                            total=item.get("total", "0"),
                            payment_method=item.get("payment_method", ""),
                            payment_method_title=item.get("payment_method_title", ""),
                            meta_data=item.get("meta_data", []),
                            notion_page_id=notion_page_id
                        )
                        orders.append(order)
                    except Exception as e:
                        logger.error(f"Error parsing order data: {e}")

                return orders
            else:
                logger.error(f"Error getting recent orders: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting recent orders: {e}")
            return []

    async def get_customer(self, customer_id: int) -> Optional[WooCustomer]:
        """
        Get a customer from WooCommerce by ID.

        Args:
            customer_id: WooCommerce customer ID

        Returns:
            WooCustomer if found, None otherwise
        """
        if not self.client:
            logger.error("WooCommerce client not initialized")
            return None

        try:
            response = self.client.get(f"customers/{customer_id}")

            if response.status_code == 200:
                data = response.json()

                # Extract Notion page ID from meta data if it exists
                notion_page_id = None
                for meta in data.get("meta_data", []):
                    if meta.get("key") == "notion_page_id":
                        notion_page_id = meta.get("value")

                customer = WooCustomer(
                    id=data.get("id"),
                    email=data.get("email"),
                    first_name=data.get("first_name"),
                    last_name=data.get("last_name"),
                    username=data.get("username"),
                    billing=data.get("billing", {}),
                    shipping=data.get("shipping", {}),
                    meta_data=data.get("meta_data", []),
                    notion_page_id=notion_page_id
                )
                return customer
            else:
                logger.error(f"Error getting customer {customer_id}: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}")
            return None

    async def sync_customer_to_notion(self, customer_id: int, notion_page_id: str) -> bool:
        """
        Update the WooCommerce customer with their associated Notion page ID.

        Args:
            customer_id: WooCommerce customer ID
            notion_page_id: Notion page ID

        Returns:
            True if sync successful, False otherwise
        """
        update_data = {
            "meta_data": [
                {
                    "key": "notion_page_id",
                    "value": notion_page_id
                },
                {
                    "key": "synced_to_notion",
                    "value": "true"
                },
                {
                    "key": "notion_sync_time",
                    "value": datetime.now().isoformat()
                }
            ]
        }

        if not self.client:
            logger.error("WooCommerce client not initialized")
            return False

        try:
            response = self.client.put(f"customers/{customer_id}", update_data)

            if response.status_code in (200, 201):
                logger.info(f"Updated WooCommerce customer: {customer_id}")
                return True
            else:
                logger.error(f"Error updating customer {customer_id}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            return False

    async def process_order_webhook(self, payload: Dict[str, Any]) -> Optional[WooOrder]:
        """
        Process a webhook notification from WooCommerce for order creation/updates.

        Args:
            payload: Webhook payload

        Returns:
            WooOrder if valid, None otherwise
        """
        try:
            # Extract order data from payload
            order_data = payload.get("order", {})
            if not order_data:
                logger.error("Invalid webhook payload: missing order data")
                return None

            # Basic payload validation
            required_fields = ["id", "status", "date_created", "customer_id"]
            for field in required_fields:
                if field not in order_data:
                    logger.error(f"Invalid webhook payload: missing required field {field}")
                    return None

            # Extract Notion page ID from meta data if it exists
            notion_page_id = None
            for meta in order_data.get("meta_data", []):
                if meta.get("key") == "notion_page_id":
                    notion_page_id = meta.get("value")

            # Create WooOrder model
            order = WooOrder(
                id=order_data.get("id"),
                status=order_data.get("status"),
                date_created=datetime.fromisoformat(order_data.get("date_created").replace("Z", "+00:00")),
                customer_id=order_data.get("customer_id"),
                customer_note=order_data.get("customer_note", ""),
                billing=order_data.get("billing", {}),
                shipping=order_data.get("shipping", {}),
                line_items=order_data.get("line_items", []),
                total=order_data.get("total", "0"),
                payment_method=order_data.get("payment_method", ""),
                payment_method_title=order_data.get("payment_method_title", ""),
                meta_data=order_data.get("meta_data", []),
                notion_page_id=notion_page_id
            )

            logger.info(f"Processed WooCommerce order webhook for order {order.id}")
            return order
        except Exception as e:
            logger.error(f"Error processing order webhook: {e}")
            return None
