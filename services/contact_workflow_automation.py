#!/usr/bin/env python3
"""
Contact-Driven Workflow Automation Service

This service implements intelligent, automated workflows based on the enriched contact data
from the Phase 1 enrichment. It provides targeted automation for different contact types
and lead sources, routing to appropriate business entities.

Key Features:
- Contact classification-based workflow triggers
- Business entity-specific engagement sequences
- Lead source-based automation paths
- Multi-channel notification and task creation
- Engagement tracking and analytics
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from loguru import logger
from notion_client import Client

from services.notion_service import NotionService
from services.termius_notification_service import TermiusNotificationService
from agents.task_management_agent import TaskManagementAgent
from workflow.workflow_engine import WorkflowEngine
from utils.message_bus import MessageBus


class ContactType(Enum):
    """Contact type classifications from enrichment."""
    ARTIST = "Artist"
    GALLERY_CONTACT = "Gallery Contact"
    BUSINESS_CONTACT = "Business Contact"
    POTENTIAL_CLIENT = "Potential Client"
    ACADEMIC_CONTACT = "Academic Contact"
    MEDIA_CONTACT = "Media Contact"
    GENERAL_CONTACT = "General Contact"


class LeadSource(Enum):
    """Lead source classifications from enrichment."""
    WEBSITE = "Website"
    EVENT = "Event"
    REFERRAL = "Referral"


class BusinessEntity(Enum):
    """Business entities for workflow routing."""
    THE_7_SPACE = "The 7 Space"
    AM_CONSULTING = "AM Consulting"
    HIGHERSELF_CORE = "HigherSelf Core"


@dataclass
class ContactWorkflowTrigger:
    """Represents a contact-based workflow trigger."""
    contact_id: str
    contact_email: str
    contact_types: List[ContactType]
    lead_source: LeadSource
    trigger_event: str  # 'new_contact', 'contact_updated', 'engagement_detected'
    business_entities: List[BusinessEntity]
    metadata: Dict[str, Any]


@dataclass
class WorkflowAction:
    """Represents an action to be taken in a workflow."""
    action_type: str  # 'send_notification', 'create_task', 'send_email', 'schedule_follow_up'
    target: str
    content: Dict[str, Any]
    delay_hours: int = 0
    conditions: Dict[str, Any] = None


class ContactWorkflowAutomation:
    """
    Main service for contact-driven workflow automation.
    
    Orchestrates intelligent workflows based on contact classifications,
    lead sources, and business entity requirements.
    """

    def __init__(self):
        """Initialize the contact workflow automation service."""
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
        self.contacts_db_id = os.getenv('NOTION_CONTACTS_PROFILES_DB')
        self.tasks_db_id = os.getenv('NOTION_TASKS_DB')
        self.workflows_db_id = os.getenv('NOTION_ACTIVE_WORKFLOW_INSTANCES_DB')
        self.notifications_db_id = os.getenv('NOTION_NOTIFICATIONS_TEMPLATES_DB')
        
        # Initialize services
        self.notion_service = NotionService.from_env()
        self.termius_service = TermiusNotificationService()
        self.task_agent = TaskManagementAgent()
        self.workflow_engine = WorkflowEngine()
        self.message_bus = MessageBus()
        
        # Workflow templates
        self.workflow_templates = self._initialize_workflow_templates()
        
        logger.info("Contact Workflow Automation service initialized")

    def _initialize_workflow_templates(self) -> Dict[str, List[WorkflowAction]]:
        """Initialize workflow templates for different contact types and business entities."""
        return {
            # The 7 Space - Artist/Gallery Workflows
            "the7space_artist_welcome": [
                WorkflowAction(
                    action_type="send_notification",
                    target="admin",
                    content={
                        "title": "New Artist Contact",
                        "message": "New artist contact added to The 7 Space pipeline",
                        "priority": "high"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="gallery_team",
                    content={
                        "title": "Review Artist Portfolio",
                        "description": "Review new artist contact and assess exhibition potential",
                        "category": "OUTREACH",
                        "priority": "HIGH"
                    },
                    delay_hours=2
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "artist_welcome_sequence",
                        "subject": "Welcome to The 7 Space Community",
                        "personalization": "artist_focused"
                    },
                    delay_hours=24
                )
            ],
            
            # AM Consulting - Business Contact Workflows
            "am_consulting_business_lead": [
                WorkflowAction(
                    action_type="send_notification",
                    target="consulting_team",
                    content={
                        "title": "New Business Lead",
                        "message": "New business contact requires consultation assessment",
                        "priority": "high"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="business_development",
                    content={
                        "title": "Qualify Business Lead",
                        "description": "Assess business needs and consultation fit",
                        "category": "SALES",
                        "priority": "HIGH"
                    },
                    delay_hours=1
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "business_consultation_intro",
                        "subject": "Strategic Consultation Opportunity",
                        "personalization": "business_focused"
                    },
                    delay_hours=4
                )
            ],
            
            # HigherSelf Core - General Contact Workflows
            "higherself_general_welcome": [
                WorkflowAction(
                    action_type="send_notification",
                    target="community_team",
                    content={
                        "title": "New Community Member",
                        "message": "New contact added to HigherSelf community",
                        "priority": "medium"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="community_engagement",
                    content={
                        "title": "Welcome New Community Member",
                        "description": "Send personalized welcome and onboarding materials",
                        "category": "COMMUNITY",
                        "priority": "MEDIUM"
                    },
                    delay_hours=6
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "community_welcome_sequence",
                        "subject": "Welcome to The HigherSelf Network",
                        "personalization": "community_focused"
                    },
                    delay_hours=12
                )
            ],
            
            # Lead Source Specific Workflows
            "event_lead_follow_up": [
                WorkflowAction(
                    action_type="create_task",
                    target="event_team",
                    content={
                        "title": "Event Lead Follow-up",
                        "description": "Follow up with contact from recent event",
                        "category": "EVENT",
                        "priority": "HIGH"
                    },
                    delay_hours=24
                ),
                WorkflowAction(
                    action_type="schedule_follow_up",
                    target="contact",
                    content={
                        "template": "event_follow_up_sequence",
                        "subject": "Great meeting you at our event!",
                        "personalization": "event_focused"
                    },
                    delay_hours=48
                )
            ],
            
            "referral_lead_priority": [
                WorkflowAction(
                    action_type="send_notification",
                    target="admin",
                    content={
                        "title": "Priority Referral Lead",
                        "message": "High-priority referral contact requires immediate attention",
                        "priority": "urgent"
                    }
                ),
                WorkflowAction(
                    action_type="create_task",
                    target="leadership_team",
                    content={
                        "title": "Handle Referral Lead",
                        "description": "Personal outreach to referral contact",
                        "category": "SALES",
                        "priority": "URGENT"
                    },
                    delay_hours=2
                )
            ]
        }

    async def process_contact_trigger(self, trigger: ContactWorkflowTrigger) -> Dict[str, Any]:
        """
        Process a contact-based workflow trigger.
        
        Args:
            trigger: ContactWorkflowTrigger containing contact info and trigger event
            
        Returns:
            Dict containing workflow execution results
        """
        logger.info(f"Processing contact workflow trigger for {trigger.contact_email}")
        
        try:
            # Determine appropriate workflows based on contact classification
            workflows_to_execute = self._determine_workflows(trigger)
            
            # Execute workflows
            execution_results = []
            for workflow_name in workflows_to_execute:
                result = await self._execute_workflow(workflow_name, trigger)
                execution_results.append(result)
            
            # Log workflow execution
            await self._log_workflow_execution(trigger, workflows_to_execute, execution_results)
            
            return {
                "success": True,
                "contact_id": trigger.contact_id,
                "workflows_executed": workflows_to_execute,
                "results": execution_results
            }
            
        except Exception as e:
            logger.error(f"Error processing contact workflow trigger: {e}")
            return {
                "success": False,
                "contact_id": trigger.contact_id,
                "error": str(e)
            }

    def _determine_workflows(self, trigger: ContactWorkflowTrigger) -> List[str]:
        """Determine which workflows to execute based on contact classification."""
        workflows = []
        
        # Business entity-specific workflows
        for entity in trigger.business_entities:
            if entity == BusinessEntity.THE_7_SPACE:
                if any(ct in [ContactType.ARTIST, ContactType.GALLERY_CONTACT] for ct in trigger.contact_types):
                    workflows.append("the7space_artist_welcome")
            
            elif entity == BusinessEntity.AM_CONSULTING:
                if any(ct in [ContactType.BUSINESS_CONTACT, ContactType.POTENTIAL_CLIENT] for ct in trigger.contact_types):
                    workflows.append("am_consulting_business_lead")
            
            elif entity == BusinessEntity.HIGHERSELF_CORE:
                workflows.append("higherself_general_welcome")
        
        # Lead source-specific workflows
        if trigger.lead_source == LeadSource.EVENT:
            workflows.append("event_lead_follow_up")
        elif trigger.lead_source == LeadSource.REFERRAL:
            workflows.append("referral_lead_priority")
        
        return workflows

    async def _execute_workflow(self, workflow_name: str, trigger: ContactWorkflowTrigger) -> Dict[str, Any]:
        """Execute a specific workflow template."""
        if workflow_name not in self.workflow_templates:
            raise ValueError(f"Unknown workflow template: {workflow_name}")
        
        actions = self.workflow_templates[workflow_name]
        action_results = []
        
        for action in actions:
            if action.delay_hours > 0:
                # Schedule delayed action
                await self._schedule_delayed_action(action, trigger, action.delay_hours)
                action_results.append({"action": action.action_type, "status": "scheduled"})
            else:
                # Execute immediate action
                result = await self._execute_action(action, trigger)
                action_results.append(result)
        
        return {
            "workflow": workflow_name,
            "actions_executed": len(action_results),
            "results": action_results
        }

    async def _execute_action(self, action: WorkflowAction, trigger: ContactWorkflowTrigger) -> Dict[str, Any]:
        """Execute a specific workflow action."""
        try:
            if action.action_type == "send_notification":
                return await self._send_notification(action, trigger)
            elif action.action_type == "create_task":
                return await self._create_task(action, trigger)
            elif action.action_type == "schedule_follow_up":
                return await self._schedule_follow_up(action, trigger)
            else:
                return {"action": action.action_type, "status": "unsupported"}

        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {e}")
            return {"action": action.action_type, "status": "error", "error": str(e)}

    async def _send_notification(self, action: WorkflowAction, trigger: ContactWorkflowTrigger) -> Dict[str, Any]:
        """Send notification via Termius integration."""
        content = action.content
        message = f"{content['title']}: {content['message']} (Contact: {trigger.contact_email})"

        # Send via Termius notification service
        notification_data = {
            "source": "contact_workflow",
            "event_type": "contact_automation",
            "timestamp": datetime.utcnow(),
            "data": {
                "message": message,
                "status": "info",
                "environment": "production",
                "workflow": "Contact Automation",
                "actor": "Workflow Engine",
                "contact_id": trigger.contact_id,
                "priority": content.get("priority", "medium")
            }
        }

        success = await self.termius_service.process_github_actions_webhook(notification_data)

        return {
            "action": "send_notification",
            "status": "success" if success else "failed",
            "target": action.target,
            "message": message
        }

    async def _create_task(self, action: WorkflowAction, trigger: ContactWorkflowTrigger) -> Dict[str, Any]:
        """Create task in Notion Tasks database."""
        content = action.content

        # Determine business entity for task assignment
        business_entity_id = self._get_business_entity_id(trigger.business_entities[0] if trigger.business_entities else BusinessEntity.HIGHERSELF_CORE)

        task_data = {
            "title": content["title"],
            "description": f"{content['description']}\n\nContact: {trigger.contact_email}\nContact ID: {trigger.contact_id}",
            "business_entity_id": business_entity_id,
            "category": content.get("category", "ADMIN"),
            "priority": content.get("priority", "MEDIUM"),
            "source": "AUTOMATION",
            "workflow_instance_id": f"contact_workflow_{trigger.contact_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

        result = await self.task_agent.create_task(**task_data)

        return {
            "action": "create_task",
            "status": "success" if result.get("status") == "success" else "failed",
            "task_id": result.get("task_id"),
            "title": content["title"]
        }

    async def _schedule_follow_up(self, action: WorkflowAction, trigger: ContactWorkflowTrigger) -> Dict[str, Any]:
        """Schedule follow-up communication."""
        content = action.content

        # Create follow-up task in Notion
        follow_up_task = {
            "title": f"Follow-up: {content['subject']}",
            "description": f"Send follow-up communication to {trigger.contact_email}\n\nTemplate: {content['template']}\nPersonalization: {content['personalization']}",
            "business_entity_id": self._get_business_entity_id(trigger.business_entities[0] if trigger.business_entities else BusinessEntity.HIGHERSELF_CORE),
            "category": "COMMUNICATION",
            "priority": "MEDIUM",
            "source": "AUTOMATION",
            "due_date": (datetime.now() + timedelta(hours=action.delay_hours)).date() if action.delay_hours > 0 else None
        }

        result = await self.task_agent.create_task(**follow_up_task)

        return {
            "action": "schedule_follow_up",
            "status": "success" if result.get("status") == "success" else "failed",
            "task_id": result.get("task_id"),
            "template": content["template"]
        }

    async def _schedule_delayed_action(self, action: WorkflowAction, trigger: ContactWorkflowTrigger, delay_hours: int):
        """Schedule an action to be executed after a delay."""
        # For now, create a task to execute the action later
        # In a production system, this would use a job queue like Celery or Redis

        scheduled_task = {
            "title": f"Scheduled Action: {action.action_type}",
            "description": f"Execute {action.action_type} for contact {trigger.contact_email}\n\nAction Details: {json.dumps(action.content, indent=2)}",
            "business_entity_id": self._get_business_entity_id(BusinessEntity.HIGHERSELF_CORE),
            "category": "AUTOMATION",
            "priority": "LOW",
            "source": "AUTOMATION",
            "due_date": (datetime.now() + timedelta(hours=delay_hours)).date()
        }

        await self.task_agent.create_task(**scheduled_task)
        logger.info(f"Scheduled {action.action_type} for {trigger.contact_email} in {delay_hours} hours")

    def _get_business_entity_id(self, entity: BusinessEntity) -> str:
        """Get the business entity ID for task assignment."""
        # These would be actual Notion page IDs in production
        entity_mapping = {
            BusinessEntity.THE_7_SPACE: "the7space_entity_id",
            BusinessEntity.AM_CONSULTING: "amconsulting_entity_id",
            BusinessEntity.HIGHERSELF_CORE: "higherself_entity_id"
        }
        return entity_mapping.get(entity, "higherself_entity_id")

    async def _log_workflow_execution(self, trigger: ContactWorkflowTrigger, workflows: List[str], results: List[Dict[str, Any]]):
        """Log workflow execution to Notion for tracking and analytics."""
        try:
            log_data = {
                "Contact ID": {"rich_text": [{"text": {"content": trigger.contact_id}}]},
                "Contact Email": {"email": trigger.contact_email},
                "Trigger Event": {"rich_text": [{"text": {"content": trigger.trigger_event}}]},
                "Workflows Executed": {"rich_text": [{"text": {"content": ", ".join(workflows)}}]},
                "Execution Results": {"rich_text": [{"text": {"content": json.dumps(results, indent=2)}}]},
                "Timestamp": {"date": {"start": datetime.now().isoformat()}},
                "Status": {"select": {"name": "Completed"}}
            }

            # Create log entry in Active Workflow Instances database
            await self.notion.pages.create(
                parent={"database_id": self.workflows_db_id},
                properties=log_data
            )

            logger.info(f"Logged workflow execution for contact {trigger.contact_email}")

        except Exception as e:
            logger.error(f"Error logging workflow execution: {e}")

    async def monitor_contact_changes(self):
        """Monitor Notion Contacts database for changes and trigger workflows."""
        logger.info("Starting contact change monitoring...")

        while True:
            try:
                # Query recently updated contacts (last 5 minutes)
                five_minutes_ago = (datetime.now() - timedelta(minutes=5)).isoformat()

                response = await self.notion.databases.query(
                    database_id=self.contacts_db_id,
                    filter={
                        "property": "Last edited time",
                        "last_edited_time": {
                            "after": five_minutes_ago
                        }
                    }
                )

                for contact in response.get("results", []):
                    await self._process_contact_change(contact)

                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                logger.error(f"Error monitoring contact changes: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

    async def _process_contact_change(self, contact: Dict[str, Any]):
        """Process a detected contact change."""
        try:
            properties = contact.get("properties", {})

            # Extract contact information
            contact_id = contact["id"]
            email_prop = properties.get("Email", {})
            email = email_prop.get("email", "") if email_prop else ""

            if not email:
                return  # Skip contacts without email

            # Extract contact types
            contact_types = []
            contact_type_prop = properties.get("Contact Type", {})
            if contact_type_prop.get("multi_select"):
                for ct in contact_type_prop["multi_select"]:
                    try:
                        contact_types.append(ContactType(ct["name"]))
                    except ValueError:
                        pass  # Skip unknown contact types

            # Extract lead source
            lead_source = LeadSource.WEBSITE  # Default
            lead_source_prop = properties.get("Lead Source", {})
            if lead_source_prop.get("select"):
                try:
                    lead_source = LeadSource(lead_source_prop["select"]["name"])
                except ValueError:
                    pass  # Use default

            # Determine business entities based on contact types
            business_entities = self._determine_business_entities(contact_types)

            # Create workflow trigger
            trigger = ContactWorkflowTrigger(
                contact_id=contact_id,
                contact_email=email,
                contact_types=contact_types,
                lead_source=lead_source,
                trigger_event="contact_updated",
                business_entities=business_entities,
                metadata={"notion_page_id": contact_id}
            )

            # Process the trigger
            await self.process_contact_trigger(trigger)

        except Exception as e:
            logger.error(f"Error processing contact change: {e}")

    def _determine_business_entities(self, contact_types: List[ContactType]) -> List[BusinessEntity]:
        """Determine relevant business entities based on contact types."""
        entities = []

        # The 7 Space - Artists and Gallery Contacts
        if any(ct in [ContactType.ARTIST, ContactType.GALLERY_CONTACT] for ct in contact_types):
            entities.append(BusinessEntity.THE_7_SPACE)

        # AM Consulting - Business and Potential Clients
        if any(ct in [ContactType.BUSINESS_CONTACT, ContactType.POTENTIAL_CLIENT] for ct in contact_types):
            entities.append(BusinessEntity.AM_CONSULTING)

        # HigherSelf Core - All contacts
        entities.append(BusinessEntity.HIGHERSELF_CORE)

        return entities
