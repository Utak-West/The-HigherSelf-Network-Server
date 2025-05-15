"""
Agent Model Service

This service provides intelligent model selection capabilities for agents,
mapping agent needs to appropriate AI models while maintaining Notion as the central hub.
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from pydantic import BaseModel, Field

from models.huggingface_model_registry import model_registry, ModelMetadata
from services.ai_providers import AICompletionRequest, AICompletionResponse
from services.ai_router import AIRouter
from models.base import AgentCapability


class AgentModelRequest(BaseModel):
    """Request for model selection based on agent needs."""
    agent_id: str = Field(..., description="ID of the requesting agent")
    agent_capabilities: List[AgentCapability] = Field(default_factory=list, 
                                                     description="Agent capabilities")
    task_type: str = Field(..., description="Type of task to perform")
    content: str = Field(..., description="Content to process")
    content_language: str = Field("en", description="Language of the content")
    resource_constraints: Optional[Dict[str, Any]] = Field(None, 
                                                          description="Resource constraints")
    performance_priority: Optional[str] = Field("balanced", 
                                               description="Priority: speed, quality, or balanced")
    additional_context: Optional[Dict[str, Any]] = Field(None, 
                                                        description="Additional context")


class AgentModelService:
    """
    Service for mapping agent needs to appropriate AI models.
    Provides intelligent model selection based on agent capabilities and task requirements.
    """
    
    def __init__(self, ai_router: Optional[AIRouter] = None):
        """
        Initialize the Agent Model Service.
        
        Args:
            ai_router: Optional AIRouter instance
        """
        self.ai_router = ai_router
        
        # Task type to Hugging Face task mapping
        self.task_mapping = {
            # Content generation tasks
            "generate_text": "text-generation",
            "creative_writing": "text-generation",
            "content_creation": "text-generation",
            "blog_writing": "text-generation",
            "email_drafting": "text-generation",
            
            # Summarization tasks
            "summarize_content": "summarization",
            "article_summary": "summarization",
            "meeting_notes": "summarization",
            "document_summary": "summarization",
            
            # Translation tasks
            "translate_en_to_fr": "translation",
            "translate_en_to_es": "translation",
            "translate_content": "translation",
            
            # Analysis tasks
            "sentiment_analysis": "sentiment-analysis",
            "feedback_analysis": "sentiment-analysis",
            "review_analysis": "sentiment-analysis",
            
            # Question answering tasks
            "answer_question": "question-answering",
            "extract_information": "question-answering",
            "knowledge_query": "question-answering"
        }
        
        # Agent capability to preferred model size mapping
        self.capability_size_mapping = {
            AgentCapability.CONTENT_CREATION: "large",
            AgentCapability.CONTENT_DISTRIBUTION: "medium",
            AgentCapability.CLIENT_COMMUNICATION: "medium",
            AgentCapability.LEAD_MANAGEMENT: "small",
            AgentCapability.WORKFLOW_MANAGEMENT: "small",
            AgentCapability.TASK_AUTOMATION: "small",
            AgentCapability.NOTIFICATION_DISPATCH: "tiny",
            AgentCapability.ANALYTICS_PROCESSING: "medium",
            AgentCapability.AI_INTEGRATION: "large"
        }
        
        # Agent capability to performance priority mapping
        self.capability_priority_mapping = {
            AgentCapability.CONTENT_CREATION: "quality",
            AgentCapability.CONTENT_DISTRIBUTION: "balanced",
            AgentCapability.CLIENT_COMMUNICATION: "quality",
            AgentCapability.LEAD_MANAGEMENT: "balanced",
            AgentCapability.WORKFLOW_MANAGEMENT: "speed",
            AgentCapability.TASK_AUTOMATION: "speed",
            AgentCapability.NOTIFICATION_DISPATCH: "speed",
            AgentCapability.ANALYTICS_PROCESSING: "quality",
            AgentCapability.AI_INTEGRATION: "quality"
        }
        
        # Agent personality to model preference mapping
        self.agent_personality_mapping = {
            "Nyra": {"size_preference": "medium", "speed_preference": "fast"},
            "Solari": {"size_preference": "small", "speed_preference": "very fast"},
            "Ruvo": {"size_preference": "small", "speed_preference": "very fast"},
            "Liora": {"size_preference": "large", "speed_preference": "medium"},
            "Sage": {"size_preference": "medium", "speed_preference": "medium"},
            "Elan": {"size_preference": "large", "speed_preference": "medium"},
            "Zevi": {"size_preference": "medium", "speed_preference": "fast"}
        }
    
    def map_task_to_huggingface_task(self, task_type: str) -> str:
        """Map an agent task type to a Hugging Face task type."""
        return self.task_mapping.get(task_type, "text-generation")
    
    def get_size_preference_for_capabilities(self, capabilities: List[AgentCapability]) -> str:
        """Determine the preferred model size based on agent capabilities."""
        if not capabilities:
            return "medium"
        
        # Get all size preferences for the agent's capabilities
        size_preferences = [self.capability_size_mapping.get(cap, "medium") 
                           for cap in capabilities]
        
        # Count occurrences of each size
        size_counts = {"tiny": 0, "small": 0, "medium": 0, "large": 0, "xlarge": 0}
        for size in size_preferences:
            if size in size_counts:
                size_counts[size] += 1
        
        # Return the most common size preference
        return max(size_counts.items(), key=lambda x: x[1])[0]
    
    def get_performance_priority(self, capabilities: List[AgentCapability]) -> str:
        """Determine the performance priority based on agent capabilities."""
        if not capabilities:
            return "balanced"
        
        # Get all priority preferences for the agent's capabilities
        priority_preferences = [self.capability_priority_mapping.get(cap, "balanced") 
                               for cap in capabilities]
        
        # Count occurrences of each priority
        priority_counts = {"speed": 0, "balanced": 0, "quality": 0}
        for priority in priority_preferences:
            if priority in priority_counts:
                priority_counts[priority] += 1
        
        # Return the most common priority preference
        return max(priority_counts.items(), key=lambda x: x[1])[0]
    
    def select_model_for_agent(self, request: AgentModelRequest) -> Tuple[str, Dict[str, Any]]:
        """
        Select the best model for an agent based on its needs.
        
        Args:
            request: AgentModelRequest with agent details and task requirements
            
        Returns:
            Tuple of (model_id, parameters)
        """
        # Map agent task to Hugging Face task
        hf_task = self.map_task_to_huggingface_task(request.task_type)
        
        # Determine size preference based on agent capabilities
        size_preference = self.get_size_preference_for_capabilities(request.agent_capabilities)
        
        # Determine performance priority
        performance_priority = request.performance_priority or self.get_performance_priority(
            request.agent_capabilities)
        
        # Map performance priority to speed preference
        speed_mapping = {
            "speed": "fast",
            "balanced": "medium",
            "quality": "slow"
        }
        speed_preference = speed_mapping.get(performance_priority, "medium")
        
        # Check for agent personality overrides
        agent_name = request.agent_id.split('_')[0].capitalize()
        if agent_name in self.agent_personality_mapping:
            personality_prefs = self.agent_personality_mapping[agent_name]
            size_preference = personality_prefs.get("size_preference", size_preference)
            speed_preference = personality_prefs.get("speed_preference", speed_preference)
        
        # Select model from registry
        model_metadata = model_registry.select_model_for_task(
            task=hf_task,
            size_preference=size_preference,
            speed_preference=speed_preference,
            language=request.content_language
        )
        
        if not model_metadata:
            # Fallback to default model for the task
            models = model_registry.get_models_for_task(hf_task)
            if models:
                model_metadata = models[0]
            else:
                # Ultimate fallback
                return "gpt2", {"temperature": 0.7, "max_length": 100}
        
        # Return model ID and default parameters
        return model_metadata.id, model_metadata.default_parameters
    
    async def process_agent_request(self, request: AgentModelRequest) -> AICompletionResponse:
        """
        Process an agent's request by selecting and calling the appropriate model.
        
        Args:
            request: AgentModelRequest with agent details and task requirements
            
        Returns:
            AICompletionResponse with the model's response
        """
        if not self.ai_router:
            raise ValueError("AI Router is required for processing requests")
        
        # Select the best model for this request
        model_id, parameters = self.select_model_for_agent(request)
        
        # Create completion request
        completion_request = AICompletionRequest(
            prompt=request.content,
            model=model_id,
            **parameters
        )
        
        # Process with Hugging Face provider
        return await self.ai_router.get_completion(
            request=completion_request,
            provider_name="huggingface"
        )
