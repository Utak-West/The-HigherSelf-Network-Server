"""
Content Lifecycle Agent for The HigherSelf Network.

This agent manages the complete content lifecycle including:
- Idea generation using Perplexity research
- Content drafting using LLMs (Claude/ChatGPT)
- Media creation integration with tools like Canva/Invoke
- Transcription using Plaud
- Distribution to platforms like Beehiiv, Instagram, WordPress

All operations maintain Notion as the central data hub.
"""

import asyncio
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from loguru import logger

from agents.base_agent import BaseAgent
from models.base import AgentCapability, ApiPlatform
from models.content_models import (
    ContentPlatform,
    ContentRequest,
    ContentStage,
    ContentType,
    ResearchData,
)
from models.notion_db_models import ContentItem, ContentPlan, WorkflowInstance
from services.notion_service import NotionService


class ContentLifecycleAgent(BaseAgent):
    """
    Agent that manages the complete content lifecycle from idea to distribution.
    Uses Notion as the central hub for all content data and workflows.
    """

    def __init__(
        self,
        agent_id: str = "ContentLifecycleAgent",
        name: str = "Content Lifecycle Agent",
        description: str = "Manages content from idea to distribution",
        version: str = "1.0.0",
        business_entities: List[str] = None,
        api_keys: Dict[str, str] = None,
        notion_service: Optional[NotionService] = None,
    ):
        """Initialize the Content Lifecycle Agent."""
        capabilities = [
            AgentCapability.CONTENT_CREATION,
            AgentCapability.CONTENT_DISTRIBUTION,
            AgentCapability.AI_INTEGRATION,
        ]

        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.PERPLEXITY,
            ApiPlatform.OPENAI,
            ApiPlatform.ANTHROPIC,
            ApiPlatform.BEEHIIV,
            ApiPlatform.WORDPRESS,
        ]

        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
            notion_service=notion_service,
        )

        # Set up API credentials
        self.api_keys = api_keys or {}

        # Retrieve API keys from environment if not provided
        api_key_names = [
            "PERPLEXITY_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "PLAUD_API_KEY",
            "BEEHIIV_API_KEY",
        ]

        for key_name in api_key_names:
            if key_name not in self.api_keys and os.environ.get(key_name):
                self.api_keys[key_name] = os.environ.get(key_name)

        self.logger.info("Content Lifecycle Agent initialized")

    async def generate_content_ideas(
        self,
        business_entity_id: str,
        topic_area: str,
        count: int = 5,
        content_type: Optional[ContentType] = None,
    ) -> Dict[str, Any]:
        """
        Generate content ideas using Perplexity for research.
        Stores results in Notion as the central hub.
        """
        self.logger.info(f"Generating {count} content ideas for topic: {topic_area}")

        # This would use Perplexity API in a full implementation
        # For now, simulate idea generation
        ideas = []
        for i in range(count):
            ideas.append(
                {
                    "title": f"Sample idea {i+1} for {topic_area}",
                    "brief": f"This is a potential content piece about {topic_area}",
                    "content_type": (
                        content_type.value
                        if content_type
                        else ContentType.BLOG_POST.value
                    ),
                    "keywords": [f"{topic_area}", "sample", f"keyword{i}"],
                }
            )

        # Store ideas in Notion (central hub)
        notion_svc = await self.notion_service
        stored_ideas = []

        for idea in ideas:
            content_item = ContentItem(
                title=idea["title"],
                content_type=idea["content_type"],
                stage=ContentStage.IDEA.value,
                brief=idea["brief"],
                keywords=idea["keywords"],
                business_entity_id=business_entity_id,
                created_by=self.agent_id,
            )

            item_id = await notion_svc.create_page(content_item)
            idea["notion_id"] = item_id
            stored_ideas.append(idea)

        return {"status": "success", "ideas": stored_ideas, "topic_area": topic_area}

    async def research_content_topic(
        self, content_item_id: str, depth: str = "medium"
    ) -> Dict[str, Any]:
        """
        Research a content topic using Perplexity.
        Stores research results in Notion as the central hub.
        """
        notion_svc = await self.notion_service
        content_item = await notion_svc.get_page(ContentItem, content_item_id)

        if not content_item:
            return {
                "status": "error",
                "message": f"Content item {content_item_id} not found",
            }

        # This would use Perplexity API in a full implementation
        # For now, simulate research results
        research_results = {
            "summary": f"Research summary for {content_item.title}",
            "key_points": ["Key finding 1", "Key finding 2", "Key finding 3"],
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"},
            ],
        }

        # Update content item in Notion with research results
        content_item.research_data = research_results
        content_item.stage = ContentStage.RESEARCH.value
        content_item.last_updated = datetime.now()

        await notion_svc.update_page(content_item)

        return {
            "status": "success",
            "content_item_id": content_item_id,
            "research_results": research_results,
        }

    async def generate_content_draft(
        self, content_item_id: str, llm_provider: str = "anthropic"
    ) -> Dict[str, Any]:
        """
        Generate a content draft using an LLM.
        Stores draft in Notion as the central hub.
        """
        notion_svc = await self.notion_service
        content_item = await notion_svc.get_page(ContentItem, content_item_id)

        if not content_item:
            return {
                "status": "error",
                "message": f"Content item {content_item_id} not found",
            }

        # This would use the appropriate LLM API in a full implementation
        # For now, simulate draft generation
        draft_content = f"# {content_item.title}\n\n"
        draft_content += "## Introduction\n\n"
        draft_content += f"This is a sample draft for {content_item.title}.\n\n"
        draft_content += "## Key Points\n\n"

        if content_item.research_data and "key_points" in content_item.research_data:
            for point in content_item.research_data["key_points"]:
                draft_content += f"- {point}\n"

        draft_content += "\n## Conclusion\n\n"
        draft_content += "This concludes our sample draft.\n"

        # Update content item in Notion with draft
        content_item.draft_content = draft_content
        content_item.stage = ContentStage.DRAFT.value
        content_item.last_updated = datetime.now()

        await notion_svc.update_page(content_item)

        return {
            "status": "success",
            "content_item_id": content_item_id,
            "draft_preview": draft_content[:200] + "...",  # Return just a preview
        }

    async def process_transcription(
        self,
        audio_url: str,
        business_entity_id: str,
        content_type: ContentType = ContentType.BLOG_POST,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process audio transcription using Plaud.
        Stores transcription in Notion as the central hub.
        """
        # This would use Plaud API in a full implementation
        # For now, simulate transcription
        transcription = "This is a sample transcription of audio content."

        # Create content item in Notion
        notion_svc = await self.notion_service

        content_item = ContentItem(
            title=title or f"Transcription {datetime.now().isoformat()}",
            content_type=content_type.value,
            stage=ContentStage.DRAFT.value,
            draft_content=transcription,
            business_entity_id=business_entity_id,
            source_url=audio_url,
            created_by=self.agent_id,
        )

        item_id = await notion_svc.create_page(content_item)

        return {
            "status": "success",
            "content_item_id": item_id,
            "transcription_length": len(transcription),
        }

    async def distribute_content(
        self, content_item_id: str, platforms: List[ContentPlatform]
    ) -> Dict[str, Any]:
        """
        Distribute content to specified platforms.
        Updates distribution status in Notion as the central hub.
        """
        notion_svc = await self.notion_service
        content_item = await notion_svc.get_page(ContentItem, content_item_id)

        if not content_item:
            return {
                "status": "error",
                "message": f"Content item {content_item_id} not found",
            }

        # Ensure content is in final stage
        if content_item.stage != ContentStage.FINAL.value:
            return {
                "status": "error",
                "message": f"Content must be in FINAL stage for distribution, current stage: {content_item.stage}",
            }

        # This would use the appropriate platform APIs in a full implementation
        # For now, simulate distribution
        distribution_results = {}

        for platform in platforms:
            distribution_results[platform.value] = {
                "status": "success",
                "url": f"https://example.com/{platform.value}/{content_item_id}",
                "timestamp": datetime.now().isoformat(),
            }

        # Update content item in Notion with distribution results
        if not content_item.distribution_data:
            content_item.distribution_data = {}

        content_item.distribution_data.update(distribution_results)
        content_item.stage = ContentStage.PUBLISHED.value
        content_item.last_updated = datetime.now()

        await notion_svc.update_page(content_item)

        return {
            "status": "success",
            "content_item_id": content_item_id,
            "platforms": [p.value for p in platforms],
        }

    async def process_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process an event received by this agent."""
        event_handlers = {
            "generate_content_ideas": self.generate_content_ideas,
            "research_content_topic": self.research_content_topic,
            "generate_content_draft": self.generate_content_draft,
            "process_transcription": self.process_transcription,
            "distribute_content": self.distribute_content,
        }

        handler = event_handlers.get(event_type)
        if not handler:
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}",
            }

        try:
            return await handler(**event_data)
        except Exception as e:
            self.logger.error(f"Error processing {event_type}: {e}")
            return {"status": "error", "message": str(e)}

    async def check_health(self) -> Dict[str, Any]:
        """Check the health status of this agent."""
        health_checks = {
            "notion_api": False,
            "perplexity_api": False,
            "llm_api": False,
            "distribution_apis": False,
        }

        # Check Notion API
        try:
            notion_svc = await self.notion_service
            await notion_svc.query_database(ContentItem, limit=1)
            health_checks["notion_api"] = True
        except Exception as e:
            self.logger.error(f"Notion API health check failed: {e}")

        # Check other APIs based on available keys
        health_checks["perplexity_api"] = "PERPLEXITY_API_KEY" in self.api_keys
        health_checks["llm_api"] = (
            "OPENAI_API_KEY" in self.api_keys or "ANTHROPIC_API_KEY" in self.api_keys
        )
        health_checks["distribution_apis"] = "BEEHIIV_API_KEY" in self.api_keys

        return {
            "agent_id": self.agent_id,
            "status": "healthy" if all(health_checks.values()) else "degraded",
            "checks": health_checks,
            "timestamp": datetime.now().isoformat(),
        }
