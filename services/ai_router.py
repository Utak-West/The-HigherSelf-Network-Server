"""
AI Router Service for The HigherSelf Network Server.
This service routes AI requests to the appropriate provider while maintaining Notion as the central hub.
"""

import os
from typing import Any, Dict, List, Optional

from loguru import logger
from pydantic import BaseModel

from services.ai_providers import (AICompletionRequest, AICompletionResponse,
                                   AIProvider, AnthropicProvider,
                                   HuggingFaceProvider, OpenAIProvider)

# Import mock provider for testing
try:
    from services.ai_providers.mock_provider import MockAIProvider
except ImportError:
    # Mock provider not available
    MockAIProvider = None


class AIRouterConfig(BaseModel):
    """Configuration for the AI Router."""

    default_provider: str = "openai"
    default_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None

    class Config:
        env_prefix = "AI_ROUTER_"


class AIRouter:
    """
    Router service for AI providers.
    Dynamically selects the appropriate provider based on request requirements.
    Ensures all data is processed and stored in Notion as the central hub.
    """

    def __init__(self):
        """Initialize the AI Router."""
        self.providers: Dict[str, AIProvider] = {}
        self.default_provider = os.environ.get("AI_ROUTER_DEFAULT_PROVIDER", "openai")
        self.default_model = os.environ.get("AI_ROUTER_DEFAULT_MODEL")
        self.initialized = False

    async def initialize(self) -> bool:
        """
        Initialize all AI providers.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize OpenAI provider
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if openai_api_key:
                openai_provider = OpenAIProvider(api_key=openai_api_key)
                if await openai_provider.initialize():
                    self.providers["openai"] = openai_provider
                    logger.info("OpenAI provider initialized")

            # Initialize Anthropic provider
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
            if anthropic_api_key:
                anthropic_provider = AnthropicProvider(api_key=anthropic_api_key)
                if await anthropic_provider.initialize():
                    self.providers["anthropic"] = anthropic_provider
                    logger.info("Anthropic provider initialized")

            # Initialize Hugging Face provider
            huggingface_api_key = os.environ.get("HUGGINGFACE_API_KEY")
            if huggingface_api_key:
                huggingface_provider = HuggingFaceProvider(api_key=huggingface_api_key)
                if await huggingface_provider.initialize():
                    self.providers["huggingface"] = huggingface_provider
                    logger.info("Hugging Face provider initialized")

            # Check if at least one provider is available
            if not self.providers:
                logger.warning(
                    "No AI providers could be initialized. Using mock provider for testing."
                )

                # Use mock provider as fallback
                if MockAIProvider:
                    mock_provider = MockAIProvider()
                    if await mock_provider.initialize():
                        self.providers["mock"] = mock_provider
                        self.default_provider = "mock"
                        logger.info("Mock provider initialized as fallback")
                    else:
                        logger.error("Failed to initialize mock provider")
                        return False
                else:
                    logger.error(
                        "No AI providers could be initialized and mock provider is not available."
                    )
                    return False

            # Ensure default provider is available
            if self.default_provider not in self.providers:
                self.default_provider = next(iter(self.providers.keys()))
                logger.warning(
                    f"Default provider not available. Using {self.default_provider} instead."
                )

            self.initialized = True
            logger.info(
                f"AI Router initialized with providers: {', '.join(self.providers.keys())}"
            )
            return True
        except Exception as e:
            logger.error(f"Error initializing AI Router: {e}")
            return False

    async def get_completion(
        self, request: AICompletionRequest, provider_name: Optional[str] = None
    ) -> AICompletionResponse:
        """
        Get a completion from the appropriate AI provider.

        Args:
            request: AICompletionRequest with prompt and parameters
            provider_name: Optional name of provider to use (defaults to router's default)

        Returns:
            AICompletionResponse with generated text and metadata
        """
        if not self.initialized:
            success = await self.initialize()
            if not success:
                return AICompletionResponse(
                    text="Error: AI Router initialization failed. Check your API keys and configuration.",
                    provider="none",
                    model="none",
                    metadata={"error": "Initialization failed"},
                )

        # Determine which provider to use
        provider_name = provider_name or self.default_provider

        # Check if any providers are available
        if not self.providers:
            logger.error("No AI providers available")
            return AICompletionResponse(
                text="Error: No AI providers available. Check your API keys and configuration.",
                provider="none",
                model="none",
                metadata={"error": "No providers available"},
            )

        if provider_name not in self.providers:
            logger.warning(
                f"Requested provider {provider_name} not available. Using {self.default_provider}."
            )
            provider_name = self.default_provider

            # If default provider is also not available, use the first available provider
            if provider_name not in self.providers:
                provider_name = next(iter(self.providers.keys()))
                logger.warning(
                    f"Default provider not available. Using {provider_name} instead."
                )

        provider = self.providers[provider_name]

        # Determine the best model for this task if not specified
        if not request.model:
            # Try to infer task type from prompt
            task_type = "generate"  # Default task type
            prompt_lower = request.prompt.lower()

            # Check for task-specific keywords
            task_keywords = {
                "summarize": ["summarize", "summary", "condense", "shorten"],
                "translate": [
                    "translate",
                    "translation",
                    "convert to",
                    "in french",
                    "in spanish",
                ],
                "sentiment": ["sentiment", "feeling", "emotion", "attitude", "opinion"],
                "question": [
                    "answer this question",
                    "find in the text",
                    "extract from passage",
                ],
                "classify": ["classify", "categorize", "label", "tag", "identify type"],
                "analyze": ["analyze", "analysis", "examine", "investigate"],
            }

            for task, keywords in task_keywords.items():
                if any(keyword in prompt_lower for keyword in keywords):
                    task_type = task
                    break

            # Estimate content length
            content_length = len(request.prompt)

            # Select best model based on provider, task, and content length
            selected_model = self.select_model_for_task(
                provider_name=provider_name,
                task_type=task_type,
                content_length=content_length,
            )

            if selected_model:
                request.model = selected_model
            elif self.default_model:
                request.model = self.default_model

        # Get completion from the selected provider
        try:
            logger.info(
                f"Routing completion request to {provider_name} provider with model {request.model or 'default'}"
            )
            response = await provider.get_completion(request)
            return response
        except Exception as e:
            logger.error(f"Error getting completion from {provider_name}: {e}")

            # Try fallback to default provider if different from requested
            if provider_name != self.default_provider:
                try:
                    fallback_provider = self.providers[self.default_provider]
                    logger.info(f"Falling back to {self.default_provider} provider")
                    return await fallback_provider.get_completion(request)
                except Exception as fallback_error:
                    logger.error(
                        f"Fallback to {self.default_provider} also failed: {fallback_error}"
                    )

            # Return error response
            return AICompletionResponse(
                text=f"Error: {str(e)}",
                provider=provider_name,
                model=request.model or "unknown",
                metadata={"error": str(e)},
            )

    def get_available_providers(self) -> List[str]:
        """
        Get a list of available provider names.

        Returns:
            List of provider names
        """
        return list(self.providers.keys())

    def get_available_models(self, provider_name: Optional[str] = None) -> List[str]:
        """
        Get a list of available models for a specific provider or all providers.

        Args:
            provider_name: Optional name of provider to get models for

        Returns:
            List of model identifiers
        """
        if provider_name and provider_name in self.providers:
            return self.providers[provider_name].get_available_models()

        # If no provider specified or not found, return all models from all providers
        all_models = []
        for provider in self.providers.values():
            all_models.extend(provider.get_available_models())

        return all_models

    def select_provider_for_task(self, request: AICompletionRequest) -> str:
        """
        Intelligently select the best provider for a given task based on the request.

        Args:
            request: AICompletionRequest with prompt and parameters

        Returns:
            Provider name string
        """
        # Enhanced routing logic based on task requirements, prompt complexity, and model capabilities
        try:
            # Estimate token count (very rough approximation)
            estimated_tokens = len(request.prompt.split()) * 1.3

            # Check if a specific model is requested
            if request.model:
                # If model is a Hugging Face model and provider is available, use it
                try:
                    from models.huggingface_model_registry import \
                        model_registry

                    if (
                        request.model in model_registry.get_all_model_ids()
                        and "huggingface" in self.providers
                    ):
                        return "huggingface"
                except ImportError:
                    # Model registry not available, fall back to other selection methods
                    pass

            # For very long prompts, prefer models with larger context windows
            if estimated_tokens > 8000:
                if "anthropic" in self.providers:
                    return "anthropic"  # Claude has large context window
                elif "openai" in self.providers:
                    return "openai"  # GPT models have large context windows

            # Task-specific routing based on prompt content
            prompt_lower = request.prompt.lower()

            # For complex reasoning, creative, or analytical tasks, prefer Claude or GPT
            complex_keywords = [
                "analyze",
                "explain",
                "compare",
                "evaluate",
                "synthesize",
                "reason",
                "critique",
                "assess",
                "review",
                "examine",
            ]
            if any(keyword in prompt_lower for keyword in complex_keywords):
                if "anthropic" in self.providers:
                    return "anthropic"  # Claude excels at complex reasoning
                elif "openai" in self.providers:
                    return "openai"  # GPT is also good at reasoning

            # For specific NLP tasks, prefer Hugging Face specialized models
            nlp_tasks = {
                "summarize": ["summarize", "summary", "condense", "shorten"],
                "translate": [
                    "translate",
                    "translation",
                    "convert to",
                    "in french",
                    "in spanish",
                ],
                "sentiment": ["sentiment", "feeling", "emotion", "attitude", "opinion"],
                "question": [
                    "answer this question",
                    "find in the text",
                    "extract from passage",
                ],
                "classify": ["classify", "categorize", "label", "tag", "identify type"],
            }

            # Check if prompt contains any NLP task keywords
            for task, keywords in nlp_tasks.items():
                if (
                    any(keyword in prompt_lower for keyword in keywords)
                    and "huggingface" in self.providers
                ):
                    return "huggingface"  # Hugging Face has specialized models for these tasks

            # For creative content generation
            creative_keywords = [
                "creative",
                "story",
                "poem",
                "write",
                "generate",
                "imagine",
            ]
            if any(keyword in prompt_lower for keyword in creative_keywords):
                if "openai" in self.providers:
                    return "openai"  # GPT is good at creative content
                elif "anthropic" in self.providers:
                    return "anthropic"  # Claude is also good at creative content

            # Default to the router's default provider
            return self.default_provider
        except Exception as e:
            logger.error(f"Error in provider selection: {e}")
            return self.default_provider

    def select_model_for_task(
        self,
        provider_name: str,
        task_type: str,
        content_length: Optional[int] = None,
        performance_priority: str = "balanced",
    ) -> Optional[str]:
        """
        Select the best model for a specific task and provider.

        Args:
            provider_name: Name of the provider
            task_type: Type of task to perform
            content_length: Optional length of content to process
            performance_priority: Priority (speed, quality, balanced)

        Returns:
            Model identifier or None if no suitable model found
        """
        # For Hugging Face, use the model registry if available
        if provider_name == "huggingface":
            try:
                from models.huggingface_model_registry import model_registry

                # Map task type to Hugging Face task
                task_mapping = {
                    "summarize": "summarization",
                    "translate": "translation",
                    "sentiment": "sentiment-analysis",
                    "question": "question-answering",
                    "generate": "text-generation",
                    "classify": "text-classification",
                }

                hf_task = task_mapping.get(task_type, "text-generation")

                # Map performance priority to size and speed preferences
                size_mapping = {
                    "speed": "small",
                    "balanced": "medium",
                    "quality": "large",
                }

                speed_mapping = {
                    "speed": "fast",
                    "balanced": "medium",
                    "quality": "slow",
                }

                # Select model from registry
                model_metadata = model_registry.select_model_for_task(
                    task=hf_task,
                    size_preference=size_mapping.get(performance_priority, "medium"),
                    speed_preference=speed_mapping.get(performance_priority, "medium"),
                )

                if model_metadata:
                    return model_metadata.id
            except ImportError:
                # Model registry not available, fall back to default model selection
                pass

        # For OpenAI, select based on task and content length
        elif provider_name == "openai":
            if task_type in ["summarize", "translate", "sentiment"]:
                return "gpt-3.5-turbo"  # Good balance for most tasks
            elif task_type in ["question", "generate"] and (content_length or 0) > 4000:
                return "gpt-4"  # Better for complex or long content
            else:
                return "gpt-3.5-turbo"  # Default

        # For Anthropic, select based on task complexity
        elif provider_name == "anthropic":
            if (
                task_type in ["question", "generate", "analyze"]
                and performance_priority == "quality"
            ):
                return "claude-2"  # Best quality for complex tasks
            else:
                return "claude-instant-1"  # Faster for most tasks

        # If no specific selection logic, return None to use provider's default
        return None
