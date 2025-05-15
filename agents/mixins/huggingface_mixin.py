"""
Hugging Face Mixin for Agents

This module provides a mixin that can be used by any agent to easily access
Hugging Face capabilities with intelligent model selection.
"""

from typing import Dict, List, Any, Optional, Tuple
from loguru import logger

from models.huggingface_model_registry import model_registry, ModelMetadata
from services.agent_model_service import AgentModelRequest, AgentModelService
from services.ai_router import AIRouter
from services.ai_providers import AICompletionRequest, AICompletionResponse
from models.base import AgentCapability


class HuggingFaceMixin:
    """
    Mixin that provides Hugging Face capabilities to any agent.
    
    This mixin can be used by any agent to easily access Hugging Face models
    with intelligent model selection based on the agent's capabilities and needs.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the Hugging Face mixin."""
        # Store reference to AI router if provided
        self.ai_router = kwargs.get('ai_router')
        
        # Create agent model service
        self.agent_model_service = None
        
        # Call parent init if exists
        super_init = getattr(super(), '__init__', None)
        if super_init:
            super_init(*args, **kwargs)
    
    async def setup_huggingface(self, ai_router: Optional[AIRouter] = None):
        """
        Set up Hugging Face integration for this agent.
        
        Args:
            ai_router: Optional AIRouter instance
        """
        if ai_router:
            self.ai_router = ai_router
        
        # Create agent model service if not already created
        if not self.agent_model_service and self.ai_router:
            self.agent_model_service = AgentModelService(ai_router=self.ai_router)
            logger.info(f"Hugging Face integration set up for agent {self.agent_id}")
    
    async def get_huggingface_completion(self, 
                                        task_type: str, 
                                        content: str,
                                        language: str = "en",
                                        performance_priority: Optional[str] = None) -> str:
        """
        Get a completion from the best Hugging Face model for this agent and task.
        
        Args:
            task_type: Type of task to perform
            content: Content to process
            language: Language of the content
            performance_priority: Optional priority override (speed, quality, balanced)
            
        Returns:
            Generated text from the model
        """
        if not self.agent_model_service:
            if not self.ai_router:
                raise ValueError("AI Router not available. Call setup_huggingface first.")
            await self.setup_huggingface(self.ai_router)
        
        # Create request
        request = AgentModelRequest(
            agent_id=self.agent_id,
            agent_capabilities=getattr(self, 'capabilities', []),
            task_type=task_type,
            content=content,
            content_language=language,
            performance_priority=performance_priority
        )
        
        # Process request
        try:
            response = await self.agent_model_service.process_agent_request(request)
            return response.text
        except Exception as e:
            logger.error(f"Error getting Hugging Face completion: {e}")
            return f"Error: {str(e)}"
    
    async def summarize_text(self, text: str, language: str = "en") -> str:
        """
        Summarize text using the best Hugging Face model for this agent.
        
        Args:
            text: Text to summarize
            language: Language of the text
            
        Returns:
            Summarized text
        """
        return await self.get_huggingface_completion(
            task_type="summarize_content",
            content=text,
            language=language
        )
    
    async def generate_text(self, prompt: str, language: str = "en") -> str:
        """
        Generate text using the best Hugging Face model for this agent.
        
        Args:
            prompt: Prompt to generate from
            language: Language to generate in
            
        Returns:
            Generated text
        """
        return await self.get_huggingface_completion(
            task_type="generate_text",
            content=prompt,
            language=language
        )
    
    async def translate_text(self, text: str, source_lang: str = "en", target_lang: str = "fr") -> str:
        """
        Translate text using the best Hugging Face model for this agent.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        # Map language pair to task type
        task_type = f"translate_{source_lang}_to_{target_lang}"
        
        return await self.get_huggingface_completion(
            task_type=task_type,
            content=text,
            language=source_lang
        )
    
    async def analyze_sentiment(self, text: str, language: str = "en") -> str:
        """
        Analyze sentiment of text using the best Hugging Face model for this agent.
        
        Args:
            text: Text to analyze
            language: Language of the text
            
        Returns:
            Sentiment analysis result
        """
        return await self.get_huggingface_completion(
            task_type="sentiment_analysis",
            content=text,
            language=language
        )
    
    async def answer_question(self, question: str, context: str, language: str = "en") -> str:
        """
        Answer a question using the best Hugging Face model for this agent.
        
        Args:
            question: Question to answer
            context: Context for the question
            language: Language of the question and context
            
        Returns:
            Answer to the question
        """
        # Combine question and context
        content = f"Question: {question}\n\nContext: {context}"
        
        return await self.get_huggingface_completion(
            task_type="answer_question",
            content=content,
            language=language
        )
    
    def get_available_huggingface_tasks(self) -> List[str]:
        """
        Get a list of available Hugging Face tasks.
        
        Returns:
            List of task names
        """
        return model_registry.get_all_tasks()
    
    def get_recommended_models_for_task(self, task: str) -> List[Dict[str, Any]]:
        """
        Get recommended models for a specific task.
        
        Args:
            task: Task name
            
        Returns:
            List of model information dictionaries
        """
        models = model_registry.get_models_for_task(task)
        return [
            {
                "id": model.id,
                "description": model.description,
                "size_category": model.size_category,
                "inference_speed": model.inference_speed,
                "recommended_for": model.recommended_for
            }
            for model in models
        ]
