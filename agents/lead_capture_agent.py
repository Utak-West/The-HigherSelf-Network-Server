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
from pydantic import BaseModel, Field, EmailStr, field_validatorfrom loguru import logger

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

    async def _generic_event_to_standardized_lead(self, event_data: Dict[str, Any]) -> StandardizedLead:
        """
        Convert a generic event (e.g., from Zapier) to a standardized lead.

        Args:
            event_data: Dictionary containing event details. Expected keys include:
                        'email', 'name', 'source_platform', 'event_id', 'details',
                        'ai_insights', 'raw_payload', 'event_name'.
        Returns:
            StandardizedLead object
        """
        email = event_data.get("email")
        if not email:
            raise ValueError("Email is required but was not found in the generic event data")

        full_name = event_data.get("name")
        first_name = None
        last_name = None
        if full_name:
            parts = full_name.split(" ", 1)
            first_name = parts[0]
            if len(parts) > 1:
                last_name = parts[1]

        source = event_data.get("source_platform", "UnknownIntegration")
        source_id = event_data.get("event_id") # This would be the Zapier-provided ID or event-specific ID
        if not source_id:
            # Fallback: Generate a source_id if not provided, using email and timestamp to ensure uniqueness
            timestamp_str = datetime.now().isoformat()
            source_id_data = f"{email.lower()}:{source}:{timestamp_str}"
            source_id = hashlib.md5(source_id_data.encode()).hexdigest()
            logger.warning(f"Generated fallback source_id for generic event: {source_id} for email: {email}")


        # Consolidate various details into additional_data
        additional_data_payload = event_data.get("details", {})
        if event_data.get("ai_insights"):
            additional_data_payload["ai_insights"] = event_data.get("ai_insights")
        if event_data.get("raw_payload"): # Storing the raw payload is good for debugging
            additional_data_payload["raw_payload"] = event_data.get("raw_payload")
        if event_data.get("event_name"):
            additional_data_payload["event_name"] = event_data.get("event_name")
        if event_data.get("integration_source"): # As set in api/server.py
             additional_data_payload["integration_source"] = event_data.get("integration_source")


        # Attempt to extract phone and interests if they exist in 'details'
        # This depends on how Zapier (or the event source) structures the data
        phone = additional_data_payload.pop("phone", event_data.get("phone")) # Check top-level too
        interests_data = additional_data_payload.pop("interests", event_data.get("interests", []))
        
        interests = []
        if isinstance(interests_data, list):
            interests = [str(item) for item in interests_data]
        elif isinstance(interests_data, str) and interests_data:
            interests = [s.strip() for s in interests_data.split(',')] # Handle comma-separated string
        elif interests_data: # If it's some other non-empty type, stringify it
            interests = [str(interests_data)]


        return StandardizedLead(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            source=source, 
            source_id=source_id, 
            submission_date=datetime.now(), # Use current time as submission time for agent processing
            interests=interests,
            additional_data=additional_data_payload
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
        
        # Query for existing workflow instances with this email
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
            # Ensure start_date is offset-aware for comparison if datetime.now() is
            # For simplicity, assuming both are naive or both are aware with same timezone
            if instance.start_date: # Check if start_date is not None
                try:
                    hours_diff = (datetime.now() - instance.start_date).total_seconds() / 3600
                    if hours_diff <= self.lead_deduplication_window_hours:
                        # Check if it's from the same source (or a similar integration source)
                        # This condition might need refinement based on how you want to treat duplicates
                        # from slightly different integration points (e.g. "ZapierEventbrite" vs "Eventbrite")
                        if instance.source_system and lead.source and \
                           (instance.source_system.lower() == lead.source.lower() or \
                            lead.source.lower() in instance.source_system.lower() or \
                            instance.source_system.lower() in lead.source.lower()):
                            self.logger.info(f"Found duplicate lead: {lead.email} from {lead.source} (matches existing {instance.source_system})")
                            return instance
                except TypeError as e:
                    # This can happen if one datetime is naive and the other is aware
                    self.logger.error(f"TypeError during date comparison for duplicate check (lead: {lead.email}): {e}. Instance start_date: {instance.start_date}, now: {datetime.now()}")
                    # Potentially skip this instance or handle timezone conversion
                    continue # Skip this instance if date comparison fails
        
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
        workflow_filter_conditions = {
            "property": "workflow_id",
            "rich_text": {
                "equals": workflow_id
            }
        }
        
        workflows = await notion_svc.query_database(
            Workflow,
            filter_conditions=workflow_filter_conditions, # Corrected variable name
            limit=1
        )
        
        if not workflows:
            raise ValueError(f"Workflow with ID {workflow_id} not found")
            
        workflow = workflows[0]
        initial_state = workflow.initial_state or "New Lead" # Fallback initial state
        
        # Create the workflow instance
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            business_entity=business_entity_id, # Ensure this matches Notion's expected type (e.g., relation or text)
            current_state=initial_state,
            client_lead_email=lead.email,
            client_lead_name=f"{lead.first_name or ''} {lead.last_name or ''}".strip() or lead.email, # Fallback to email if name is empty
            client_lead_phone=lead.phone,
            source_system=lead.source,
            source_record_id=lead.source_id,
            key_data_payload={
                "lead_fingerprint": lead.get_fingerprint(),
                "interests": lead.interests,
                "additional_data": lead.additional_data # This now contains ai_insights, raw_payload etc.
            }
            # Ensure start_date, last_transition_date are handled by Pydantic defaults or set explicitly if needed
        )
        
        # Add initial history entry
        instance.add_history_entry(
            action=f"[{self.agent_id}] Lead captured from {lead.source}",
            details={
                "email": lead.email,
                "source": lead.source,
                "source_id": lead.source_id,
                "submission_timestamp": lead.submission_date.isoformat(), # Use standardized lead's submission_date
                "processing_timestamp": datetime.now().isoformat()
            }
        )
        
        # Create the instance in Notion
        instance.page_id = await notion_svc.create_page(instance)
        
        self.logger.info(f"Created workflow instance (ID: {instance.page_id}) for lead: {lead.email} in workflow: {workflow_id}")
        
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
        """
        self.logger.info(f"Processing Typeform webhook for form: {payload.get('form_id')}")
        
        try:
            submission = TypeformSubmission(
                form_id=payload.get("form_id"),
                response_id=payload.get("response_id"),
                submitted_at=datetime.fromisoformat(payload.get("submitted_at").replace("Z", "+00:00")), # Ensure timezone aware
                answers=payload.get("answers", {})
            )
            lead = await self._typeform_to_standardized_lead(submission)
        except Exception as e:
            self.logger.error(f"Error parsing Typeform submission: {e} - Payload: {payload}")
            return {"status": "error", "message": f"Error parsing Typeform data: {str(e)}"}

        existing_instance = await self._check_for_duplicates(lead)
        if existing_instance:
            self.logger.info(f"Duplicate lead found for Typeform: {lead.email}")
            await self.log_action(
                workflow_instance=existing_instance,
                action="Received duplicate Typeform submission",
                details={"source_id": lead.source_id, "submission_date": lead.submission_date.isoformat()}
            )
            return {
                "status": "duplicate",
                "message": "Lead already exists",
                "instance_id": existing_instance.instance_id
            }
        
        instance = await self._create_workflow_instance(lead, business_entity_id, workflow_id)
        
        hubspot_contact_id = None
        if sync_to_hubspot:
            hubspot_contact_id = await self._sync_lead_to_hubspot(lead)
            if hubspot_contact_id:
                instance.hubspot_contact_id = hubspot_contact_id
                notion_svc = await self.notion_service
                await notion_svc.update_page(instance) # Save HubSpot ID to Notion
                await self.log_action(
                    workflow_instance=instance,
                    action="Synced lead to HubSpot",
                    details={"hubspot_contact_id": hubspot_contact_id}
                )
        
        return {
            "status": "success",
            "message": "Lead captured and workflow created",
            "instance_id": instance.page_id, # Use page_id from Notion
            "workflow_id": instance.workflow_id,
            "hubspot_contact_id": hubspot_contact_id
        }

    async def process_generic_event_registration(
        self,
        event_data: Dict[str, Any], # This is the event_data_for_agent from api/server.py
    ) -> Dict[str, Any]:
        """
        Process a generic event registration (e.g., from Zapier).
        """
        self.logger.info(f"Processing generic event registration from: {event_data.get('source_platform', 'Unknown Source')} for: {event_data.get('email')}")

        business_entity_id = event_data.get("business_entity_id")
        workflow_id = event_data.get("workflow_id")
        sync_to_hubspot = event_data.get("sync_to_hubspot", True)

        if not business_entity_id or not workflow_id:
            msg = "Missing business_entity_id or workflow_id for generic_event_registration."
            self.logger.error(msg)
            return {"status": "error", "message": msg}

        try:
            lead = await self._generic_event_to_standardized_lead(event_data)
        except ValueError as e:
            self.logger.error(f"Error standardizing generic event lead: {e}")
            return {"status": "error", "message": str(e)}
        
        existing_instance = await self._check_for_duplicates(lead)
        if existing_instance:
            self.logger.info(f"Duplicate lead found for generic event: {lead.email}")
            await self.log_action(
                workflow_instance=existing_instance,
                action="Received duplicate submission from generic event",
                details={"source": lead.source, "source_id": lead.source_id, "submission_date": lead.submission_date.isoformat()}
            )
            return {
                "status": "duplicate",
                "message": "Lead already exists",
                "instance_id": existing_instance.instance_id # Should be page_id
            }
        
        instance = await self._create_workflow_instance(lead, business_entity_id, workflow_id)
        
        hubspot_contact_id = None
        if sync_to_hubspot:
            hubspot_contact_id = await self._sync_lead_to_hubspot(lead)
            if hubspot_contact_id:
                instance.hubspot_contact_id = hubspot_contact_id
                notion_svc = await self.notion_service
                await notion_svc.update_page(instance)
                await self.log_action(
                    workflow_instance=instance,
                    action="Synced lead to HubSpot from generic event",
                    details={"hubspot_contact_id": hubspot_contact_id}
                )
        
        return {
            "status": "success",
            "message": "Generic event lead captured and workflow created",
            "instance_id": instance.page_id, # Use page_id from Notion
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
        """
        self.logger.info(f"Processing website form submission for form: {form_id}")
        
        submission_id = f"web_{hashlib.md5(json.dumps(form_data, sort_keys=True).encode()).hexdigest()}" # Sort keys for consistency
        
        try:
            submission = WebsiteFormSubmission(
                form_id=form_id,
                submission_id=submission_id,
                submitted_at=datetime.now(), # Consistent submission time
                fields=form_data
            )
            lead = await self._website_form_to_standardized_lead(submission)
        except Exception as e:
            self.logger.error(f"Error parsing website form submission: {e} - Data: {form_data}")
            return {"status": "error", "message": f"Error parsing website form data: {str(e)}"}
            
        existing_instance = await self._check_for_duplicates(lead)
        if existing_instance:
            self.logger.info(f"Duplicate lead found for website form: {lead.email}")
            await self.log_action(
                workflow_instance=existing_instance,
                action="Received duplicate website form submission",
                details={"source_id": lead.source_id, "submission_date": lead.submission_date.isoformat()}
            )
            return {
                "status": "duplicate",
                "message": "Lead already exists",
                "instance_id": existing_instance.instance_id # Should be page_id
            }
        
        instance = await self._create_workflow_instance(lead, business_entity_id, workflow_id)
        
        hubspot_contact_id = None
        if sync_to_hubspot:
            hubspot_contact_id = await self._sync_lead_to_hubspot(lead)
            if hubspot_contact_id:
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
            "instance_id": instance.page_id, # Use page_id from Notion
            "workflow_id": instance.workflow_id,
            "hubspot_contact_id": hubspot_contact_id
        }
    
    async def process_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main event processing method for the Lead Capture Agent.
        Routes events to specific handlers based on event_type.
        """
        self.logger.info(f"LeadCaptureAgent received event: {event_type} with data: {event_data}")

        if not event_type or not event_data:
            self.logger.error("Event type or event data missing")
            return {"status": "error", "message": "Event type or event data missing"}

        try:
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
            elif event_type == "generic_event_registration":
                # The event_data itself is the direct payload for this new handler
                return await self.process_generic_event_registration(event_data=event_data)
            else:
                self.logger.warning(f"Unhandled event type in LeadCaptureAgent: {event_type}")
                return {"status": "error", "message": f"Unhandled event type: {event_type}"}
        except Exception as e:
            self.logger.exception(f"Error processing event in LeadCaptureAgent ({event_type}): {e}")
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

    async def check_health(self) -> Dict[str, Any]:
        """
        Check the health status of this agent.
        
        Returns:
            Health check result
        """
        health_checks = {
            "notion_api": False,
            "typeform_api": False, # Assuming this is for specific Typeform interactions if API key used
            "hubspot_api": False  # Assuming this is for specific HubSpot interactions if API key used
        }
        
        # Check Notion API
        try:
            notion_svc = await self.notion_service
            # A lightweight check, e.g., retrieving a known small database or page
            # For now, we'll assume if notion_service getter works, basic connectivity is there.
            # A more robust check would involve a minimal, non-mutating API call.
            if notion_svc and notion_svc.client: # Basic check
                 health_checks["notion_api"] = True
            # Consider: await notion_svc.query_database(WorkflowInstance, limit=1)
            # This was in the original, but might be too heavy for a quick health check if DB is large.
            # Let's try a lighter check if possible or rely on initialization.
        except Exception as e:
            self.logger.error(f"Notion API health check failed: {e}")
        
        # Typeform & HubSpot are typically outbound from this agent if specific methods are called
        # Their "health" in this context might mean API keys are present.
        if self.typeform_api_key:
            health_checks["typeform_api"] = True # Indicates capability is configured
        
        if self.hubspot_api_key:
            health_checks["hubspot_api"] = True # Indicates capability is configured
        
        # Overall health depends primarily on Notion as it's the core data store
        overall_status = "healthy" if health_checks["notion_api"] else "unhealthy"
        if overall_status == "healthy" and not (health_checks["typeform_api"] and health_checks["hubspot_api"]):
            # If Notion is fine, but other optional integrations aren't fully configured, it's 'degraded'
            # This depends on how critical these are. For now, if keys are missing, it's just not using them.
            pass # Or set to degraded if those keys being missing is a problem

        return {
            "agent_id": self.agent_id,
            "status": overall_status,
            "checks": health_checks,
            "timestamp": datetime.now().isoformat()
        }
