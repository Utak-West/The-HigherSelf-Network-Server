"""
Hugging Face Service for The HigherSelf Network Server.
This service provides specialized Hugging Face functionality beyond the basic AI provider.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from loguru import logger
from pydantic import BaseModel, Field

from models.base import NotionIntegrationConfig
from services.notion_service import NotionService
from services.ai_providers.huggingface_provider import HuggingFaceProvider


class HuggingFaceModelConfig(BaseModel):
    """Configuration for a Hugging Face model."""
    model_id: str = Field(..., description="Hugging Face model ID")
    task: str = Field(..., description="Task type like 'text-generation', 'summarization', etc.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model-specific parameters")


class NotionHuggingFaceIntegration(BaseModel):
    """Configuration for Notion to Hugging Face integration."""
    notion_page_id: str = Field(..., description="Notion page ID to process")
    model_config: HuggingFaceModelConfig = Field(..., description="Hugging Face model configuration")
    input_property: str = Field(..., description="Notion property to use as input")
    output_property: str = Field(..., description="Notion property to update with the result")
    workflow_instance_id: Optional[str] = Field(None, description="ID of the workflow instance in Notion")


class HuggingFaceService:
    """
    Service for specialized Hugging Face functionality.
    Provides integration with Notion and other HigherSelf Network systems.
    """
    
    def __init__(self, api_token: Optional[str] = None, notion_service: Optional[NotionService] = None):
        """
        Initialize the Hugging Face service.
        
        Args:
            api_token: Hugging Face API token (optional, will use env var if not provided)
            notion_service: NotionService instance for Notion integration
        """
        self.api_token = api_token or os.environ.get("HUGGINGFACE_API_KEY")
        if not self.api_token:
            logger.warning("Hugging Face API key not provided in env or constructor")
            
        self.api_url = "https://api-inference.huggingface.co/models/"
        self.headers = {"Authorization": f"Bearer {self.api_token}"} if self.api_token else {}
        self.notion_service = notion_service
        
        # Initialize the provider for completions
        self.provider = HuggingFaceProvider(api_key=self.api_token)
        
    async def initialize(self) -> bool:
        """
        Initialize the service and validate credentials.
        
        Returns:
            True if initialization successful, False otherwise
        """
        if not self.api_token:
            logger.error("Hugging Face API key not provided")
            return False
            
        return await self.provider.initialize()
        
    def query_model(self, model_config: HuggingFaceModelConfig, inputs: str) -> Dict[str, Any]:
        """
        Query a Hugging Face model with standardized error handling.
        
        Args:
            model_config: Configuration for the model to use
            inputs: Input text to process
            
        Returns:
            Model response as a dictionary
        """
        try:
            response = requests.post(
                f"{self.api_url}{model_config.model_id}",
                headers=self.headers,
                json={"inputs": inputs, **model_config.parameters}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_msg = f"Hugging Face API error: {str(e)}"
            logger.error(error_msg)
            raise
    
    def format_hf_output(self, response: Any, task: str) -> str:
        """
        Format Hugging Face response based on task type.
        
        Args:
            response: Raw response from Hugging Face API
            task: Task type (e.g., 'text-generation', 'summarization')
            
        Returns:
            Formatted output as a string
        """
        try:
            if task == "text-generation":
                if isinstance(response, list) and len(response) > 0:
                    return response[0].get("generated_text", str(response))
            elif task == "summarization":
                if isinstance(response, list) and len(response) > 0:
                    return response[0].get("summary_text", str(response))
            elif task == "question-answering":
                if isinstance(response, dict):
                    return response.get("answer", str(response))
            elif task == "translation":
                if isinstance(response, list) and len(response) > 0:
                    return response[0].get("translation_text", str(response))
            elif task == "sentiment-analysis":
                if isinstance(response, list) and len(response) > 0:
                    result = response[0]
                    return f"Label: {result.get('label', 'Unknown')}, Score: {result.get('score', 'Unknown')}"
            
            # Default fallback - JSON stringify
            return json.dumps(response)
        except Exception as e:
            logger.error(f"Error formatting HF output: {e}")
            return str(response)
    
    async def process_notion_integration(self, integration: NotionHuggingFaceIntegration) -> bool:
        """
        Process a full Notion-to-HuggingFace-to-Notion workflow.
        
        Args:
            integration: Configuration for the integration
            
        Returns:
            True if processing successful, False otherwise
        """
        if not self.notion_service:
            logger.error("Notion service not provided, cannot process integration")
            return False
            
        workflow_id = integration.workflow_instance_id
        
        try:
            # Get the Notion page
            page = await self.notion_service.get_page(integration.notion_page_id)
            if not page:
                logger.error(f"Could not find Notion page with ID {integration.notion_page_id}")
                return False
                
            # Extract input from Notion
            input_text = await self.notion_service.extract_property_text(
                page, 
                integration.input_property
            )
            
            if not input_text:
                error_msg = f"Could not extract input text from property '{integration.input_property}'"
                logger.error(error_msg)
                
                if workflow_id:
                    await self.notion_service.log_to_workflow_history(
                        workflow_id, 
                        "ERROR", 
                        error_msg
                    )
                return False
            
            # Log the start of processing
            if workflow_id:
                await self.notion_service.log_to_workflow_history(
                    workflow_id,
                    "INFO",
                    f"Processing text with Hugging Face model {integration.model_config.model_id}"
                )
            
            # Query Hugging Face
            result = self.query_model(integration.model_config, input_text)
            
            # Format the output
            formatted_output = self.format_hf_output(result, integration.model_config.task)
            
            # Update Notion with result
            await self.notion_service.update_page_property(
                integration.notion_page_id,
                integration.output_property,
                formatted_output
            )
            
            # Update workflow state if applicable
            if workflow_id:
                await self.notion_service.update_workflow_state(
                    workflow_id,
                    "HuggingFace_Processing_Complete",
                    "Completed"
                )
                
                await self.notion_service.log_to_workflow_history(
                    workflow_id,
                    "INFO",
                    f"Successfully processed text with Hugging Face model {integration.model_config.model_id}"
                )
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing Hugging Face integration: {str(e)}"
            logger.error(error_msg)
            
            if workflow_id and self.notion_service:
                await self.notion_service.log_to_workflow_history(
                    workflow_id, 
                    "ERROR", 
                    error_msg
                )
                
                await self.notion_service.update_workflow_state(
                    workflow_id,
                    "HuggingFace_Processing_Failed",
                    "Failed"
                )
            
            return False
    
    def get_available_models_for_task(self, task: str) -> List[Dict[str, str]]:
        """
        Get a list of recommended models for a specific task.
        
        Args:
            task: Task type (e.g., 'text-generation', 'summarization')
            
        Returns:
            List of model information dictionaries
        """
        # This is a simplified implementation - in production you might want to
        # query the Hugging Face API for current models or maintain a curated list
        task_models = {
            "text-generation": [
                {"id": "gpt2", "description": "OpenAI GPT-2 model for text generation"},
                {"id": "distilgpt2", "description": "Distilled version of GPT-2"},
                {"id": "EleutherAI/gpt-neo-1.3B", "description": "GPT-Neo 1.3B parameters model"}
            ],
            "summarization": [
                {"id": "facebook/bart-large-cnn", "description": "BART model fine-tuned on CNN Daily Mail"},
                {"id": "sshleifer/distilbart-cnn-12-6", "description": "Distilled BART for summarization"}
            ],
            "translation": [
                {"id": "Helsinki-NLP/opus-mt-en-fr", "description": "English to French translation"},
                {"id": "Helsinki-NLP/opus-mt-en-es", "description": "English to Spanish translation"}
            ],
            "sentiment-analysis": [
                {"id": "distilbert-base-uncased-finetuned-sst-2-english", "description": "DistilBERT fine-tuned for sentiment"}
            ],
            "question-answering": [
                {"id": "deepset/roberta-base-squad2", "description": "RoBERTa fine-tuned on SQuAD2"},
                {"id": "distilbert-base-cased-distilled-squad", "description": "Distilled BERT for QA"}
            ]
        }
        
        return task_models.get(task, [])
