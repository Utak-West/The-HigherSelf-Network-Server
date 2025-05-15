"""
API routes for Hugging Face Pro integration.
These routes provide access to Hugging Face models, spaces, and inference capabilities.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from services.notion_service import get_notion_client
from integrations.huggingface.utils import create_huggingface_service, create_notion_sync
from integrations.huggingface.models import (
    HuggingFaceModelReference, 
    HuggingFaceSpace, 
    HuggingFaceAgent,
    ModelType,
    SpaceFramework
)

router = APIRouter(
    prefix="/huggingface",
    tags=["huggingface"],
    responses={404: {"description": "Not found"}},
)

# Pydantic models for API requests/responses
class ModelRequest(BaseModel):
    """Request for model operations."""
    model_id: str
    notion_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None

class SpaceRequest(BaseModel):
    """Request for space operations."""
    space_id: str
    notion_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    framework: Optional[str] = None

class InferenceRequest(BaseModel):
    """Request for model inference."""
    model_id: str
    inputs: Any
    parameters: Dict[str, Any] = Field(default_factory=dict)
    task: Optional[str] = None

# Routes for Hugging Face models
@router.get("/models", response_model=List[Dict[str, Any]])
async def list_models(search: Optional[str] = None, task: Optional[str] = None, limit: Optional[int] = 50):
    """List available Hugging Face models with optional filtering."""
    hf_service = create_huggingface_service()
    filter_by = {}
    
    if search:
        filter_by["search"] = search
    if task:
        filter_by["task"] = task
    if limit:
        filter_by["limit"] = limit
        
    return hf_service.list_models(filter_by)

@router.get("/models/{model_id}", response_model=Dict[str, Any])
async def get_model_info(model_id: str):
    """Get detailed information about a specific model."""
    try:
        hf_service = create_huggingface_service()
        return hf_service.get_model_info(model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error accessing model: {str(e)}")

@router.post("/models/notion", response_model=Dict[str, Any])
async def sync_model_to_notion(request: ModelRequest, background_tasks: BackgroundTasks):
    """Create or update a model reference in Notion."""
    try:
        hf_service = create_huggingface_service()
        notion_client = get_notion_client()
        notion_sync = create_notion_sync(notion_client)
        
        # Create model reference
        model = hf_service.create_notion_model_reference(
            model_id=request.model_id,
            notion_id=request.notion_id,
            name=request.name,
            description=request.description
        )
        
        # Sync to Notion (can be slow, so do it in the background)
        background_tasks.add_task(notion_sync.sync_model_to_notion, model)
        
        return {
            "status": "processing",
            "model": model.dict(exclude={"history_log"}),
            "message": "Model is being synchronized with Notion"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing model to Notion: {str(e)}")

# Routes for Hugging Face spaces
@router.get("/spaces", response_model=List[Dict[str, Any]])
async def list_spaces(search: Optional[str] = None, limit: Optional[int] = 50):
    """List available Hugging Face Spaces with optional filtering."""
    hf_service = create_huggingface_service()
    filter_by = {}
    
    if search:
        filter_by["search"] = search
    if limit:
        filter_by["limit"] = limit
        
    return hf_service.list_spaces(filter_by)

@router.post("/spaces/notion", response_model=Dict[str, Any])
async def sync_space_to_notion(request: SpaceRequest, background_tasks: BackgroundTasks):
    """Create or update a space reference in Notion."""
    try:
        hf_service = create_huggingface_service()
        notion_client = get_notion_client()
        notion_sync = create_notion_sync(notion_client)
        
        # Convert framework string to enum if provided
        framework = None
        if request.framework:
            try:
                framework = SpaceFramework(request.framework.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid framework: {request.framework}")
        
        # Create space reference
        space = hf_service.create_notion_space_reference(
            space_id=request.space_id,
            notion_id=request.notion_id,
            name=request.name,
            description=request.description,
            framework=framework
        )
        
        # Sync to Notion (in the background)
        background_tasks.add_task(notion_sync.sync_space_to_notion, space)
        
        return {
            "status": "processing",
            "space": space.dict(exclude={"history_log"}),
            "message": "Space is being synchronized with Notion"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing space to Notion: {str(e)}")

# Route for model inference
@router.post("/inference", response_model=Dict[str, Any])
async def run_inference(request: InferenceRequest):
    """Run inference using a Hugging Face model."""
    try:
        hf_service = create_huggingface_service()
        result = hf_service.run_inference(
            model_id=request.model_id,
            inputs=request.inputs,
            task=request.task,
            **request.parameters
        )
        
        return {
            "model_id": request.model_id,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")

# Route for Notion synchronization
@router.post("/notion/sync", response_model=Dict[str, str])
async def run_full_sync(background_tasks: BackgroundTasks):
    """Run a full synchronization between Notion and Hugging Face."""
    try:
        notion_client = get_notion_client()
        notion_sync = create_notion_sync(notion_client)
        
        # Run sync in background to avoid timeout
        background_tasks.add_task(notion_sync.full_sync)
        
        return {
            "status": "processing",
            "message": "Full synchronization started in the background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")
