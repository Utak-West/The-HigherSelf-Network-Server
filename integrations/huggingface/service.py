"""
Hugging Face Pro integration service for The HigherSelf Network.
Provides access to models, spaces, datasets, and agents with Notion integration.
"""
from typing import List, Dict, Any, Optional, Union
import os
from datetime import datetime
import json
from pydantic import ValidationError
from loguru import logger

# HuggingFace libraries
from huggingface_hub import HfApi, InferenceClient, HfFolder
from huggingface_hub.utils import RepositoryNotFoundError, GatedRepoError

# Local imports
from .config import HuggingFaceIntegrationConfig, NotionHuggingFaceConfig
from .models import (
    HuggingFaceModelReference,
    HuggingFaceSpace,
    HuggingFaceDataset,
    HuggingFaceAgent,
    ModelType,
    SpaceFramework
)

class HuggingFaceService:
    """
    Service for interacting with Hugging Face Pro features.
    Maintains Notion as the central data hub for all operations.
    """
    
    def __init__(self, config: HuggingFaceIntegrationConfig):
        """
        Initialize the Hugging Face service.
        
        Args:
            config: HuggingFace integration configuration
        """
        self.config = config
        self._api = None
        self._inference_client = None
        self._login()
        
    def _login(self) -> None:
        """Authenticate with Hugging Face API."""
        api_key = self.config.api_key.get_secret_value()
        HfFolder.save_token(api_key)
        self._api = HfApi(token=api_key)
        logger.info(f"Authenticated with Hugging Face API as organization: {self.config.organization or 'default'}")
        
    @property
    def api(self) -> HfApi:
        """Get the authenticated Hugging Face API client."""
        if not self._api:
            self._login()
        return self._api
    
    @property
    def inference_client(self) -> InferenceClient:
        """Get the Hugging Face Inference API client."""
        if not self._inference_client:
            self._inference_client = InferenceClient(token=self.config.api_key.get_secret_value())
        return self._inference_client
    
    def list_models(self, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available models based on filter criteria.
        
        Args:
            filter_by: Optional dictionary of filter parameters
            
        Returns:
            List of model information dictionaries
        """
        # Default filter for models with Pro features
        if not filter_by:
            filter_by = {}
        
        models = self.api.list_models(
            author=filter_by.get("author"),
            search=filter_by.get("search"),
            model_name=filter_by.get("model_name"),
            task=filter_by.get("task"),
            filter=filter_by.get("filter"),
            sort=filter_by.get("sort", "downloads"),
            direction=filter_by.get("direction", -1),
            limit=filter_by.get("limit", 50),
        )
        
        return [model.to_dict() for model in models]
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_id: Hugging Face model ID
            
        Returns:
            Dictionary containing model information
        """
        try:
            model_info = self.api.model_info(model_id)
            return model_info.to_dict()
        except (RepositoryNotFoundError, GatedRepoError) as e:
            logger.error(f"Error fetching model {model_id}: {str(e)}")
            raise ValueError(f"Could not access model {model_id}: {str(e)}")
    
    def create_notion_model_reference(self, 
                                    model_id: str, 
                                    notion_id: str,
                                    name: Optional[str] = None,
                                    description: Optional[str] = None) -> HuggingFaceModelReference:
        """
        Create a reference to a Hugging Face model in Notion.
        
        Args:
            model_id: Hugging Face model ID
            notion_id: Notion page ID where this model is referenced
            name: Optional display name for the model
            description: Optional description for the model reference
            
        Returns:
            HuggingFaceModelReference object
        """
        model_info = self.get_model_info(model_id)
        
        # Determine model type from tags or pipeline tag
        model_type = ModelType.TEXT_GENERATION  # Default
        if "pipeline_tag" in model_info:
            try:
                model_type = ModelType(model_info["pipeline_tag"])
            except ValueError:
                logger.warning(f"Unknown pipeline tag: {model_info['pipeline_tag']}, defaulting to {model_type}")
        
        return HuggingFaceModelReference(
            notion_id=notion_id,
            name=name or model_info.get("modelId"),
            description=description or model_info.get("description", ""),
            tags=model_info.get("tags", []),
            model_id=model_id,
            model_type=model_type,
            hub_url=f"https://huggingface.co/{model_id}",
            model_version=model_info.get("sha"),
            # Add other relevant fields from model_info
        )
    
    def run_inference(self, 
                    model_id: str, 
                    inputs: Union[str, List[str], Dict[str, Any]],
                    task: Optional[str] = None,
                    **parameters) -> Any:
        """
        Run inference using a Hugging Face model.
        
        Args:
            model_id: Hugging Face model ID or inference endpoint
            inputs: Input data for the model
            task: Optional task type if not specified by the model
            parameters: Additional parameters for the model
            
        Returns:
            Model output
        """
        # Check if this is a custom inference endpoint
        if model_id in self.config.inference_endpoints:
            model_id = self.config.inference_endpoints[model_id]
            
        return self.inference_client.post(
            model_id,
            json={"inputs": inputs, "parameters": parameters},
            task=task
        )
    
    def list_spaces(self, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available Hugging Face Spaces.
        
        Args:
            filter_by: Optional dictionary of filter parameters
            
        Returns:
            List of space information dictionaries
        """
        if not filter_by:
            filter_by = {}
            
        organization = self.config.organization if self.config.organization else None
        
        spaces = self.api.list_spaces(
            author=filter_by.get("author") or organization,
            search=filter_by.get("search"),
            sort=filter_by.get("sort", "modified"),
            direction=filter_by.get("direction", -1),
            limit=filter_by.get("limit", 50),
        )
        
        return [space.to_dict() for space in spaces]
    
    def create_notion_space_reference(self,
                                     space_id: str,
                                     notion_id: str,
                                     name: Optional[str] = None,
                                     description: Optional[str] = None,
                                     framework: Optional[SpaceFramework] = None) -> HuggingFaceSpace:
        """
        Create a reference to a Hugging Face Space in Notion.
        
        Args:
            space_id: Hugging Face Space ID
            notion_id: Notion page ID where this space is referenced
            name: Optional display name for the space
            description: Optional description for the space
            framework: Space framework (gradio, streamlit, etc.)
            
        Returns:
            HuggingFaceSpace object
        """
        # Format space_id to ensure it follows username/space_name format
        if "/" not in space_id:
            if self.config.organization:
                space_id = f"{self.config.organization}/{space_id}"
            else:
                raise ValueError(f"Space ID {space_id} must include username/org name if no organization is configured")
        
        try:
            space_info = self.api.space_info(space_id)
            space_info_dict = space_info.to_dict()
            
            # Determine framework if not provided
            if not framework:
                sdk = space_info_dict.get("sdk", "").lower()
                if sdk in [f.value for f in SpaceFramework]:
                    framework = SpaceFramework(sdk)
                else:
                    framework = SpaceFramework.GRADIO  # Default
            
            return HuggingFaceSpace(
                notion_id=notion_id,
                name=name or space_info_dict.get("id"),
                description=description or space_info_dict.get("description", ""),
                space_id=space_id,
                space_url=f"https://huggingface.co/spaces/{space_id}",
                framework=framework,
                hardware=space_info_dict.get("hardware", "cpu-basic"),
                tags=space_info_dict.get("tags", []),
            )
            
        except (RepositoryNotFoundError, GatedRepoError) as e:
            logger.error(f"Error fetching space {space_id}: {str(e)}")
            raise ValueError(f"Could not access space {space_id}: {str(e)}")
    
    def upload_to_space(self,
                       space_id: str,
                       file_path: str,
                       path_in_repo: str) -> Dict[str, Any]:
        """
        Upload a file to a Hugging Face Space.
        
        Args:
            space_id: Space ID to upload to
            file_path: Local file path
            path_in_repo: Path within the space repository
            
        Returns:
            Response from the API
        """
        try:
            result = self.api.upload_file(
                path_or_fileobj=file_path,
                path_in_repo=path_in_repo,
                repo_id=space_id,
                repo_type="space"
            )
            logger.info(f"Uploaded {file_path} to space {space_id} at {path_in_repo}")
            return result
        except Exception as e:
            logger.error(f"Error uploading file to space {space_id}: {str(e)}")
            raise

    def list_datasets(self, filter_by: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        List available Hugging Face Datasets.
        
        Args:
            filter_by: Optional dictionary of filter parameters
            
        Returns:
            List of dataset information dictionaries
        """
        if not filter_by:
            filter_by = {}
            
        organization = self.config.organization if self.config.organization else None
        
        datasets = self.api.list_datasets(
            author=filter_by.get("author") or organization,
            search=filter_by.get("search"),
            filter=filter_by.get("filter"),
            sort=filter_by.get("sort", "downloads"),
            direction=filter_by.get("direction", -1),
            limit=filter_by.get("limit", 50),
        )
        
        return [dataset.to_dict() for dataset in datasets]
