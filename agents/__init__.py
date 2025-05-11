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

All agents maintain Notion as the central hub for data storage and processing.
"""

from agents.base_agent import BaseAgent
from agents.lead_capture_agent import LeadCaptureAgent
from agents.booking_agent import BookingAgent
from agents.content_lifecycle_agent import ContentLifecycleAgent
from agents.audience_segmentation_agent import AudienceSegmentationAgent
from agents.task_management_agent import TaskManagementAgent
from agents.marketing_campaign_agent import MarketingCampaignAgent
from agents.community_engagement_agent import CommunityEngagementAgent

# Import agent personalities
from agents.agent_personalities import (
    Nyra,  # LeadCaptureAgent
    Solari,  # BookingAgent
    Ruvo,  # TaskManagementAgent
    Liora,  # MarketingCampaignAgent
    Sage,  # CommunityEngagementAgent
    Elan,  # ContentLifecycleAgent
    Zevi,  # AudienceSegmentationAgent
    GraceOrchestrator,
    create_agent_collective,
    create_grace_orchestrator
)

__all__ = [
    # Base agent class
    'BaseAgent',
    
    # Original agent implementations
    'LeadCaptureAgent',
    'BookingAgent',
    'ContentLifecycleAgent',
    'AudienceSegmentationAgent',
    'TaskManagementAgent',
    'MarketingCampaignAgent',
    'CommunityEngagementAgent',
    
    # Named agent personalities
    'Nyra',   # LeadCaptureAgent
    'Solari', # BookingAgent
    'Ruvo',   # TaskManagementAgent
    'Liora',  # MarketingCampaignAgent
    'Sage',   # CommunityEngagementAgent
    'Elan',   # ContentLifecycleAgent
    'Zevi',   # AudienceSegmentationAgent
    
    # Orchestration
    'GraceOrchestrator',
    'create_agent_collective',
    'create_grace_orchestrator'
]
