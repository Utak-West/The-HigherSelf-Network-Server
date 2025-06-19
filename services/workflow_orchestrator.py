#!/usr/bin/env python3
"""
Workflow Orchestrator Service

This service orchestrates all contact-driven workflows, integrating the various
components of the automation system to provide seamless, intelligent workflow
execution across all business entities.

Key Responsibilities:
- Coordinate workflow execution across business entities
- Manage workflow state and transitions
- Handle workflow dependencies and sequencing
- Provide analytics and reporting on workflow performance
- Ensure proper integration with Notion databases
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from loguru import logger
from notion_client import Client

from services.contact_workflow_automation import (
    ContactWorkflowAutomation,
    ContactWorkflowTrigger,
    ContactType,
    LeadSource,
    BusinessEntity
)
from config.business_entity_workflows import BusinessEntityWorkflows
from templates.contact_engagement_templates import ContactEngagementTemplates
from services.notion_service import NotionService
from agents.task_management_agent import TaskManagementAgent


@dataclass
class WorkflowExecution:
    """Represents a complete workflow execution."""
    execution_id: str
    contact_id: str
    contact_email: str
    business_entities: List[str]
    workflows_executed: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, paused
    results: List[Dict[str, Any]] = None
    metrics: Dict[str, Any] = None


@dataclass
class WorkflowAnalytics:
    """Analytics data for workflow performance."""
    total_executions: int
    success_rate: float
    average_execution_time: float
    top_performing_workflows: List[str]
    contact_type_breakdown: Dict[str, int]
    business_entity_performance: Dict[str, Dict[str, Any]]
    engagement_metrics: Dict[str, float]


class WorkflowOrchestrator:
    """
    Main orchestrator for all contact-driven workflows.
    
    Coordinates workflow execution, manages state, and provides
    comprehensive analytics and reporting capabilities.
    """

    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
        self.contacts_db_id = os.getenv('NOTION_CONTACTS_PROFILES_DB')
        self.workflows_db_id = os.getenv('NOTION_ACTIVE_WORKFLOW_INSTANCES_DB')
        self.tasks_db_id = os.getenv('NOTION_TASKS_DB')
        
        # Initialize services
        self.workflow_automation = ContactWorkflowAutomation()
        self.business_workflows = BusinessEntityWorkflows()
        self.engagement_templates = ContactEngagementTemplates()
        self.notion_service = NotionService()
        self.task_agent = TaskManagementAgent()
        
        # Execution tracking
        self.active_executions: Dict[str, WorkflowExecution] = {}
        self.execution_history: List[WorkflowExecution] = []
        
        logger.info("Workflow Orchestrator initialized")

    async def execute_contact_workflow(
        self,
        contact_id: str,
        trigger_event: str = "manual",
        override_workflows: Optional[List[str]] = None
    ) -> WorkflowExecution:
        """
        Execute a complete contact workflow with full orchestration.
        
        Args:
            contact_id: Notion contact page ID
            trigger_event: Event that triggered the workflow
            override_workflows: Optional list of specific workflows to execute
            
        Returns:
            WorkflowExecution object with execution details
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{contact_id[:8]}"
        
        try:
            # Fetch contact data from Notion
            contact_data = await self._fetch_contact_data(contact_id)
            if not contact_data:
                raise ValueError(f"Contact not found: {contact_id}")
            
            # Create workflow trigger
            trigger = await self._create_workflow_trigger(contact_data, trigger_event)
            
            # Create execution record
            execution = WorkflowExecution(
                execution_id=execution_id,
                contact_id=contact_id,
                contact_email=trigger.contact_email,
                business_entities=[be.value for be in trigger.business_entities],
                workflows_executed=[],
                start_time=datetime.now(),
                results=[]
            )
            
            self.active_executions[execution_id] = execution
            
            # Determine workflows to execute
            if override_workflows:
                workflows_to_execute = override_workflows
            else:
                workflows_to_execute = self._determine_optimal_workflows(trigger)
            
            execution.workflows_executed = workflows_to_execute
            
            # Execute workflows sequentially with proper coordination
            for workflow_name in workflows_to_execute:
                workflow_result = await self._execute_coordinated_workflow(
                    workflow_name, trigger, execution
                )
                execution.results.append(workflow_result)
            
            # Complete execution
            execution.end_time = datetime.now()
            execution.status = "completed"
            execution.metrics = await self._calculate_execution_metrics(execution)
            
            # Store execution in Notion
            await self._store_execution_record(execution)
            
            # Move to history
            self.execution_history.append(execution)
            del self.active_executions[execution_id]
            
            logger.info(f"Workflow execution completed: {execution_id}")
            return execution
            
        except Exception as e:
            logger.error(f"Error in workflow execution {execution_id}: {e}")
            if execution_id in self.active_executions:
                self.active_executions[execution_id].status = "failed"
                self.active_executions[execution_id].end_time = datetime.now()
            raise

    async def _fetch_contact_data(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Fetch contact data from Notion."""
        try:
            response = await self.notion.pages.retrieve(page_id=contact_id)
            return response
        except Exception as e:
            logger.error(f"Error fetching contact data: {e}")
            return None

    async def _create_workflow_trigger(
        self, contact_data: Dict[str, Any], trigger_event: str
    ) -> ContactWorkflowTrigger:
        """Create a workflow trigger from contact data."""
        properties = contact_data.get("properties", {})
        
        # Extract contact information
        email_prop = properties.get("Email", {})
        email = email_prop.get("email", "") if email_prop else ""
        
        # Extract contact types
        contact_types = []
        contact_type_prop = properties.get("Contact Type", {})
        if contact_type_prop.get("multi_select"):
            for ct in contact_type_prop["multi_select"]:
                try:
                    contact_types.append(ContactType(ct["name"]))
                except ValueError:
                    pass
        
        # Extract lead source
        lead_source = LeadSource.WEBSITE
        lead_source_prop = properties.get("Lead Source", {})
        if lead_source_prop.get("select"):
            try:
                lead_source = LeadSource(lead_source_prop["select"]["name"])
            except ValueError:
                pass
        
        # Determine business entities
        business_entities = self._determine_business_entities_from_types(contact_types)
        
        return ContactWorkflowTrigger(
            contact_id=contact_data["id"],
            contact_email=email,
            contact_types=contact_types,
            lead_source=lead_source,
            trigger_event=trigger_event,
            business_entities=business_entities,
            metadata={"notion_page_id": contact_data["id"]}
        )

    def _determine_optimal_workflows(self, trigger: ContactWorkflowTrigger) -> List[str]:
        """Determine the optimal workflows to execute based on contact data."""
        workflows = []
        
        # Business entity-specific workflows
        for entity in trigger.business_entities:
            entity_workflows = self.business_workflows.get_entity_workflows(entity.value)
            
            # Select most appropriate workflow for each entity
            if entity == BusinessEntity.THE_7_SPACE:
                if any(ct in [ContactType.ARTIST, ContactType.GALLERY_CONTACT] for ct in trigger.contact_types):
                    workflows.append("the7space_artist_discovery")
                else:
                    workflows.append("the7space_wellness_inquiry")
            
            elif entity == BusinessEntity.AM_CONSULTING:
                if trigger.lead_source == LeadSource.REFERRAL:
                    workflows.append("am_consulting_lead_qualification")
                else:
                    workflows.append("am_consulting_business_welcome")
            
            elif entity == BusinessEntity.HIGHERSELF_CORE:
                workflows.append("higherself_community_onboarding")
        
        # Lead source-specific workflows
        if trigger.lead_source == LeadSource.EVENT:
            workflows.append("event_lead_hot_follow_up")
        elif trigger.lead_source == LeadSource.REFERRAL:
            workflows.append("referral_vip_treatment")
        
        return list(set(workflows))  # Remove duplicates

    async def _execute_coordinated_workflow(
        self, workflow_name: str, trigger: ContactWorkflowTrigger, execution: WorkflowExecution
    ) -> Dict[str, Any]:
        """Execute a workflow with full coordination and template integration."""
        try:
            # Get workflow template
            workflow_actions = self.business_workflows.get_workflow_template(workflow_name)
            if not workflow_actions:
                return {"workflow": workflow_name, "status": "template_not_found"}
            
            # Execute each action with enhanced coordination
            action_results = []
            for action in workflow_actions:
                # Enhance action with personalized templates
                enhanced_action = await self._enhance_action_with_templates(action, trigger)
                
                # Execute action
                if action.delay_hours > 0:
                    # Schedule delayed action
                    await self._schedule_coordinated_action(enhanced_action, trigger, execution)
                    action_results.append({"action": action.action_type, "status": "scheduled"})
                else:
                    # Execute immediate action
                    result = await self._execute_enhanced_action(enhanced_action, trigger, execution)
                    action_results.append(result)
            
            return {
                "workflow": workflow_name,
                "status": "completed",
                "actions_executed": len(action_results),
                "results": action_results
            }
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_name}: {e}")
            return {"workflow": workflow_name, "status": "error", "error": str(e)}

    async def _enhance_action_with_templates(self, action, trigger: ContactWorkflowTrigger):
        """Enhance workflow action with personalized templates."""
        if action.action_type == "schedule_follow_up" and "template" in action.content:
            template_id = action.content["template"]
            
            # Get contact data for personalization
            contact_data = {
                "first_name": trigger.metadata.get("first_name", ""),
                "last_name": trigger.metadata.get("last_name", ""),
                "email": trigger.contact_email,
                "contact_type": [ct.value for ct in trigger.contact_types],
                "lead_source": trigger.lead_source.value
            }
            
            # Personalize template
            personalized = self.engagement_templates.personalize_template(template_id, contact_data)
            if personalized:
                action.content.update(personalized)
        
        return action

    async def _execute_enhanced_action(self, action, trigger: ContactWorkflowTrigger, execution: WorkflowExecution):
        """Execute an enhanced action with full integration."""
        # Use the existing action execution from ContactWorkflowAutomation
        return await self.workflow_automation._execute_action(action, trigger)

    async def _schedule_coordinated_action(self, action, trigger: ContactWorkflowTrigger, execution: WorkflowExecution):
        """Schedule a coordinated action with proper tracking."""
        # Create a more sophisticated scheduled task
        scheduled_task = {
            "title": f"Scheduled Workflow Action: {action.action_type}",
            "description": f"Execute {action.action_type} for {trigger.contact_email}\n\nExecution ID: {execution.execution_id}\nWorkflow Context: {json.dumps(action.content, indent=2)}",
            "business_entity_id": "higherself_entity_id",
            "category": "AUTOMATION",
            "priority": "MEDIUM",
            "source": "WORKFLOW_ORCHESTRATOR",
            "due_date": (datetime.now() + timedelta(hours=action.delay_hours)).date(),
            "workflow_instance_id": execution.execution_id
        }
        
        await self.task_agent.create_task(**scheduled_task)

    def _determine_business_entities_from_types(self, contact_types: List[ContactType]) -> List[BusinessEntity]:
        """Determine business entities from contact types."""
        entities = []
        
        if any(ct in [ContactType.ARTIST, ContactType.GALLERY_CONTACT] for ct in contact_types):
            entities.append(BusinessEntity.THE_7_SPACE)
        
        if any(ct in [ContactType.BUSINESS_CONTACT, ContactType.POTENTIAL_CLIENT] for ct in contact_types):
            entities.append(BusinessEntity.AM_CONSULTING)
        
        entities.append(BusinessEntity.HIGHERSELF_CORE)
        
        return entities

    async def _calculate_execution_metrics(self, execution: WorkflowExecution) -> Dict[str, Any]:
        """Calculate metrics for a workflow execution."""
        duration = (execution.end_time - execution.start_time).total_seconds()
        
        return {
            "execution_duration_seconds": duration,
            "workflows_count": len(execution.workflows_executed),
            "actions_count": sum(len(result.get("results", [])) for result in execution.results),
            "success_rate": len([r for r in execution.results if r.get("status") == "completed"]) / len(execution.results) if execution.results else 0,
            "business_entities": execution.business_entities
        }

    async def _store_execution_record(self, execution: WorkflowExecution):
        """Store execution record in Notion."""
        try:
            execution_data = {
                "Execution ID": {"rich_text": [{"text": {"content": execution.execution_id}}]},
                "Contact ID": {"rich_text": [{"text": {"content": execution.contact_id}}]},
                "Contact Email": {"email": execution.contact_email},
                "Business Entities": {"rich_text": [{"text": {"content": ", ".join(execution.business_entities)}}]},
                "Workflows Executed": {"rich_text": [{"text": {"content": ", ".join(execution.workflows_executed)}}]},
                "Start Time": {"date": {"start": execution.start_time.isoformat()}},
                "End Time": {"date": {"start": execution.end_time.isoformat() if execution.end_time else ""}},
                "Status": {"select": {"name": execution.status.title()}},
                "Results": {"rich_text": [{"text": {"content": json.dumps(execution.results, indent=2)}}]},
                "Metrics": {"rich_text": [{"text": {"content": json.dumps(execution.metrics, indent=2) if execution.metrics else ""}}]}
            }
            
            await self.notion.pages.create(
                parent={"database_id": self.workflows_db_id},
                properties=execution_data
            )
            
        except Exception as e:
            logger.error(f"Error storing execution record: {e}")

    async def get_workflow_analytics(self, days_back: int = 30) -> WorkflowAnalytics:
        """Get comprehensive workflow analytics."""
        try:
            # Calculate date range
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            # Query execution records
            response = await self.notion.databases.query(
                database_id=self.workflows_db_id,
                filter={
                    "property": "Start Time",
                    "date": {"after": start_date}
                }
            )
            
            executions = response.get("results", [])
            
            # Calculate analytics
            total_executions = len(executions)
            successful_executions = len([e for e in executions if self._get_property_value(e, "Status") == "Completed"])
            success_rate = successful_executions / total_executions if total_executions > 0 else 0
            
            # Calculate average execution time
            durations = []
            for execution in executions:
                start_time_str = self._get_property_value(execution, "Start Time")
                end_time_str = self._get_property_value(execution, "End Time")
                if start_time_str and end_time_str:
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    durations.append((end_time - start_time).total_seconds())
            
            avg_execution_time = sum(durations) / len(durations) if durations else 0
            
            return WorkflowAnalytics(
                total_executions=total_executions,
                success_rate=success_rate,
                average_execution_time=avg_execution_time,
                top_performing_workflows=[],  # Would need more complex analysis
                contact_type_breakdown={},  # Would need contact type analysis
                business_entity_performance={},  # Would need entity-specific analysis
                engagement_metrics={}  # Would need engagement tracking
            )
            
        except Exception as e:
            logger.error(f"Error calculating workflow analytics: {e}")
            return WorkflowAnalytics(0, 0.0, 0.0, [], {}, {}, {})

    def _get_property_value(self, page: Dict[str, Any], property_name: str) -> str:
        """Extract property value from Notion page."""
        properties = page.get("properties", {})
        prop = properties.get(property_name, {})
        
        if "rich_text" in prop and prop["rich_text"]:
            return prop["rich_text"][0]["text"]["content"]
        elif "select" in prop and prop["select"]:
            return prop["select"]["name"]
        elif "email" in prop:
            return prop["email"]
        elif "date" in prop and prop["date"]:
            return prop["date"]["start"]
        
        return ""
