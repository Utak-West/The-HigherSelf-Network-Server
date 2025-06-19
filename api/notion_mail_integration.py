#!/usr/bin/env python3
"""
Notion Mail Integration API Endpoints

FastAPI endpoints for automated email classification and workflow automation
following established patterns from the HigherSelf Network Server.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

from config.testing_mode import is_api_disabled
from services.notion_mail_integration import (
    EmailCategory,
    EmailClassificationResult,
    EmailContent,
    NotionMailIntegrationConfig,
    NotionMailIntegrationService,
)

# Create router following established patterns
router = APIRouter(
    prefix="/notion-mail",
    tags=["notion-mail-integration"],
    responses={404: {"description": "Not found"}},
)

# Global service instance
_mail_integration_service: Optional[NotionMailIntegrationService] = None


def get_mail_integration_service() -> NotionMailIntegrationService:
    """Get or create the mail integration service instance."""
    global _mail_integration_service
    
    if _mail_integration_service is None:
        config = NotionMailIntegrationConfig(
            notion_api_token=os.getenv("NOTION_API_TOKEN", ""),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            enable_auto_classification=os.getenv("ENABLE_EMAIL_AUTO_CLASSIFICATION", "true").lower() == "true",
            enable_workflow_automation=os.getenv("ENABLE_EMAIL_WORKFLOW_AUTOMATION", "true").lower() == "true",
            confidence_threshold=float(os.getenv("EMAIL_CLASSIFICATION_CONFIDENCE_THRESHOLD", "0.7")),
            testing_mode=is_api_disabled("notion") or os.getenv("TESTING_MODE", "false").lower() == "true",
            am_consulting_response_time=int(os.getenv("AM_CONSULTING_RESPONSE_TIME", "4")),
            the_7_space_response_time=int(os.getenv("THE_7_SPACE_RESPONSE_TIME", "24")),
            higherself_core_response_time=int(os.getenv("HIGHERSELF_CORE_RESPONSE_TIME", "12"))
        )
        _mail_integration_service = NotionMailIntegrationService(config)
    
    return _mail_integration_service


# Request/Response Models
class EmailClassificationRequest(BaseModel):
    """Request model for email classification."""
    sender_email: str = Field(..., description="Email address of the sender")
    sender_name: Optional[str] = Field(None, description="Name of the sender")
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    received_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="When email was received")
    message_id: str = Field(..., description="Unique message identifier")
    thread_id: Optional[str] = Field(None, description="Email thread identifier")
    attachments: List[str] = Field(default_factory=list, description="List of attachment names")


class EmailClassificationResponse(BaseModel):
    """Response model for email classification."""
    success: bool
    classification: EmailClassificationResult
    processing_time_ms: float
    workflow_triggered: bool = False
    workflow_results: Optional[Dict[str, Any]] = None
    message: str = "Email classified successfully"


class EmailWorkflowRequest(BaseModel):
    """Request model for email workflow processing."""
    email: EmailContent
    classification: EmailClassificationResult
    force_workflow: bool = Field(False, description="Force workflow execution even for non-business categories")


class EmailWorkflowResponse(BaseModel):
    """Response model for email workflow processing."""
    success: bool
    workflow_results: Dict[str, Any]
    message: str


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    timestamp: datetime
    configuration: Dict[str, Any]
    classification_configs_loaded: int
    testing_mode: bool


# API Endpoints
@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    service: NotionMailIntegrationService = Depends(get_mail_integration_service)
) -> HealthCheckResponse:
    """
    Health check endpoint for Notion Mail Integration service.
    
    Returns service status and configuration information.
    """
    try:
        return HealthCheckResponse(
            status="healthy",
            service="notion-mail-integration",
            timestamp=datetime.utcnow(),
            configuration={
                "auto_classification_enabled": service.config.enable_auto_classification,
                "workflow_automation_enabled": service.config.enable_workflow_automation,
                "confidence_threshold": service.config.confidence_threshold,
                "response_time_slas": {
                    "am_consulting": service.config.am_consulting_response_time,
                    "the_7_space": service.config.the_7_space_response_time,
                    "higherself_core": service.config.higherself_core_response_time
                }
            },
            classification_configs_loaded=len(service.classification_configs),
            testing_mode=service.config.testing_mode
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service unhealthy: {str(e)}")


@router.post("/classify", response_model=EmailClassificationResponse)
async def classify_email(
    request: EmailClassificationRequest,
    background_tasks: BackgroundTasks,
    service: NotionMailIntegrationService = Depends(get_mail_integration_service)
) -> EmailClassificationResponse:
    """
    Classify an email using AI analysis and business rules.
    
    This endpoint classifies emails into business entity categories and
    optionally triggers workflow automation based on the classification.
    """
    start_time = datetime.utcnow()
    
    try:
        # Convert request to EmailContent
        email_content = EmailContent(
            sender_email=request.sender_email,
            sender_name=request.sender_name,
            subject=request.subject,
            body=request.body,
            received_at=request.received_at,
            message_id=request.message_id,
            thread_id=request.thread_id,
            attachments=request.attachments
        )
        
        # Classify the email
        classification = await service.classify_email(email_content)
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Prepare response
        response = EmailClassificationResponse(
            success=True,
            classification=classification,
            processing_time_ms=processing_time,
            workflow_triggered=False
        )
        
        # Trigger workflow automation if enabled and classification has business entity
        if (service.config.enable_workflow_automation and 
            classification.business_entity and 
            classification.confidence >= service.config.confidence_threshold):
            
            # Process workflow in background
            background_tasks.add_task(
                process_email_workflow_background,
                service,
                email_content,
                classification
            )
            response.workflow_triggered = True
            response.message = "Email classified and workflow triggered"
        
        logger.info(
            f"Email classified as {classification.category.value} "
            f"with {classification.confidence:.2f} confidence "
            f"in {processing_time:.1f}ms"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error classifying email: {e}")
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Return error response with fallback classification
        return EmailClassificationResponse(
            success=False,
            classification=EmailClassificationResult(
                category=EmailCategory.OTHER,
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}",
                priority_score=8
            ),
            processing_time_ms=processing_time,
            message=f"Classification failed: {str(e)}"
        )


@router.post("/workflow", response_model=EmailWorkflowResponse)
async def process_email_workflow(
    request: EmailWorkflowRequest,
    service: NotionMailIntegrationService = Depends(get_mail_integration_service)
) -> EmailWorkflowResponse:
    """
    Process email workflow automation based on classification.
    
    This endpoint manually triggers workflow automation for a classified email.
    """
    try:
        # Process workflow
        workflow_results = await service.process_email_workflow(
            request.email,
            request.classification
        )
        
        return EmailWorkflowResponse(
            success=workflow_results.get("success", False),
            workflow_results=workflow_results,
            message="Workflow processed successfully" if workflow_results.get("success") else "Workflow processing failed"
        )
        
    except Exception as e:
        logger.error(f"Error processing email workflow: {e}")
        return EmailWorkflowResponse(
            success=False,
            workflow_results={"error": str(e)},
            message=f"Workflow processing failed: {str(e)}"
        )


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_email_categories(
    service: NotionMailIntegrationService = Depends(get_mail_integration_service)
) -> List[Dict[str, Any]]:
    """
    Get all available email categories with their configuration.
    
    Returns category information including priority, colors, and business entities.
    """
    try:
        categories = []
        
        for category in EmailCategory:
            config = service.category_config.get(category, {})
            classification_config = service.classification_configs.get(category, {})
            
            categories.append({
                "category": category.value,
                "priority": config.get("priority", 8),
                "color": config.get("color", "gray"),
                "business_entity": config.get("entity"),
                "confidence_threshold": classification_config.get("confidence_threshold", 0.7),
                "response_time_sla_hours": classification_config.get("response_time_sla_hours"),
                "expected_daily_volume": classification_config.get("expected_daily_volume", 0),
                "target_accuracy": classification_config.get("target_accuracy", 0.7)
            })
        
        return sorted(categories, key=lambda x: x["priority"])
        
    except Exception as e:
        logger.error(f"Error getting email categories: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/stats", response_model=Dict[str, Any])
async def get_classification_stats(
    service: NotionMailIntegrationService = Depends(get_mail_integration_service)
) -> Dict[str, Any]:
    """
    Get classification statistics and performance metrics.
    
    Returns statistics about email classification performance and volumes.
    """
    try:
        # This would typically query a database for actual statistics
        # For now, return configuration-based expected metrics
        
        total_expected_volume = sum(
            config.get("expected_daily_volume", 0)
            for config in service.classification_configs.values()
        )
        
        category_stats = {}
        for category in EmailCategory:
            config = service.classification_configs.get(category, {})
            category_stats[category.value] = {
                "expected_daily_volume": config.get("expected_daily_volume", 0),
                "target_accuracy": config.get("target_accuracy", 0.7),
                "confidence_threshold": config.get("confidence_threshold", 0.7),
                "response_time_sla_hours": config.get("response_time_sla_hours")
            }
        
        return {
            "total_expected_daily_volume": total_expected_volume,
            "category_stats": category_stats,
            "service_config": {
                "auto_classification_enabled": service.config.enable_auto_classification,
                "workflow_automation_enabled": service.config.enable_workflow_automation,
                "global_confidence_threshold": service.config.confidence_threshold,
                "testing_mode": service.config.testing_mode
            },
            "business_entity_slas": {
                "am_consulting": service.config.am_consulting_response_time,
                "the_7_space": service.config.the_7_space_response_time,
                "higherself_core": service.config.higherself_core_response_time
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting classification stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# Background task function
async def process_email_workflow_background(
    service: NotionMailIntegrationService,
    email_content: EmailContent,
    classification: EmailClassificationResult
) -> None:
    """Process email workflow in background task."""
    try:
        workflow_results = await service.process_email_workflow(email_content, classification)
        logger.info(f"Background workflow processing completed for {email_content.sender_email}")
    except Exception as e:
        logger.error(f"Background workflow processing failed: {e}")


# Webhook endpoint for email providers
@router.post("/webhook/email-received")
async def email_received_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    service: NotionMailIntegrationService = Depends(get_mail_integration_service)
) -> Dict[str, Any]:
    """
    Webhook endpoint for receiving emails from email providers.
    
    This endpoint can be configured with email services to automatically
    process incoming emails through the classification and workflow system.
    """
    try:
        # Parse webhook payload (format depends on email provider)
        payload = await request.json()
        
        # Extract email data from payload
        # This would need to be customized based on the email provider's webhook format
        email_data = payload.get("email", {})
        
        if not email_data:
            raise HTTPException(status_code=400, detail="No email data in webhook payload")
        
        # Convert to EmailContent
        email_content = EmailContent(
            sender_email=email_data.get("from", ""),
            sender_name=email_data.get("from_name"),
            subject=email_data.get("subject", ""),
            body=email_data.get("body", ""),
            received_at=datetime.fromisoformat(email_data.get("received_at", datetime.utcnow().isoformat())),
            message_id=email_data.get("message_id", ""),
            thread_id=email_data.get("thread_id"),
            attachments=email_data.get("attachments", [])
        )
        
        # Process email classification and workflow in background
        background_tasks.add_task(
            process_email_webhook_background,
            service,
            email_content
        )
        
        return {
            "success": True,
            "message": "Email webhook received and processing started",
            "email_id": email_content.message_id
        }
        
    except Exception as e:
        logger.error(f"Error processing email webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


async def process_email_webhook_background(
    service: NotionMailIntegrationService,
    email_content: EmailContent
) -> None:
    """Process email webhook in background task."""
    try:
        # Classify email
        classification = await service.classify_email(email_content)
        
        # Process workflow if applicable
        if (service.config.enable_workflow_automation and 
            classification.business_entity and 
            classification.confidence >= service.config.confidence_threshold):
            
            await service.process_email_workflow(email_content, classification)
        
        logger.info(f"Webhook email processing completed for {email_content.sender_email}")
        
    except Exception as e:
        logger.error(f"Webhook email processing failed: {e}")
