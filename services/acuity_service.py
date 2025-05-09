"""
Acuity Scheduling integration service for The HigherSelf Network Server.
This service handles integration with Acuity Scheduling while maintaining Notion as the central hub.
"""

import os
import json
import base64
import aiohttp
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta
from loguru import logger
from pydantic import BaseModel, Field, validator

from services.base_service import BaseService, ServiceCredentials


class AcuityCredentials(ServiceCredentials):
    """Credentials for Acuity Scheduling API integration."""
    user_id: str
    api_key: str
    base_url: str = "https://acuityscheduling.com/api/v1"
    
    class Config:
        env_prefix = "ACUITY_"
    
    @validator('user_id', 'api_key')
    def validate_required_fields(cls, v):
        if not v:
            raise ValueError("This field is required")
        return v


class AcuityAppointment(BaseModel):
    """Model representing an Acuity Scheduling appointment."""
    id: Optional[int] = None
    calendar_id: int
    appointment_type_id: int
    datetime: datetime
    end_time: Optional[datetime] = None
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    end_time_string: Optional[str] = None
    time_zone: str
    paid: Optional[bool] = None
    amount_paid: Optional[float] = None
    price: Optional[float] = None
    type: str
    location: Optional[str] = None
    canceled: bool = False
    calendar: Optional[str] = None
    notes: Optional[str] = None
    forms: List[Dict[str, Any]] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    certificate: Optional[str] = None
    confirmation_page: Optional[str] = None
    confirmation_email: Optional[str] = None
    notion_page_id: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if not v or '@' not in v:
            raise ValueError("Valid email is required")
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if not v:
            raise ValueError("Name fields cannot be empty")
        return v


class AcuityService(BaseService):
    """
    Service for interacting with Acuity Scheduling.
    Ensures all scheduling data is synchronized with Notion as the central hub.
    """
    
    def __init__(self, user_id: str = None, api_key: str = None, base_url: str = None):
        """
        Initialize the Acuity Scheduling service.
        
        Args:
            user_id: Acuity Scheduling User ID
            api_key: Acuity Scheduling API Key
            base_url: Base URL for the Acuity API
        """
        # Get credentials from environment if not provided
        user_id = user_id or os.environ.get("ACUITY_USER_ID")
        api_key = api_key or os.environ.get("ACUITY_API_KEY")
        base_url = base_url or os.environ.get("ACUITY_BASE_URL", "https://acuityscheduling.com/api/v1")
        
        # Create credentials object
        credentials = None
        if user_id and api_key:
            credentials = AcuityCredentials(
                service_name="acuity",
                user_id=user_id,
                api_key=api_key,
                base_url=base_url
            )
        
        # Initialize base service
        super().__init__(service_name="acuity", credentials=credentials)
        
        # Specific Acuity properties
        self.user_id = user_id
        self.api_key = api_key
        self.base_url = base_url
        
        if not self.user_id or not self.api_key:
            logger.warning("Acuity Scheduling credentials not fully configured")
    
    def _get_auth_header(self) -> Dict[str, str]:
        """
        Generate the Authorization header for Acuity API requests.
        
        Returns:
            Dictionary containing the Authorization header
        """
        if not self.user_id or not self.api_key:
            raise ValueError("Acuity credentials not configured")
            
        auth_string = f"{self.user_id}:{self.api_key}"
        auth_bytes = auth_string.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {"Authorization": f"Basic {auth_b64}"}
    
    async def validate_credentials(self) -> bool:
        """
        Validate the Acuity Scheduling API credentials.
        
        Returns:
            True if credentials are valid, False otherwise
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return False
        
        try:
            # Use base service async request with retry logic
            url = f"{self.base_url}/me"
            headers = self._get_auth_header()
            
            await self.async_get(url, headers=headers)
            
            # Update credentials verification timestamp
            if self.credentials:
                self.credentials.last_verified = datetime.now()
                
            logger.info("Acuity Scheduling credentials validated successfully")
            return True
        except Exception as e:
            logger.error(f"Invalid Acuity Scheduling credentials: {e}")
            return False
    
    async def get_appointment_types(self) -> List[Dict[str, Any]]:
        """
        Get all appointment types configured in Acuity.
        
        Returns:
            List of appointment type dictionaries
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return []
        
        try:
            url = f"{self.base_url}/appointment-types"
            headers = self._get_auth_header()
            
            # Use base service async request with retry logic
            appointment_types = await self.async_get(url, headers=headers)
            
            logger.info(f"Retrieved {len(appointment_types)} appointment types from Acuity")
            return appointment_types
        except Exception as e:
            logger.error(f"Error getting appointment types: {e}")
            return []
    
    async def get_calendars(self) -> List[Dict[str, Any]]:
        """
        Get all calendars configured in Acuity.
        
        Returns:
            List of calendar dictionaries
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return []
        
        try:
            url = f"{self.base_url}/calendars"
            headers = self._get_auth_header()
            
            # Use async request with retry logic
            calendars = await self.async_get(url, headers=headers)
            
            logger.info(f"Retrieved {len(calendars)} calendars from Acuity")
            return calendars
        except Exception as e:
            logger.error(f"Error getting calendars: {e}")
            return []
    
    async def get_appointment(self, appointment_id: int) -> Optional[AcuityAppointment]:
        """
        Get a specific appointment by ID.
        
        Args:
            appointment_id: Acuity appointment ID
            
        Returns:
            AcuityAppointment if found, None otherwise
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return None
        
        try:
            url = f"{self.base_url}/appointments/{appointment_id}"
            headers = self._get_auth_header()
            
            # Use async request with retry logic
            appointment_data = await self.async_get(url, headers=headers)
            
            # Parse the appointment data
            appointment = AcuityAppointment(
                id=appointment_data.get("id"),
                calendar_id=appointment_data.get("calendarID"),
                appointment_type_id=appointment_data.get("appointmentTypeID"),
                datetime=datetime.fromisoformat(appointment_data.get("datetime").replace("Z", "+00:00")),
                first_name=appointment_data.get("firstName", ""),
                last_name=appointment_data.get("lastName", ""),
                email=appointment_data.get("email", ""),
                phone=appointment_data.get("phone"),
                date=appointment_data.get("date"),
                time=appointment_data.get("time"),
                end_time_string=appointment_data.get("endTime"),
                time_zone=appointment_data.get("timezone", "UTC"),
                paid=appointment_data.get("paid"),
                amount_paid=appointment_data.get("amountPaid"),
                price=appointment_data.get("price"),
                type=appointment_data.get("type", ""),
                location=appointment_data.get("location"),
                canceled=appointment_data.get("canceled", False),
                calendar=appointment_data.get("calendar"),
                notes=appointment_data.get("notes"),
                forms=appointment_data.get("forms", []),
                labels=appointment_data.get("labels", []),
                certificate=appointment_data.get("certificate"),
                confirmation_page=appointment_data.get("confirmationPage"),
                confirmation_email=appointment_data.get("confirmationEmail")
            )
            
            # Check for custom fields that might contain Notion page ID
            if "forms" in appointment_data:
                for form in appointment_data["forms"]:
                    for field in form.get("values", []):
                        if field.get("fieldID") == "notion_page_id" or field.get("name") == "Notion Page ID":
                            appointment.notion_page_id = field.get("value")
            
            # Calculate end time if not provided
            if not appointment.end_time and appointment.datetime:
                # Default to 1 hour if we can't determine the duration
                duration = 60
                for apt_type in await self.get_appointment_types():
                    if apt_type.get("id") == appointment.appointment_type_id:
                        duration = apt_type.get("duration", 60)
                        break
                
                appointment.end_time = appointment.datetime + timedelta(minutes=duration)
            
            logger.info(f"Retrieved Acuity appointment: {appointment_id}")
            return appointment
        except Exception as e:
            logger.error(f"Error getting appointment {appointment_id}: {e}")
            return None
    
    async def get_appointments(self, min_date: datetime = None, max_date: datetime = None) -> List[AcuityAppointment]:
        """
        Get appointments within a date range.
        
        Args:
            min_date: Optional start date for the range
            max_date: Optional end date for the range
            
        Returns:
            List of AcuityAppointment objects
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return []
        
        try:
            url = f"{self.base_url}/appointments"
            headers = self._get_auth_header()
            params = {}
            
            if min_date:
                params["minDate"] = min_date.strftime("%Y-%m-%d")
            
            if max_date:
                params["maxDate"] = max_date.strftime("%Y-%m-%d")
            
            # Use async request with retry logic
            appointments_data = await self.async_get(url, headers=headers, params=params)
            appointments = []
            
            for data in appointments_data:
                try:
                    # Parse the appointment data
                    appointment = AcuityAppointment(
                        id=data.get("id"),
                        calendar_id=data.get("calendarID"),
                        appointment_type_id=data.get("appointmentTypeID"),
                        datetime=datetime.fromisoformat(data.get("datetime").replace("Z", "+00:00")),
                        first_name=data.get("firstName", ""),
                        last_name=data.get("lastName", ""),
                        email=data.get("email", ""),
                        phone=data.get("phone"),
                        date=data.get("date"),
                        time=data.get("time"),
                        end_time_string=data.get("endTime"),
                        time_zone=data.get("timezone", "UTC"),
                        paid=data.get("paid"),
                        amount_paid=data.get("amountPaid"),
                        price=data.get("price"),
                        type=data.get("type", ""),
                        location=data.get("location"),
                        canceled=data.get("canceled", False),
                        calendar=data.get("calendar"),
                        notes=data.get("notes"),
                        forms=data.get("forms", []),
                        labels=data.get("labels", []),
                        certificate=data.get("certificate"),
                        confirmation_page=data.get("confirmationPage"),
                        confirmation_email=data.get("confirmationEmail")
                    )
                    
                    # Check for custom fields that might contain Notion page ID
                    if "forms" in data:
                        for form in data["forms"]:
                            for field in form.get("values", []):
                                if field.get("fieldID") == "notion_page_id" or field.get("name") == "Notion Page ID":
                                    appointment.notion_page_id = field.get("value")
                    
                    appointments.append(appointment)
                except Exception as e:
                    logger.error(f"Error parsing appointment data: {e}")
            
            logger.info(f"Retrieved {len(appointments)} appointments from Acuity")
            return appointments
        except Exception as e:
            logger.error(f"Error getting appointments: {e}")
            return []
    
    async def create_appointment(self, appointment: AcuityAppointment) -> Optional[int]:
        """
        Create a new appointment in Acuity.
        
        Args:
            appointment: AcuityAppointment model with appointment details
            
        Returns:
            Appointment ID if successful, None otherwise
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return None
        
        try:
            # Validate appointment data first
            self.validate_model(appointment)
            
            url = f"{self.base_url}/appointments"
            headers = self._get_auth_header()
            
            # Prepare appointment data
            payload = {
                "appointmentTypeID": appointment.appointment_type_id,
                "calendarID": appointment.calendar_id,
                "datetime": appointment.datetime.isoformat(),
                "firstName": appointment.first_name,
                "lastName": appointment.last_name,
                "email": appointment.email
            }
            
            if appointment.phone:
                payload["phone"] = appointment.phone
            
            if appointment.notes:
                payload["notes"] = appointment.notes
            
            # Add custom fields for Notion integration if provided
            if appointment.notion_page_id:
                if "fields" not in payload:
                    payload["fields"] = []
                
                payload["fields"].append({
                    "id": "notion_page_id",  # This ID must exist in Acuity's custom field configuration
                    "value": appointment.notion_page_id
                })
            
            # Use async request with retry logic
            data = await self.async_post(url, json_data=payload, headers=headers)
            
            appointment_id = data.get("id")
            logger.info(f"Created Acuity appointment: {appointment_id}")
            return appointment_id
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error creating appointment: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return None
    
    async def update_appointment(self, appointment_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing appointment in Acuity.
        
        Args:
            appointment_id: Acuity appointment ID
            update_data: Dictionary of fields to update
            
        Returns:
            True if update successful, False otherwise
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return False
        
        try:
            url = f"{self.base_url}/appointments/{appointment_id}"
            headers = self._get_auth_header()
            
            # Use async request with retry logic
            await self.async_put(url, json_data=update_data, headers=headers)
            
            logger.info(f"Updated Acuity appointment: {appointment_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating appointment {appointment_id}: {e}")
            return False
    
    async def cancel_appointment(self, appointment_id: int, cancellation_reason: str = None) -> bool:
        """
        Cancel an appointment in Acuity.
        
        Args:
            appointment_id: Acuity appointment ID
            cancellation_reason: Optional reason for cancellation
            
        Returns:
            True if cancellation successful, False otherwise
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return False
        
        try:
            url = f"{self.base_url}/appointments/{appointment_id}/cancel"
            headers = self._get_auth_header()
            headers["Content-Type"] = "application/json"
            
            payload = {}
            if cancellation_reason:
                payload["cancelNote"] = cancellation_reason
            
            response = requests.put(url, headers=headers, json=payload)
            response.raise_for_status()
            
            logger.info(f"Cancelled Acuity appointment: {appointment_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}")
            return False
    
    async def reschedule_appointment(self, appointment_id: int, new_datetime: datetime) -> bool:
        """
        Reschedule an appointment in Acuity.
        
        Args:
            appointment_id: Acuity appointment ID
            new_datetime: New date and time for the appointment
            
        Returns:
            True if rescheduling successful, False otherwise
        """
        return await self.update_appointment(appointment_id, {"datetime": new_datetime.isoformat()})
    
    async def get_available_times(self, appointment_type_id: int, date: datetime) -> List[Dict[str, Any]]:
        """
        Get available time slots for a specific appointment type and date.
        
        Args:
            appointment_type_id: Acuity appointment type ID
            date: Date to check for availability
            
        Returns:
            List of available time slots
        """
        if not self.user_id or not self.api_key:
            logger.error("Acuity Scheduling credentials not configured")
            return []
        
        try:
            url = f"{self.base_url}/availability/times"
            headers = self._get_auth_header()
            
            params = {
                "appointmentTypeID": appointment_type_id,
                "date": date.strftime("%Y-%m-%d")
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            availability = response.json()
            logger.info(f"Retrieved {len(availability)} available time slots for appointment type {appointment_type_id}")
            return availability
        except Exception as e:
            logger.error(f"Error getting available times: {e}")
            return []
    
    async def sync_appointment_to_notion(self, appointment_id: int, notion_page_id: str) -> bool:
        """
        Update an Acuity appointment with its associated Notion page ID.
        This is done through custom fields in Acuity.
        
        Args:
            appointment_id: Acuity appointment ID
            notion_page_id: Notion page ID
            
        Returns:
            True if sync successful, False otherwise
        """
        try:
            # First, get the current appointment to check if it has custom fields
            appointment = await self.get_appointment(appointment_id)
            if not appointment:
                logger.error(f"Could not find appointment {appointment_id} to sync with Notion")
                return False
            
            # Add or update custom fields to store Notion page ID
            # NOTE: This assumes a custom field has been created in Acuity with ID "notion_page_id"
            update_data = {
                "fields": [
                    {
                        "id": "notion_page_id",
                        "value": notion_page_id
                    }
                ]
            }
            
            # Also update the notes field to include the Notion link
            notes = appointment.notes or ""
            if "Notion Page:" not in notes:
                notion_link = f"Notion Page: https://notion.so/{notion_page_id.replace('-', '')}"
                if notes:
                    notes += f"\n\n{notion_link}"
                else:
                    notes = notion_link
                
                update_data["notes"] = notes
            
            # Update the appointment
            return await self.update_appointment(appointment_id, update_data)
        except Exception as e:
            logger.error(f"Error syncing appointment {appointment_id} to Notion: {e}")
            return False
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> Optional[AcuityAppointment]:
        """
        Process a webhook notification from Acuity Scheduling.
        
        Args:
            webhook_data: Webhook payload data
            
        Returns:
            AcuityAppointment if valid, None otherwise
        """
        try:
            # Validate webhook data
            if "id" not in webhook_data or "action" not in webhook_data:
                logger.error("Invalid Acuity webhook data: missing required fields")
                return None
            
            # Get the appointment details
            appointment_id = webhook_data.get("id")
            appointment = await self.get_appointment(appointment_id)
            
            if not appointment:
                logger.error(f"Could not retrieve appointment {appointment_id} from webhook")
                return None
            
            action = webhook_data.get("action")
            logger.info(f"Processed Acuity webhook: {action} for appointment {appointment_id}")
            
            return appointment
        except Exception as e:
            logger.error(f"Error processing Acuity webhook: {e}")
            return None
