"""
Hugging Face Router

This module provides API endpoints for Hugging Face integration.
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException
from loguru import logger

from models.huggingface_models import (
    HuggingFaceModelConfig,
    HuggingFaceModelInfo,
    HuggingFaceProcessResponse,
    HuggingFaceResponse,
    HuggingFaceTaskModels,
    NotionHuggingFaceIntegration,
)
from services.huggingface_service import HuggingFaceService
from services.notion_service import NotionService
from utils.auth import verify_webhook_signature

# Create router
router = APIRouter(
    prefix="/api/huggingface",
    tags=["huggingface"],
    responses={404: {"description": "Not found"}},
)


# Get services
async def get_huggingface_service():
    """Get or initialize the Hugging Face service."""
    # In a real implementation, this would be a singleton or dependency injection
    notion_service = await get_notion_service()
    return HuggingFaceService(notion_service=notion_service)


async def get_notion_service():
    """Get or initialize the Notion service."""
    # In a real implementation, this would be a singleton or dependency injection
    return NotionService()


# Endpoints
@router.post("/process", response_model=HuggingFaceProcessResponse)
async def process_huggingface_integration(
    integration: NotionHuggingFaceIntegration = Body(...),
    huggingface_service: HuggingFaceService = Depends(get_huggingface_service),
    notion_service: NotionService = Depends(get_notion_service),
):
    """
    Process a Hugging Face integration request directly via API.

    This endpoint is for direct API calls, not webhooks.
    """
    try:
        # Get Notion page data
        page = await notion_service.get_page(integration.notion_page_id)

        # Process the integration
        response = await huggingface_service.process_notion_integration(
            integration, page.properties
        )

        return HuggingFaceProcessResponse(
            status="success",
            message="Successfully processed Hugging Face integration",
            data=response,
        )
    except Exception as e:
        logger.error(f"Error processing Hugging Face integration: {str(e)}")

        if integration.workflow_instance_id:
            await notion_service.log_to_workflow_history(
                integration.workflow_instance_id,
                "ERROR",
                f"API error: {str(e)}",
                "HuggingFaceIntegration",
            )

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhooks/notion", dependencies=[Depends(verify_webhook_signature)])
async def notion_huggingface_webhook(
    integration: NotionHuggingFaceIntegration = Body(...),
    huggingface_service: HuggingFaceService = Depends(get_huggingface_service),
    notion_service: NotionService = Depends(get_notion_service),
):
    """
    Webhook endpoint for Notion to trigger Hugging Face processing.

    This endpoint includes signature verification for security.
    """
    try:
        # Get Notion page data
        page = await notion_service.get_page(integration.notion_page_id)

        # Log the start of processing to the workflow history
        if integration.workflow_instance_id:
            await notion_service.log_to_workflow_history(
                integration.workflow_instance_id,
                "INFO",
                f"Received webhook for Hugging Face processing with model {integration.model_config.model_id}",
                "HuggingFaceIntegration",
            )

        # Process the integration
        response = await huggingface_service.process_notion_integration(
            integration, page.properties
        )

        return HuggingFaceProcessResponse(
            status="success", message="Successfully processed webhook", data=response
        )
    except Exception as e:
        logger.error(f"Error processing Hugging Face webhook: {str(e)}")

        if integration.workflow_instance_id:
            await notion_service.log_to_workflow_history(
                integration.workflow_instance_id,
                "ERROR",
                f"Webhook error: {str(e)}",
                "HuggingFaceIntegration",
            )

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/{task}")
async def list_available_models(task: str):
    """
    List available Hugging Face models for a specific task.

    Helps users discover appropriate models for their use cases.
    """
    # This is a simplified implementation - in production you might want to
    # query the Hugging Face API for current models or maintain a curated list
    task_models = {
        "text-generation": [
            {"id": "gpt2", "description": "OpenAI GPT-2 model for text generation"},
            {"id": "distilgpt2", "description": "Distilled version of GPT-2"},
            {
                "id": "EleutherAI/gpt-neo-1.3B",
                "description": "GPT-Neo 1.3B parameters model",
            },
        ],
        "summarization": [
            {
                "id": "facebook/bart-large-cnn",
                "description": "BART model fine-tuned on CNN Daily Mail",
            },
            {
                "id": "sshleifer/distilbart-cnn-12-6",
                "description": "Distilled BART for summarization",
            },
        ],
        "translation": [
            {
                "id": "Helsinki-NLP/opus-mt-en-fr",
                "description": "English to French translation",
            },
            {
                "id": "Helsinki-NLP/opus-mt-en-es",
                "description": "English to Spanish translation",
            },
        ],
        "sentiment-analysis": [
            {
                "id": "distilbert-base-uncased-finetuned-sst-2-english",
                "description": "DistilBERT fine-tuned for sentiment",
            }
        ],
        "question-answering": [
            {
                "id": "deepset/roberta-base-squad2",
                "description": "RoBERTa fine-tuned on SQuAD2",
            },
            {
                "id": "distilbert-base-cased-distilled-squad",
                "description": "Distilled BERT for QA",
            },
        ],
    }

    return {"task": task, "models": task_models.get(task, [])}


@router.get("/model-info/{model_id}")
async def get_model_info(model_id: str):
    """
    Get detailed information about a specific Hugging Face model.
    """
    # In a production environment, this would query the Hugging Face API
    # For now, we'll return some basic information for a few models
    models = {
        "gpt2": {
            "id": "gpt2",
            "task": "text-generation",
            "description": "OpenAI GPT-2 model for text generation",
            "parameters": {
                "temperature": 0.7,
                "max_length": 100,
                "top_k": 0,
                "top_p": 0.9,
            },
        },
        "facebook/bart-large-cnn": {
            "id": "facebook/bart-large-cnn",
            "task": "summarization",
            "description": "BART model fine-tuned on CNN Daily Mail",
            "parameters": {"max_length": 150, "min_length": 30, "length_penalty": 2.0},
        },
    }

    # Return model info or a 404 if not found
    if model_id in models:
        return models[model_id]
    else:
        # For any model not in our static list, we'd return a generic template
        return {
            "id": model_id,
            "task": "unknown",
            "description": f"Information not available for {model_id}",
            "parameters": {},
        }
