"""
Hugging Face Models

This module defines models for Hugging Face integration with The HigherSelf Network.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime

class HuggingFaceModelConfig(BaseModel):
    """Configuration for a Hugging Face model"""
    model_id: str = Field(..., description="Hugging Face model ID")
    task: str = Field(..., description="Task type like 'text-generation', 'summarization', etc.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Model-specific parameters")

class NotionHuggingFaceIntegration(BaseModel):
    """Configuration for Notion to Hugging Face integration"""
    notion_page_id: str = Field(..., description="Notion page ID to process")
    model_config: HuggingFaceModelConfig = Field(..., description="Hugging Face model configuration")
    input_property: str = Field(..., description="Notion property to use as input")
    output_property: str = Field(..., description="Notion property to update with the result")
    workflow_instance_id: Optional[str] = Field(None, description="ID of the workflow instance in Notion")

class HuggingFaceModelInfo(BaseModel):
    """Information about a Hugging Face model"""
    id: str
    task: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class HuggingFaceTaskModels(BaseModel):
    """Models available for a specific task"""
    task: str
    models: List[Dict[str, str]]

class HuggingFaceResponse(BaseModel):
    """Response from a Hugging Face model"""
    model_id: str
    task: str
    input: str
    output: Any
    raw_response: Dict[str, Any] = Field(default_factory=dict)
    processed_at: datetime = Field(default_factory=datetime.now)

class HuggingFaceProcessResponse(BaseModel):
    """Response for processing a Hugging Face integration"""
    status: str
    message: str
    data: Optional[HuggingFaceResponse] = None
