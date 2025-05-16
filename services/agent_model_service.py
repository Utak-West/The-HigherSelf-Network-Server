"""Agent Model Service for The HigherSelf Network Server.

This service provides intelligent model selection capabilities for agents,
mapping agent needs to appropriate AI models based on task requirements,
agent capabilities, resource constraints, and performance priorities.
It optimizes model selection to balance quality, speed, and efficiency.
"""

import os
from typing import Any, Dict, List, Optional, Tuple

from utils.logging_utils import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

from pydantic import BaseModel, Field

from models.base import AgentCapability
from models.huggingface_model_registry import ModelMetadata, model_registry
from services.ai_providers import AICompletionRequest, AICompletionResponse
from services.ai_router import AIRouter


class AgentModelRequest(BaseModel):
    """Request for model selection based on agent needs.

    This model contains all the necessary information for the model service
    to select the most appropriate AI model for a specific agent task.
    """

    agent_id: str = Field(..., description="ID of the requesting agent")
    agent_capabilities: List[AgentCapability] = Field(
        default_factory=list, description="Agent capabilities"
    )
    task_type: str = Field(..., description="Type of task to perform")
    content: str = Field(..., description="Content to process")
    content_language: str = Field("en", description="Language of the content")
    resource_constraints: Optional[Dict[str, Any]] = Field(
        None, description="Resource constraints"
    )
    performance_priority: Optional[str] = Field(
        "balanced", description="Priority: speed, quality, or balanced"
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context"
    )


class AgentModelService:
    """Service for mapping agent needs to appropriate AI models.

    This service provides intelligent model selection based on agent capabilities,
    task requirements, and resource constraints. It maintains mappings between
    agent tasks and Hugging Face task types, and uses these to select the most
    appropriate model for each request.
    """

    def __init__(self, ai_router: Optional[AIRouter] = None):
        """Initialize the Agent Model Service.

        Creates a new service instance with mappings between agent tasks, capabilities,
        and model preferences. Sets up personality profiles for different agent types.

        Args:
            ai_router: Optional AIRouter instance for routing completion requests
                to the appropriate provider. If None, requests will fail until
                an AIRouter is provided.
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
            "knowledge_query": "question-answering",
        }

        # Agent capability to preferred model size mapping
        self.capability_size_mapping = {
            AgentCapability.CONTENT_CREATION: "large",
            AgentCapability.CONTENT_DISTRIBUTION: "medium",
            AgentCapability.CLIENT_COMMUNICATION: "medium",
            AgentCapability.LEAD_PROCESSING: "small",
            AgentCapability.WORKFLOW_MANAGEMENT: "small",
            AgentCapability.TASK_CREATION: "small",
            AgentCapability.NOTIFICATION_DISPATCH: "tiny",
            AgentCapability.AUDIENCE_ANALYSIS: "medium",
            AgentCapability.CONTENT_GENERATION: "large",
        }

        # Agent capability to performance priority mapping
        self.capability_priority_mapping = {
            AgentCapability.CONTENT_CREATION: "quality",
            AgentCapability.CONTENT_DISTRIBUTION: "balanced",
            AgentCapability.CLIENT_COMMUNICATION: "quality",
            AgentCapability.LEAD_PROCESSING: "balanced",
            AgentCapability.WORKFLOW_MANAGEMENT: "speed",
            AgentCapability.TASK_CREATION: "speed",
            AgentCapability.NOTIFICATION_DISPATCH: "speed",
            AgentCapability.AUDIENCE_ANALYSIS: "quality",
            AgentCapability.CONTENT_GENERATION: "quality",
        }

        # Agent personality to model preference mapping
        self.agent_personality_mapping = {
            "Nyra": {"size_preference": "medium", "speed_preference": "fast"},
            "Solari": {"size_preference": "small", "speed_preference": "very fast"},
            "Ruvo": {"size_preference": "small", "speed_preference": "very fast"},
            "Liora": {"size_preference": "large", "speed_preference": "medium"},
            "Sage": {"size_preference": "medium", "speed_preference": "medium"},
            "Elan": {"size_preference": "large", "speed_preference": "medium"},
            "Zevi": {"size_preference": "medium", "speed_preference": "fast"},
        }

    def map_task_to_huggingface_task(self, task_type: str) -> str:
        """Map an agent task type to a Hugging Face task type.

        Converts from agent-specific task types to standardized Hugging Face
        task categories for model selection.

        Args:
            task_type: The agent-specific task type (e.g., "blog_writing",
                      "sentiment_analysis", "answer_question")

        Returns:
            str: The corresponding Hugging Face task type (e.g., "text-generation",
                "sentiment-analysis", "question-answering")
        """
        return self.task_mapping.get(task_type, "text-generation")

    def get_size_preference_for_capabilities(
        self, capabilities: List[AgentCapability]
    ) -> str:
        """Determine the preferred model size based on agent capabilities.

        Analyzes the agent's capabilities and returns the most appropriate
        model size (tiny, small, medium, large, xlarge).

        Args:
            capabilities: List of agent capabilities

        Returns:
            str: The preferred model size
        """
        if not capabilities:
            logger.info("No capabilities provided, using 'medium' as default size")
            return "medium"

        # Get all size preferences for the agent's capabilities
        size_preferences = [
            self.capability_size_mapping.get(cap, "medium") for cap in capabilities
        ]

        # Count occurrences of each size
        size_counts = {"tiny": 0, "small": 0, "medium": 0, "large": 0, "xlarge": 0}
        for size in size_preferences:
            if size in size_counts:
                size_counts[size] += 1

        # Return the most common size preference
        return max(size_counts.items(), key=lambda x: x[1])[0]

    def get_performance_priority(self, capabilities: List[AgentCapability]) -> str:
        """Determine the performance priority based on agent capabilities.

        Analyzes the agent's capabilities and returns the most appropriate
        performance priority (speed, balanced, quality).

        Args:
            capabilities: List of agent capabilities

        Returns:
            str: The preferred performance priority
        """
        if not capabilities:
            logger.info(
                "No capabilities provided, using 'balanced' as default priority"
            )
            return "balanced"

        # Get all priority preferences for the agent's capabilities
        priority_preferences = [
            self.capability_priority_mapping.get(cap, "balanced")
            for cap in capabilities
        ]

        # Count occurrences of each priority
        priority_counts = {"speed": 0, "balanced": 0, "quality": 0}
        for priority in priority_preferences:
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Return the most common priority preference
        return max(priority_counts.items(), key=lambda x: x[1])[0]

    def select_model_for_agent(
        self, request: AgentModelRequest
    ) -> Tuple[str, Dict[str, Any]]:
        """Select the best model for an agent based on its needs.

        Analyzes the agent's request including capabilities, task type, and other
        preferences to select the most appropriate model from the registry.

        Args:
            request: AgentModelRequest with agent details and task requirements

        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - model_id: The ID of the selected model
                - parameters: Default parameters for using the model
        """
        logger.info(
            f"Selecting model for agent '{request.agent_id}', task '{request.task_type}'"
        )

        # Map agent task to Hugging Face task
        hf_task = self.map_task_to_huggingface_task(request.task_type)
        logger.debug(f"Mapped to HF task: '{hf_task}'")

        # Determine size preference based on agent capabilities
        size_preference = self.get_size_preference_for_capabilities(
            request.agent_capabilities
        )

        # Determine performance priority
        performance_priority = (
            request.performance_priority
            or self.get_performance_priority(request.agent_capabilities)
        )

        # Map performance priority to speed preference
        speed_mapping = {"speed": "fast", "balanced": "medium", "quality": "slow"}
        speed_preference = speed_mapping.get(performance_priority, "medium")

        # Check for agent personality overrides
        agent_name = request.agent_id.split("_")[0].capitalize()
        if agent_name in self.agent_personality_mapping:
            personality_prefs = self.agent_personality_mapping[agent_name]
            orig_size_pref = size_preference
            orig_speed_pref = speed_preference

            size_preference = personality_prefs.get("size_preference", size_preference)
            speed_preference = personality_prefs.get(
                "speed_preference", speed_preference
            )

            logger.debug(
                f"Applied personality overrides for '{agent_name}': "
                f"size: {orig_size_pref} → {size_preference}, "
                f"speed: {orig_speed_pref} → {speed_preference}"
            )

        # Select model from registry
        model_metadata = model_registry.select_model_for_task(
            task=hf_task,
            size_preference=size_preference,
            speed_preference=speed_preference,
            language=request.content_language,
        )

        if not model_metadata:
            logger.warning(
                f"No model found for task '{hf_task}' with size '{size_preference}' "
                f"and speed '{speed_preference}'. Attempting fallback..."
            )

            # Fallback to default model for the task
            models = model_registry.get_models_for_task(hf_task)
            if models:
                model_metadata = models[0]
                logger.info(f"Using fallback model: {model_metadata.id}")
            else:
                # Ultimate fallback
                logger.warning(
                    f"No models found for task '{hf_task}', using global fallback 'gpt2'"
                )
                return "gpt2", {"temperature": 0.7, "max_length": 100}

        # Return model ID and default parameters
        logger.info(
            f"Selected model '{model_metadata.id}' for agent '{request.agent_id}'"
        )
        return model_metadata.id, model_metadata.default_parameters

    async def process_agent_request(
        self, request: AgentModelRequest
    ) -> AICompletionResponse:
        """Process an agent's request by selecting and calling the appropriate model.

        This method handles the end-to-end process of:
        1. Selecting the best model for the agent's task
        2. Creating a completion request with appropriate parameters
        3. Routing the request to the AI provider
        4. Returning the model's response

        Args:
            request: AgentModelRequest with agent details and task requirements

        Returns:
            AICompletionResponse: The model's response to the agent's request

        Raises:
            ValueError: If the AI Router is not initialized
        """
        if not self.ai_router:
            error_msg = "AI Router is required for processing requests"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            # Select the best model for this request
            model_id, parameters = self.select_model_for_agent(request)

            # Create completion request
            completion_request = AICompletionRequest(
                prompt=request.content, model=model_id, **parameters
            )

            # Process with Hugging Face provider
            logger.debug(
                f"Sending completion request to provider with model '{model_id}'"
            )
            return await self.ai_router.get_completion(
                request=completion_request, provider_name="huggingface"
            )
        except Exception as e:
            error_msg = f"Error processing agent request: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
