"""
Agents for The HigherSelf Network Server.

This package contains agent implementations for various automation tasks,
aligned with the 16-database Notion structure and the comprehensive automation map.
"""

from agents.base_agent import BaseAgent
from agents.lead_capture_agent import LeadCaptureAgent
from agents.booking_agent import BookingAgent
from agents.content_lifecycle_agent import ContentLifecycleAgent
from agents.audience_segmentation_agent import AudienceSegmentationAgent
from agents.task_management_agent import TaskManagementAgent
from agents.marketing_campaign_agent import MarketingCampaignAgent
from agents.community_engagement_agent import CommunityEngagementAgent

__all__ = [
    'BaseAgent',
    'LeadCaptureAgent',
    'BookingAgent',
    'ContentLifecycleAgent',
    'AudienceSegmentationAgent',
    'TaskManagementAgent',
    'MarketingCampaignAgent',
    'CommunityEngagementAgent'
]
