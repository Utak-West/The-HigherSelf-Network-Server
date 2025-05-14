"""
Higher Self Network Server API Integration for Softr interfaces.
This module provides the core connectivity between Softr and the Higher Self Network.
Follows the centralized deployment principles specified in The HigherSelf Network guidelines.
"""
import os
import requests
import json
import hmac
import hashlib
import time
from typing import Dict, List, Optional, Any, Union, Type, TypeVar
from datetime import datetime
from loguru import logger
from pydantic import BaseModel

from ..models.softr_integration_models import (
    SoftrIntegrationConfig, ApiResponse, WebhookPayload,
    UserProfileData, WorkflowTriggerRequest
)

T = TypeVar('T', bound=BaseModel)


class HigherSelfNetworkAPI:
    """
    Client for the Higher Self Network Server API.
    Handles all interactions between Softr interfaces and the backend server.
    """
    
    def __init__(self, config: SoftrIntegrationConfig):
        """
        Initialize the API client with configuration.
        
        Args:
            config: Configuration object for Higher Self Network API
        """
        self.config = config
        self.base_url = config.server_api_endpoint
        self.api_key = config.api_key
        self.webhook_secret = config.webhook_secret
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-Softr-Site-Id': config.softr_site_id
        })
        
        # Validate connection
        try:
            self._test_connection()
            logger.info("Successfully connected to Higher Self Network API")
        except Exception as e:
            logger.error(f"Failed to connect to Higher Self Network API: {e}")
            raise ConnectionError(f"Failed to connect to Higher Self Network API: {e}")
    
    def _test_connection(self) -> bool:
        """Test the API connection"""
        response = self.session.get(f"{self.base_url}/health")
        if response.status_code != 200:
            raise ConnectionError(f"API connection failed with status {response.status_code}")
        return True
    
    def _validate_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Validate webhook signature using HMAC.
        
        Args:
            payload: The raw payload data
            signature: The signature provided in the webhook header
            
        Returns:
            Whether the signature is valid
        """
        payload_str = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def handle_webhook(self, payload: Dict[str, Any], signature: str) -> ApiResponse:
        """
        Process incoming webhook from Softr.
        
        Args:
            payload: The webhook payload
            signature: The signature for verification
            
        Returns:
            API response with processing result
        """
        # Validate signature
        if not self._validate_webhook_signature(payload, signature):
            logger.warning("Invalid webhook signature received")
            return ApiResponse(
                success=False,
                message="Invalid signature",
                errors=[{"code": "INVALID_SIGNATURE", "message": "The webhook signature is invalid"}]
            )
        
        # Parse webhook payload
        try:
            webhook_data = WebhookPayload(**payload)
        except Exception as e:
            logger.error(f"Failed to parse webhook payload: {e}")
            return ApiResponse(
                success=False,
                message="Invalid payload format",
                errors=[{"code": "INVALID_PAYLOAD", "message": str(e)}]
            )
        
        # Process based on event type
        try:
            event_type = webhook_data.event_type
            logger.info(f"Processing webhook event: {event_type}")
            
            # Initialize workflow in the Higher Self Network
            workflow_request = WorkflowTriggerRequest(
                workflow_id=f"softr_{event_type.value}_workflow",
                trigger_event=event_type.value,
                trigger_data=webhook_data.data
            )
            
            # Call the workflow trigger endpoint
            response = await self.trigger_workflow(workflow_request)
            
            return ApiResponse(
                success=True,
                message=f"Successfully processed {event_type} webhook",
                data={"workflow_request": workflow_request.dict(), "response": response}
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return ApiResponse(
                success=False,
                message="Webhook processing error",
                errors=[{"code": "PROCESSING_ERROR", "message": str(e)}]
            )
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfileData]:
        """
        Retrieve user profile data from Higher Self Network.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile data if found
        """
        try:
            response = self.session.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return UserProfileData(**response.json())
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"User {user_id} not found")
                return None
            logger.error(f"HTTP error getting user profile: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise
    
    async def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> ApiResponse:
        """
        Update user profile in Higher Self Network.
        
        Args:
            user_id: User identifier
            data: Fields to update
            
        Returns:
            API response with result
        """
        try:
            response = self.session.patch(f"{self.base_url}/users/{user_id}", json=data)
            response.raise_for_status()
            return ApiResponse(**response.json())
        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            raise
    
    async def trigger_workflow(self, request: WorkflowTriggerRequest) -> Dict[str, Any]:
        """
        Trigger a workflow in the Higher Self Network.
        
        Args:
            request: Workflow trigger request
            
        Returns:
            Response data from the workflow system
        """
        try:
            response = self.session.post(
                f"{self.base_url}/workflows/trigger",
                json=request.dict()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            raise
    
    async def get_data_collection(
        self, 
        collection_name: str,
        page: int = 1,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve data collection from Higher Self Network.
        
        Args:
            collection_name: Name of the collection
            page: Page number for pagination
            limit: Items per page
            filters: Query filters
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)
            
        Returns:
            Collection data with pagination info
        """
        params = {
            "page": page,
            "limit": limit
        }
        
        if filters:
            params["filters"] = json.dumps(filters)
        
        if sort_by:
            params["sort_by"] = sort_by
            params["sort_direction"] = sort_direction or "asc"
        
        try:
            response = self.session.get(
                f"{self.base_url}/collections/{collection_name}",
                params=params
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting collection data: {e}")
            raise
    
    async def create_collection_item(
        self, 
        collection_name: str,
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new item in a collection.
        
        Args:
            collection_name: Name of the collection
            item_data: Data for the new item
            
        Returns:
            Created item data
        """
        try:
            response = self.session.post(
                f"{self.base_url}/collections/{collection_name}",
                json=item_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating collection item: {e}")
            raise
    
    async def update_collection_item(
        self,
        collection_name: str,
        item_id: str,
        item_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an item in a collection.
        
        Args:
            collection_name: Name of the collection
            item_id: ID of the item to update
            item_data: Updated data
            
        Returns:
            Updated item data
        """
        try:
            response = self.session.patch(
                f"{self.base_url}/collections/{collection_name}/{item_id}",
                json=item_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error updating collection item: {e}")
            raise
    
    async def get_artwork_details(self, artwork_id: str) -> Dict[str, Any]:
        """
        Get details for a specific artwork.
        
        Args:
            artwork_id: Artwork identifier
            
        Returns:
            Artwork details
        """
        return await self._get_resource("artworks", artwork_id)
    
    async def get_event_details(self, event_id: str) -> Dict[str, Any]:
        """
        Get details for a specific event.
        
        Args:
            event_id: Event identifier
            
        Returns:
            Event details
        """
        return await self._get_resource("events", event_id)
    
    async def get_service_details(self, service_id: str) -> Dict[str, Any]:
        """
        Get details for a specific wellness service.
        
        Args:
            service_id: Service identifier
            
        Returns:
            Service details
        """
        return await self._get_resource("services", service_id)
    
    async def create_booking(self, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new booking for a service.
        
        Args:
            booking_data: Booking information
            
        Returns:
            Created booking details
        """
        try:
            response = self.session.post(
                f"{self.base_url}/bookings",
                json=booking_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating booking: {e}")
            raise
    
    async def create_purchase(self, purchase_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new art purchase record.
        
        Args:
            purchase_data: Purchase information
            
        Returns:
            Created purchase details with payment link
        """
        try:
            response = self.session.post(
                f"{self.base_url}/purchases",
                json=purchase_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error creating purchase: {e}")
            raise
    
    async def _get_resource(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Generic method to get a resource by ID.
        
        Args:
            resource_type: Type of resource (artworks, events, etc.)
            resource_id: Resource identifier
            
        Returns:
            Resource details
        """
        try:
            response = self.session.get(f"{self.base_url}/{resource_type}/{resource_id}")
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"{resource_type.capitalize()} {resource_id} not found")
                return None
            logger.error(f"HTTP error getting {resource_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting {resource_type}: {e}")
            raise


def create_api_client(config: Optional[SoftrIntegrationConfig] = None) -> HigherSelfNetworkAPI:
    """
    Factory function to create the Higher Self Network API client.
    
    Args:
        config: Configuration object or None to load from environment
        
    Returns:
        Configured API client
    """
    if config is None:
        config = SoftrIntegrationConfig(
            server_api_endpoint=os.getenv("HIGHERSELF_SERVER_API_ENDPOINT"),
            api_key=os.getenv("HIGHERSELF_API_KEY"),
            webhook_secret=os.getenv("HIGHERSELF_WEBHOOK_SECRET"),
            softr_site_id=os.getenv("HIGHERSELF_SOFTR_SITE_ID")
        )
    
    return HigherSelfNetworkAPI(config)
