"""
Agents for The HigherSelf Network Server.

This package contains agent implementations for various automation tasks,
aligned with the 16-database Notion structure and the comprehensive automation map.

The agent system features named personalities, each with a distinct tone and focus area:
- Nyra: Lead Capture Specialist (intuitive & responsive)
- Solari: Booking & Order Manager (clear & luminous)
- Ruvo: Task Orchestrator (grounded & task-driven)
- Liora: Marketing Strategist (elegant & strategic)
- Sage: Community Curator (warm & connected)
- Elan: Content Choreographer (creative & adaptive)
- Zevi: Audience Analyst (analytical & sharp)
- Atlas: Knowledge Retrieval Specialist (knowledgeable & resourceful)

All agents maintain Notion as the central hub for data storage and processing.
"""

# Import agent personalities
from agents.agent_personalities import Elan  # ContentLifecycleAgent
from agents.agent_personalities import Liora  # MarketingCampaignAgent
from agents.agent_personalities import Nyra  # LeadCaptureAgent
from agents.agent_personalities import Ruvo  # TaskManagementAgent
from agents.agent_personalities import Sage  # CommunityEngagementAgent
from agents.agent_personalities import Solari  # BookingAgent
from agents.agent_personalities import Zevi  # AudienceSegmentationAgent
from agents.agent_personalities import (
    GraceFields,
    create_agent_collective,
    create_grace_orchestrator,
)
from agents.audience_segmentation_agent import AudienceSegmentationAgent
from agents.base_agent import BaseAgent
from agents.booking_agent import BookingAgent
from agents.community_engagement_agent import CommunityEngagementAgent
from agents.content_lifecycle_agent import ContentLifecycleAgent
from agents.lead_capture_agent import LeadCaptureAgent
from agents.marketing_campaign_agent import MarketingCampaignAgent
from agents.rag_agent import Atlas, RAGAgent  # Knowledge Retrieval Specialist
from agents.task_management_agent import TaskManagementAgent

__all__ = [
    # Base agent class
    "BaseAgent",
    # Original agent implementations
    "LeadCaptureAgent",
    "BookingAgent",
    "ContentLifecycleAgent",
    "AudienceSegmentationAgent",
    "TaskManagementAgent",
    "MarketingCampaignAgent",
    "CommunityEngagementAgent",
    "RAGAgent",
    # Named agent personalities
    "Nyra",  # LeadCaptureAgent
    "Solari",  # BookingAgent
    "Ruvo",  # TaskManagementAgent
    "Liora",  # MarketingCampaignAgent
    "Sage",  # CommunityEngagementAgent
    "Elan",  # ContentLifecycleAgent
    "Zevi",  # AudienceSegmentationAgent
    "Atlas",  # RAGAgent
    # Orchestration
    "GraceFields",
    "create_agent_collective",
    "create_grace_orchestrator",
]
