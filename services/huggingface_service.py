"""
Hugging Face Service

This module provides integration with Hugging Face's AI models.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from loguru import logger
from pydantic import BaseModel, Field

from models.base import ApiPlatform
from models.huggingface_models import (
    HuggingFaceModelConfig,
    HuggingFaceResponse,
    NotionHuggingFaceIntegration,
)
from services.ai_providers.huggingface_provider import HuggingFaceProvider
from services.base_service import BaseService
from services.notion_service import NotionService


class HuggingFaceServiceConfig(BaseModel):
    """Configuration for Hugging Face service."""

    api_key: str
    api_url: str = "https://api-inference.huggingface.co/models/"


class HuggingFaceService(BaseService):
    """Service for interacting with Hugging Face API"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        credentials: Optional[Dict[str, Any]] = None,
        notion_service: Optional[NotionService] = None,
    ):
        """
        Initialize the Hugging Face service.

        Args:
            api_key: Hugging Face API key (optional, can be provided in credentials)
            api_url: Hugging Face API URL (optional, defaults to standard URL)
            credentials: Dictionary containing credentials (optional)
            notion_service: NotionService instance for integration (optional)
        """
        # Initialize base service
        super().__init__(service_name="huggingface", credentials=credentials)

        # Get credentials from parameters or environment
        self.api_key = api_key or credentials.get("api_key") if credentials else None
        if not self.api_key:
            self.api_key = os.getenv("HUGGINGFACE_API_KEY")

        self.api_url = api_url or credentials.get("api_url") if credentials else None
        if not self.api_url:
            self.api_url = os.getenv(
                "HUGGINGFACE_API_URL", "https://api-inference.huggingface.co/models/"
            )

        # Store Notion service for integration
        self.notion_service = notion_service

        # Initialize the provider for completions
        self.provider = HuggingFaceProvider(api_key=self.api_key)

        # Log warning if credentials are missing
        if not self.api_key:
            logger.warning("Hugging Face API key not configured")

    async def initialize(self) -> bool:
        """
        Initialize the service and validate credentials.

        Returns:
            True if initialization successful, False otherwise
        """
        if not self.api_key:
            logger.error("Hugging Face API key not provided")
            return False

        return await self.provider.initialize()

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Hugging Face API requests.

        Returns:
            Dictionary of headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def query_model(
        self, model_config: HuggingFaceModelConfig, inputs: str
    ) -> Dict[str, Any]:
        """
        Query a Hugging Face model with standardized error handling.

        Args:
            model_config: Configuration for the model to query
            inputs: Input text to process

        Returns:
            Dictionary containing the model's response
        """
        try:
            response = requests.post(
                f"{self.api_url}{model_config.model_id}",
                headers=self._get_headers(),
                json={"inputs": inputs, **model_config.parameters},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            error_msg = f"Hugging Face API error: {str(e)}"
            logger.error(error_msg)
            raise

    def format_hf_output(self, response: Any, task: str) -> str:
        """
        Format Hugging Face response based on task type for storage in Notion.

        Args:
            response: Raw response from Hugging Face API
            task: Task type (e.g., 'text-generation', 'summarization')

        Returns:
            Formatted string output
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
            logger.error(f"Error formatting HF output: {str(e)}")
            return str(response)

    async def process_notion_integration(
        self,
        integration: NotionHuggingFaceIntegration,
        notion_data: Optional[Dict[str, Any]] = None,
    ) -> HuggingFaceResponse:
        """
        Process a full Notion-to-HuggingFace-to-Notion workflow.

        Args:
            integration: Configuration for the integration
            notion_data: Optional pre-fetched Notion page data

        Returns:
            HuggingFaceResponse object with the results
        """
        workflow_id = integration.workflow_instance_id

        try:
            # Get Notion data if not provided
            if not notion_data and self.notion_service:
                page = await self.notion_service.get_page(integration.notion_page_id)
                notion_data = page.properties

            if not notion_data:
                raise ValueError(
                    "Notion data not provided and Notion service not available"
                )

            # Extract input from Notion
            input_text = ""
            input_prop = integration.input_property

            # Handle different Notion property types
            if input_prop in notion_data:
                prop_data = notion_data[input_prop]

                if "rich_text" in prop_data:
                    input_text = "".join(
                        [text.get("plain_text", "") for text in prop_data["rich_text"]]
                    )
                elif "title" in prop_data:
                    input_text = "".join(
                        [text.get("plain_text", "") for text in prop_data["title"]]
                    )
                elif "content" in prop_data:
                    input_text = prop_data["content"]
                elif "text" in prop_data:
                    input_text = prop_data["text"]["content"]
                else:
                    # Try to extract any string value
                    for key, value in prop_data.items():
                        if isinstance(value, str):
                            input_text = value
                            break

            if not input_text:
                error_msg = f"Could not extract input text from property '{input_prop}'"
                if workflow_id and self.notion_service:
                    await self.notion_service.log_to_workflow_history(
                        workflow_id, "ERROR", error_msg
                    )
                raise ValueError(error_msg)

            # Log the start of processing
            if workflow_id and self.notion_service:
                await self.notion_service.log_to_workflow_history(
                    workflow_id,
                    "INFO",
                    f"Processing text with Hugging Face model {integration.model_config.model_id}",
                )

            # Query Hugging Face
            result = await self.query_model(integration.model_config, input_text)

            # Format the output
            formatted_output = self.format_hf_output(
                result, integration.model_config.task
            )

            # Prepare Notion property update based on property type
            output_properties = {}

            # Special case for rich_text or title fields
            output_properties[integration.output_property] = {
                "rich_text": [{"text": {"content": formatted_output}}]
            }

            # Update Notion with result if notion service is available
            if self.notion_service:
                await self.notion_service.update_page(
                    page_id=integration.notion_page_id, properties=output_properties
                )

                # Update workflow state
                if workflow_id:
                    await self.notion_service.update_workflow_state(
                        workflow_id, "HuggingFace_Processing_Complete", "Completed"
                    )

                    await self.notion_service.log_to_workflow_history(
                        workflow_id,
                        "INFO",
                        f"Successfully processed text with Hugging Face model {integration.model_config.model_id}",
                    )

            # Create and return response
            return HuggingFaceResponse(
                model_id=integration.model_config.model_id,
                task=integration.model_config.task,
                input=input_text,
                output=formatted_output,
                raw_response=result,
            )

        except Exception as e:
            error_msg = f"Error processing Hugging Face integration: {str(e)}"
            logger.error(error_msg)

            if workflow_id and self.notion_service:
                await self.notion_service.log_to_workflow_history(
                    workflow_id, "ERROR", error_msg
                )
                await self.notion_service.update_workflow_state(
                    workflow_id, "HuggingFace_Processing_Failed", "Failed"
                )

            raise

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

        return task_models.get(task, [])
