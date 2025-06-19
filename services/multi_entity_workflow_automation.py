#!/usr/bin/env python3
"""
Multi-Entity Workflow Automation Service

Comprehensive workflow automation system that handles entity-specific workflows
across The 7 Space, AM Consulting, and HigherSelf Core business entities.

Features:
- Entity-specific workflow templates
- Intelligent workflow routing
- Cross-entity opportunity identification
- Scalable multi-tenant architecture
- Advanced analytics and reporting
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from config.business_entity_workflows import (
    BusinessEntityWorkflows, EngagementChannel, WorkflowPriority
)
from models.notion_db_models import ContactWorkflowTrigger
from services.contact_workflow_automation import (
    ContactWorkflowAutomation, WorkflowAction, ContactType, LeadSource
)
from services.notion_service import NotionService


class EntityWorkflowTemplate:
    """Template for entity-specific workflows."""
    
    def __init__(self, entity_name: str, template_name: str, actions: List[WorkflowAction]):
        self.entity_name = entity_name
        self.template_name = template_name
        self.actions = actions
        self.created_at = datetime.now()
        self.success_metrics = []
        self.performance_data = {}


class MultiEntityWorkflowAutomation:
    """
    Advanced workflow automation system for multiple business entities.
    
    Manages entity-specific workflows, intelligent routing, and cross-entity
    opportunities across The 7 Space, AM Consulting, and HigherSelf Core.
    """
    
    def __init__(self, notion_client: NotionService):
        self.notion_client = notion_client
        self.business_workflows = BusinessEntityWorkflows()
        self.base_automation = ContactWorkflowAutomation()
        
        # Initialize entity-specific workflow templates
        self.entity_templates = self._initialize_entity_templates()
        
        # Workflow execution tracking
        self.active_workflows = {}
        self.workflow_metrics = {
            "the_7_space": {"executed": 0, "successful": 0, "avg_completion_time": 0},
            "am_consulting": {"executed": 0, "successful": 0, "avg_completion_time": 0},
            "higherself_core": {"executed": 0, "successful": 0, "avg_completion_time": 0}
        }
        
        logger.info("Multi-Entity Workflow Automation initialized")
    
    def _initialize_entity_templates(self) -> Dict[str, Dict[str, EntityWorkflowTemplate]]:
        """Initialize entity-specific workflow templates."""
        templates = {
            "the_7_space": self._create_7space_templates(),
            "am_consulting": self._create_am_consulting_templates(),
            "higherself_core": self._create_higherself_core_templates()
        }
        
        logger.info(f"Initialized {sum(len(t) for t in templates.values())} workflow templates")
        return templates
    
    def _create_7space_templates(self) -> Dict[str, EntityWorkflowTemplate]:
        """Create workflow templates for The 7 Space."""
        return {
            "artist_inquiry": EntityWorkflowTemplate(
                entity_name="the_7_space",
                template_name="artist_inquiry",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="artist_welcome_email",
                        personalization_data={"focus": "artistic_journey"}
                    ),
                    WorkflowAction(
                        action_type="create_task",
                        target="gallery_team",
                        delay_hours=2,
                        template="review_artist_portfolio",
                        personalization_data={"priority": "high"}
                    ),
                    WorkflowAction(
                        action_type="schedule_follow_up",
                        target="contact",
                        delay_hours=72,
                        template="exhibition_opportunity_discussion",
                        personalization_data={"meeting_type": "portfolio_review"}
                    )
                ]
            ),
            "wellness_booking": EntityWorkflowTemplate(
                entity_name="the_7_space",
                template_name="wellness_booking",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="wellness_welcome_email",
                        personalization_data={"focus": "healing_journey"}
                    ),
                    WorkflowAction(
                        action_type="create_booking_link",
                        target="contact",
                        delay_hours=1,
                        template="wellness_session_booking",
                        personalization_data={"services": "meditation_healing"}
                    ),
                    WorkflowAction(
                        action_type="send_reminder",
                        target="contact",
                        delay_hours=24,
                        template="wellness_session_reminder",
                        personalization_data={"preparation_tips": True}
                    )
                ]
            ),
            "gallery_visitor": EntityWorkflowTemplate(
                entity_name="the_7_space",
                template_name="gallery_visitor",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="gallery_welcome_email",
                        personalization_data={"focus": "art_appreciation"}
                    ),
                    WorkflowAction(
                        action_type="add_to_newsletter",
                        target="contact",
                        delay_hours=4,
                        template="art_community_newsletter",
                        personalization_data={"interests": "exhibitions_events"}
                    ),
                    WorkflowAction(
                        action_type="invite_to_event",
                        target="contact",
                        delay_hours=168,  # 1 week
                        template="upcoming_exhibition_invite",
                        personalization_data={"event_type": "art_opening"}
                    )
                ]
            )
        }
    
    def _create_am_consulting_templates(self) -> Dict[str, EntityWorkflowTemplate]:
        """Create workflow templates for AM Consulting."""
        return {
            "business_inquiry": EntityWorkflowTemplate(
                entity_name="am_consulting",
                template_name="business_inquiry",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="business_welcome_email",
                        personalization_data={"focus": "business_transformation"}
                    ),
                    WorkflowAction(
                        action_type="create_task",
                        target="consulting_team",
                        delay_hours=1,
                        template="qualify_business_lead",
                        personalization_data={"priority": "urgent"}
                    ),
                    WorkflowAction(
                        action_type="schedule_consultation",
                        target="contact",
                        delay_hours=4,
                        template="complimentary_consultation_booking",
                        personalization_data={"duration": "60_minutes"}
                    )
                ]
            ),
            "proposal_follow_up": EntityWorkflowTemplate(
                entity_name="am_consulting",
                template_name="proposal_follow_up",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=24,
                        template="proposal_follow_up_email",
                        personalization_data={"focus": "next_steps"}
                    ),
                    WorkflowAction(
                        action_type="create_task",
                        target="consulting_team",
                        delay_hours=48,
                        template="proposal_status_check",
                        personalization_data={"priority": "high"}
                    ),
                    WorkflowAction(
                        action_type="schedule_follow_up",
                        target="contact",
                        delay_hours=120,  # 5 days
                        template="proposal_discussion_call",
                        personalization_data={"meeting_type": "decision_support"}
                    )
                ]
            ),
            "client_onboarding": EntityWorkflowTemplate(
                entity_name="am_consulting",
                template_name="client_onboarding",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="client_welcome_email",
                        personalization_data={"focus": "partnership_success"}
                    ),
                    WorkflowAction(
                        action_type="create_project",
                        target="consulting_team",
                        delay_hours=2,
                        template="client_project_setup",
                        personalization_data={"project_type": "consulting_engagement"}
                    ),
                    WorkflowAction(
                        action_type="schedule_kickoff",
                        target="contact",
                        delay_hours=24,
                        template="project_kickoff_meeting",
                        personalization_data={"meeting_type": "project_initiation"}
                    )
                ]
            )
        }
    
    def _create_higherself_core_templates(self) -> Dict[str, EntityWorkflowTemplate]:
        """Create workflow templates for HigherSelf Core."""
        return {
            "community_interest": EntityWorkflowTemplate(
                entity_name="higherself_core",
                template_name="community_interest",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="community_welcome_email",
                        personalization_data={"focus": "personal_growth"}
                    ),
                    WorkflowAction(
                        action_type="add_to_community",
                        target="contact",
                        delay_hours=4,
                        template="community_platform_access",
                        personalization_data={"access_level": "member"}
                    ),
                    WorkflowAction(
                        action_type="invite_to_event",
                        target="contact",
                        delay_hours=72,
                        template="welcome_networking_event",
                        personalization_data={"event_type": "virtual_meetup"}
                    )
                ]
            ),
            "content_engagement": EntityWorkflowTemplate(
                entity_name="higherself_core",
                template_name="content_engagement",
                actions=[
                    WorkflowAction(
                        action_type="send_content",
                        target="contact",
                        delay_hours=0,
                        template="personalized_content_share",
                        personalization_data={"content_type": "growth_insights"}
                    ),
                    WorkflowAction(
                        action_type="track_engagement",
                        target="contact",
                        delay_hours=24,
                        template="content_engagement_tracking",
                        personalization_data={"metrics": "opens_clicks_shares"}
                    ),
                    WorkflowAction(
                        action_type="follow_up_content",
                        target="contact",
                        delay_hours=168,  # 1 week
                        template="related_content_recommendation",
                        personalization_data={"content_series": "growth_journey"}
                    )
                ]
            ),
            "platform_onboarding": EntityWorkflowTemplate(
                entity_name="higherself_core",
                template_name="platform_onboarding",
                actions=[
                    WorkflowAction(
                        action_type="send_email",
                        target="contact",
                        delay_hours=0,
                        template="platform_welcome_email",
                        personalization_data={"focus": "platform_benefits"}
                    ),
                    WorkflowAction(
                        action_type="create_profile",
                        target="contact",
                        delay_hours=2,
                        template="platform_profile_setup",
                        personalization_data={"profile_type": "growth_seeker"}
                    ),
                    WorkflowAction(
                        action_type="assign_mentor",
                        target="contact",
                        delay_hours=48,
                        template="mentor_assignment",
                        personalization_data={"mentor_type": "growth_guide"}
                    )
                ]
            )
        }
    
    async def execute_entity_workflow(
        self, entity_name: str, template_name: str, contact_data: Dict[str, Any],
        trigger_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute an entity-specific workflow."""
        
        start_time = datetime.now()
        execution_id = f"{entity_name}_{template_name}_{int(start_time.timestamp())}"
        
        try:
            # Get workflow template
            template = self.entity_templates.get(entity_name, {}).get(template_name)
            if not template:
                raise ValueError(f"Template {template_name} not found for entity {entity_name}")
            
            logger.info(f"Executing {entity_name} workflow: {template_name}")
            
            # Track active workflow
            self.active_workflows[execution_id] = {
                "entity": entity_name,
                "template": template_name,
                "contact_email": contact_data.get("email"),
                "start_time": start_time,
                "status": "executing",
                "actions_completed": 0,
                "total_actions": len(template.actions)
            }
            
            # Execute workflow actions
            action_results = []
            for i, action in enumerate(template.actions):
                try:
                    # Execute action with entity-specific context
                    action_result = await self._execute_entity_action(
                        action, contact_data, entity_name, trigger_context
                    )
                    action_results.append(action_result)
                    
                    # Update progress
                    self.active_workflows[execution_id]["actions_completed"] = i + 1
                    
                    logger.info(f"Completed action {i+1}/{len(template.actions)} for {execution_id}")
                    
                except Exception as e:
                    logger.error(f"Error executing action {i+1} for {execution_id}: {e}")
                    action_results.append({"error": str(e), "action": action.action_type})
            
            # Calculate completion time
            completion_time = (datetime.now() - start_time).total_seconds()
            
            # Update workflow status
            self.active_workflows[execution_id]["status"] = "completed"
            self.active_workflows[execution_id]["completion_time"] = completion_time
            
            # Update metrics
            self._update_workflow_metrics(entity_name, completion_time, True)
            
            return {
                "success": True,
                "execution_id": execution_id,
                "entity": entity_name,
                "template": template_name,
                "actions_executed": len(action_results),
                "completion_time": completion_time,
                "results": action_results
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {execution_id}: {e}")
            
            # Update metrics for failure
            self._update_workflow_metrics(entity_name, 0, False)
            
            return {
                "success": False,
                "execution_id": execution_id,
                "entity": entity_name,
                "template": template_name,
                "error": str(e)
            }
    
    async def _execute_entity_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], 
        entity_name: str, trigger_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a single workflow action with entity-specific context."""
        
        # Add delay if specified
        if action.delay_hours > 0:
            logger.info(f"Scheduling action {action.action_type} with {action.delay_hours}h delay")
            # In production, this would use a task queue like Celery
            await asyncio.sleep(1)  # Simulate delay for demo
        
        # Execute action based on type
        if action.action_type == "send_email":
            return await self._execute_send_email_action(action, contact_data, entity_name)
        elif action.action_type == "create_task":
            return await self._execute_create_task_action(action, contact_data, entity_name)
        elif action.action_type == "schedule_follow_up":
            return await self._execute_schedule_followup_action(action, contact_data, entity_name)
        elif action.action_type == "create_booking_link":
            return await self._execute_create_booking_action(action, contact_data, entity_name)
        elif action.action_type == "add_to_newsletter":
            return await self._execute_newsletter_action(action, contact_data, entity_name)
        elif action.action_type == "invite_to_event":
            return await self._execute_event_invite_action(action, contact_data, entity_name)
        else:
            return await self._execute_generic_action(action, contact_data, entity_name)
    
    async def _execute_send_email_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute email sending action."""
        email_template = action.template
        personalization = action.personalization_data or {}
        
        # Entity-specific email customization
        if entity_name == "the_7_space":
            subject_prefix = "The 7 Space - "
            signature = "The 7 Space Art Gallery & Wellness Center"
        elif entity_name == "am_consulting":
            subject_prefix = "AM Consulting - "
            signature = "AM Consulting - Strategic Business Transformation"
        else:  # higherself_core
            subject_prefix = "HigherSelf Network - "
            signature = "The HigherSelf Network Community"
        
        return {
            "action": "send_email",
            "template": email_template,
            "recipient": contact_data.get("email"),
            "subject_prefix": subject_prefix,
            "signature": signature,
            "personalization": personalization,
            "status": "sent",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_create_task_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute task creation action."""
        return {
            "action": "create_task",
            "template": action.template,
            "target": action.target,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_schedule_followup_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute follow-up scheduling action."""
        return {
            "action": "schedule_follow_up",
            "template": action.template,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "scheduled_for": (datetime.now() + timedelta(hours=action.delay_hours)).isoformat(),
            "status": "scheduled",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_create_booking_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute booking link creation action."""
        return {
            "action": "create_booking_link",
            "template": action.template,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "booking_link": f"https://{entity_name}.com/book/{contact_data.get('email', 'contact')}",
            "status": "created",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_newsletter_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute newsletter subscription action."""
        return {
            "action": "add_to_newsletter",
            "template": action.template,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "newsletter_list": f"{entity_name}_community",
            "status": "subscribed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_event_invite_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute event invitation action."""
        return {
            "action": "invite_to_event",
            "template": action.template,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "event_type": action.personalization_data.get("event_type", "general"),
            "status": "invited",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _execute_generic_action(
        self, action: WorkflowAction, contact_data: Dict[str, Any], entity_name: str
    ) -> Dict[str, Any]:
        """Execute generic action."""
        return {
            "action": action.action_type,
            "template": action.template,
            "entity": entity_name,
            "contact_email": contact_data.get("email"),
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }
    
    def _update_workflow_metrics(self, entity_name: str, completion_time: float, success: bool):
        """Update workflow execution metrics."""
        if entity_name in self.workflow_metrics:
            metrics = self.workflow_metrics[entity_name]
            metrics["executed"] += 1
            
            if success:
                metrics["successful"] += 1
                # Update average completion time
                current_avg = metrics["avg_completion_time"]
                successful_count = metrics["successful"]
                metrics["avg_completion_time"] = (
                    (current_avg * (successful_count - 1) + completion_time) / successful_count
                )
    
    async def get_entity_workflow_status(self, entity_name: Optional[str] = None) -> Dict[str, Any]:
        """Get workflow status for specific entity or all entities."""
        if entity_name:
            return {
                "entity": entity_name,
                "templates": list(self.entity_templates.get(entity_name, {}).keys()),
                "metrics": self.workflow_metrics.get(entity_name, {}),
                "active_workflows": [
                    w for w in self.active_workflows.values() 
                    if w["entity"] == entity_name
                ]
            }
        else:
            return {
                "all_entities": {
                    entity: {
                        "templates": list(templates.keys()),
                        "metrics": self.workflow_metrics.get(entity, {}),
                        "active_workflows": [
                            w for w in self.active_workflows.values() 
                            if w["entity"] == entity
                        ]
                    }
                    for entity, templates in self.entity_templates.items()
                },
                "total_active_workflows": len(self.active_workflows)
            }
    
    async def identify_optimal_workflow(
        self, contact_data: Dict[str, Any], entity_name: str, analysis_result: Dict[str, Any]
    ) -> str:
        """Identify the optimal workflow template for a contact."""
        
        entity_templates = self.entity_templates.get(entity_name, {})
        if not entity_templates:
            return "default"
        
        # Simple rule-based workflow selection (can be enhanced with ML)
        contact_message = contact_data.get("message", "").lower()
        contact_interests = contact_data.get("interests", [])
        
        if entity_name == "the_7_space":
            if any(keyword in contact_message for keyword in ["artist", "exhibition", "portfolio"]):
                return "artist_inquiry"
            elif any(keyword in contact_message for keyword in ["wellness", "meditation", "healing"]):
                return "wellness_booking"
            else:
                return "gallery_visitor"
        
        elif entity_name == "am_consulting":
            if any(keyword in contact_message for keyword in ["proposal", "follow", "decision"]):
                return "proposal_follow_up"
            elif any(keyword in contact_message for keyword in ["client", "project", "engagement"]):
                return "client_onboarding"
            else:
                return "business_inquiry"
        
        elif entity_name == "higherself_core":
            if any(keyword in contact_message for keyword in ["platform", "access", "account"]):
                return "platform_onboarding"
            elif any(keyword in contact_message for keyword in ["content", "article", "resource"]):
                return "content_engagement"
            else:
                return "community_interest"
        
        return list(entity_templates.keys())[0]  # Default to first template
