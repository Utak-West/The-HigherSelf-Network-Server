"""
Lead Capture Agent for The HigherSelf Network Server.

This agent is responsible for:
1. Capturing leads from various sources (TypeForm, website forms, etc.)
2. Processing and standardizing lead data
3. Creating workflow instances in Notion for lead follow-up
4. Optionally syncing with HubSpot CRM

All operations follow the Pydantic model framework and maintain proper
logging in the Notion workflow instances.
"""

import os
import json
import hashlib
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
from loguru import logger

from models.base import AgentCapability, ApiPlatform
from models.notion_db_models import WorkflowInstance, BusinessEntity, Workflow
from agents.base_agent import BaseAgent


class TypeformSubmission(BaseModel):
    """Model for a Typeform submission."""
    form_id: str
    response_id: str
    submitted_at: datetime
    answers: Dict[str, Any]


class WebsiteFormSubmission(BaseModel):
    """Model for a generic website form submission."""
    form_id: str
    submission_id: str
    submitted_at: datetime
    fields: Dict[str, Any]


class StandardizedLead(BaseModel):
    """Standardized internal representation of a lead across all sources."""
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    source: str
    source_id: str
    submission_date: datetime
    interests: List[str] = Field(default_factory=list)
    additional_data: Dict[str, Any] = Field(default_factory=dict)
    
    def get_fingerprint(self) -> str:
        """Generate a fingerprint for deduplication based on email and source."""
        data = f"{self.email.lower()}:{self.source}:{self.source_id}"
        return hashlib.md5(data.encode()).hexdigest()


class LeadCaptureAgent(BaseAgent):
    """
    Agent responsible for capturing leads from various sources
    and creating workflow instances in Notion.
    """
    
    def __init__(
        self,
        agent_id: str = "LeadCaptureAgent",
        name: str = "Lead Capture Agent",
        description: str = "Captures leads from various sources and creates workflow instances",
        version: str = "1.0.0",
        business_entities: List[str] = None,
        typeform_api_key: Optional[str] = None,
        hubspot_api_key: Optional[str] = None,
        lead_deduplication_window_hours: int = 24
    ):
        """
        Initialize the Lead Capture Agent.
        
        Args:
            agent_id: Unique identifier
            name: Human-readable name
            description: Agent description
            version: Agent version
            business_entities: Associated business entities
            typeform_api_key: Optional Typeform API key
            hubspot_api_key: Optional HubSpot API key
            lead_deduplication_window_hours: Hours to check for duplicates
        """
        capabilities = [
            AgentCapability.LEAD_PROCESSING,
            AgentCapability.CRM_SYNC,
            AgentCapability.WORKFLOW_MANAGEMENT
        ]
        
        apis_utilized = [
            ApiPlatform.NOTION,
            ApiPlatform.TYPEFORM,
            ApiPlatform.HUBSPOT
        ]
        
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            version=version,
            capabilities=capabilities,
            apis_utilized=apis_utilized,
            business_entities=business_entities
        )
        
        # Set up API credentials
        self.typeform_api_key = typeform_api_key or os.environ.get("TYPEFORM_API_KEY")
        self.hubspot_api_key = hubspot_api_key or os.environ.get("HUBSPOT_API_KEY")
        
        # Set deduplication window
        self.lead_deduplication_window_hours = lead_deduplication_window_hours
        
        self.logger.info("Lead Capture Agent initialized")
    
    async def _typeform_to_standardized_lead(self, submission: TypeformSubmission) -> StandardizedLead:
        """
        Convert a Typeform submission to a standardized lead.
        
        Args:
            submission: TypeformSubmission data
            
        Returns:
            StandardizedLead object
        """
        # Extract fields from answers
        # This would be customized based on the actual form structure
        email = None
        first_name = None
        last_name = None
        phone = None
        interests = []
        additional_data = {}
        
        for field_key, answer in submission.answers.items():
            # Process each answer based on field_key
            # This requires knowledge of your Typeform structure
            if "email" in field_key.lower():
                email = answer
            elif "first_name" in field_key.lower() or "firstname" in field_key.lower():
                first_name = answer
            elif "last_name" in field_key.lower() or "lastname" in field_key.lower():
                last_name = answer
            elif "phone" in field_key.lower():
                phone = answer
            elif "interest" in field_key.lower():
                interests.append(answer)
            else:
                additional_data[field_key] = answer
        
        if not email:
            raise ValueError("Email is required but was not found in the Typeform submission")
            
        return StandardizedLead(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            source="Typeform",
            source_id=submission.response_id,
            submission_date=submission.submitted_at,
            interests=interests,
            additional_data=additional_data
        )
    
    async def _website_form_to_standardized_lead(self, submission: WebsiteFormSubmission) -> StandardizedLead:
        """
        Convert a website form submission to a standardized lead.
        
        Args:
            submission: WebsiteFormSubmission data
            
        Returns:
            StandardizedLead object
        """
        # Extract fields from the submission
        email = submission.fields.get("email")
        first_name = submission.fields.get("first_name")
        last_name = submission.fields.get("last_name")
        phone = submission.fields.get("phone")
        
        interests = []
        if "interests" in submission.fields and isinstance(submission.fields["interests"], list):
            interests = submission.fields["interests"]
        
        # Copy remaining fields to additional_data
        additional_data = {k: v for k, v in submission.fields.items()
                          if k not in ["email", "first_name", "last_name", "phone", "interests"]}
        
        if not email:
            raise ValueError("Email is required but was not found in the website form submission")
            
        return StandardizedLead(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            source="Website",
            source_id=submission.submission_id,
            submission_date=submission.submitted_at,
            interests=interests,
            additional_data=additional_data
        )
    
    async def _check_for_duplicates(self, lead: StandardizedLead) -> Optional[WorkflowInstance]:
        """
        Check if a lead already exists in Notion within the deduplication window.
        
        Args:
            lead: StandardizedLead to check
            
        Returns:
            Existing WorkflowInstance if found, None otherwise
        """
        notion_svc = await self.notion_service
        
        # Calculate the cutoff date for deduplication
        from_date = datetime.now().isoformat()
        
        # Query for existing workflow instances with this email
        # This is a simplified filter and would need to be customized
        # based on the actual Notion database structure
        filter_conditions = {
            "property": "client_lead_email",
            "rich_text": {
                "equals": lead.email.lower()
            }
        }
        
        existing_instances = await notion_svc.query_database(
            WorkflowInstance,
            filter_conditions=filter_conditions
        )
        
        # Check if any match our deduplication criteria
        for instance in existing_instances:
            # Check if it's recent (within our window)
            hours_diff = (datetime.now() - instance.start_date).total_seconds() / 3600
            if hours_diff <= self.lead_deduplication_window_hours:
                # Check if it's from the same source
                if instance.source_system == lead.source:
                    self.logger.info(f"Found duplicate lead: {lead.email} from {lead.source}")
                    return instance
        
        return None
    
    async def _create_workflow_instance(
        self, 
        lead: StandardizedLead,
        business_entity_id: str,
        workflow_id: str
    ) -> WorkflowInstance:
        """
        Create a new workflow instance in Notion for a lead.
        
        Args:
            lead: StandardizedLead data
            business_entity_id: Business entity ID
            workflow_id: Workflow ID to instantiate
            
        Returns:
            Created WorkflowInstance
        """
        notion_svc = await self.notion_service
        
        # Get the workflow definition to determine initial state
        filter_conditions = {
            "property": "workflow_id",
            "rich_text": {
                "equals": workflow_id
            }
        }
        
        workflows = await notion_svc.query_database(
            Workflow,
            filter_conditions=filter_conditions,
            limit=1
        )
        
        if not workflows:
            raise ValueError(f"Workflow with ID {workflow_id} not found")
            
        workflow = workflows[0]
        initial_state = workflow.initial_state
        
        # Create the workflow instance
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            business_entity=business_entity_id,
            current_state=initial_state,
            client_lead_email=lead.email,
            client_lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip(),
            client_lead_phone=lead.phone,
            source_system=lead.source,
            source_record_id=lead.source_id,
            key_data_payload={
                "lead_fingerprint": lead.get_fingerprint(),
                "interests": lead.interests,
                "additional_data": lead.additional_data
            }
        )
        
        # Add initial history entry
        instance.add_history_entry(
            action=f"[{self.agent_id}] Lead captured from {lead.source}",
            details={
                "email": lead.email,
                "source": lead.source,
                "source_id": lead.source_id,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Create the instance in Notion
        instance.page_id = await notion_svc.create_page(instance)
        
        self.logger.info(f"Created workflow instance for lead: {lead.email} in workflow: {workflow_id}")
        
        return instance
    
    async def _sync_lead_to_hubspot(self, lead: StandardizedLead) -> Optional[str]:
        """
        Sync a lead to HubSpot CRM.
        
        Args:
            lead: StandardizedLead to sync
            
        Returns:
            HubSpot contact ID if successful, None otherwise
        """
        if not self.hubspot_api_key:
            self.logger.warning("HubSpot API key not set, skipping sync")
            return None
            
        # This would be implemented using the HubSpot API
        # For now, we'll just log it
        self.logger.info(f"Syncing lead {lead.email} to HubSpot (mock implementation)")
        
        # Return a mock contact ID
        return f"hubspot_{lead.get_fingerprint()}"
    
    async def process_typeform_webhook(
        self, 
        payload: Dict[str, Any],
        business_entity_id: str,
        workflow_id: str,
        sync_to_hubspot: bool = True
    ) -> Dict[str, Any]:
        """
        Process a webhook from Typeform.
        
        Args:
            payload: Webhook payload from Typeform
            business_entity_id: Business entity ID
            workflow_id: Workflow ID to instantiate
            sync_to_hubspot: Whether to sync to HubSpot
            
        Returns:
            Processing result
        """
        self.logger.info(f"Processing Typeform webhook for form: {payload.get('form_id')}")
        
        # Convert payload to TypeformSubmission
        submission = TypeformSubmission(
            form_id=payload.get("form_id"),
            response_id=payload.get("response_id"),
            submitted_at=datetime.fromisoformat(payload.get("submitted_at")),
            answers=payload.get("answers", {})
        )
        
        # Convert to standardized lead
        lead = await self._typeform_to_standardized_lead(submission)
        
        # Check for duplicates
        existing_instance = await self._check_for_duplicates(lead)
        
        if existing_instance:
            self.logger.info(f"Duplicate lead found: {lead.email} - updating existing workflow instance")
            
            # Log the duplicate submission
            await self.log_action(
                workflow_instance=existing_instance,
                action="Received duplicate submission",
                details={
                    "source": "Typeform",
                    "source_id": lead.source_id,
                    "submission_date": lead.submission_date.isoformat()
                }
            )
            
            return {
                "status": "duplicate",
                "message": "Lead already exists",
                "instance_id": existing_instance.instance_id,
                "workflow_id": existing_instance.workflow_id
            }
        
        # Create new workflow instance
        instance = await self._create_workflow_instance(
            lead=lead,
            business_entity_id=business_entity_id,
            workflow_id=workflow_id
        )
        
        # Sync to HubSpot if requested
        hubspot_contact_id = None
        if sync_to_hubspot:
            hubspot_contact_id = await self._sync_lead_to_hubspot(lead)
            
            if hubspot_contact_id:
                # Update the workflow instance with the HubSpot contact ID
                instance.hubspot_contact_id = hubspot_contact_id
                
                notion_svc = await self.notion_service
                await notion_svc.update_page(instance)
                
                await self.log_action(
                    workflow_instance=instance,
                    action="Synced lead to HubSpot",
                    details={"hubspot_contact_id": hubspot_contact_id}
                )
        
        return {
            "status": "success",
            "message": "Lead captured and workflow created",
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "hubspot_contact_id": hubspot_contact_id
        }
    
    async def process_website_form(
        self, 
        form_data: Dict[str, Any],
        form_id: str,
        business_entity_id: str,
        workflow_id: str,
        sync_to_hubspot: bool = True
    ) -> Dict[str, Any]:
        """
        Process a website form submission.
        
        Args:
            form_data: Form submission data
            form_id: Identifier for the form
            business_entity_id: Business entity ID
            workflow_id: Workflow ID to instantiate
            sync_to_hubspot: Whether to sync to HubSpot
            
        Returns:
            Processing result
        """
        self.logger.info(f"Processing website form submission for form: {form_id}")
        
        # Generate a submission ID
        submission_id = f"web_{hashlib.md5(json.dumps(form_data).encode()).hexdigest()}"
        
        # Convert to WebsiteFormSubmission
        submission = WebsiteFormSubmission(
            form_id=form_id,
            submission_id=submission_id,
            submitted_at=datetime.now(),
            fields=form_data
        )
        
        # Convert to standardized lead
        lead = await self._website_form_to_standardized_lead(submission)
        
        # Check for duplicates
        existing_instance = await self._check_for_duplicates(lead)
        
        if existing_instance:
            self.logger.info(f"Duplicate lead found: {lead.email} - updating existing workflow instance")
            
            # Log the duplicate submission
            await self.log_action(
                workflow_instance=existing_instance,
                action="Received duplicate submission",
                details={
                    "source": "Website",
                    "source_id": lead.source_id,
                    "submission_date": lead.submission_date.isoformat()
                }
            )
            
            return {
                "status": "duplicate",
                "message": "Lead already exists",
                "instance_id": existing_instance.instance_id,
                "workflow_id": existing_instance.workflow_id
            }
        
        # Create new workflow instance
        instance = await self._create_workflow_instance(
            lead=lead,
            business_entity_id=business_entity_id,
            workflow_id=workflow_id
        )
        
        # Sync to HubSpot if requested
        hubspot_contact_id = None
        if sync_to_hubspot:
            hubspot_contact_id = await self._sync_lead_to_hubspot(lead)
            
            if hubspot_contact_id:
                # Update the workflow instance with the HubSpot contact ID
                instance.hubspot_contact_id = hubspot_contact_id
                
                notion_svc = await self.notion_service
                await notion_svc.update_page(instance)
                
                await self.log_action(
                    workflow_instance=instance,
                    action="Synced lead to HubSpot",
                    details={"hubspot_contact_id": hubspot_contact_id}
                )
        
        return {
            "status": "success",
            "message": "Lead captured and workflow created",
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "hubspot_contact_id": hubspot_contact_id
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
        if event_type == "typeform_webhook":
            return await self.process_typeform_webhook(
                payload=event_data.get("payload", {}),
                business_entity_id=event_data.get("business_entity_id"),
                workflow_id=event_data.get("workflow_id"),
                sync_to_hubspot=event_data.get("sync_to_hubspot", True)
            )
        elif event_type == "website_form":
            return await self.process_website_form(
                form_data=event_data.get("form_data", {}),
                form_id=event_data.get("form_id"),
                business_entity_id=event_data.get("business_entity_id"),
                workflow_id=event_data.get("workflow_id"),
                sync_to_hubspot=event_data.get("sync_to_hubspot", True)
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
            "typeform_api": False,
            "hubspot_api": False
        }
        
        # Check Notion API
        try:
            notion_svc = await self.notion_service
            # Try to query a database to verify connection
            await notion_svc.query_database(WorkflowInstance, limit=1)
            health_checks["notion_api"] = True
        except Exception as e:
            self.logger.error(f"Notion API health check failed: {e}")
        
        # Check Typeform API (mock check for now)
        if self.typeform_api_key:
            health_checks["typeform_api"] = True
        
        # Check HubSpot API (mock check for now)
        if self.hubspot_api_key:
            health_checks["hubspot_api"] = True
        
        return {
            "agent_id": self.agent_id,
            "status": "healthy" if all(health_checks.values()) else "degraded",
            "checks": health_checks,
            "timestamp": datetime.now().isoformat()
        }
