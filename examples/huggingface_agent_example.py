"""
Example of using the Hugging Face mixin in an agent.

This example shows how to create an agent that uses the Hugging Face mixin
to access Hugging Face models with intelligent model selection.
"""

import asyncio
import os
from typing import Any, Dict, List

from loguru import logger

from agents.base_agent import BaseAgent
from agents.mixins.huggingface_mixin import HuggingFaceMixin
from models.base import AgentCapability, ApiPlatform
from services.ai_router import AIRouter
from services.notion_service import NotionService


class ContentProcessingAgent(BaseAgent, HuggingFaceMixin):
    """
    Example agent that uses the Hugging Face mixin for content processing.

    This agent demonstrates how to use the Hugging Face mixin to access
    Hugging Face models with intelligent model selection.
    """

    def __init__(
        self,
        agent_id: str = "content_processing_agent",
        name: str = "Content Processing Agent",
        description: str = "Processes content using Hugging Face models",
        ai_router: AIRouter = None,
        notion_service: NotionService = None,
    ):
        """Initialize the Content Processing Agent."""
        # Initialize base agent
        BaseAgent.__init__(
            self,
            agent_id=agent_id,
            name=name,
            description=description,
            capabilities=[
                AgentCapability.CONTENT_CREATION,
                AgentCapability.AI_INTEGRATION,
                AgentCapability.ANALYTICS_PROCESSING,
            ],
            apis_utilized=[ApiPlatform.NOTION, ApiPlatform.HUGGINGFACE],
            notion_service=notion_service,
        )

        # Initialize Hugging Face mixin
        HuggingFaceMixin.__init__(self, ai_router=ai_router)

        logger.info(f"Content Processing Agent initialized: {agent_id}")

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process an event received by this agent.

        Args:
            event_type: Type of event
            event_data: Event data

        Returns:
            Processing result
        """
        logger.info(f"Processing event: {event_type}")

        if event_type == "content_summarize":
            # Summarize content
            text = event_data.get("content", "")
            summary = await self.summarize_text(text)
            return {"summary": summary}

        elif event_type == "content_translate":
            # Translate content
            text = event_data.get("content", "")
            source_lang = event_data.get("source_language", "en")
            target_lang = event_data.get("target_language", "fr")
            translation = await self.translate_text(text, source_lang, target_lang)
            return {"translation": translation}

        elif event_type == "content_sentiment":
            # Analyze sentiment
            text = event_data.get("content", "")
            sentiment = await self.analyze_sentiment(text)
            return {"sentiment": sentiment}

        elif event_type == "content_generate":
            # Generate content
            prompt = event_data.get("prompt", "")
            generated_text = await self.generate_text(prompt)
            return {"generated_text": generated_text}

        elif event_type == "content_qa":
            # Answer question
            question = event_data.get("question", "")
            context = event_data.get("context", "")
            answer = await self.answer_question(question, context)
            return {"answer": answer}

        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {"error": f"Unknown event type: {event_type}"}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.

        Returns:
            Health check result
        """
        # Check if Hugging Face integration is set up
        huggingface_ready = self.agent_model_service is not None

        return {
            "status": "healthy" if huggingface_ready else "degraded",
            "huggingface_integration": "ready" if huggingface_ready else "not_ready",
            "available_tasks": self.get_available_huggingface_tasks()
            if huggingface_ready
            else [],
        }


async def main():
    """Run a simple example of the Content Processing Agent."""
    # Create AI Router
    ai_router = AIRouter()
    await ai_router.initialize()

    # Create agent
    agent = ContentProcessingAgent(ai_router=ai_router)

    # Set up Hugging Face integration
    await agent.setup_huggingface(ai_router)

    # Process some example events
    summarize_result = await agent.process_event(
        "content_summarize",
        {
            "content": "The HigherSelf Network Server is a comprehensive automation platform that integrates with various services including Notion, Hugging Face, and more. It features a system of specialized agents, each with distinct capabilities and personalities, working together to automate business processes while maintaining Notion as the central data hub."
        },
    )

    sentiment_result = await agent.process_event(
        "content_sentiment",
        {
            "content": "I absolutely love the new features in the latest update! The interface is much more intuitive and responsive."
        },
    )

    # Print results
    print("\nSummarization Result:")
    print(summarize_result["summary"])

    print("\nSentiment Analysis Result:")
    print(sentiment_result["sentiment"])

    # Check agent health
    health = await agent.check_health()
    print("\nAgent Health:")
    print(health)


if __name__ == "__main__":
    # Set up environment variables for testing
    os.environ["HUGGINGFACE_API_KEY"] = "your_api_key_here"

    # Run the example
    asyncio.run(main())
