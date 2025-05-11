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

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from loguru import logger

from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import WorkflowInstance, ContentItem, ContentPlan
from agents.base_agent import BaseAgent
from services.notion_service import NotionService


class ContentType(str, Enum):
    """Types of content handled by the ContentLifecycleAgent."""
    BLOG_POST = "blog_post"
    SOCIAL_MEDIA = "social_media"
    EMAIL_NEWSLETTER = "email_newsletter"
    VIDEO_SCRIPT = "video_script"
    PODCAST_SCRIPT = "podcast_script"
    COURSE_MATERIAL = "course_material"
    WORKSHOP_MATERIAL = "workshop_material"


class ContentStage(str, Enum):
    """Stages in the content lifecycle workflow."""
    IDEA = "idea"
    RESEARCH = "research"
    DRAFT = "draft"
    REVIEW = "review"
    MEDIA_CREATION = "media_creation"
    FINAL = "final"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ContentPlatform(str, Enum):
    """Distribution platforms for content."""
    WORDPRESS = "wordpress"
    BEEHIIV = "beehiiv"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TUTORM = "tutorm"


class ContentRequest(BaseModel):
    """Model for a content creation request."""
    title: str
    content_type: ContentType
    brief: str
    audience: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    target_platforms: List[ContentPlatform] = Field(default_factory=list)
    required_media: bool = False
    target_completion_date: Optional[datetime] = None
    references: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)


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
        perplexity_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        plaud_api_key: Optional[str] = None,
        beehiiv_api_key: Optional[str] = None,
        notion_service: Optional[NotionService] = None
    ):
        """
        Initialize the Content Lifecycle Agent.
        
        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            version: Agent version
            business_entities: Associated business entities
            perplexity_api_key: API key for Perplexity research
            openai_api_key: API key for OpenAI (GPT)
            anthropic_api_key: API key for Anthropic (Claude)
            plaud_api_key: API key for Plaud transcription
            beehiiv_api_key: API key for Beehiiv newsletter
            notion_service: Optional NotionService instance
        """
        capabilities = [
            AgentCapability.CONTENT_CREATION,
            AgentCapability.CONTENT_DISTRIBUTION,
            AgentCapability.AI_INTEGRATION
        ]
        
        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.PERPLEXITY,
            ApiPlatform.OPENAI,
            ApiPlatform.ANTHROPIC,
            ApiPlatform.BEEHIIV,
            ApiPlatform.WORDPRESS
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities,
            notion_service=notion_service
        )
        
        # Set up API credentials - retrieve from environment if not provided
        self.perplexity_api_key = perplexity_api_key or os.environ.get("PERPLEXITY_API_KEY")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.plaud_api_key = plaud_api_key or os.environ.get("PLAUD_API_KEY")
        self.beehiiv_api_key = beehiiv_api_key or os.environ.get("BEEHIIV_API_KEY")
        
        self.logger.info("Content Lifecycle Agent initialized")
    
    async def generate_content_ideas(
        self,
        business_entity_id: str,
        topic_area: str,
        count: int = 5,
        content_type: Optional[ContentType] = None
    ) -> Dict[str, Any]:
        """
        Generate content ideas using Perplexity for research.
        Stores results in Notion as the central hub.
        
        Args:
            business_entity_id: Business entity ID
            topic_area: General topic to generate ideas about
            count: Number of ideas to generate
            content_type: Optional specific content type
            
        Returns:
            Generated ideas
        """
        self.logger.info(f"Generating {count} content ideas for topic: {topic_area}")
        
        # This would use Perplexity API in a full implementation
        # For now, simulate idea generation
        ideas = []
        for i in range(count):
            ideas.append({
                "title": f"Sample idea {i+1} for {topic_area}",
                "brief": f"This is a potential content piece about {topic_area}",
                "content_type": content_type.value if content_type else ContentType.BLOG_POST.value,
                "keywords": [f"{topic_area}", "sample", f"keyword{i}"]
            })
        
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
                created_by=self.agent_id
            )
            
            item_id = await notion_svc.create_page(content_item)
            idea["notion_id"] = item_id
            stored_ideas.append(idea)
        
        self.logger.info(f"Generated and stored {len(stored_ideas)} content ideas in Notion")
        
        return {
            "status": "success",
            "ideas": stored_ideas,
            "topic_area": topic_area,
            "business_entity_id": business_entity_id
        }
    
    async def research_content_topic(
        self,
        content_item_id: str,
        depth: str = "medium"
    ) -> Dict[str, Any]:
        """
        Research a content topic using Perplexity.
        Stores research results in Notion as the central hub.
        
        Args:
            content_item_id: Notion ID of the content item
            depth: Research depth (shallow, medium, deep)
            
        Returns:
            Research results
        """
        self.logger.info(f"Researching content item {content_item_id} with {depth} depth")
        
        # Get content item from Notion
        notion_svc = await self.notion_service
        content_item = await notion_svc.get_page(ContentItem, content_item_id)
        
        if not content_item:
            return {
                "status": "error",
                "message": f"Content item {content_item_id} not found"
            }
        
        # This would use Perplexity API in a full implementation
        # For now, simulate research results
        research_results = {
            "summary": f"Research summary for {content_item.title}",
            "key_points": [
                "Key finding 1",
                "Key finding 2",
                "Key finding 3"
            ],
            "sources": [
                {"title": "Source 1", "url": "https://example.com/1"},
                {"title": "Source 2", "url": "https://example.com/2"}
            ]
        }
        
        # Update content item in Notion with research results
        content_item.research_data = research_results
        content_item.stage = ContentStage.RESEARCH.value
        content_item.last_updated = datetime.now()
        
        await notion_svc.update_page(content_item)
        
        self.logger.info(f"Updated content item {content_item_id} with research data in Notion")
        
        return {
            "status": "success",
            "content_item_id": content_item_id,
            "research_results": research_results
        }
    
    async def generate_content_draft(
        self,
        content_item_id: str,
        llm_provider: str = "anthropic"
    ) -> Dict[str, Any]:
        """
        Generate a content draft using an LLM.
        Stores draft in Notion as the central hub.
        
        Args:
            content_item_id: Notion ID of the content item
            llm_provider: Which LLM to use (anthropic/claude or openai/gpt)
            
        Returns:
            Generated draft
        """
        self.logger.info(f"Generating content draft for {content_item_id} using {llm_provider}")
        
        # Get content item from Notion
        notion_svc = await self.notion_service
        content_item = await notion_svc.get_page(ContentItem, content_item_id)
        
        if not content_item:
            return {
                "status": "error",
                "message": f"Content item {content_item_id} not found"
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
        
        self.logger.info(f"Updated content item {content_item_id} with draft content in Notion")
        
        return {
            "status": "success",
            "content_item_id": content_item_id,
            "draft_content": draft_content
        }
    
    async def process_transcription(
        self,
        audio_url: str,
        business_entity_id: str,
        content_type: ContentType = ContentType.BLOG_POST,
        title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process audio transcription using Plaud.
        Stores transcription in Notion as the central hub.
        
        Args:
            audio_url: URL to the audio file
            business_entity_id: Business entity ID
            content_type: Type of content to create
            title: Optional title for the content
            
        Returns:
            Transcription results
        """
        self.logger.info(f"Processing transcription from {audio_url}")
        
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
            created_by=self.agent_id
        )
        
        item_id = await notion_svc.create_page(content_item)
        
        self.logger.info(f"Created content item {item_id} with transcription in Notion")
        
        return {
            "status": "success",
            "content_item_id": item_id,
            "transcription": transcription
        }
    
    async def distribute_content(
        self,
        content_item_id: str,
        platforms: List[ContentPlatform]
    ) -> Dict[str, Any]:
        """
        Distribute content to specified platforms.
        Updates distribution status in Notion as the central hub.
        
        Args:
            content_item_id: Notion ID of the content item
            platforms: List of platforms to distribute to
            
        Returns:
            Distribution results
        """
        self.logger.info(f"Distributing content {content_item_id} to {platforms}")
        
        # Get content item from Notion
        notion_svc = await self.notion_service
        content_item = await notion_svc.get_page(ContentItem, content_item_id)
        
        if not content_item:
            return {
                "status": "error",
                "message": f"Content item {content_item_id} not found"
            }
        
        # Ensure content is in final stage
        if content_item.stage != ContentStage.FINAL.value:
            return {
                "status": "error",
                "message": f"Content must be in FINAL stage for distribution, current stage: {content_item.stage}"
            }
        
        # This would use the appropriate platform APIs in a full implementation
        # For now, simulate distribution
        distribution_results = {}
        
        for platform in platforms:
            distribution_results[platform.value] = {
                "status": "success",
                "url": f"https://example.com/{platform.value}/{content_item_id}",
                "timestamp": datetime.now().isoformat()
            }
        
        # Update content item in Notion with distribution results
        if not content_item.distribution_data:
            content_item.distribution_data = {}
            
        content_item.distribution_data.update(distribution_results)
        content_item.stage = ContentStage.PUBLISHED.value
        content_item.last_updated = datetime.now()
        
        await notion_svc.update_page(content_item)
        
        self.logger.info(f"Updated content item {content_item_id} with distribution data in Notion")
        
        return {
            "status": "success",
            "content_item_id": content_item_id,
            "distribution_results": distribution_results
        }
    
    async def create_content_plan(
        self,
        business_entity_id: str,
        plan_name: str,
        content_types: List[ContentType],
        duration_weeks: int,
        frequency: Dict[str, int]
    ) -> Dict[str, Any]:
        """
        Create a content plan in Notion.
        
        Args:
            business_entity_id: Business entity ID
            plan_name: Name of the content plan
            content_types: Types of content to include
            duration_weeks: Duration of the plan in weeks
            frequency: Publishing frequency by content type
            
        Returns:
            Created content plan
        """
        self.logger.info(f"Creating content plan: {plan_name}")
        
        # Create content plan in Notion
        notion_svc = await self.notion_service
        
        content_plan = ContentPlan(
            name=plan_name,
            business_entity_id=business_entity_id,
            duration_weeks=duration_weeks,
            content_types=[ct.value for ct in content_types],
            frequency=frequency,
            created_by=self.agent_id
        )
        
        plan_id = await notion_svc.create_page(content_plan)
        
        self.logger.info(f"Created content plan {plan_id} in Notion")
        
        return {
            "status": "success",
            "plan_id": plan_id,
            "plan_name": plan_name
        }
    
    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an event received by this agent.
        
        Args:
            event_type: Type of event
            event_data: Event data
            
        Returns:
            Processing result
        """
        if event_type == "generate_content_ideas":
            return await self.generate_content_ideas(
                business_entity_id=event_data.get("business_entity_id"),
                topic_area=event_data.get("topic_area"),
                count=event_data.get("count", 5),
                content_type=event_data.get("content_type")
            )
        elif event_type == "research_content_topic":
            return await self.research_content_topic(
                content_item_id=event_data.get("content_item_id"),
                depth=event_data.get("depth", "medium")
            )
        elif event_type == "generate_content_draft":
            return await self.generate_content_draft(
                content_item_id=event_data.get("content_item_id"),
                llm_provider=event_data.get("llm_provider", "anthropic")
            )
        elif event_type == "process_transcription":
            return await self.process_transcription(
                audio_url=event_data.get("audio_url"),
                business_entity_id=event_data.get("business_entity_id"),
                content_type=event_data.get("content_type", ContentType.BLOG_POST),
                title=event_data.get("title")
            )
        elif event_type == "distribute_content":
            return await self.distribute_content(
                content_item_id=event_data.get("content_item_id"),
                platforms=event_data.get("platforms", [])
            )
        else:
            return {
                "status": "error",
                "message": f"Unsupported event type: {event_type}"
            }
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.
        
        Returns:
            Health check result
        """
        health_checks = {
            "notion_api": False,
            "perplexity_api": False,
            "llm_api": False,
            "distribution_apis": False
        }
        
        # Check Notion API
        try:
            notion_svc = await self.notion_service
            # Try to query a database to verify connection
            await notion_svc.query_database(ContentItem, limit=1)
            health_checks["notion_api"] = True
        except Exception as e:
            self.logger.error(f"Notion API health check failed: {e}")
        
        # Check Perplexity API (mock check for now)
        if self.perplexity_api_key:
            health_checks["perplexity_api"] = True
        
        # Check LLM API (mock check for now)
        if self.openai_api_key or self.anthropic_api_key:
            health_checks["llm_api"] = True
        
        # Check distribution APIs (mock check for now)
        if self.beehiiv_api_key:
            health_checks["distribution_apis"] = True
        
        return {
            "agent_id": self.agent_id,
            "status": "healthy" if all(health_checks.values()) else "degraded",
            "checks": health_checks,
            "timestamp": datetime.now().isoformat()
        }