#!/usr/bin/env python3
"""
The 7 Space Workflow Automation Service

Automated workflow orchestration service for The 7 Space Art Gallery & Wellness Center.
Handles contact management, gallery operations, wellness center automation, and
integration with the 191 Notion contacts within the multi-entity architecture.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
from dataclasses import dataclass, asdict

from config.the7space.contact_management_config import (
    the7space_contact_manager,
    The7SpaceContactType,
    The7SpaceLeadSource,
    The7SpaceEngagementLevel,
    The7SpaceWorkflowAction,
    The7SpaceWorkflowTemplate
)
from services.notion_service import NotionService
from services.mongodb_service import MongoDBService
from services.redis_service import RedisService
from utils.logging_utils import setup_logger

# Setup logging
logger = setup_logger(__name__)

@dataclass
class WorkflowExecution:
    """Workflow execution tracking"""
    workflow_id: str
    contact_id: str
    template_name: str
    status: str  # "pending", "running", "completed", "failed", "cancelled"
    current_action: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class The7SpaceWorkflowAutomation:
    """
    Comprehensive workflow automation service for The 7 Space.
    
    Manages contact workflows, gallery operations, wellness center automation,
    and integration with the 191 Notion contacts database.
    """
    
    def __init__(self):
        self.business_entity = "the_7_space"
        self.contact_manager = the7space_contact_manager
        
        # Initialize services
        self.notion_service = NotionService()
        self.mongodb_service = MongoDBService()
        self.redis_service = RedisService()
        
        # Workflow execution tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_queue = asyncio.Queue()
        
        # Configuration
        self.config = self.contact_manager.get_automation_config()
        self.max_concurrent_workflows = self.config["processing"]["max_concurrent_workflows"]
        self.batch_size = self.config["processing"]["batch_size"]
        
        logger.info(f"Initialized The 7 Space Workflow Automation for {self.business_entity}")
    
    async def start_automation_engine(self):
        """Start the workflow automation engine"""
        logger.info("Starting The 7 Space workflow automation engine...")
        
        # Start workflow processors
        tasks = []
        for i in range(self.max_concurrent_workflows):
            task = asyncio.create_task(self._workflow_processor(f"processor_{i}"))
            tasks.append(task)
        
        # Start monitoring tasks
        tasks.append(asyncio.create_task(self._contact_monitor()))
        tasks.append(asyncio.create_task(self._workflow_scheduler()))
        tasks.append(asyncio.create_task(self._cleanup_completed_workflows()))
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Workflow automation engine error: {e}")
            raise
    
    async def process_new_contact(self, contact_data: Dict[str, Any]) -> bool:
        """Process a new contact and trigger appropriate workflows"""
        try:
            contact_id = contact_data.get("id") or contact_data.get("contact_id")
            if not contact_id:
                logger.error("Contact ID missing from contact data")
                return False
            
            logger.info(f"Processing new contact: {contact_id}")
            
            # Determine contact segment and workflows
            segment = self.contact_manager.get_contact_segment(contact_data)
            workflows = self.contact_manager.get_workflows_for_contact(contact_data)
            
            logger.info(f"Contact {contact_id} assigned to segment: {segment}")
            logger.info(f"Triggering workflows: {workflows}")
            
            # Store contact in MongoDB
            await self._store_contact_data(contact_id, contact_data, segment)
            
            # Queue workflows for execution
            for workflow_name in workflows:
                await self._queue_workflow(contact_id, workflow_name, contact_data)
            
            # Update analytics
            await self._update_contact_analytics(contact_id, "new_contact", segment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing new contact: {e}")
            return False
    
    async def process_contact_update(self, contact_id: str, update_data: Dict[str, Any]) -> bool:
        """Process contact update and trigger relevant workflows"""
        try:
            logger.info(f"Processing contact update: {contact_id}")
            
            # Get existing contact data
            existing_contact = await self._get_contact_data(contact_id)
            if not existing_contact:
                logger.warning(f"Contact not found for update: {contact_id}")
                return False
            
            # Merge update data
            updated_contact = {**existing_contact, **update_data}
            
            # Check if segment has changed
            old_segment = existing_contact.get("segment")
            new_segment = self.contact_manager.get_contact_segment(updated_contact)
            
            if old_segment != new_segment:
                logger.info(f"Contact {contact_id} segment changed: {old_segment} -> {new_segment}")
                
                # Cancel existing workflows if segment changed significantly
                await self._cancel_contact_workflows(contact_id, "segment_change")
                
                # Queue new workflows for new segment
                new_workflows = self.contact_manager.get_workflows_for_contact(updated_contact)
                for workflow_name in new_workflows:
                    await self._queue_workflow(contact_id, workflow_name, updated_contact)
            
            # Update contact data
            await self._store_contact_data(contact_id, updated_contact, new_segment)
            
            # Update analytics
            await self._update_contact_analytics(contact_id, "contact_update", new_segment)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing contact update: {e}")
            return False
    
    async def trigger_gallery_workflow(self, workflow_type: str, data: Dict[str, Any]) -> bool:
        """Trigger gallery-specific workflows"""
        try:
            logger.info(f"Triggering gallery workflow: {workflow_type}")
            
            if workflow_type == "new_artwork":
                return await self._process_new_artwork(data)
            elif workflow_type == "exhibition_update":
                return await self._process_exhibition_update(data)
            elif workflow_type == "artist_application":
                return await self._process_artist_application(data)
            elif workflow_type == "gallery_visit":
                return await self._process_gallery_visit(data)
            else:
                logger.warning(f"Unknown gallery workflow type: {workflow_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering gallery workflow: {e}")
            return False
    
    async def trigger_wellness_workflow(self, workflow_type: str, data: Dict[str, Any]) -> bool:
        """Trigger wellness center specific workflows"""
        try:
            logger.info(f"Triggering wellness workflow: {workflow_type}")
            
            if workflow_type == "appointment_booking":
                return await self._process_appointment_booking(data)
            elif workflow_type == "class_registration":
                return await self._process_class_registration(data)
            elif workflow_type == "wellness_consultation":
                return await self._process_wellness_consultation(data)
            elif workflow_type == "meditation_session":
                return await self._process_meditation_session(data)
            else:
                logger.warning(f"Unknown wellness workflow type: {workflow_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error triggering wellness workflow: {e}")
            return False
    
    async def get_contact_workflow_status(self, contact_id: str) -> Dict[str, Any]:
        """Get workflow status for a contact"""
        try:
            # Get active workflows for contact
            active_workflows = [
                asdict(workflow) for workflow in self.active_workflows.values()
                if workflow.contact_id == contact_id
            ]
            
            # Get completed workflows from MongoDB
            completed_workflows = await self.mongodb_service.find(
                "workflow_executions",
                {"contact_id": contact_id, "status": {"$in": ["completed", "failed", "cancelled"]}}
            )
            
            return {
                "contact_id": contact_id,
                "active_workflows": active_workflows,
                "completed_workflows": completed_workflows,
                "total_workflows": len(active_workflows) + len(completed_workflows)
            }
            
        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {"error": str(e)}
    
    async def get_automation_analytics(self) -> Dict[str, Any]:
        """Get automation analytics and metrics"""
        try:
            # Get contact statistics
            total_contacts = await self.mongodb_service.count("contacts", {"business_entity": self.business_entity})
            
            # Get workflow statistics
            workflow_stats = await self.mongodb_service.aggregate("workflow_executions", [
                {"$match": {"business_entity": self.business_entity}},
                {"$group": {
                    "_id": "$status",
                    "count": {"$sum": 1}
                }}
            ])
            
            # Get segment distribution
            segment_stats = await self.mongodb_service.aggregate("contacts", [
                {"$match": {"business_entity": self.business_entity}},
                {"$group": {
                    "_id": "$segment",
                    "count": {"$sum": 1}
                }}
            ])
            
            # Get recent activity
            recent_activity = await self.mongodb_service.find(
                "workflow_executions",
                {"business_entity": self.business_entity},
                sort=[("started_at", -1)],
                limit=10
            )
            
            return {
                "total_contacts": total_contacts,
                "target_contacts": 191,
                "workflow_statistics": {item["_id"]: item["count"] for item in workflow_stats},
                "segment_distribution": {item["_id"]: item["count"] for item in segment_stats},
                "active_workflows": len(self.active_workflows),
                "recent_activity": recent_activity,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting automation analytics: {e}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _workflow_processor(self, processor_id: str):
        """Process workflows from the queue"""
        logger.info(f"Starting workflow processor: {processor_id}")
        
        while True:
            try:
                # Get workflow from queue
                workflow_data = await self.workflow_queue.get()
                
                if workflow_data is None:  # Shutdown signal
                    break
                
                # Execute workflow
                await self._execute_workflow(workflow_data)
                
                # Mark task as done
                self.workflow_queue.task_done()
                
            except Exception as e:
                logger.error(f"Workflow processor {processor_id} error: {e}")
                await asyncio.sleep(5)  # Brief pause before continuing
    
    async def _execute_workflow(self, workflow_data: Dict[str, Any]):
        """Execute a single workflow"""
        workflow_id = workflow_data["workflow_id"]
        contact_id = workflow_data["contact_id"]
        template_name = workflow_data["template_name"]
        
        try:
            logger.info(f"Executing workflow {workflow_id} for contact {contact_id}")
            
            # Get workflow template
            template = self.contact_manager.get_workflow_templates().get(template_name)
            if not template:
                logger.error(f"Workflow template not found: {template_name}")
                return
            
            # Create workflow execution record
            execution = WorkflowExecution(
                workflow_id=workflow_id,
                contact_id=contact_id,
                template_name=template_name,
                status="running",
                started_at=datetime.now(),
                metadata=workflow_data.get("metadata", {})
            )
            
            self.active_workflows[workflow_id] = execution
            
            # Execute workflow actions
            for i, action in enumerate(template.actions):
                execution.current_action = i
                
                # Check if workflow should be cancelled
                if execution.status == "cancelled":
                    break
                
                # Apply delay if specified
                if action.delay_hours > 0:
                    await asyncio.sleep(action.delay_hours * 3600)  # Convert hours to seconds
                
                # Execute action
                success = await self._execute_workflow_action(action, contact_id, workflow_data)
                
                if not success:
                    execution.status = "failed"
                    execution.error_message = f"Action {i} failed"
                    break
            
            # Mark workflow as completed if all actions succeeded
            if execution.status == "running":
                execution.status = "completed"
                execution.completed_at = datetime.now()
            
            # Store execution record
            await self._store_workflow_execution(execution)
            
            # Remove from active workflows
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            
            logger.info(f"Workflow {workflow_id} completed with status: {execution.status}")
            
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            
            # Update execution record with error
            if workflow_id in self.active_workflows:
                execution = self.active_workflows[workflow_id]
                execution.status = "failed"
                execution.error_message = str(e)
                execution.completed_at = datetime.now()
                
                await self._store_workflow_execution(execution)
                del self.active_workflows[workflow_id]
    
    async def _execute_workflow_action(self, action: The7SpaceWorkflowAction, contact_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Execute a single workflow action"""
        try:
            logger.info(f"Executing action {action.action_type} for contact {contact_id}")
            
            if action.action_type == "send_email":
                return await self._send_email_action(action, contact_id, workflow_data)
            elif action.action_type == "create_task":
                return await self._create_task_action(action, contact_id, workflow_data)
            elif action.action_type == "schedule_follow_up":
                return await self._schedule_follow_up_action(action, contact_id, workflow_data)
            elif action.action_type == "update_contact":
                return await self._update_contact_action(action, contact_id, workflow_data)
            elif action.action_type == "send_notification":
                return await self._send_notification_action(action, contact_id, workflow_data)
            else:
                logger.warning(f"Unknown action type: {action.action_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {e}")
            return False
    
    async def _queue_workflow(self, contact_id: str, workflow_name: str, contact_data: Dict[str, Any]):
        """Queue a workflow for execution"""
        workflow_id = f"{contact_id}_{workflow_name}_{int(datetime.now().timestamp())}"
        
        workflow_data = {
            "workflow_id": workflow_id,
            "contact_id": contact_id,
            "template_name": workflow_name,
            "contact_data": contact_data,
            "business_entity": self.business_entity,
            "queued_at": datetime.now().isoformat(),
            "metadata": {
                "segment": self.contact_manager.get_contact_segment(contact_data),
                "contact_type": contact_data.get("contact_type"),
                "lead_source": contact_data.get("lead_source")
            }
        }
        
        await self.workflow_queue.put(workflow_data)
        logger.info(f"Queued workflow {workflow_id} for contact {contact_id}")
    
    async def _store_contact_data(self, contact_id: str, contact_data: Dict[str, Any], segment: str):
        """Store contact data in MongoDB"""
        contact_record = {
            "contact_id": contact_id,
            "business_entity": self.business_entity,
            "segment": segment,
            "data": contact_data,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        await self.mongodb_service.upsert(
            "contacts",
            {"contact_id": contact_id, "business_entity": self.business_entity},
            contact_record
        )
    
    async def _get_contact_data(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact data from MongoDB"""
        contact = await self.mongodb_service.find_one(
            "contacts",
            {"contact_id": contact_id, "business_entity": self.business_entity}
        )
        return contact.get("data") if contact else None
    
    async def _store_workflow_execution(self, execution: WorkflowExecution):
        """Store workflow execution record"""
        execution_record = asdict(execution)
        execution_record["business_entity"] = self.business_entity
        
        await self.mongodb_service.insert("workflow_executions", execution_record)
    
    async def _update_contact_analytics(self, contact_id: str, event_type: str, segment: str):
        """Update contact analytics"""
        analytics_record = {
            "contact_id": contact_id,
            "business_entity": self.business_entity,
            "event_type": event_type,
            "segment": segment,
            "timestamp": datetime.now()
        }
        
        await self.mongodb_service.insert("contact_analytics", analytics_record)
    
    async def _contact_monitor(self):
        """Monitor for new contacts from Notion"""
        logger.info("Starting contact monitor...")
        
        while True:
            try:
                # Check for new contacts in Notion
                # This would integrate with the Notion service to detect changes
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Contact monitor error: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _workflow_scheduler(self):
        """Schedule periodic workflow tasks"""
        logger.info("Starting workflow scheduler...")
        
        while True:
            try:
                # Perform scheduled tasks
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Workflow scheduler error: {e}")
                await asyncio.sleep(300)  # Wait before retrying
    
    async def _cleanup_completed_workflows(self):
        """Clean up completed workflow records"""
        logger.info("Starting workflow cleanup task...")
        
        while True:
            try:
                # Clean up old completed workflows
                cutoff_date = datetime.now() - timedelta(days=30)
                
                await self.mongodb_service.delete_many(
                    "workflow_executions",
                    {
                        "business_entity": self.business_entity,
                        "status": {"$in": ["completed", "failed", "cancelled"]},
                        "completed_at": {"$lt": cutoff_date}
                    }
                )
                
                await asyncio.sleep(86400)  # Run daily
                
            except Exception as e:
                logger.error(f"Workflow cleanup error: {e}")
                await asyncio.sleep(3600)  # Wait before retrying
    
    # Action execution methods (simplified implementations)
    
    async def _send_email_action(self, action: The7SpaceWorkflowAction, contact_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Send email action implementation"""
        logger.info(f"Sending email to contact {contact_id}")
        # Implementation would integrate with email service
        return True
    
    async def _create_task_action(self, action: The7SpaceWorkflowAction, contact_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Create task action implementation"""
        logger.info(f"Creating task for contact {contact_id}")
        # Implementation would create task in task management system
        return True
    
    async def _schedule_follow_up_action(self, action: The7SpaceWorkflowAction, contact_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Schedule follow-up action implementation"""
        logger.info(f"Scheduling follow-up for contact {contact_id}")
        # Implementation would schedule follow-up workflow
        return True
    
    async def _update_contact_action(self, action: The7SpaceWorkflowAction, contact_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Update contact action implementation"""
        logger.info(f"Updating contact {contact_id}")
        # Implementation would update contact data
        return True
    
    async def _send_notification_action(self, action: The7SpaceWorkflowAction, contact_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Send notification action implementation"""
        logger.info(f"Sending notification for contact {contact_id}")
        # Implementation would send notification to team
        return True
    
    async def _cancel_contact_workflows(self, contact_id: str, reason: str):
        """Cancel all active workflows for a contact"""
        cancelled_count = 0
        
        for workflow_id, execution in list(self.active_workflows.items()):
            if execution.contact_id == contact_id:
                execution.status = "cancelled"
                execution.error_message = f"Cancelled: {reason}"
                execution.completed_at = datetime.now()
                
                await self._store_workflow_execution(execution)
                del self.active_workflows[workflow_id]
                cancelled_count += 1
        
        if cancelled_count > 0:
            logger.info(f"Cancelled {cancelled_count} workflows for contact {contact_id}: {reason}")
    
    # Gallery workflow implementations
    
    async def _process_new_artwork(self, data: Dict[str, Any]) -> bool:
        """Process new artwork workflow"""
        logger.info("Processing new artwork workflow")
        # Implementation for new artwork processing
        return True
    
    async def _process_exhibition_update(self, data: Dict[str, Any]) -> bool:
        """Process exhibition update workflow"""
        logger.info("Processing exhibition update workflow")
        # Implementation for exhibition updates
        return True
    
    async def _process_artist_application(self, data: Dict[str, Any]) -> bool:
        """Process artist application workflow"""
        logger.info("Processing artist application workflow")
        # Implementation for artist applications
        return True
    
    async def _process_gallery_visit(self, data: Dict[str, Any]) -> bool:
        """Process gallery visit workflow"""
        logger.info("Processing gallery visit workflow")
        # Implementation for gallery visits
        return True
    
    # Wellness workflow implementations
    
    async def _process_appointment_booking(self, data: Dict[str, Any]) -> bool:
        """Process appointment booking workflow"""
        logger.info("Processing appointment booking workflow")
        # Implementation for appointment bookings
        return True
    
    async def _process_class_registration(self, data: Dict[str, Any]) -> bool:
        """Process class registration workflow"""
        logger.info("Processing class registration workflow")
        # Implementation for class registrations
        return True
    
    async def _process_wellness_consultation(self, data: Dict[str, Any]) -> bool:
        """Process wellness consultation workflow"""
        logger.info("Processing wellness consultation workflow")
        # Implementation for wellness consultations
        return True
    
    async def _process_meditation_session(self, data: Dict[str, Any]) -> bool:
        """Process meditation session workflow"""
        logger.info("Processing meditation session workflow")
        # Implementation for meditation sessions
        return True

# Global instance for The 7 Space workflow automation
the7space_workflow_automation = The7SpaceWorkflowAutomation()
