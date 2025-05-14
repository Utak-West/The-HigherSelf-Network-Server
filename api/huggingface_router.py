"""
Hugging Face API Router for The HigherSelf Network Server.
Provides endpoints for Hugging Face integration with Notion.
"""

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from typing import Dict, Any, List, Optional
from loguru import logger
from pydantic import BaseModel

from services.huggingface_service import (
    HuggingFaceService,
    HuggingFaceModelConfig,
    NotionHuggingFaceIntegration
)
from services.notion_service import NotionService
from models.notion_db_models import WorkflowInstance
from utils.auth import verify_api_key


# Create router
router = APIRouter(
    prefix="/huggingface",
    tags=["huggingface"],
    responses={404: {"description": "Not found"}},
)

# Service instances will be injected via dependency
huggingface_service: Optional[HuggingFaceService] = None
notion_service: Optional[NotionService] = None


class HuggingFaceResponse(BaseModel):
    """Standard response for Hugging Face endpoints."""
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None


@router.get("/", response_model=HuggingFaceResponse)
async def get_huggingface_info():
    """Get information about the Hugging Face integration."""
    if not huggingface_service:
        raise HTTPException(status_code=503, detail="Hugging Face service not initialized")
        
    return {
        "status": "success",
        "message": "Hugging Face integration is available",
        "data": {
            "provider": "huggingface",
            "available_tasks": [
                "text-generation",
                "summarization",
                "translation",
                "sentiment-analysis",
                "question-answering"
            ]
        }
    }


@router.get("/models/{task}", response_model=HuggingFaceResponse)
async def list_available_models(task: str):
    """
    List available Hugging Face models for a specific task.
    Helps users discover appropriate models for their use cases.
    """
    if not huggingface_service:
        raise HTTPException(status_code=503, detail="Hugging Face service not initialized")
        
    models = huggingface_service.get_available_models_for_task(task)
    
    return {
        "status": "success",
        "message": f"Available models for {task}",
        "data": {
            "task": task,
            "models": models
        }
    }


@router.post("/process", response_model=HuggingFaceResponse)
async def process_huggingface_integration(
    integration: NotionHuggingFaceIntegration = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """
    Process a Hugging Face integration request.
    This endpoint processes text from a Notion page using a Hugging Face model
    and updates the page with the result.
    """
    if not huggingface_service:
        raise HTTPException(status_code=503, detail="Hugging Face service not initialized")
        
    if not notion_service:
        raise HTTPException(status_code=503, detail="Notion service not initialized")
    
    try:
        # Process the integration
        success = await huggingface_service.process_notion_integration(integration)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to process integration")
        
        return {
            "status": "success",
            "message": "Successfully processed Hugging Face integration",
            "data": {
                "notion_page_id": integration.notion_page_id,
                "model_id": integration.model_config.model_id,
                "task": integration.model_config.task
            }
        }
    except Exception as e:
        logger.error(f"Error processing Hugging Face integration: {e}")
        
        if integration.workflow_instance_id and notion_service:
            await notion_service.log_to_workflow_history(
                integration.workflow_instance_id,
                "ERROR",
                f"API error: {str(e)}"
            )
            
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/notion", response_model=HuggingFaceResponse)
async def notion_huggingface_webhook(
    request: Request,
    integration: NotionHuggingFaceIntegration = Body(...)
):
    """
    Webhook endpoint for Notion to trigger Hugging Face processing.
    This endpoint can be called from Notion automations or external systems.
    """
    if not huggingface_service:
        raise HTTPException(status_code=503, detail="Hugging Face service not initialized")
        
    if not notion_service:
        raise HTTPException(status_code=503, detail="Notion service not initialized")
    
    try:
        # Log the start of processing to the workflow history
        if integration.workflow_instance_id:
            await notion_service.log_to_workflow_history(
                integration.workflow_instance_id,
                "INFO",
                f"Received webhook for Hugging Face processing with model {integration.model_config.model_id}"
            )
        
        # Process the integration
        success = await huggingface_service.process_notion_integration(integration)
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to process integration")
        
        return {
            "status": "success",
            "message": "Successfully processed webhook",
            "data": {
                "notion_page_id": integration.notion_page_id,
                "model_id": integration.model_config.model_id
            }
        }
    except Exception as e:
        logger.error(f"Error processing Hugging Face webhook: {e}")
        
        if integration.workflow_instance_id and notion_service:
            await notion_service.log_to_workflow_history(
                integration.workflow_instance_id,
                "ERROR",
                f"Webhook error: {str(e)}"
            )
            
        raise HTTPException(status_code=500, detail=str(e))


# Initialize services
def init_router(hf_service: HuggingFaceService, notion_svc: NotionService):
    """Initialize the router with required services."""
    global huggingface_service, notion_service
    huggingface_service = hf_service
    notion_service = notion_svc
    logger.info("Hugging Face router initialized")
