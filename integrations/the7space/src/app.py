"""
The 7 Space Integration Application
Connects Softr interfaces with the Higher Self Network server
Acts as the central backend for The 7 Space Art Gallery & Wellness Center
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from api.higherself_network_api import HigherSelfNetworkAPI, create_api_client
from models.softr_integration_models import (ApiResponse, ArtPurchaseRequest,
                                             ArtPurchaseResponse,
                                             ArtworkListRequest,
                                             ArtworkListResponse,
                                             EmailSubscriptionRequest,
                                             EventListRequest,
                                             EventListResponse,
                                             ServiceBookingRequest,
                                             ServiceBookingResponse,
                                             SoftrIntegrationConfig,
                                             UserProfileData, WebhookPayload)

# Load environment variables
load_dotenv()

# Initialize Fast API app
app = FastAPI(
    title="The 7 Space Integration API",
    description="API for The 7 Space Art Gallery & Wellness Center",
    version="1.0.0",
)

# Configure CORS to allow Softr requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific Softr domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logger.add("logs/app.log", rotation="500 MB", level="INFO")


# Create API client dependency
async def get_api_client() -> HigherSelfNetworkAPI:
    """Dependency to get the Higher Self Network API client"""
    config = SoftrIntegrationConfig(
        server_api_endpoint=os.getenv("HIGHERSELF_SERVER_API_ENDPOINT"),
        api_key=os.getenv("HIGHERSELF_API_KEY"),
        webhook_secret=os.getenv("HIGHERSELF_WEBHOOK_SECRET"),
        softr_site_id=os.getenv("HIGHERSELF_SOFTR_SITE_ID"),
    )
    return create_api_client(config)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "The 7 Space Integration API",
        "version": "1.0.0",
        "status": "active",
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }


@app.post("/webhooks/softr", response_model=ApiResponse)
async def handle_softr_webhook(
    request: Request,
    x_softr_signature: Optional[str] = Header(None),
    api_client: HigherSelfNetworkAPI = Depends(get_api_client),
):
    """
    Handle incoming webhooks from Softr

    Args:
        request: FastAPI request object
        x_softr_signature: Webhook signature for verification
        api_client: Higher Self Network API client

    Returns:
        API response object
    """
    if not x_softr_signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")

    # Get request body
    payload = await request.json()
    logger.info(f"Received webhook: {json.dumps(payload)[:200]}...")

    # Process webhook
    try:
        response = await api_client.handle_webhook(payload, x_softr_signature)
        return response
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return ApiResponse(
            success=False,
            message=f"Error processing webhook: {str(e)}",
            errors=[{"code": "PROCESSING_ERROR", "message": str(e)}],
        )


@app.get("/artworks", response_model=ArtworkListResponse)
async def list_artworks(
    request: ArtworkListRequest = Depends(),
    api_client: HigherSelfNetworkAPI = Depends(get_api_client),
):
    """
    List artworks with filtering and pagination

    Args:
        request: Artwork list request parameters
        api_client: Higher Self Network API client

    Returns:
        Paginated list of artworks
    """
    try:
        data = await api_client.get_data_collection(
            collection_name="artworks",
            page=request.page,
            limit=request.limit,
            filters=request.filters,
            sort_by=request.sort_by,
            sort_direction=request.sort_direction,
        )

        return ArtworkListResponse(
            items=data.get("items", []),
            total=data.get("total", 0),
            page=data.get("page", request.page),
            limit=data.get("limit", request.limit),
            has_more=data.get("has_more", False),
        )
    except Exception as e:
        logger.error(f"Error listing artworks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events", response_model=EventListResponse)
async def list_events(
    request: EventListRequest = Depends(),
    api_client: HigherSelfNetworkAPI = Depends(get_api_client),
):
    """
    List events with filtering and pagination

    Args:
        request: Event list request parameters
        api_client: Higher Self Network API client

    Returns:
        Paginated list of events
    """
    try:
        # Build filters based on request parameters
        filters = {}
        if request.start_date:
            filters["start_date"] = {"$gte": request.start_date.isoformat()}
        if request.end_date:
            filters["end_date"] = {"$lte": request.end_date.isoformat()}
        if request.event_type:
            filters["event_type"] = {"$in": request.event_type}

        data = await api_client.get_data_collection(
            collection_name="events",
            page=request.page,
            limit=request.limit,
            filters=filters,
            sort_by=request.sort_by or "start_date",
            sort_direction=request.sort_direction or "asc",
        )

        return EventListResponse(
            items=data.get("items", []),
            total=data.get("total", 0),
            page=data.get("page", request.page),
            limit=data.get("limit", request.limit),
            has_more=data.get("has_more", False),
        )
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/artworks/{artwork_id}", response_model=Dict[str, Any])
async def get_artwork(
    artwork_id: str, api_client: HigherSelfNetworkAPI = Depends(get_api_client)
):
    """
    Get details for a specific artwork

    Args:
        artwork_id: Artwork identifier
        api_client: Higher Self Network API client

    Returns:
        Artwork details
    """
    try:
        artwork = await api_client.get_artwork_details(artwork_id)
        if not artwork:
            raise HTTPException(
                status_code=404, detail=f"Artwork {artwork_id} not found"
            )
        return artwork
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting artwork {artwork_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/events/{event_id}", response_model=Dict[str, Any])
async def get_event(
    event_id: str, api_client: HigherSelfNetworkAPI = Depends(get_api_client)
):
    """
    Get details for a specific event

    Args:
        event_id: Event identifier
        api_client: Higher Self Network API client

    Returns:
        Event details
    """
    try:
        event = await api_client.get_event_details(event_id)
        if not event:
            raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
        return event
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting event {event_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/services/{service_id}", response_model=Dict[str, Any])
async def get_service(
    service_id: str, api_client: HigherSelfNetworkAPI = Depends(get_api_client)
):
    """
    Get details for a specific wellness service

    Args:
        service_id: Service identifier
        api_client: Higher Self Network API client

    Returns:
        Service details
    """
    try:
        service = await api_client.get_service_details(service_id)
        if not service:
            raise HTTPException(
                status_code=404, detail=f"Service {service_id} not found"
            )
        return service
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bookings", response_model=ServiceBookingResponse)
async def create_booking(
    booking_request: ServiceBookingRequest,
    api_client: HigherSelfNetworkAPI = Depends(get_api_client),
):
    """
    Create a new service booking

    Args:
        booking_request: Booking details
        api_client: Higher Self Network API client

    Returns:
        Created booking details
    """
    try:
        booking_data = booking_request.dict()
        response = await api_client.create_booking(booking_data)
        return ServiceBookingResponse(**response)
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/purchases", response_model=ArtPurchaseResponse)
async def create_purchase(
    purchase_request: ArtPurchaseRequest,
    api_client: HigherSelfNetworkAPI = Depends(get_api_client),
):
    """
    Create a new art purchase

    Args:
        purchase_request: Purchase details
        api_client: Higher Self Network API client

    Returns:
        Created purchase details with payment link
    """
    try:
        purchase_data = purchase_request.dict()
        response = await api_client.create_purchase(purchase_data)
        return ArtPurchaseResponse(**response)
    except Exception as e:
        logger.error(f"Error creating purchase: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/subscribe", response_model=ApiResponse)
async def email_subscribe(
    subscription: EmailSubscriptionRequest,
    api_client: HigherSelfNetworkAPI = Depends(get_api_client),
):
    """
    Subscribe to email notifications

    Args:
        subscription: Subscription details
        api_client: Higher Self Network API client

    Returns:
        API response
    """
    try:
        # Trigger email subscription workflow
        await api_client.trigger_workflow(
            request={
                "workflow_id": "email_subscription_workflow",
                "trigger_event": "email_subscription",
                "trigger_data": subscription.dict(),
                "source": "the7space_website",
            }
        )

        return ApiResponse(
            success=True,
            message="Subscription successful",
            data={"email": subscription.email},
        )
    except Exception as e:
        logger.error(f"Error subscribing email: {e}")
        return ApiResponse(
            success=False,
            message=f"Subscription failed: {str(e)}",
            errors=[{"code": "SUBSCRIPTION_ERROR", "message": str(e)}],
        )


@app.get("/user/{user_id}", response_model=UserProfileData)
async def get_user_profile(
    user_id: str, api_client: HigherSelfNetworkAPI = Depends(get_api_client)
):
    """
    Get user profile data

    Args:
        user_id: User identifier
        api_client: Higher Self Network API client

    Returns:
        User profile data
    """
    try:
        user = await api_client.get_user_profile(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard/{dashboard_type}", response_model=Dict[str, Any])
async def get_dashboard_data(
    dashboard_type: str, api_client: HigherSelfNetworkAPI = Depends(get_api_client)
):
    """
    Get data for specific dashboard type

    Args:
        dashboard_type: Type of dashboard (sales, inventory, events, etc.)
        api_client: Higher Self Network API client

    Returns:
        Dashboard data structure
    """
    valid_types = ["sales", "inventory", "events", "wellness", "clients"]
    if dashboard_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dashboard type. Must be one of: {', '.join(valid_types)}",
        )

    try:
        # Get all required data collections for this dashboard type
        data = {}

        if dashboard_type == "sales":
            data["sales_summary"] = await api_client.get_data_collection(
                "sales_summary"
            )
            data["sales_by_month"] = await api_client.get_data_collection(
                "sales_by_month"
            )
            data["sales_by_category"] = await api_client.get_data_collection(
                "sales_by_category"
            )
            data["recent_sales"] = await api_client.get_data_collection("recent_sales")

        elif dashboard_type == "inventory":
            data["inventory_summary"] = await api_client.get_data_collection(
                "inventory_summary"
            )
            data["inventory_by_medium"] = await api_client.get_data_collection(
                "inventory_by_medium"
            )
            data["inventory_by_status"] = await api_client.get_data_collection(
                "inventory_by_status"
            )
            data["inventory_by_price_range"] = await api_client.get_data_collection(
                "inventory_by_price_range"
            )
            data["recent_acquisitions"] = await api_client.get_data_collection(
                "recent_acquisitions"
            )

        elif dashboard_type == "events":
            data["events_summary"] = await api_client.get_data_collection(
                "events_summary"
            )
            data["events"] = await api_client.get_data_collection("events")
            data["events_by_type"] = await api_client.get_data_collection(
                "events_by_type"
            )
            data["attendance_by_month"] = await api_client.get_data_collection(
                "attendance_by_month"
            )

        elif dashboard_type == "wellness":
            data["wellness_summary"] = await api_client.get_data_collection(
                "wellness_summary"
            )
            data["bookings"] = await api_client.get_data_collection("bookings")
            data["services_by_popularity"] = await api_client.get_data_collection(
                "services_by_popularity"
            )
            data["bookings_by_hour"] = await api_client.get_data_collection(
                "bookings_by_hour"
            )

        elif dashboard_type == "clients":
            data["client_summary"] = await api_client.get_data_collection(
                "client_summary"
            )
            data["client_acquisition_by_month"] = await api_client.get_data_collection(
                "client_acquisition_by_month"
            )
            data["client_interests"] = await api_client.get_data_collection(
                "client_interests"
            )
            data["top_clients"] = await api_client.get_data_collection("top_clients")

        return {
            "dashboard_type": dashboard_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

    except Exception as e:
        logger.error(f"Error getting {dashboard_type} dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the FastAPI application using Uvicorn
    uvicorn.run(
        "app:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENV", "development") == "development",
    )
